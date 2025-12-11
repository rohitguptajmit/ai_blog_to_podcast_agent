import os
from pathlib import Path
from uuid import uuid4

import streamlit as st
from openai import OpenAI

import requests
from bs4 import BeautifulSoup

# Optional: Firecrawl & ElevenLabs
try:
    from firecrawl import Firecrawl
except ImportError:
    Firecrawl = None

try:
    from elevenlabs.client import ElevenLabs
    from elevenlabs import save as eleven_save
except ImportError:
    ElevenLabs = None
    eleven_save = None


# -----------------------------
# Streamlit Page Setup
# -----------------------------
st.set_page_config(page_title="📰 ➡️ 🎙️ Blog to Podcast", page_icon="🎙️")
st.title("📰 ➡️ 🎙️ Blog to Podcast Agent")

st.write(
    "Convert any blog into a podcast-style audio summary.\n\n"
    "- ✅ Only **OpenAI** key is required\n"
    "- 🔍 **Firecrawl** is optional (for richer scraping)\n"
    "- 🗣️ **ElevenLabs** is optional (for premium voices)\n"
    "- 🌐 If Firecrawl is missing/unavailable, URL content is fetched via simple web scraping"
)

# -----------------------------
# Sidebar – API Keys
# -----------------------------
st.sidebar.header("🔑 API Keys")

openai_key = st.sidebar.text_input("OpenAI API Key", type="password")

with st.sidebar.expander("Optional: Firecrawl & ElevenLabs"):
    firecrawl_key = st.text_input("Firecrawl API Key (optional)", type="password")
    elevenlabs_key = st.text_input("ElevenLabs API Key (optional)", type="password")

st.sidebar.markdown(
    "- OpenAI → **required**\n"
    "- Firecrawl → used *if available* for URL scraping\n"
    "- ElevenLabs → used *if available* for audio; otherwise OpenAI TTS"
)

# -----------------------------
# Main Inputs
# -----------------------------
blog_url = st.text_input(
    "Blog URL (optional)",
    help="If provided, content will be fetched from this URL. Manual content (below) takes priority."
)

manual_content = st.text_area(
    "Or paste blog content manually",
    "",
    height=200,
    help="Manual content overrides URL. If you don't want to scrape, just paste the blog here.",
)

max_chars = st.slider(
    "Max characters in podcast script",
    min_value=500,
    max_value=4000,
    value=2000,
    step=250,
    help="Upper limit for the generated podcast script."
)

# -----------------------------
# Voice Selection
# -----------------------------
st.subheader("🎤 Voice Selection")

# These are just example lists; adjust to match what your accounts support.
openai_voices = ["coral", "alloy", "verse", "spark", "lunar"]
elevenlabs_voices = ["Rachel", "Adam", "Bella", "Dorothy", "James"]

voice_choice = st.selectbox(
    "Choose Podcast Voice",
    options=openai_voices + elevenlabs_voices,
    index=0,
    help=(
        "If you select an ElevenLabs voice but no ElevenLabs key is provided, "
        "the app will fall back to OpenAI TTS."
    ),
)


# -----------------------------
# Helper Functions
# -----------------------------
def get_openai_client(api_key: str) -> OpenAI:
    """Create an OpenAI client."""
    os.environ["OPENAI_API_KEY"] = api_key
    return OpenAI(api_key=api_key)


def fetch_content_with_firecrawl(url: str, api_key: str) -> str:
    """Fetch page content using Firecrawl (markdown)."""
    if Firecrawl is None:
        raise RuntimeError("firecrawl-py is not installed, but Firecrawl was requested.")

    firecrawl = Firecrawl(api_key=api_key)
    doc = firecrawl.scrape(url, formats=["markdown"])
    # Expected shape: {"success": True, "data": {"markdown": "...", ...}}
    if not doc or "data" not in doc or "markdown" not in doc["data"]:
        raise RuntimeError(f"Unexpected Firecrawl response: {doc}")
    content = doc["data"]["markdown"] or ""
    return content.strip()


def fetch_content_with_requests(url: str) -> str:
    """
    Simple fallback: fetch page with requests + BeautifulSoup
    and extract visible paragraph text.
    """
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Prefer <article> if present
    article = soup.find("article")
    if article:
        paragraphs = article.find_all("p")
    else:
        paragraphs = soup.find_all("p")

    text_chunks = []
    for p in paragraphs:
        txt = p.get_text(strip=True)
        if txt:
            text_chunks.append(txt)

    full_text = "\n\n".join(text_chunks)
    # Safety limit
    return full_text[:15000]


