# 📰➡️🎙️ Blog-to-Podcast Generator (OpenAI + Optional Firecrawl & ElevenLabs)

A simple, powerful Streamlit application that converts any blog article into a podcast-style audio episode.

This project is designed for **maximum flexibility**:

- ✅ Works fully with **only your OpenAI API key**
- 🔍 **Firecrawl** (optional) for rich web scraping
- 🗣️ **ElevenLabs** (optional) for premium speech synthesis
- 🌐 If Firecrawl is missing, the app automatically uses `requests + BeautifulSoup`
- 🎤 User can **select from multiple AI voices** (OpenAI or ElevenLabs)

---

## 🚀 Features

- **Paste blog content OR provide a URL**
- **Firecrawl → (optional)** high-quality Markdown scraping  
  Automatically falls back to BeautifulSoup scraping
- **BeautifulSoup → (automatic fallback)** simple paragraph extraction
- **Podcast-style script generation** using OpenAI GPT-4o-mini
- **Voice selection menu**  
  - OpenAI Voices → coral, alloy, verse, spark, lunar  
  - ElevenLabs Voices → Rachel, Adam, Bella, Dorothy, James  
- **Automatic fallback logic**  
  If selected ElevenLabs voice but no API key → app uses OpenAI TTS
- **Clean UI with Streamlit**
- **Downloadable MP3 output**

---

## 📁 Project Structure

    blog_to_podcast_agent.py     # Main Streamlit application
    requirements.txt             # Dependencies
    README.md                    # Project documentation

---

## 🔧 Requirements

Add these packages to your environment (included in `requirements.txt`):

    streamlit
    openai>=1.10.0
    requests
    beautifulsoup4
    firecrawl-py           # optional
    elevenlabs             # optional

---

## 🔑 API Keys

Only **OpenAI** is mandatory.

    OpenAI API Key          → required
    Firecrawl API Key       → optional (for URL scraping)
    ElevenLabs API Key      → optional (for premium voices)

The app UI allows you to enter these keys in the sidebar.

---

## ▶️ How to Run

1. Install dependencies:

    pip install -r requirements.txt

2. Run Streamlit app:

    streamlit run blog_to_podcast_agent.py

3. Open the app in your browser  
   Usually auto-opens at:  
   `http://localhost:8501`

---

## 📝 Usage Guide

### 1. Provide Blog Input
You have two choices:

- **Paste the blog content manually**  
  → This always takes priority

- **Enter a blog URL**  
  → App tries Firecrawl if key is present  
  → If missing, uses a built-in BeautifulSoup scraper

### 2. Choose Script Length
Use the slider to control podcast script size (500–4000 characters).

### 3. Select Voice
Pick from OpenAI or ElevenLabs voices:

- OpenAI: coral, alloy, verse, spark, lunar  
- ElevenLabs: Rachel, Adam, Bella, Dorothy, James  

If you select an ElevenLabs voice without providing its key →  
App automatically falls back to OpenAI TTS.

### 4. Generate Podcast
Click **"Generate Podcast"**:

- OpenAI will create the podcast script  
- Audio will be synthesized using chosen voice  
- You can preview and download the MP3

---

## 🧠 How It Works (Logic Flow)

    IF manual content provided:
        use manual content
    ELSE IF URL provided:
        IF Firecrawl key exists:
            try Firecrawl scraper
            IF Firecrawl fails:
                fallback → BeautifulSoup
        ELSE:
            use BeautifulSoup scraper

    Generate podcast script using OpenAI GPT-4o-mini

    IF selected voice is ElevenLabs AND key exists:
        try ElevenLabs TTS
        IF failure:
            fallback → OpenAI TTS
    ELSE:
        use OpenAI TTS with chosen OpenAI voice

This layered fallback approach ensures the app **always works**, even with minimal keys.

---

## 🎧 Supported Voices

### OpenAI Voices
- coral (default fallback)
- alloy
- verse
- spark
- lunar

### ElevenLabs Voices
- Rachel
- Adam
- Bella
- Dorothy
- James

---

## 💡 Notes & Tips

- Some websites block basic scrapers; Firecrawl improves extraction quality.
- OpenAI TTS voices are extremely natural and cost-effective.
- ElevenLabs voices provide studio-grade narration if available.
- You can extend the app to support:
  - Multiple languages  
  - Voice previews  
  - Episode intros/outros  
  - Batch URL processing

---

## ❤️ Acknowledgments

Powered by:
- OpenAI GPT-4o-mini (text & TTS)
- Firecrawl (optional rich scraping)
- ElevenLabs (optional TTS)
- Streamlit UI

