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

load_dotenv()

app = FastAPI()

# 1. Serve Static Files (CSS/JS/HTML)
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- GEMINI CONFIG ---
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# Use 2.5 Flash or Flash Latest
model = genai.GenerativeModel('gemini-2.5-flash')

# Ensure DB tables exist
Base.metadata.create_all(bind=engine)

# --- HELPER: AI SUMMARIZER ---
def generate_summary(text):
    # Rate Limiting: Sleep 2s to avoid hitting free tier limits
    time.sleep(2)
    
    try:
        prompt = f"""
        You are a news editor. 
        1. Summarize this text in one concise sentence.
        2. Classify sentiment as Positive, Negative, or Neutral.
        Format: SUMMARY | SENTIMENT
        Text: {text}
        """
        response = model.generate_content(prompt)
        content = response.text.strip()
        
        if "|" in content:
            summary, sentiment = content.split("|", 1)
            return summary.strip(), sentiment.strip()
        return content, "Neutral"
    except Exception as e:
        print(f"AI Error: {e}")
        return "Summary unavailable", "Neutral"

# --- ROUTES ---

# Serve the Frontend
@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.post("/scrape")
def scrape_news(db: Session = Depends(get_db)):
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="NewsAPI Key missing")
    
    # Categories to scrape
    categories = ["technology", "business", "science"]
    total_scraped = 0
    
    for category in categories:
        print(f"Fetching {category} news...")
        url = f"https://newsapi.org/v2/top-headlines?category={category}&language=en&apiKey={api_key}"
        
        try:
            resp = requests.get(url)
            data = resp.json()
            articles = data.get("articles", [])[:4] # Limit 4 per category (12 total)
            
            for article in articles:
                # Validation
                if not article.get('title') or not article.get('description'):
                    continue
                
                # Duplicate Check
                existing = db.query(NewsItem).filter(NewsItem.url == article['url']).first()
                if existing:
                    continue

                # AI Process
                raw_text = f"{article['title']} - {article['description']}"
                summary, sentiment = generate_summary(raw_text)
                
                # Save
                news_item = NewsItem(
                    title=article['title'],
                    url=article['url'],
                    summary=summary,
                    sentiment_score=sentiment
                )
                db.add(news_item)
                db.commit()
                total_scraped += 1
                
        except Exception as e:
            print(f"Error scraping {category}: {e}")
            continue

    return {"message": f"Scraped {total_scraped} new articles across categories."}

@app.get("/news")
def get_news(db: Session = Depends(get_db)):
    # Return top 20 latest news
    return db.query(NewsItem).order_by(NewsItem.id.desc()).limit(20).all()