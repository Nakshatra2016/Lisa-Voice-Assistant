import difflib
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta

import pyttsx3
import requests
import speech_recognition as sr

import contacts
import music_library

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

recognizer = sr.Recognizer()
engine = pyttsx3.init()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
# Optional dedicated NewsAPI keys. If unset, both commands use NEWS_API_KEY.
CRYPTO_NEWS_API_KEY = os.getenv("CRYPTO_NEWS_API_KEY") or NEWS_API_KEY
FOREX_NEWS_API_KEY = os.getenv("FOREX_NEWS_API_KEY") or NEWS_API_KEY
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Model used for the general "ask Lisa anything" fallback. See
# https://docs.claude.com/en/docs/about-claude/models/overview for current model IDs.
ANTHROPIC_MODEL = "claude-sonnet-5"

WAKE_WORDS = ["lisa", "liza", "leesa", "lisha"]  # common mis-hears for "Lisa" in en-IN

# Recognizer tuning — Google's en-IN model is decent, but these help with
# background noise and cut down on truncated / merged words.
recognizer.pause_threshold = 0.8          # how long a pause means "they've finished talking"
recognizer.non_speaking_duration = 0.5
recognizer.dynamic_energy_threshold = True

voices = engine.getProperty("voices")
for voice in voices:
    if "veena" in voice.name.lower() or "india" in voice.name.lower():
        engine.setProperty("voice", voice.id)
        break

engine.setProperty("rate", 170)

# Commands that "run command" is never allowed to execute, no matter what,
# even after voice confirmation. This is a safety net, not a full sandbox —
# don't treat it as bulletproof.
DANGEROUS_PATTERNS = [
    r"\brm\s+-rf\b",
    r"\bsudo\b",
    r"\bmkfs\b",
    r"\bdd\s+if=",
    r">\s*/dev/sd",
    r"\bshutdown\b",
    r"\breboot\b",
    r":\(\)\s*\{.*\};:",  # fork bomb
    r"\bdiskutil\s+eraseDisk\b",
]

# Known command "trigger" phrases, used for fuzzy matching against what the
# recognizer heard, so near-miss transcriptions (very common with accents)
# still map to the right action.
KNOWN_TRIGGERS = [
    "open google", "open facebook", "open youtube", "open linkedin",
    "play", "news", "market news", "trading news", "crypto news", "forex news", "call", "close",
    "open", "hello", "time", "date", "run command", "search",
]


def speak(text):
    print(f"Lisa: {text}")
    engine.say(text)
    engine.runAndWait()


def listen(timeout=6, phrase_time_limit=6, prompt=None):
    """Listen once and return recognized text, or None if nothing usable was heard."""
    if prompt:
        print(prompt)
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.6)
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        text = recognizer.recognize_google(audio, language="en-IN")
        print(f"Heard: {text}")
        return text
    except (sr.WaitTimeoutError, sr.UnknownValueError):
        return None
    except sr.RequestError as e:
        print(f"Speech recognition service error: {e}")
        return None


def best_trigger_match(command_lower):
    """Fuzzy-match the first word(s) of the heard command against known
    triggers to survive misrecognitions (e.g. 'plate kesariya' -> 'play
    kesariya'). Returns (matched_trigger, remainder) or None.
    Only checks from the start of the phrase, so we don't accidentally
    rewrite the middle of a command (e.g. a song title that happens to be
    close to a trigger word)."""
    words = command_lower.split()
    for n in (2, 1):
        if len(words) < n:
            continue
        chunk = " ".join(words[:n])
        match = difflib.get_close_matches(chunk, KNOWN_TRIGGERS, n=1, cutoff=0.7)
        if match and match[0] != chunk:
            remainder = " ".join(words[n:])
            return match[0], remainder
    return None


# ---------------------------------------------------------------------------
# News
# ---------------------------------------------------------------------------

def fetch_general_news():
    if not NEWS_API_KEY:
        speak("News API key not found")
        return
    try:
        r = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={"country": "us", "apiKey": NEWS_API_KEY},
            timeout=10,
        )
        if r.status_code != 200:
            speak("Could not fetch news")
            return
        articles = r.json().get("articles", [])
        if not articles:
            speak("No news articles found")
            return
        for article in articles[:5]:
            title = article.get("title", "")
            speak(title)
    except requests.RequestException:
        speak("Network error while fetching news")


