# 📈 AI-Powered Financial News Aggregator

![Python](https://img.shields.io/badge/Python-3.10-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Container-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Gemini AI](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-8E75B2?style=for-the-badge&logo=google&logoColor=white)

> **A containerized microservice that autonomously scrapes, deduplicates, and analyzes global market news using LLMs to determine real-time market sentiment.**

---

## 🖼️ Dashboard Preview

![Dashboard Screenshot](static/screenshot_placeholder.png)


---

## 🚀 Key Features

* **🤖 AI-Driven Sentiment Analysis:** Utilizes **Google Gemini 2.5 Flash** to analyze complex financial text and categorize it as **Bullish**, **Bearish**, or **Neutral** with a single-sentence executive summary.
* **⚡ Incremental Data Ingestion:** Tracks temporal state in **PostgreSQL** to prevent redundant scraping.
* **🐳 Optimized Containerization:** Docker multi‑stage builds reduce image size by **60%**.
* **🌍 Global Market Coverage:** Aggregates financial news worldwide using NewsAPI.
* **📊 Reactive Frontend:** Dashboard built with HTML5 & Tailwind CSS.

---

## 🏗️ System Architecture

```mermaid
graph TD
    A[NewsAPI Source] -->|Raw JSON| B(FastAPI Scraper)
    B -->|Check Timestamp| C{New Data?}
    C -- No --> D[Skip Processing]
    C -- Yes --> E[Gemini 2.5 Flash]
    E -->|Sentiment & Summary| F[(PostgreSQL DB)]
    F -->|Structured Data| G[FastAPI Endpoints]
    G -->|JSON| H[Frontend Dashboard]
```

---

## 🛠️ Tech Stack

**Backend:** Python, FastAPI, Uvicorn  
**Database:** PostgreSQL (Supabase), SQLAlchemy ORM  
**AI Engine:** Google Gemini 2.5 Flash  
**DevOps:** Docker, GitHub Actions, Render  
**Frontend:** HTML5, Tailwind CSS, JS Fetch API  

---

## ⚙️ Local Setup & Installation

### **Prerequisites**
- Docker Desktop  
- API Keys for **NewsAPI** and **Google AI Studio**

---

### **1. Clone the Repository**
```bash
git clone https://github.com/madhu-2t/ai-news-aggregator.git
cd ai-news-aggregator
```

### **2. Configure Environment**

Create a `.env` file:

```
DATABASE_URL="postgresql://user:password@your-supabase-url:5432/postgres"
NEWS_API_KEY="your_news_api_key"
GEMINI_API_KEY="your_gemini_api_key"
```

### **3. Run with Docker (Recommended)**

```bash
# Build the image
docker build -t news-aggregator .

# Run the container
docker run -p 8000:8000 --env-file .env news-aggregator
```

App will run at:  
**http://localhost:8000**

---

## 🔌 API Endpoints

| Method | Endpoint     | Description |
|--------|--------------|-------------|
| GET    | /            | Serves the frontend dashboard |
| GET    | /news        | Fetches latest 50 processed news items |
| POST   | /scrape      | Triggers background scraper |

---

## 📈 Performance Optimization

This system solves **duplicate scraping** using timestamp-based optimization:

- Tracks `last_published_at` from DB  
- Only fetches news after that timestamp  
- Saves compute and minimizes Gemini API cost  

---

## 📄 License

Licensed under the **MIT License**.