def generate_podcast_script(client: OpenAI, source_text: str, max_chars: int) -> str:
    """Use OpenAI chat completions to generate a podcast-style summary."""
    prompt = (
        "You are an expert podcast script writer.\n\n"
        "Task:\n"
        f"- Write a conversational, engaging podcast monologue based on the blog content below.\n"
        f"- Maximum length: about {max_chars} characters.\n"
        "- Use a friendly tone, like a host talking to listeners.\n"
        "- Do NOT read out section titles or links verbatim; instead, paraphrase them.\n\n"
        "Here is the blog content:\n"
        "-------------------------\n"
        f"{source_text}\n"
        "-------------------------\n"
    )

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You write concise, engaging podcast scripts."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )

    script = completion.choices[0].message.content.strip()
    # Safety hard-cut if model goes a bit above requested size
    return script[: max_chars + 200]


def tts_with_elevenlabs(text: str, api_key: str, voice: str) -> bytes:
    """Generate audio using ElevenLabs with selected voice."""
    if ElevenLabs is None or eleven_save is None:
        raise RuntimeError("elevenlabs package is not installed.")

    client = ElevenLabs(api_key=api_key)

    audio = client.generate(
        text=text,
        voice=voice,  # Selected ElevenLabs voice
        model="eleven_multilingual_v2",
    )

    tmp_path = Path(f"podcast_{uuid4().hex}_11labs.mp3")
    eleven_save(audio, str(tmp_path))
    audio_bytes = tmp_path.read_bytes()
    try:
        tmp_path.unlink(missing_ok=True)
    except Exception:
        pass

    return audio_bytes


def tts_with_openai(client: OpenAI, text: str, voice: str) -> bytes:
    """Generate audio using OpenAI Text-to-Speech with selected voice."""
    audio_path = Path(f"podcast_{uuid4().hex}_openai.mp3")

    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice=voice,   # Selected OpenAI voice
        input=text,
        instructions="Speak like a warm, friendly podcast host.",
    ) as response:
        response.stream_to_file(audio_path)

    audio_bytes = audio_path.read_bytes()
    try:
        audio_path.unlink(missing_ok=True)
    except Exception:
        pass

    return audio_bytes


# -----------------------------
# Main Action
# -----------------------------
generate_btn = st.button("🎙️ Generate Podcast", disabled=not openai_key)

if generate_btn:
    if not openai_key:
        st.error("OpenAI API key is required to generate the podcast.")
    else:
        try:
            client = get_openai_client(openai_key)

            # 1️⃣ Decide source text
            if manual_content.strip():
                # Manual content takes priority over URL
                blog_text = manual_content.strip()
            else:
                if not blog_url.strip():
                    st.error("Please either paste blog content or provide a URL.")
                    st.stop()

                url = blog_url.strip()

                # Try Firecrawl first if key is present
                blog_text = ""
                if firecrawl_key:
                    try:
                        with st.spinner("Scraping blog content with Firecrawl..."):
                            blog_text = fetch_content_with_firecrawl(url, firecrawl_key)
                    except Exception as e:
                        st.warning(
                            f"Firecrawl scraping failed, falling back to simple web scraping.\n\nDetails: {e}"
                        )

                # If no Firecrawl key or Firecrawl failed → fallback to requests+BS4
                if not blog_text:
                    with st.spinner("Scraping blog content with simple web scraping..."):
                        blog_text = fetch_content_with_requests(url)

            if not blog_text:
                st.error("No content found to summarize from the blog.")
                st.stop()

            # 2️⃣ Generate podcast script
            with st.spinner("Generating podcast script with OpenAI..."):
                script = generate_podcast_script(client, blog_text, max_chars=max_chars)

            # 3️⃣ Generate audio with voice selection
            audio_bytes = None
            used_engine = None
            used_voice = None

            # Decide whether the selected voice is an ElevenLabs voice
            wants_eleven = (voice_choice in elevenlabs_voices) and bool(elevenlabs_key)

            if wants_eleven:
                try:
                    with st.spinner(f"Generating audio with ElevenLabs voice '{voice_choice}'..."):
                        audio_bytes = tts_with_elevenlabs(script, elevenlabs_key, voice_choice)
                        used_engine = "ElevenLabs"
                        used_voice = voice_choice
                except Exception as e:
                    st.warning(
                        f"ElevenLabs audio generation failed, falling back to OpenAI TTS.\n\nDetails: {e}"
                    )

            # If ElevenLabs not used or failed → OpenAI TTS
            if audio_bytes is None:
                # Use selected voice if it's an OpenAI voice, otherwise default to 'coral'
                openai_voice = voice_choice if voice_choice in openai_voices else "coral"
                with st.spinner(f"Generating audio with OpenAI TTS voice '{openai_voice}'..."):
                    audio_bytes = tts_with_openai(client, script, openai_voice)
                    used_engine = "OpenAI TTS"
                    used_voice = openai_voice

            # 4️⃣ Show results
            st.success(f"Podcast generated successfully using {used_engine} ({used_voice}) 🎧")

            st.audio(audio_bytes, format="audio/mp3")

            st.download_button(
                "⬇️ Download Podcast",
                audio_bytes,
                file_name="podcast_episode.mp3",
                mime="audio/mp3",
            )

            with st.expander("📄 Podcast Script"):
                st.write(script)

        except Exception as e:
            st.error(f"Unexpected error: {e}")
