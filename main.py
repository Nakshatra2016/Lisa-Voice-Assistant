import speech_recognition as sr
import webbrowser
import pyttsx3
import music_library
import requests
import os
import contacts

recognizer = sr.Recognizer()
engine = pyttsx3.init()

newsapi = os.getenv("NEWS_API_KEY")

WAKE_WORD = "lisa"

voices = engine.getProperty("voices")

for voice in voices:
    if "veena" in voice.name.lower() or "india" in voice.name.lower():
        engine.setProperty("voice", voice.id)
        break

engine.setProperty("rate", 170)


def speak(text):
    engine.say(text)
    engine.runAndWait()


def process_command(c):
    if "open google" in c.lower():
        webbrowser.open("https://google.com")

    elif "open facebook" in c.lower():
        webbrowser.open("https://facebook.com")

    elif "open youtube" in c.lower():
        webbrowser.open("https://youtube.com")

    elif "open linkedin" in c.lower():
        webbrowser.open("https://linkedin.com")

    elif c.lower().startswith("play"):
        song = c.lower().replace("play", "", 1).strip()
        link = music_library.music.get(song)
        if link:
            webbrowser.open(link)
        else:
            speak("Song not found in library")

    elif "news" in c.lower():
        if not newsapi:
            speak("News API key is not set. Please set the NEWS_API_KEY environment variable.")
            return

        try:
            r = requests.get(
                f"https://newsapi.org/v2/top-headlines?country=us&apiKey={newsapi}",
                timeout=10,
            )
            if r.status_code == 200:
                data = r.json()
                articles = data.get("articles", [])
                if not articles:
                    speak("No news articles found")
                    return
                for article in articles[:5]:
                    title = article.get("title", "")
                    speak(title)
                    print(title)
            else:
                speak("Could not fetch news")
        except requests.RequestException:
            speak("Network error while fetching news")

    elif "call" in c.lower():
        name = c.lower().replace("call", "").strip()

        if name in contacts.contacts:
            number = contacts.contacts[name]
            os.system(
                f'osascript -e \'tell application "FaceTime" to open location "tel://{number}"\''
            )
            speak(f"Calling {name}")
        else:
            speak("Contact not found")

    elif "close" in c.lower():
        close_app = c.lower().replace("close", "").strip().title()
        os.system(f'osascript -e \'tell application "{close_app}" to quit\'')
        speak(f"Closing {close_app}")

    elif "open" in c.lower():
        app_name = c.lower().replace("open", "").strip().title()
        result = os.system(f'open -a "{app_name}"')
        if result == 0:
            speak(f"Opening {app_name}")
        else:
            speak(f"Could not find application {app_name}")

    elif "hello" in c.lower():
        speak("Hello! How can I assist you?")

    elif "time" in c.lower():
        from datetime import datetime
        now = datetime.now().strftime("%I:%M %p")
        speak(f"The current time is {now}")

    elif "date" in c.lower():
        from datetime import datetime
        today = datetime.now().strftime("%B %d, %Y")
        speak(f"Today is {today}")

    else:
        speak("Sorry, I did not understand that command")


if __name__ == "__main__":
    print("""
================ LISA VOICE ASSISTANT ================

Wake Word: lisa

Commands you can use:

 1. open google
 2. open facebook
 3. open youtube
 4. open linkedin
 5. play <song name>
 6. news
 7. open <app name>
 8. close <app name>
 9. call <contact name>
10. hello
11. time
12. date

====================================================
""")

    speak("Hi, I am Lisa, your voice assistant. I am now active.")

    while True:
        try:
            with sr.Microphone() as source:
                print("Listening for wake word...")
                recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=4)

            word = recognizer.recognize_google(audio, language="en-IN")
            print(f"Heard: {word}")

            if WAKE_WORD in word.lower():
                print(f"Wake word detected — Lisa active!")
                speak("Yes, how can I help you?")

                with sr.Microphone() as source:
                    print("Listening for command...")
                    recognizer.adjust_for_ambient_noise(source, duration=1)
                    audio = recognizer.listen(source, timeout=8, phrase_time_limit=6)

                command = recognizer.recognize_google(audio, language="en-IN")
                print(f"Command: {command}")
                process_command(command)

        except sr.WaitTimeoutError:
            pass  # No speech detected, keep listening
        except sr.UnknownValueError:
            pass  # Could not understand audio, keep listening
        except sr.RequestError as e:
            print(f"Speech recognition service error: {e}")
        except KeyboardInterrupt:
            print("\nLisa assistant stopped.")
            speak("Goodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
