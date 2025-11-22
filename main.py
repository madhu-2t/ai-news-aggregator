import os
import time
import requests
import google.generativeai as genai
from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db
from models import NewsItem, Base, engine
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from dateutil import parser 

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- CONFIG ---
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

Base.metadata.create_all(bind=engine)

def generate_financial_summary(text):
    # time.sleep(2) # Uncomment this if you see "429 Resource Exhausted" errors
    try:
        # Check if key is present
        if not os.getenv("GEMINI_API_KEY"):
            print("❌ ERROR: GEMINI_API_KEY is missing from environment variables!")
            return "System Error: Missing API Key", "Neutral"

        prompt = f"""
        You are a Financial Analyst. 
        1. Summarize this in 1 sentence.
        2. Sentiment: Bullish, Bearish, or Neutral.
        Format: SUMMARY | SENTIMENT
        News: {text}
        """
        
        # Explicitly use 1.5-flash
        response = model.generate_content(prompt)
        
        # Check if response was blocked by safety filters
        if not response.text:
            print(f"⚠️ Gemini blocked content for safety: {response.prompt_feedback}")
            return "Content filtered by AI", "Neutral"

        content = response.text.strip()
        if "|" in content:
            return content.split("|", 1)
        return content, "Neutral"
        
    except Exception as e:
        # THIS IS THE CRITICAL PART - PRINT THE ERROR
        print(f"🔥 AI CRASH: {str(e)}") 
        return f"Analysis Failed: {str(e)[:20]}...", "Neutral"
# --- ROUTES ---

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.post("/scrape")
def scrape_finance(db: Session = Depends(get_db)):
    api_key = os.getenv("NEWS_API_KEY")
    
    # --- 1. CALCULATE TIME THRESHOLD ---
    # Check the newest article in our DB
    last_news = db.query(NewsItem).order_by(NewsItem.published_at.desc()).first()
    
    today_midnight = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    if last_news and last_news.published_at:
        # If we have data, fetch everything PUBLISHED AFTER the last one
        # We add 1 second to avoid fetching the exact same article again
        last_time = last_news.published_at.replace(tzinfo=timezone.utc)
        from_param = (last_time + timedelta(seconds=1)).isoformat()
        print(f"🔄 Fetching global news newer than: {last_time}")
    else:
        # If DB is empty, fetch from TODAY 00:00
        from_param = today_midnight.isoformat()
        print(f"🆕 First run: Fetching global news from: {today_midnight}")

    # --- 2. GLOBAL SEARCH QUERY ---
    # searching for broad financial terms
    query = "finance OR stock market OR economy OR business"
    
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={query}&"
        f"from={from_param}&"
        f"sortBy=publishedAt&" # Important: Get Newest First
        f"language=en&"
        f"apiKey={api_key}"
    )

    try:
        resp = requests.get(url)
        data = resp.json()
        
        if data.get("status") != "ok":
            print(f"API Error: {data.get('message')}")
            return {"message": "Error from NewsAPI"}

        # The API might return thousands of results. 
        # We limit processing to the top 15 newest to save AI credits and speed.
        articles = data.get("articles", [])[:15]
        
        # Reverse list to add Oldest -> Newest (keeps DB ID order logical)
        articles.reverse() 

        count = 0
        for article in articles: 
            if not article.get('title'): continue
            
            # Parse Date
            try:
                pub_date = parser.parse(article['publishedAt'])
            except:
                continue

            # Check Duplicate URL
            if db.query(NewsItem).filter(NewsItem.url == article['url']).first():
                continue

            print(f"   + Processing: {article['title'][:40]}...")

            # AI Analysis
            raw = f"{article['title']} - {article.get('description', '')}"
            summary, sentiment = generate_financial_summary(raw)

            news_item = NewsItem(
                title=article['title'],
                url=article['url'],
                summary=summary.strip(),
                sentiment_score=sentiment.strip(),
                published_at=pub_date
            )
            db.add(news_item)
            count += 1
        
        db.commit() 

        if count == 0:
            return {"message": "No new global financial news found since last check."}
        
        return {"message": f"Scraped {count} new global articles!"}

    except Exception as e:
        return {"message": f"System Error: {str(e)}"}

@app.get("/news")
def get_news(db: Session = Depends(get_db)):
    # Return newest first
    return db.query(NewsItem).order_by(NewsItem.published_at.desc()).limit(50).all()