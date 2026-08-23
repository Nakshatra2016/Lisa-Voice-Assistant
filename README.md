# Lisa Voice Assistant

I made this voice assistant project in Python. You just say "lisa" and then tell her what to do.

## Files

- `main.py` - the main file, runs everything
- `music_library.py` - has the songs I added
- `contacts.py` - my contacts list

## How to run

First install the requirements:

```bash
pip install -r requirements.txt
```

Then just run:

```bash
python main.py
```

## What it can do

Say **"lisa"** first, then:

- open google / youtube / facebook / linkedin
- play kesariya (or any song you add in music_library.py)
- news (reads top headlines, needs a NewsAPI key)
- call mom (or any contact in contacts.py)
- open / close any app
- hello
- time
- date

## News feature

For news you need a free API key from newsapi.org. Set it like this before running:

```bash
export NEWS_API_KEY="your_key_here"
```

## Note

This only works on Mac because of the FaceTime calling and app open/close stuff.
