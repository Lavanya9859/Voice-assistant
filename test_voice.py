"""Simple voice recording test to verify microphone works."""

import os
from pathlib import Path

try:
    import speech_recognition as sr
except ImportError:
    print("❌ SpeechRecognition not installed. Run: pip install SpeechRecognition")
    exit(1)


def test_voice_capture():
    """Record a test voice sample and save it."""
    print("\n" + "="*60)
    print("🎙️  VOICE CAPTURE TEST")
    print("="*60)

    recognizer = sr.Recognizer()

    # Create output directory
    os.makedirs("test_recordings", exist_ok=True)

    print("\n📍 Available microphones:")
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"   Device {i}: {info['name']}")
        p.terminate()
    except:
        pass

    print("\n🎤 Test 1: Capture voice for 5 seconds...")
    print("   Speak clearly into your microphone now!")

    try:
        with sr.Microphone() as source:
            # Calibrate
            print("   Calibrating...")
            recognizer.adjust_for_ambient_noise(source, duration=2)

            # Listen
            print("   🔴 RECORDING... (speak now)")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            print("   ⏹️  Recording stopped")

            # Save to file
            filename = "test_recordings/test_voice.wav"
            with open(filename, "wb") as f:
                f.write(audio.get_wav_data())
            print(f"   ✓ Saved to: {filename}")

            # Try to recognize
            print("\n   🔄 Processing with Google Speech API...")
            try:
                text = recognizer.recognize_google(audio)
                print(f"   ✓ Recognized text: '{text}'")
                print("   ✅ VOICE CAPTURE WORKING!")
                return True
            except sr.UnknownValueError:
                print("   ⚠️  Google could not understand the audio")
                print("   This might mean:")
                print("     - Speech was not clear enough")
                print("     - No speech was detected")
                print("   The audio file was saved for inspection")
                return False
            except sr.RequestError as e:
                print(f"   ❌ Google API Error: {e}")
                print("   Possible issues:")
                print("     - No internet connection")
                print("     - Firewall blocking API")
                print("     - API quota exceeded")
                return False

    except sr.WaitTimeoutError:
        print("   ❌ Timeout: No audio detected within 5 seconds")
        print("   Possible issues:")
        print("     - Microphone not picking up sound")
        print("     - Sensitivity too high")
        print("     - Speaking too quietly")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_direct_google_api():
    """Test Google API with a sample audio file."""
    print("\n" + "="*60)
    print("🔄 TEST 2: Google API Connection")
    print("="*60)

    recognizer = sr.Recognizer()

    # Check if we have a saved test file
    if os.path.exists("test_recordings/test_voice.wav"):
        print("\n   Using saved test voice file...")
        try:
            with sr.AudioFile("test_recordings/test_voice.wav") as source:
                audio = recognizer.record(source)

            print("   🔄 Sending to Google API...")
            text = recognizer.recognize_google(audio)
            print(f"   ✓ Recognized: '{text}'")
            print("   ✅ GOOGLE API WORKING!")
            return True
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    else:
        print("   No test file found. Run Test 1 first.")
        return False


def main():
    print("\n" + "="*60)
    print("🎤 VOICE ASSISTANT - MICROPHONE TEST SUITE")
    print("="*60)

    # Test 1: Voice capture
    result1 = test_voice_capture()

    # Test 2: Google API (using saved file)
    result2 = test_direct_google_api()

    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"Voice Capture:    {'✅ PASS' if result1 else '❌ FAIL'}")
    print(f"Google API:       {'✅ PASS' if result2 else '❌ FAIL'}")
    print("="*60)

    if result1 and result2:
        print("\n✅ All tests passed! Microphone should work in the app.")
        print("\nNext: Run 'python gui_app.py' and click Start Listening")
    else:
        print("\n❌ Some tests failed.")
        print("\nTroubleshooting:")
        if not result1:
            print("  - Check microphone is plugged in")
            print("  - Check Windows Sound Settings")
            print("  - Try different microphone (if available)")
            print("  - Speak louder and clearer")
        if not result2:
            print("  - Check internet connection")
            print("  - Check Windows Firewall")
            print("  - Check Google API quota")

    print("\n")


if __name__ == "__main__":
    main()
