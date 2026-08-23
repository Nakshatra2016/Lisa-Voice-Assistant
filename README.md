# Lisa Voice Assistant

A Python voice assistant named **Lisa**. Say the wake word **"lisa"** and then give a command.

## Project Files

- `main.py` — main entry point and command logic
- `music_library.py` — dictionary of songs and their YouTube links
- `contacts.py` — contact names and phone numbers

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

Get a free key at https://newsapi.org

## Run

```bash
python main.py
```

## Commands

After saying **"lisa"**, you can use:

| Command | Action |
|---|---|
| `open google` | Opens Google |
| `open facebook` | Opens Facebook |
| `open youtube` | Opens YouTube |
| `open linkedin` | Opens LinkedIn |
| `play <song name>` | Plays a song from music_library |
| `news` | Reads top 5 headlines |
| `open <app name>` | Opens a Mac application |
| `close <app name>` | Closes a Mac application |
| `call <contact name>` | Calls via FaceTime |
| `hello` | Lisa greets you |
| `time` | Tells current time |
| `date` | Tells today's date |

## Customizing

- **Add songs**: Edit `music_library.py` and add entries to the `music` dictionary
- **Add contacts**: Edit `contacts.py` and add name → phone number entries

## Notes

- Requires a working microphone
- Internet connection needed for speech recognition and news
- FaceTime calling works on macOS only
