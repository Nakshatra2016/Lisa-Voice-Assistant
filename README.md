# Lisa Voice Assistant

Say "lisa" (or "liza" / "leesa" — a few common mishears are recognized too),
then tell her what to do.

## Files

- `main.py` — the main file, runs everything
- `music_library.py` — songs you've added
- `contacts.py` — your contacts list
- `com.lisa.assistant.plist` — macOS LaunchAgent definition (auto-start on login)
- `install.sh` — installs Lisa as a LaunchAgent so she starts automatically

## Setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Set your API keys (add these to `~/.zshrc` so they're always available,
not just in the current terminal session):

```bash
export NEWS_API_KEY="your_newsapi_key"
# Optional: use separate NewsAPI keys for these two categories.
# If omitted, both use NEWS_API_KEY.
export CRYPTO_NEWS_API_KEY="your_newsapi_key"
export FOREX_NEWS_API_KEY="your_newsapi_key"
export ANTHROPIC_API_KEY="your_anthropic_api_key"
```

Get a free NewsAPI key at https://newsapi.org and an Anthropic API key at
https://console.anthropic.com.

Then just run:

```bash
.venv/bin/python main.py
```

## What it can do

Say **"lisa"** first, then:

- open google / youtube / facebook / linkedin
- play kesariya (or any song you add in `music_library.py`)
- news — general top headlines
- market news / trading news / stock news — Indian market news (Sensex,
  Nifty, RBI, BSE, NSE) from yesterday and today
- crypto news — recent cryptocurrency-market headlines
- forex news — recent foreign-exchange-market headlines
- call mom (or any contact in `contacts.py`)
- open / close any app
- search `<anything>` — opens a Google search
- run command `<shell command>` — Lisa reads the command back and asks
  you to say "yes" before running it (see **Safety note** below)
- hello / time / date
- anything else — Lisa sends it to Claude and reads back a short answer

## Running Lisa automatically at login (auto-start on Mac boot)

```bash
chmod +x install.sh
./install.sh
```

This registers Lisa as a macOS **LaunchAgent** (the correct mechanism for
auto-starting a user-level background app on macOS — not a login item).
She'll start automatically whenever you log in, and relaunch herself if
she crashes. Logs go to `lisa.log` and `lisa.error.log` in this folder.

To stop/uninstall:

```bash
launchctl unload ~/Library/LaunchAgents/com.lisa.assistant.plist
rm ~/Library/LaunchAgents/com.lisa.assistant.plist
```

### macOS permissions you'll be asked for

The first time each of these happens, macOS will pop up a permission
prompt — you need to approve them for Lisa to work at all:

- **Microphone** — for listening
- **Accessibility / Automation** — for the `osascript` calls that open,
  close, and call apps

If Lisa starts silently doing nothing after a reboot, check
**System Settings → Privacy & Security** and make sure Terminal (or
whichever app is actually running the Python process) has these enabled.

## Safety note on "run command"

Lisa can run arbitrary shell commands if you say "run command ...", but:

- She always reads the command back and waits for a spoken "yes" first —
  she never executes blind.
- A short list of destructive patterns (`rm -rf`, `sudo`, `shutdown`,
  `reboot`, disk-erasing commands, fork bombs, etc.) is hard-blocked and
  will never run, confirmation or not.
- This is a safety net, not a sandbox. Speech recognition isn't perfect,
  and shell commands can do real damage — don't rely on this for anything
  you wouldn't be comfortable a slightly-misheard command running. If you
  want to tighten this further, edit `DANGEROUS_PATTERNS` in `main.py`.

## Improving accuracy for Indian accents

- Recognition uses Google's `en-IN` language model already.
- `main.py` fuzzy-matches near-miss transcriptions of known commands
  (e.g. "opne youtube" still opens YouTube), so small misrecognitions
  don't just fail silently.
- If you find recognition is consistently poor in your environment, the
  next real upgrade is swapping the Google Web Speech API for a local
  Whisper model (`openai-whisper` or `faster-whisper`), which handles
  accented English noticeably better and works offline — that's a bigger
  change (different audio pipeline) so it's not wired in by default here.

## News feature

All news commands use a free API key from newsapi.org (see Setup above).
`CRYPTO_NEWS_API_KEY` and `FOREX_NEWS_API_KEY` are optional separate keys;
when omitted, Lisa uses `NEWS_API_KEY` for both.

## General Q&A ("Jarvis mode")

Anything Lisa doesn't recognize as a specific command gets sent to Claude
as a general question and read back as a short spoken answer. This needs
`ANTHROPIC_API_KEY` set. If it's not set, Lisa just tells you so instead
of guessing.

## Note

This only works on Mac because of the FaceTime calling and app open/close
stuff (`osascript`), and the LaunchAgent auto-start mechanism.
