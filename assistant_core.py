"""Core logic for the personal voice assistant.

The assistant follows a simple rule-based workflow:
listen -> process -> speak.
"""

from __future__ import annotations

import datetime as dt
import json
import threading
import urllib.parse
import urllib.request
import webbrowser
from dataclasses import dataclass

from ml_security_engine import MLSecurityEngine, SecurityDecision
from llm_engine import LLMEngine, SmartFallback

try:
    from whisper_recognizer import ImprovedVoiceRecognizer
    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False

try:
    import speech_recognition as sr
except ImportError:  # pragma: no cover - handled at runtime
    sr = None

try:
    import pyttsx3
except ImportError:  # pragma: no cover - handled at runtime
    pyttsx3 = None

try:
    import wikipedia
except ImportError:  # pragma: no cover - handled at runtime
    wikipedia = None


@dataclass(frozen=True)
class AssistantResponse:
    """Structured response returned by the assistant."""

    text: str
    should_exit: bool = False


WEBSITE_LINKS: dict[str, tuple[str, str]] = {
    # Search & News
    "google": ("https://www.google.com", "Opening Google."),
    "bing": ("https://www.bing.com", "Opening Bing."),
    "medium": ("https://medium.com", "Opening Medium."),
    "hackernews": ("https://news.ycombinator.com", "Opening Hacker News."),
    "dev.to": ("https://dev.to", "Opening Dev.to."),
    "reddit": ("https://www.reddit.com", "Opening Reddit."),

    # Video & Streaming
    "youtube": ("https://www.youtube.com", "Opening YouTube."),
    "netflix": ("https://www.netflix.com", "Opening Netflix."),
    "disney": ("https://www.disneyplus.com", "Opening Disney Plus."),
    "spotify": ("https://www.spotify.com", "Opening Spotify."),
    "twitch": ("https://www.twitch.tv", "Opening Twitch."),

    # Development & Programming
    "github": ("https://github.com", "Opening GitHub."),
    "gitlab": ("https://gitlab.com", "Opening GitLab."),
    "bitbucket": ("https://bitbucket.org", "Opening Bitbucket."),
    "stackoverflow": ("https://stackoverflow.com", "Opening Stack Overflow."),
    "npm": ("https://www.npmjs.com", "Opening NPM."),
    "pypi": ("https://pypi.org", "Opening PyPI."),
    "docker": ("https://www.docker.com", "Opening Docker."),
    "dockerhub": ("https://hub.docker.com", "Opening Docker Hub."),

    # Coding Challenges
    "leetcode": ("https://leetcode.com", "Opening LeetCode."),
    "hackerrank": ("https://www.hackerrank.com", "Opening HackerRank."),
    "codeforces": ("https://codeforces.com", "Opening Codeforces."),
    "codechef": ("https://www.codechef.com", "Opening CodeChef."),
    "atcoder": ("https://atcoder.jp", "Opening AtCoder."),
    "codewars": ("https://www.codewars.com", "Opening Codewars."),

    # Learning Platforms
    "coursera": ("https://www.coursera.org", "Opening Coursera."),
    "udemy": ("https://www.udemy.com", "Opening Udemy."),
    "edx": ("https://www.edx.org", "Opening edX."),
    "khan academy": ("https://www.khanacademy.org", "Opening Khan Academy."),
    "codecademy": ("https://www.codecademy.com", "Opening Codecademy."),
    "w3schools": ("https://www.w3schools.com", "Opening W3Schools."),
    "mdn": ("https://developer.mozilla.org", "Opening MDN Web Docs."),

    # Social Media
    "facebook": ("https://www.facebook.com", "Opening Facebook."),
    "twitter": ("https://twitter.com", "Opening Twitter."),
    "x": ("https://x.com", "Opening X."),
    "instagram": ("https://www.instagram.com", "Opening Instagram."),
    "tiktok": ("https://www.tiktok.com", "Opening TikTok."),
    "snapchat": ("https://www.snapchat.com", "Opening Snapchat."),
    "pinterest": ("https://www.pinterest.com", "Opening Pinterest."),
    "tumblr": ("https://www.tumblr.com", "Opening Tumblr."),

    # Professional & Productivity
    "linkedin": ("https://www.linkedin.com", "Opening LinkedIn."),
    "gmail": ("https://mail.google.com", "Opening Gmail."),
    "outlook": ("https://outlook.live.com", "Opening Outlook."),
    "notion": ("https://www.notion.so", "Opening Notion."),
    "trello": ("https://trello.com", "Opening Trello."),
    "asana": ("https://asana.com", "Opening Asana."),
    "monday": ("https://monday.com", "Opening Monday.com."),
    "slack": ("https://slack.com", "Opening Slack."),
    "jira": ("https://www.atlassian.com/software/jira", "Opening Jira."),
    "confluence": ("https://www.atlassian.com/software/confluence", "Opening Confluence."),

    # Shopping & Commerce
    "amazon": ("https://www.amazon.com", "Opening Amazon."),
    "ebay": ("https://www.ebay.com", "Opening eBay."),
    "flipkart": ("https://www.flipkart.com", "Opening Flipkart."),
    "alibaba": ("https://www.alibaba.com", "Opening Alibaba."),
    "aliexpress": ("https://www.aliexpress.com", "Opening AliExpress."),
    "etsy": ("https://www.etsy.com", "Opening Etsy."),

    # Utilities & Tools
    "wikipedia": ("https://www.wikipedia.org", "Opening Wikipedia."),
    "github copilot": ("https://copilot.github.com", "Opening GitHub Copilot."),
    "chatgpt": ("https://chat.openai.com", "Opening ChatGPT."),
    "claude": ("https://claude.ai", "Opening Claude."),
    "bard": ("https://bard.google.com", "Opening Google Bard."),
    "canva": ("https://www.canva.com", "Opening Canva."),
    "figma": ("https://www.figma.com", "Opening Figma."),
    "photoshop": ("https://www.adobe.com/products/photoshop", "Opening Photoshop."),

    # Finance & Banking
    "paypal": ("https://www.paypal.com", "Opening PayPal."),
    "stripe": ("https://stripe.com", "Opening Stripe."),
    "coinbase": ("https://www.coinbase.com", "Opening Coinbase."),
    "binance": ("https://www.binance.com", "Opening Binance."),

    # Job Search
    "indeed": ("https://www.indeed.com", "Opening Indeed."),
    "glassdoor": ("https://www.glassdoor.com", "Opening Glassdoor."),
    "monster": ("https://www.monster.com", "Opening Monster."),

    # Travel
    "booking": ("https://www.booking.com", "Opening Booking.com."),
    "airbnb": ("https://www.airbnb.com", "Opening Airbnb."),
    "expedia": ("https://www.expedia.com", "Opening Expedia."),
    "tripadvisor": ("https://www.tripadvisor.com", "Opening TripAdvisor."),

    # Weather & Maps
    "weather": ("https://weather.com", "Opening Weather.com."),
    "google maps": ("https://maps.google.com", "Opening Google Maps."),
}

