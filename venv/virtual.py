import os
import sys
import time
import json
import subprocess
import datetime
import logging
from typing import Optional

import speech_recognition as sr
import pyttsx3
import wikipedia
import webbrowser
import requests
from ecapture import ecapture as ec
import wolframalpha
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    filename='assistant.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

class Assistant:
    def __init__(self):
        print('Loading your AI personal assistant - G One')
        self.engine = pyttsx3.init('sapi5')
        self.set_voice()
        self.client = self.init_wolframalpha()
        self.api_key = os.getenv('OPENWEATHER_API_KEY')  # Ensure you have this in your .env file

    def set_voice(self):
        voices = self.engine.getProperty('voices')
        if voices:
            self.engine.setProperty('voice', voices[0].id)
        else:
            logging.warning("No voices found for pyttsx3.")
        logging.info("Voice set for pyttsx3.")

    def speak(self, text: str):
        """Convert text to speech."""
        self.engine.say(text)
        self.engine.runAndWait()
        logging.info(f"Spoken: {text}")

    def wish_me(self):
        """Greet the user based on the current time."""
        hour = datetime.datetime.now().hour
        if 0 <= hour < 12:
            greeting = "Good Morning"
        elif 12 <= hour < 18:
            greeting = "Good Afternoon"
        else:
            greeting = "Good Evening"
        self.speak(f"Hello, {greeting}")
        print(f"Hello, {greeting}")
        logging.info(f"Greeted user with: {greeting}")

    def take_command(self) -> Optional[str]:
        """Listen for a voice command and return it as text."""
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Listening...")
            recognizer.pause_threshold = 1
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                command = recognizer.recognize_google(audio, language='en-in').lower()
                print(f"User said: {command}\n")
                logging.info(f"Command received: {command}")
                return command
            except sr.WaitTimeoutError:
                print("Listening timed out while waiting for phrase to start")
                logging.warning("Listening timed out.")
                return None
            except sr.UnknownValueError:
                self.speak("Sorry, I did not understand that. Please try again.")
                logging.error("Could not understand audio.")
                return None
            except sr.RequestError as e:
                self.speak("Sorry, my speech service is down.")
                logging.error(f"Speech recognition service error: {e}")
                return None

    def init_wolframalpha(self) -> Optional[wolframalpha.Client]:
        """Initialize WolframAlpha client."""
        app_id = os.getenv('WOLFRAMALPHA_APP_ID')
        if app_id:
            logging.info("WolframAlpha client initialized.")
            return wolframalpha.Client(app_id)
        else:
            logging.error("WolframAlpha App ID not found.")
            return None

    def get_weather(self, city: str) -> Optional[dict]:
        """Fetch weather data for a given city."""
        base_url = "https://api.openweathermap.org/data/2.5/weather?"
        complete_url = f"{base_url}appid={self.api_key}&q={city}"
        try:
            response = requests.get(complete_url)
            response.raise_for_status()
            data = response.json()
            if data.get("cod") != 404:
                main = data.get("main", {})
                weather = data.get("weather", [{}])[0]
                weather_info = {
                    "temperature": main.get("temp"),
                    "humidity": main.get("humidity"),
                    "description": weather.get("description")
                }
                logging.info(f"Weather fetched for {city}: {weather_info}")
                return weather_info
            else:
                self.speak("City not found.")
                logging.warning(f"City not found: {city}")
                return None
        except requests.RequestException as e:
            self.speak("Sorry, I couldn't retrieve the weather information.")
            logging.error(f"Weather API request failed: {e}")
            return None

    def search_wikipedia(self, query: str) -> Optional[str]:
        """Search Wikipedia for a query and return a summary."""
        try:
            summary = wikipedia.summary(query, sentences=3)
            logging.info(f"Wikipedia summary for {query} retrieved.")
            return summary
        except wikipedia.DisambiguationError as e:
            self.speak("Your query is ambiguous. Please be more specific.")
            logging.error(f"Wikipedia DisambiguationError: {e}")
            return None
        except wikipedia.PageError:
            self.speak("I couldn't find any information on Wikipedia for your query.")
            logging.error(f"Wikipedia PageError for query: {query}")
            return None
        except Exception as e:
            self.speak("An error occurred while searching Wikipedia.")
            logging.error(f"Wikipedia search error: {e}")
            return None

    def ask_wolframalpha(self, question: str) -> Optional[str]:
        """Ask a question to WolframAlpha and return the answer."""
        if not self.client:
            self.speak("WolframAlpha is not configured properly.")
            logging.error("WolframAlpha client not initialized.")
            return None
        try:
            res = self.client.query(question)
            answer = next(res.results).text
            logging.info(f"WolframAlpha answer for '{question}': {answer}")
            return answer
        except StopIteration:
            self.speak("I couldn't find an answer to that question.")
            logging.error(f"No results from WolframAlpha for question: {question}")
            return None
        except Exception as e:
            self.speak("An error occurred while accessing WolframAlpha.")
            logging.error(f"WolframAlpha query error: {e}")
            return None

    def run(self):
        """Main method to run the assistant."""
        self.speak("Loading your AI personal assistant G-One")
        self.wish_me()

        while True:
            self.speak("How can I assist you now?")
            statement = self.take_command()
            if not statement:
                continue

            if any(phrase in statement for phrase in ["good bye", "ok bye", "stop"]):
                farewell = "Your personal assistant G-One is shutting down. Goodbye!"
                self.speak(farewell)
                print(farewell)
                logging.info("Assistant shutdown initiated by user.")
                break

            elif 'wikipedia' in statement:
                self.speak('Searching Wikipedia...')
                query = statement.replace("wikipedia", "").strip()
                summary = self.search_wikipedia(query)
                if summary:
                    self.speak("According to Wikipedia")
                    print(summary)
                    self.speak(summary)

            elif 'open youtube' in statement:
                webbrowser.open_new_tab("https://www.youtube.com")
                self.speak("YouTube is open now.")
                logging.info("YouTube opened.")

            elif 'open google' in statement:
                webbrowser.open_new_tab("https://www.google.com")
                self.speak("Google is open now.")
                logging.info("Google opened.")

            elif 'open gmail' in statement:
                webbrowser.open_new_tab("https://mail.google.com")
                self.speak("Gmail is open now.")
                logging.info("Gmail opened.")

            elif 'weather' in statement:
                self.speak("What's the city name?")
                city = self.take_command()
                if city:
                    weather = self.get_weather(city)
                    if weather:
                        temperature_k = weather["temperature"]
                        temperature_c = temperature_k - 273.15
                        humidity = weather["humidity"]
                        description = weather["description"]
                        weather_report = (
                            f"Temperature in Celsius is {temperature_c:.2f} degrees."
                            f" Humidity is {humidity} percent."
                            f" Description: {description}."
                        )
                        self.speak(weather_report)
                        print(weather_report)

            elif 'time' in statement:
                current_time = datetime.datetime.now().strftime("%H:%M:%S")
                time_message = f"The time is {current_time}"
                self.speak(time_message)
                print(time_message)
                logging.info(f"Time reported: {current_time}")

            elif any(phrase in statement for phrase in ["who are you", "what can you do"]):
                capabilities = (
                    "I am G-One version 1.0, your personal assistant. I can perform tasks like "
                    "opening YouTube, Google, Gmail, and Stack Overflow, telling the time, "
                    "taking photos, searching Wikipedia, providing weather updates, fetching news "
                    "headlines from the Times of India, and answering computational or geographical questions."
                )
                self.speak(capabilities)
                print(capabilities)
                logging.info("Assistant explained its capabilities.")

            elif any(phrase in statement for phrase in ["who made you", "who created you", "who discovered you"]):
                creator_info = "I was built by Mirthula."
                self.speak(creator_info)
                print(creator_info)
                logging.info("Assistant provided creator information.")

            elif 'open stackoverflow' in statement:
                webbrowser.open_new_tab("https://stackoverflow.com/login")
                self.speak("Here is Stack Overflow.")
                logging.info("Stack Overflow opened.")

            elif 'news' in statement:
                news_url = "https://timesofindia.indiatimes.com/home/headlines"
                webbrowser.open_new_tab(news_url)
                self.speak('Here are some headlines from the Times of India. Happy reading!')
                logging.info("News headlines opened.")

            elif any(phrase in statement for phrase in ["camera", "take a photo"]):
                try:
                    ec.capture(0, "G-One Camera", "img.jpg")
                    self.speak("Photo taken successfully.")
                    logging.info("Photo captured.")
                except Exception as e:
                    self.speak("Sorry, I couldn't take a photo.")
                    logging.error(f"Camera capture failed: {e}")

            elif 'search' in statement:
                query = statement.replace("search", "").strip()
                if query:
                    webbrowser.open_new_tab(f"https://www.google.com/search?q={query}")
                    self.speak(f"Searching for {query} on Google.")
                    logging.info(f"Searched Google for: {query}")
                else:
                    self.speak("Please provide a search query.")
                    logging.warning("Search command issued without a query.")

            elif 'ask' in statement:
                self.speak('I can answer computational and geographical questions. What would you like to ask?')
                question = self.take_command()
                if question:
                    answer = self.ask_wolframalpha(question)
                    if answer:
                        self.speak(answer)
                        print(answer)

            elif any(phrase in statement for phrase in ["log off", "sign out"]):
                self.speak("Your PC will log off in 10 seconds. Please save your work.")
                logging.info("System logoff initiated.")
                subprocess.call(["shutdown", "/l"])
            else:
                self.speak("I did not understand that command. Please try again.")
                logging.warning(f"Unrecognized command: {statement}")

            # Short pause before next iteration
            time.sleep(1)

if __name__ == '__main__':
    assistant = Assistant()
    try:
        assistant.run()
    except KeyboardInterrupt:
        print("\nAssistant terminated by user.")
        logging.info("Assistant terminated by user via KeyboardInterrupt.")
        sys.exit()
    except Exception as e:
        print("An unexpected error occurred.")
        logging.critical(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
