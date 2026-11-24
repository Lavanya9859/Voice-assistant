"""Whisper-based speech recognition - more reliable than Google API."""

import os
import tempfile
from pathlib import Path

try:
    import speech_recognition as sr
except ImportError:
    sr = None


class WhisperRecognizer:
    """Use OpenAI Whisper for speech recognition (local or API)."""

    def __init__(self):
        """Initialize Whisper recognizer."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.use_whisper_api = bool(self.api_key)
        self.model_loaded = False

        if not self.use_whisper_api:
            try:
                # Try to load local Whisper model
                import whisper
                print("📦 Loading Whisper model locally (one-time download)...")
                self.model = whisper.load_model("base")
                self.model_loaded = True
                self.use_local_model = True
            except ImportError:
                print("⚠️  Whisper not installed. Install with: pip install openai-whisper")
                self.use_local_model = False
        else:
            self.use_local_model = False

    def is_available(self) -> bool:
        """Check if Whisper is available."""
        return self.model_loaded or self.use_whisper_api

    def recognize_speech(self, audio_file_path: str) -> str:
        """Recognize speech from an audio file using Whisper."""
        if not self.is_available():
            return None

        try:
            if self.use_whisper_api:
                return self._recognize_with_api(audio_file_path)
            else:
                return self._recognize_with_local_model(audio_file_path)
        except Exception as e:
            print(f"❌ Whisper Error: {e}")
            return None

    def _recognize_with_local_model(self, audio_file_path: str) -> str:
        """Use local Whisper model for recognition."""
        try:
            print("🔄 Transcribing with local Whisper model...")
            result = self.model.transcribe(audio_file_path, language="en")
            text = result.get("text", "").strip()

            if text:
                print(f"✓ Recognized: {text}")
                return text.lower()
            return ""
        except Exception as e:
            print(f"❌ Local Whisper Error: {e}")
            return None

    def _recognize_with_api(self, audio_file_path: str) -> str:
        """Use OpenAI Whisper API for recognition."""
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)

            print("🔄 Transcribing with OpenAI Whisper API...")

            with open(audio_file_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en"
                )

            text = transcript.text.strip()

            if text:
                print(f"✓ Recognized: {text}")
                return text.lower()
            return ""
        except Exception as e:
            print(f"❌ Whisper API Error: {e}")
            return None


class ImprovedVoiceRecognizer:
    """Improved voice recognizer using SpeechRecognition + Whisper fallback."""

    def __init__(self):
        """Initialize voice recognizer."""
        if sr is None:
            raise RuntimeError("SpeechRecognition not installed")

        self.recognizer = sr.Recognizer()
        self.whisper = WhisperRecognizer()

    def listen_and_recognize(self, device_index=None, timeout=10) -> str:
        """Listen to microphone and recognize speech."""
        print("🎤 Listening...")

        try:
            with sr.Microphone(device_index=device_index) as source:
                # Calibrate
                print("   Calibrating for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)

                # Listen
                print("   🔴 Recording... Speak now!")
                audio = self.recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=timeout
                )

                # Try Google first (faster if it works)
                try:
                    print("   🔄 Trying Google Speech API...")
                    result = self.recognizer.recognize_google(audio)
                    print(f"✓ Recognized: {result}")
                    return result.strip().lower()
                except sr.UnknownValueError:
                    print("   ⚠️  Google API: Could not understand audio")
                    # Fall back to Whisper
                    if self.whisper.is_available():
                        print("   Trying Whisper API...")
                        return self._use_whisper_fallback(audio)
                    return ""
                except sr.RequestError as e:
                    print(f"   ⚠️  Google API Error: {e}")
                    # Fall back to Whisper
                    if self.whisper.is_available():
                        print("   Trying Whisper API...")
                        return self._use_whisper_fallback(audio)
                    return ""

        except sr.WaitTimeoutError:
            print("❌ Timeout: No audio detected")
            return ""
        except Exception as e:
            print(f"❌ Error: {e}")
            return ""

    def _use_whisper_fallback(self, audio) -> str:
        """Save audio to file and use Whisper for recognition."""
        try:
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False
            ) as temp_file:
                temp_file.write(audio.get_wav_data())
                temp_path = temp_file.name

            # Use Whisper
            result = self.whisper.recognize_speech(temp_path)

            # Clean up
            Path(temp_path).unlink()

            return result or ""
        except Exception as e:
            print(f"❌ Whisper Fallback Error: {e}")
            return ""


def test_whisper():
    """Test Whisper installation and functionality."""
    print("\n" + "="*70)
    print("🧪 WHISPER TEST")
    print("="*70)

    whisper = WhisperRecognizer()

    if whisper.is_available():
        print("✅ Whisper is available!")
        print(f"   Local Model: {whisper.use_local_model}")
        print(f"   API: {whisper.use_whisper_api}")
    else:
        print("❌ Whisper is NOT available")
        print("\nTo enable Whisper:")
        print("  Option 1 - Local Model (no API key needed):")
        print("    pip install openai-whisper")
        print("\n  Option 2 - OpenAI API:")
        print("    pip install openai")
        print("    Set OPENAI_API_KEY environment variable")


if __name__ == "__main__":
    test_whisper()