def fetch_trading_news():
    """Indian stock market / trading news for yesterday and today."""
    if not NEWS_API_KEY:
        speak("News API key not found")
        return

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    query = (
        "sensex OR nifty OR \"stock market\" OR \"share market\" OR "
        "\"Indian markets\" OR RBI OR BSE OR NSE"
    )

    try:
        r = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "from": yesterday.isoformat(),
                "to": today.isoformat(),
                "language": "en",
                "sortBy": "publishedAt",
                "apiKey": NEWS_API_KEY,
            },
            timeout=10,
        )
        if r.status_code != 200:
            speak("Could not fetch trading news")
            return
        articles = r.json().get("articles", [])
        if not articles:
            speak("No trading news found for today or yesterday")
            return

        speak("Here is the latest trading news")
        for article in articles[:6]:
            title = article.get("title", "")
            source = article.get("source", {}).get("name", "")
            speak(f"From {source}: {title}")
    except requests.RequestException:
        speak("Network error while fetching trading news")


def fetch_market_news(market, query, api_key):
    """Read recent market-specific headlines from NewsAPI."""
    if not api_key:
        speak(f"{market} news API key not found")
        return

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    try:
        r = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "from": yesterday.isoformat(),
                "to": today.isoformat(),
                "language": "en",
                "sortBy": "publishedAt",
                "apiKey": api_key,
            },
            timeout=10,
        )
        if r.status_code != 200:
            speak(f"Could not fetch {market} news")
            return
        articles = r.json().get("articles", [])
        if not articles:
            speak(f"No recent {market} news found")
            return

        speak(f"Here is the latest {market} news")
        for article in articles[:6]:
            title = article.get("title", "")
            source = article.get("source", {}).get("name", "")
            speak(f"From {source}: {title}")
    except requests.RequestException:
        speak(f"Network error while fetching {market} news")


def fetch_crypto_news():
    fetch_market_news(
        "crypto market",
        "bitcoin OR ethereum OR cryptocurrency OR crypto market OR blockchain",
        CRYPTO_NEWS_API_KEY,
    )


def fetch_forex_news():
    fetch_market_news(
        "forex market",
        "forex OR foreign exchange OR currency market OR USD INR OR EUR USD OR GBP USD",
        FOREX_NEWS_API_KEY,
    )


# ---------------------------------------------------------------------------
# General "ask me anything" fallback (Jarvis-style Q&A) via the Claude API
# ---------------------------------------------------------------------------

def ask_claude(question):
    if not ANTHROPIC_API_KEY:
        speak("I don't have an Anthropic API key set up, so I can't answer general questions yet")
        return

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": ANTHROPIC_MODEL,
                "max_tokens": 300,
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "Answer briefly and conversationally, in 2-3 sentences max, "
                            f"suitable for being read aloud: {question}"
                        ),
                    }
                ],
            },
            timeout=20,
        )
        if response.status_code != 200:
            speak("I couldn't reach Claude to answer that")
            return
        data = response.json()
        text = "".join(
            block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"
        )
        speak(text.strip() or "I didn't get a clear answer for that")
    except requests.RequestException:
        speak("Network error while asking Claude")


# ---------------------------------------------------------------------------
# Guarded command execution ("run command ...")
# ---------------------------------------------------------------------------

def is_dangerous(cmd):
    return any(re.search(pattern, cmd, re.IGNORECASE) for pattern in DANGEROUS_PATTERNS)


def run_terminal_command(cmd):
    if not cmd:
        speak("I didn't catch a command to run")
        return

    if is_dangerous(cmd):
        speak("That command looks destructive, so I'm not going to run it")
        return

    speak(f"You want me to run: {cmd}. Say yes to confirm.")
    confirmation = listen(timeout=6, phrase_time_limit=4, prompt="Listening for confirmation...")
    if not confirmation or "yes" not in confirmation.lower():
        speak("Okay, not running that")
        return

    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )
        output = (result.stdout or result.stderr or "").strip()
        print(output)
        speak("Done. Check the terminal for full output.")
    except subprocess.TimeoutExpired:
        speak("That command timed out")
    except Exception as e:
        speak(f"Something went wrong running that command: {e}")


# ---------------------------------------------------------------------------
# Command handling
# ---------------------------------------------------------------------------

