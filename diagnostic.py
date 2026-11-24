"""Diagnostic tool to test microphone and speech recognition."""


def test_pyaudio():
    """Test if PyAudio is installed and microphone is available."""
    print("\n🔍 Testing PyAudio and Microphone...")
    try:
        import pyaudio
        print("✓ PyAudio is installed")

        p = pyaudio.PyAudio()
        device_count = p.get_device_count()
        print(f"✓ Found {device_count} audio device(s)")

        if device_count == 0:
            print("❌ ERROR: No audio devices found!")
            return False

        for i in range(device_count):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"  📍 Device {i}: {info['name']} (Input)")

        p.terminate()
        print("✓ PyAudio working correctly\n")
        return True
    except ImportError:
        print("❌ PyAudio is NOT installed!")
        print("   Fix: pip install pyaudio")
        return False
    except Exception as e:
        print(f"❌ PyAudio Error: {e}\n")
        return False


def test_speech_recognition():
    """Test if SpeechRecognition library is installed."""
    print("🔍 Testing SpeechRecognition...")
    try:
        import speech_recognition as sr
        print("✓ SpeechRecognition is installed")

        sr.Recognizer()
        print(f"✓ Recognizer created")

        try:
            with sr.Microphone():
                print("✓ Microphone detected and accessible")
                return True
        except Exception as e:
            print(f"❌ Microphone Error: {e}\n")
            return False
    except ImportError:
        print("❌ SpeechRecognition is NOT installed!")
        print("   Fix: pip install SpeechRecognition")
        return False


def test_microphone_audio():
    """Perform a test recording to verify microphone works."""
    print("🔍 Testing Microphone Recording...")
    try:
        import speech_recognition as sr

        recognizer = sr.Recognizer()

        with sr.Microphone() as source:
            print("   🎤 Listen for 3 seconds... (Please make some noise)")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=3)

        print("✓ Audio captured successfully")

        # Try to recognize
        try:
            text = recognizer.recognize_google(audio)
            print(f"✓ Text recognized: '{text}'")
            return True
        except sr.UnknownValueError:
            print("⚠️  Audio was captured but could not be understood")
            print("   (This is normal if you didn't speak clearly)")
            return True
        except sr.RequestError as e:
            print(f"❌ Google API Error: {e}")
            print("   Possible causes:")
            print("   - No internet connection")
            print("   - Google API quota exceeded")
            print("   - Network firewall blocking API")
            return False
    except Exception as e:
        print(f"❌ Recording Error: {e}\n")
        return False


def main():
    """Run all diagnostics."""
    print("\n" + "="*60)
    print("🛠️  VOICE ASSISTANT DIAGNOSTIC TOOL")
    print("="*60)

    results = {
        "PyAudio": test_pyaudio(),
        "SpeechRecognition": test_speech_recognition(),
        "Microphone and speech API": test_microphone_audio(),
    }

    print("\n" + "="*60)
    print("📊 DIAGNOSTIC SUMMARY")
    print("="*60)

    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if not passed:
            all_passed = False

    print("="*60)

    if all_passed:
        print("\n✅ All tests passed! Your microphone should work.")
        print("\nNext steps:")
        print("1. Run: python gui_app.py")
        print("2. Click 'Start Listening' button")
        print("3. Speak clearly into your microphone")
    else:
        print("\n❌ Some tests failed. Please fix the issues above.")
        print("\nCommon solutions:")
        print("1. Install PyAudio: pip install pyaudio")
        print("2. Check internet connection")
        print("3. Verify microphone is plugged in and working")
        print("4. Try using text input instead (no microphone needed)")
        print("5. Run this diagnostic again: python diagnostic.py")

    print("\n")


if __name__ == "__main__":
    main()