WEBSITE_CATEGORIES: dict[str, list[str]] = {
    "Search & News": ["google", "bing", "medium", "hackernews", "dev.to", "reddit"],
    "Video & Streaming": ["youtube", "netflix", "disney", "spotify", "twitch"],
    "Development": ["github", "gitlab", "bitbucket", "stackoverflow", "npm", "pypi", "docker", "dockerhub"],
    "Coding Challenges": ["leetcode", "hackerrank", "codeforces", "codechef", "atcoder", "codewars"],
    "Learning": ["coursera", "udemy", "edx", "khan academy", "codecademy", "w3schools", "mdn"],
    "Social Media": ["facebook", "twitter", "x", "instagram", "tiktok", "snapchat", "pinterest", "tumblr"],
    "Productivity": ["linkedin", "gmail", "outlook", "notion", "trello", "asana", "monday", "slack", "jira", "confluence"],
    "Shopping": ["amazon", "ebay", "flipkart", "alibaba", "aliexpress", "etsy"],
    "AI & Tools": ["wikipedia", "github copilot", "chatgpt", "claude", "bard", "canva", "figma", "photoshop"],
    "Finance": ["paypal", "stripe", "coinbase", "binance"],
    "Jobs": ["indeed", "glassdoor", "monster"],
    "Travel": ["booking", "airbnb", "expedia", "tripadvisor"],
    "Weather & Maps": ["weather", "google maps"],
}


