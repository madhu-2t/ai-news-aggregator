import os
import google.generativeai as genai
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import NewsItem, Base, engine
from pydantic import BaseModel
import requests
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# --- GEMINI SETUP ---
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# using gemini-1.5-flash because it is fast and cheap/free
# model = genai.GenerativeModel('gemini-1.5-flash')
# model = genai.GenerativeModel('gemini-1.5-flash-001')
model = genai.GenerativeModel('gemini-2.5-flash')

# Create DB tables if they don't exist
Base.metadata.create_all(bind=engine)

# Pydantic Model
class NewsOut(BaseModel):
    title: str
    summary: str
    sentiment: str

# --- HELPER: AI SUMMARIZER ---
def generate_summary(text):
    try:
        # We combine instructions into the prompt for simplicity
        prompt = f"""
        You are a financial analyst. Analyze the following news text.
        1. Summarize it in exactly 1 sentence.
        2. Determine the sentiment (Positive, Negative, or Neutral).
        
        Output format strictly like this:
        SUMMARY_TEXT | SENTIMENT
        
        News text: {text}
        """
        
        response = model.generate_content(prompt)
        
        # Parsing the response
        content = response.text.strip()
        if "|" in content:
            summary, sentiment = content.split("|", 1)
        else:
            # Fallback if AI doesn't respect format
            summary = content
            sentiment = "Neutral"
            
        return summary.strip(), sentiment.strip()
    except Exception as e:
        print(f"AI Error: {e}")
        return "Summary unavailable", "Neutral"

# --- ENDPOINTS ---

@app.post("/scrape")
def scrape_news(db: Session = Depends(get_db)):
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="NewsAPI Key missing")
        
    url = f"https://newsapi.org/v2/top-headlines?category=business&language=en&apiKey={api_key}"
    
    response = requests.get(url)
    data = response.json()
    
    if data.get("status") != "ok":
        raise HTTPException(status_code=500, detail=f"NewsAPI Error: {data.get('message')}")
    
    articles = data.get("articles", [])[:3] # Limit to 3 for testing
    
    saved_count = 0
    for article in articles:
        # Skip if article has no content
        if not article['title'] or not article['description']:
            continue
            
        # Check if URL already exists to avoid duplicates
        existing = db.query(NewsItem).filter(NewsItem.url == article['url']).first()
        if existing:
            continue

        # Generate AI Summary
        raw_text = f"{article['title']} - {article['description']}"
        summary, sentiment = generate_summary(raw_text)
        
        # Save to DB
        news_item = NewsItem(
            title=article['title'],
            url=article['url'],
            summary=summary,
            sentiment_score=sentiment
        )
        db.add(news_item)
        saved_count += 1
        
    db.commit()
    return {"message": f"Scraped and summarized {saved_count} new articles"}

@app.get("/news")
def get_news(db: Session = Depends(get_db)):
    return db.query(NewsItem).order_by(NewsItem.id.desc()).limit(10).all()