def process_command(c):
    lc = c.lower()

    if "open google" in lc:
        import webbrowser
        webbrowser.open("https://google.com")

    elif "open facebook" in lc:
        import webbrowser
        webbrowser.open("https://facebook.com")

    elif "open youtube" in lc:
        import webbrowser
        webbrowser.open("https://youtube.com")

    elif "open linkedin" in lc:
        import webbrowser
        webbrowser.open("https://linkedin.com")

    elif lc.startswith("play"):
        import webbrowser
        song = lc.replace("play", "", 1).strip()
        link = music_library.music.get(song)
        if not link:
            # fuzzy-match against the library in case of a misheard title
            close = difflib.get_close_matches(song, music_library.music.keys(), n=1, cutoff=0.6)
            link = music_library.music.get(close[0]) if close else None
        if link:
            webbrowser.open(link)
        else:
            speak("Song not found in library")

    elif "crypto news" in lc or "crypto market" in lc:
        fetch_crypto_news()

    elif "forex news" in lc or "forex market" in lc or "currency news" in lc:
        fetch_forex_news()

    elif "trading news" in lc or "market news" in lc or "stock news" in lc:
        fetch_trading_news()

    elif "news" in lc:
        fetch_general_news()

    elif lc.startswith("run command"):
        cmd = c[len("run command"):].strip(" :")
        run_terminal_command(cmd)

    elif "call" in lc:
        name = lc.replace("call", "").strip()
        if name in contacts.contacts:
            number = contacts.contacts[name]
            os.system(
                f'osascript -e \'tell application "FaceTime" to open location "tel://{number}"\''
            )
            speak(f"Calling {name}")
        else:
            speak("Contact not found")

    elif "close" in lc:
        close_app = lc.replace("close", "").strip().title()
        os.system(f'osascript -e \'tell application "{close_app}" to quit\'')
        speak(f"Closing {close_app}")

    elif lc.startswith("search"):
        import webbrowser
        query = c[len("search"):].strip()
        if query:
            webbrowser.open(f"https://www.google.com/search?q={requests.utils.quote(query)}")
            speak(f"Searching for {query}")
        else:
            speak("What should I search for?")

    elif "open" in lc:
        import webbrowser
        app_name = lc.replace("open", "").strip().title()
        result = os.system(f'open -a "{app_name}"')
        if result == 0:
            speak(f"Opening {app_name}")
        else:
            speak(f"Could not find application {app_name}")

    elif "hello" in lc:
        speak("Hello! How can I help you?")

    elif "time" in lc:
        now = datetime.now().strftime("%I:%M %p")
        speak(f"The current time is {now}")

    elif "date" in lc:
        today = datetime.now().strftime("%B %d, %Y")
        speak(f"Today is {today}")

    else:
        # Nothing matched directly — try a fuzzy match against known triggers
        # before giving up, since Indian-accented speech often gets
        # transcribed slightly off (e.g. "opne", "clos", "playy").
        match = best_trigger_match(lc)
        if match:
            trigger, remainder = match
            retried = f"{trigger} {remainder}".strip()
            print(f"No exact match, retrying as: {retried}")
            process_command(retried)
            return
        # Final fallback: treat it as a general question for Claude.
        ask_claude(c)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def heard_wake_word(text):
    lc = text.lower()
    if any(w in lc for w in WAKE_WORDS):
        return True
    # fuzzy check in case Google transcribed the wake word as something close
    return any(difflib.get_close_matches(w, lc.split(), n=1, cutoff=0.75) for w in WAKE_WORDS)


def main():
    print("""
================ LISA VOICE ASSISTANT ================

Wake Word: lisa

Commands you can use:

 1. open google / facebook / youtube / linkedin
 2. play <song name>
 3. news
 4. market news / trading news / stock news
 5. crypto news
 6. forex news
 7. open <app name>
 8. close <app name>
 9. call <contact name>
10. run command <shell command>   (asks for spoken confirmation)
11. search <anything>
12. hello / time / date
13. anything else — Lisa will try to answer it directly

====================================================
""")

    speak("Hi, I am Lisa, your voice assistant. I am now active.")

    while True:
        try:
            heard = listen(timeout=5, phrase_time_limit=4, prompt="Listening for wake word...")
            if not heard or not heard_wake_word(heard):
                continue

            print("Wake word detected — Lisa active!")
            speak("Yes, how can I help you?")

            command = listen(timeout=8, phrase_time_limit=8, prompt="Listening for command...")
            if command:
                process_command(command)
            else:
                speak("Sorry, I didn't catch that")

        except KeyboardInterrupt:
            print("\nLisa assistant stopped.")
            speak("Goodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    if "--check" in sys.argv:
        # quick self-test hook used by install.sh, not part of normal voice flow
        print("Lisa main.py imported and syntax OK")
        sys.exit(0)
    main()
