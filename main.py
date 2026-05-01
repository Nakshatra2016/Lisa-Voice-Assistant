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

WAKE_WORD = "vanshika"

voices = engine.getProperty("voices")

for voice in voices:
    if "veena" in voice.name.lower() or "india" in voice.name.lower():
        engine.setProperty("voice", voice.id)
        break

engine.setProperty("rate", 170)


def speak(text):
    engine.stop()
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
        try:
            song = c.lower().replace("play", "", 1).strip()
            link = music_library.music[song]
            webbrowser.open(link)
        except KeyError:
            speak("Song not found")

    elif "news" in c.lower():
        if not newsapi:
            speak("News API key is not set")
            return

        r = requests.get(
            f"https://newsapi.org/v2/top-headlines?country=us&apiKey={newsapi}",
            timeout=10,
        )

        if r.status_code == 200:
            data = r.json()
            articles = data.get("articles", [])

            for article in articles[:5]:
                speak(article["title"])
                print(article["title"])
        else:
            speak("Could not fetch news")

    elif "call" in c.lower():
        name = c.lower().replace("call", "").strip()

        if name in contacts.contacts:
            number = contacts.contacts[name]

            script = f'''
            osascript -e 'tell application "FaceTime"
            activate
            open location "tel://{number}"
            end tell'
            '''

            os.system(script)
            speak(f"Calling {name}")

        else:
            speak("Contact not found")

    elif "close" in c.lower():
        close_app = c.lower().replace("close", "").strip()
        command = f'''osascript -e 'tell application "{close_app}" to quit' '''
        os.system(command)
        speak(f"Closing {close_app}")

    elif "open" in c.lower():
        app_name = c.lower().replace("open", "").strip()
        os.system(f'open -a "{app_name}"')
        speak(f"Opening {app_name}")

    elif "hello" in c.lower():
        speak("hi user")


if __name__ == "__main__":
    print("""
================ AI ASSISTANT COMMANDS ================

Wake Word: vanshika

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

=======================================================
""")

    speak("Vanshika assistant is now active")

    while True:
        try:

            with sr.Microphone() as source:

                print("Listening for wake word...")

                recognizer.adjust_for_ambient_noise(source, duration=1)

                audio = recognizer.listen(source, timeout=3, phrase_time_limit=3)

            word = recognizer.recognize_google(audio, language="en-IN")

            if WAKE_WORD in word.lower():

                print(f"{WAKE_WORD} active")
                speak("Yes, how can I help you")

                with sr.Microphone() as source:

                    print("Listening for command...")

                    recognizer.adjust_for_ambient_noise(source, duration=1)

                    audio = recognizer.listen(source)

                command = recognizer.recognize_google(audio, language="en-IN")

                print("Command:", command)

                process_command(command)

        except Exception as e:
            print("Error:", e)
