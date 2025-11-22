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

# 1. Serve Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- GEMINI CONFIG ---
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

Base.metadata.create_all(bind=engine)

# --- HELPER: FINANCIAL ANALYST AI ---
def generate_financial_summary(text):
    time.sleep(2) # Rate limiting
    
    try:
        # Specialized prompt for finance
        prompt = f"""
        You are a Senior Financial Analyst. 
        1. Analyze this news for market impact. Summarize in 1 sharp sentence.
        2. Classify sentiment strictly as: Bullish, Bearish, or Neutral.
        
        Format: SUMMARY | SENTIMENT
        News: {text}
        """
        response = model.generate_content(prompt)
        content = response.text.strip()
        
        if "|" in content:
            summary, sentiment = content.split("|", 1)
            return summary.strip(), sentiment.strip()
        return content, "Neutral"
    except Exception as e:
        print(f"AI Error: {e}")
        return "Analysis pending...", "Neutral"

# --- ROUTES ---

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.post("/scrape")
def scrape_finance(db: Session = Depends(get_db)):
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="NewsAPI Key missing")
    
    # STRATEGY: Mix of Indian and Global Markets
    sources = [
        {"country": "in", "category": "business", "label": "🇮🇳 India Market"},
        {"country": "us", "category": "business", "label": "🇺🇸 US Market"}
    ]
    
    total_scraped = 0
    
    for source in sources:
        print(f"Fetching {source['label']}...")
        url = f"https://newsapi.org/v2/top-headlines?country={source['country']}&category={source['category']}&apiKey={api_key}"
        
        try:
            resp = requests.get(url)
            data = resp.json()
            articles = data.get("articles", [])[:6] # Fetch 6 from India, 6 from US
            
            for article in articles:
                if not article.get('title'):
                    continue
                
                # Check duplicates
                existing = db.query(NewsItem).filter(NewsItem.url == article['url']).first()
                if existing:
                    continue

                # AI Analysis
                raw_text = f"{article['title']} - {article.get('description', '')}"
                summary, sentiment = generate_financial_summary(raw_text)
                
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
            print(f"Error scraping {source['label']}: {e}")
            continue

    return {"message": f"Analysed {total_scraped} financial news items."}

@app.get("/news")
def get_news(db: Session = Depends(get_db)):
    return db.query(NewsItem).order_by(NewsItem.id.desc()).limit(20).all()