class VoiceAssistant:
    """Simple voice assistant for microphone-driven interaction."""

    def __init__(
        self,
        threshold: int = 300,
        security_threshold: float = 0.70,
        security_model_path: str = "models/security_model.pkl",
    ) -> None:
        self.threshold = threshold
        self.engine = pyttsx3.init() if pyttsx3 else None
        self.recognizer = sr.Recognizer() if sr else None

        # Try to use Whisper recognizer for better accuracy
        self.voice_recognizer = None
        if HAS_WHISPER:
            try:
                self.voice_recognizer = ImprovedVoiceRecognizer()
                print("✓ Using Whisper for speech recognition (more accurate!)")
            except Exception as e:
                print(f"⚠️  Could not load Whisper: {e}")
                print("   Falling back to Google Speech API")

        self.security_engine = MLSecurityEngine(
            model_path=security_model_path,
            threshold=security_threshold,
        )
        self.llm_engine = LLMEngine()
        self.fallback = SmartFallback()
        self.last_security_decision: SecurityDecision | None = None
        self._speech_lock = threading.Lock()

        if self.recognizer is not None:
            self.recognizer.energy_threshold = threshold
            self.recognizer.dynamic_energy_threshold = True

    def speak(self, message: str) -> None:
        """Speak the response and mirror it in the terminal."""

        print(f"Assistant: {message}")
        if self.engine is None or not message:
            return

        with self._speech_lock:
            self.engine.stop()
            self.engine.say(message)
            self.engine.runAndWait()

    def calibrate_microphone(self, duration: float = 0.3) -> None:
        """Calibrate the microphone once before continuous listening starts."""

        if self.recognizer is None:
            raise RuntimeError("SpeechRecognition is not installed.")

        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=duration)
        except (OSError, AttributeError) as exc:
            raise RuntimeError(
                "Microphone input is unavailable. Install PyAudio or use the text box instead."
            ) from exc

    def listen(self) -> str:
        """Listen to the microphone and return recognized speech."""

        # Use Whisper if available (much more accurate!)
        if self.voice_recognizer:
            try:
                result = self.voice_recognizer.listen_and_recognize(timeout=10)
                if result:
                    return result
                else:
                    print("⏱️  No speech detected or recognition failed")
                    return ""
            except Exception as e:
                print(f"⚠️  Whisper Error: {e}, falling back to Google API")

        # Fallback to Google Speech API
        if self.recognizer is None:
            raise RuntimeError("SpeechRecognition is not installed.")

        try:
            with sr.Microphone() as source:
                print("🎤 Listening... (please speak clearly)")
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                # Listen with a timeout
                try:
                    audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=10)
                except sr.WaitTimeoutError:
                    print("⏱️  No audio detected within timeout. Please try again.")
                    return ""
        except (OSError, AttributeError) as exc:
            error_msg = str(exc)
            print(f"❌ Microphone Error: {error_msg}")
            raise RuntimeError(
                f"Microphone input is unavailable. {error_msg}. Install PyAudio or use the text box instead."
            ) from exc

        try:
            print("🔄 Processing speech...")
            result = self.recognizer.recognize_google(audio).strip().lower()
            print(f"✓ Recognized: {result}")
            return result
        except sr.UnknownValueError:
            print("❓ Could not understand audio. Please speak clearly and try again.")
            return ""
        except sr.RequestError as e:
            print(f"❌ Speech Recognition API Error: {e}")
            print("🔧 Troubleshooting: Check internet connection or Google API limits")
            return ""

    def get_weather(self, location: str) -> str:
        """Fetch current weather for a location using Open-Meteo."""

        if not location:
            return "Please tell me a city name for the weather check."

        geocode_url = "https://geocoding-api.open-meteo.com/v1/search?" + urllib.parse.urlencode(
            {
                "name": location,
                "count": 1,
                "language": "en",
                "format": "json",
            }
        )

        try:
            with urllib.request.urlopen(geocode_url, timeout=10) as response:
                geocode_data = json.loads(response.read().decode("utf-8"))
        except Exception:
            return "I could not reach the weather service right now."

        results = geocode_data.get("results") or []
        if not results:
            return f"I could not find weather information for {location}."

        place = results[0]
        latitude = place.get("latitude")
        longitude = place.get("longitude")
        place_name = place.get("name", location)
        country = place.get("country")
        admin1 = place.get("admin1")

        forecast_url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(
            {
                "latitude": latitude,
                "longitude": longitude,
                "current_weather": "true",
                "timezone": "auto",
            }
        )

        try:
            with urllib.request.urlopen(forecast_url, timeout=10) as response:
                weather_data = json.loads(response.read().decode("utf-8"))
        except Exception:
            return "I could not reach the weather service right now."

        current_weather = weather_data.get("current_weather") or {}
        temperature = current_weather.get("temperature")
        windspeed = current_weather.get("windspeed")
        weathercode = current_weather.get("weathercode")
        description = self._weather_description(weathercode)

        location_parts = [part for part in [place_name, admin1, country] if part]
        formatted_location = ", ".join(location_parts)

        return (
            f"Current weather for {formatted_location}: {description}, "
            f"{temperature} degrees Celsius, wind speed {windspeed} kilometers per hour."
        )

    def _weather_description(self, code: object) -> str:
        """Convert an Open-Meteo weather code into a human readable description."""

        weather_codes = {
            0: "clear sky",
            1: "mainly clear",
            2: "partly cloudy",
            3: "overcast",
            45: "foggy",
            48: "rime fog",
            51: "light drizzle",
            53: "moderate drizzle",
            55: "dense drizzle",
            56: "light freezing drizzle",
            57: "dense freezing drizzle",
            61: "slight rain",
            63: "moderate rain",
            65: "heavy rain",
            66: "light freezing rain",
            67: "heavy freezing rain",
            71: "slight snow fall",
            73: "moderate snow fall",
            75: "heavy snow fall",
            77: "snow grains",
            80: "slight rain showers",
            81: "moderate rain showers",
            82: "violent rain showers",
            85: "slight snow showers",
            86: "heavy snow showers",
            95: "thunderstorm",
            96: "thunderstorm with slight hail",
            99: "thunderstorm with heavy hail",
        }

        try:
            return weather_codes.get(int(code), "current conditions")
        except (TypeError, ValueError):
            return "current conditions"

    def _open_website(self, target: str) -> AssistantResponse:
        """Open a known website or a direct URL."""

        normalized_target = target.strip().lower()
        if normalized_target in WEBSITE_LINKS:
            url, message = WEBSITE_LINKS[normalized_target]
            webbrowser.open(url)
            return AssistantResponse(message)

        if normalized_target.startswith("http://") or normalized_target.startswith("https://"):
            webbrowser.open(normalized_target)
            return AssistantResponse(f"Opening {normalized_target}.")

        # Generate available sites list for helpful response
        available_sites = sorted(WEBSITE_LINKS)
        sites_list = ", ".join(available_sites[:10]) + f", and {len(available_sites) - 10} more sites..."
        return AssistantResponse(
            f"I can open: {sites_list}. Or tell me a full website link."
        )

    def _greeting_response(self, command: str) -> AssistantResponse:
        """Return a friendly greeting based on the current time and command."""

        hour = dt.datetime.now().hour
        if hour < 12:
            time_of_day = "morning"
        elif hour < 18:
            time_of_day = "afternoon"
        else:
            time_of_day = "evening"

        greetings = {
            "hello": f"Hello. Good {time_of_day}.",
            "hi": f"Hi there. Good {time_of_day}.",
            "hey": f"Hey. Good {time_of_day}.",
            "good morning": "Good morning. How can I help you?",
            "good afternoon": "Good afternoon. How can I help you?",
            "good evening": "Good evening. How can I help you?",
            "good night": "Good night. Sleep well, sweet dreams.",
            "how are you": "I am doing well. How can I help you?",
            "what's up": "I am ready to help you.",
            "whats up": "I am ready to help you.",
            "thank you": "You are welcome.",
            "thanks": "You are welcome.",
        }

        normalized = command.strip().lower()
        for phrase, response in greetings.items():
            if phrase in normalized:
                return AssistantResponse(response)

        return AssistantResponse("Hello. How can I help you?")

    def _extract_weather_location(self, command: str) -> str:
        """Extract a location from a weather-style query."""

        normalized = command.strip().lower().replace("wheather", "weather")
        patterns = [
            "weather in",
            "weather for",
            "weather at",
            "weather of",
            "weather details in",
            "weather details for",
            "weather details at",
            "tell me weather details in",
            "tell me weather details for",
            "tell me weather details at",
            "show me weather details in",
            "show me weather details for",
            "show me weather details at",
            "show weather in",
            "show weather for",
            "show weather at",
            "tell me weather in",
            "tell me weather for",
            "tell me weather at",
            "what is the weather in",
            "what is the weather for",
            "what is the weather at",
            "what's the weather in",
            "what's the weather for",
            "what's the weather at",
            "weather",
        ]

        for pattern in patterns:
            if normalized.startswith(pattern):
                location = normalized.removeprefix(pattern).strip()
                return location

        return ""

    def _get_websites_list(self) -> str:
        """Return a formatted list of all available websites."""

        available_sites = sorted(WEBSITE_LINKS)
        response = f"I can open {len(available_sites)} websites:\n\n"
        for category, sites in WEBSITE_CATEGORIES.items():
            response += f"📌 {category}: {', '.join(sites)}\n"
        response += f"\nJust say 'open [website name]' to open any of them. I also support direct URLs."
        return response

    def process_command(self, command: str) -> AssistantResponse:
        """Validate a command, then process it using simple if/elif rules."""

        security_decision = self.security_engine.inspect(command)
        self.last_security_decision = security_decision
        if not security_decision.allowed:
            probability = security_decision.threat_probability * 100
            return AssistantResponse(
                f"Command blocked by the security policy. Threat probability: {probability:.1f}%."
            )

        normalized = security_decision.sanitized_text.lower().replace("wheather", "weather")

        if not normalized:
            return AssistantResponse("I did not catch that. Please try again.")

        if any(word in normalized for word in ["exit", "quit", "stop"]):
            return AssistantResponse("Goodbye.", should_exit=True)

        # Check for website-related questions
        if any(phrase in normalized for phrase in ["which websites", "what websites", "which sites", "what sites", "can you open", "websites available"]):
            return AssistantResponse(self._get_websites_list())

        if "time" in normalized:
            current_time = dt.datetime.now().strftime("%I:%M %p")
            return AssistantResponse(f"The current time is {current_time}.")

        if "date" in normalized or "day" in normalized:
            current_date = dt.datetime.now().strftime("%A, %d %B %Y")
            return AssistantResponse(f"Today is {current_date}.")

        if normalized.startswith("open "):
            target = normalized.removeprefix("open ").strip()

            if target.startswith("website "):
                target = target.removeprefix("website ").strip()

            return self._open_website(target)

        if "weather" in normalized:
            location = self._extract_weather_location(normalized)

            if not location:
                return AssistantResponse(
                    "Please tell me a city or place name, like weather in London or weather for Mumbai."
                )

            return AssistantResponse(self.get_weather(location))

        if any(
            phrase in normalized
            for phrase in [
                "hello",
                "hi",
                "hey",
                "good morning",
                "good afternoon",
                "good evening",
                "how are you",
                "what's up",
                "whats up",
                "thanks",
                "thank you",
            ]
        ):
            return self._greeting_response(normalized)

        if normalized.startswith("search wikipedia") or normalized.startswith("wikipedia"):
            if wikipedia is None:
                return AssistantResponse("Wikipedia is not installed.")

            query = normalized.replace("search wikipedia", "").replace("wikipedia", "").strip()
            if not query:
                return AssistantResponse("Please tell me what to search on Wikipedia.")

            try:
                summary = wikipedia.summary(query, sentences=2, auto_suggest=True)
                return AssistantResponse(summary)
            except Exception:
                return AssistantResponse(f"I could not find information about {query}.")

        if "who are you" in normalized or "your name" in normalized:
            return AssistantResponse("I am a personal voice assistant built with Python.")

        # Try LLM for unknown questions
        llm_response = self._try_llm(command)
        if llm_response:
            return AssistantResponse(llm_response)

        return AssistantResponse("I can help with time, date, weather, greetings, websites, and Wikipedia search. Ask me 'which websites can you open?' to see all available sites.")

    def _try_llm(self, command: str) -> str | None:
        """Try to get a response from LLM engine."""
        # First try LLM if available
        if self.llm_engine.is_available():
            context = "You are a helpful voice assistant. Keep responses concise (1-2 sentences max). Focus on being helpful and natural."
            response = self.llm_engine.query(command, context)
            if response:
                return response

        # Fall back to smart pattern matching
        fallback_response = self.fallback.respond(command)
        return fallback_response

    def run(self) -> None:
        """Start the assistant loop."""

        self.speak("Voice assistant started.")

        while True:
            command = self.listen()
            response = self.process_command(command)
            self.speak(response.text)

            if response.should_exit:
                break