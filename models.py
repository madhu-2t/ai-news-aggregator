from database import Base, engine
from sqlalchemy import Column, Integer, String, Text

class NewsItem(Base):
    __tablename__ = "news_items"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    url = Column(String)
    summary = Column(Text)  # This is where the AI summary goes
    sentiment_score = Column(String) # "Positive", "Negative", "Neutral"

# Create the tables in the DB automatically
Base.metadata.create_all(bind=engine)