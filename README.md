# Vanshika AI Assistant

A small Python voice assistant. The main project files are:

- `main.py`
- `music_library.py`
- `contacts.py`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set your News API key before running the news command:

```bash
export NEWS_API_KEY="your_newsapi_key_here"
```

## Run

```bash
python main.py
```

## Commands

- `open google`
- `open facebook`
- `open youtube`
- `open linkedin`
- `play <song name>`
- `news`
- `open <app name>`
- `close <app name>`
- `call <contact name>`
- `hello`

## Upload To GitHub

Check `contacts.py` before uploading because it contains phone numbers.

```bash
git init
git add .
git commit -m "Initial Vanshika assistant project"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```
