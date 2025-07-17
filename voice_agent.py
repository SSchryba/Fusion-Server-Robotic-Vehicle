"""Voice Agent with speech recognition and text-to-speech."""

import os
import logging
import openai
import pyttsx3
import speech_recognition as sr
import pyautogui

logger = logging.getLogger(__name__)


class VoiceAgent:
    """Simple voice assistant using OpenAI, speech recognition and TTS."""

    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.engine = pyttsx3.init()
        self._setup_voice()
        self.recognizer = sr.Recognizer()

    def _setup_voice(self):
        """Configure a female sounding voice with a cheerful rate."""
        try:
            voices = self.engine.getProperty("voices")
            for voice in voices:
                if "female" in voice.name.lower():
                    self.engine.setProperty("voice", voice.id)
                    break
            self.engine.setProperty("rate", 185)
        except Exception as exc:
            logger.warning("Could not set female voice: %s", exc)

    def speak(self, text: str) -> None:
        """Speak text using text-to-speech."""
        logger.info("Speaking: %s", text)
        self.engine.say(text)
        self.engine.runAndWait()

    def listen(self) -> str:
        """Listen for speech and convert to text."""
        with sr.Microphone() as source:
            logger.info("Listening...")
            audio = self.recognizer.listen(source)
        try:
            text = self.recognizer.recognize_google(audio)
            logger.info("Heard: %s", text)
            return text
        except sr.UnknownValueError:
            logger.warning("Speech not understood")
            return ""
        except sr.RequestError as exc:
            logger.error("Speech recognition error: %s", exc)
            return ""

    def generate_response(self, prompt: str) -> str:
        """Generate a bubbly response using OpenAI's API."""
        if not openai.api_key:
            logger.error("OPENAI_API_KEY not configured")
            return "I need my API key to chat!"
        messages = [
            {
                "role": "system",
                "content": (
                    "You are Kairo, a bubbly female coding assistant. "
                    "Answer cheerfully and helpfully."
                ),
            },
            {"role": "user", "content": prompt},
        ]
        try:
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo", messages=messages, temperature=0.7
            )
            return completion.choices[0].message.content.strip()
        except Exception as exc:
            logger.error("OpenAI request failed: %s", exc)
            return "Sorry, I couldn't reach my brain right now."

    def handle_command(self, text: str) -> str:
        """Handle special commands that control the computer."""
        lower = text.lower()
        if lower.startswith("type "):
            pyautogui.typewrite(text[5:])
            return f"Typed: {text[5:]}"
        if lower.startswith("move mouse "):
            try:
                coords = lower[len("move mouse "):].split(",")
                x, y = int(coords[0].strip()), int(coords[1].strip())
                pyautogui.moveTo(x, y)
                return f"Moved mouse to {x},{y}"
            except Exception as exc:
                logger.error("Invalid mouse command: %s", exc)
                return "Couldn't move the mouse."
        return self.generate_response(text)

    def run(self) -> None:
        """Main interaction loop."""
        self.speak("Hello! I'm ready to help you.")
        while True:
            text = self.listen()
            if not text:
                continue
            if text.lower() in {"quit", "exit", "stop"}:
                self.speak("Bye bye!")
                break
            response = self.handle_command(text)
            self.speak(response)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    agent = VoiceAgent()
    agent.run()
