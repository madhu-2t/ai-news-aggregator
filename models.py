from sqlalchemy import Column, Integer, String, Text, DateTime
from database import Base, engine

class NewsItem(Base):
    __tablename__ = "news_items"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    url = Column(String, unique=True) 
    summary = Column(Text)
    sentiment_score = Column(String)
    published_at = Column(DateTime(timezone=True)) # The article's real timestamp

Base.metadata.create_all(bind=engine)