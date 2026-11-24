"""Advanced microphone tester to find working device."""

try:
    import speech_recognition as sr
    import pyaudio
except ImportError:
    print("❌ Required libraries not installed")
    print("Run: pip install SpeechRecognition pyaudio")
    exit(1)


def test_each_device():
    """Test audio capture from each available device."""
    print("\n" + "="*70)
    print("🔍 TESTING EACH MICROPHONE DEVICE")
    print("="*70)

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 4000  # Default

    p = pyaudio.PyAudio()
    device_count = p.get_device_count()

    working_devices = []

    for i in range(device_count):
        info = p.get_device_info_by_index(i)

        # Only test input devices
        if info['maxInputChannels'] == 0:
            continue

        device_name = info['name']
        print(f"\n📍 Testing Device {i}: {device_name}")
        print(f"   Channels: {info['maxInputChannels']}, Sample Rate: {int(info['defaultSampleRate'])}")

        try:
            with sr.Microphone(device_index=i) as source:
                print(f"   ⏳ Calibrating... (listening for 2 seconds)")
                recognizer.adjust_for_ambient_noise(source, duration=2)

                print(f"   🔴 RECORDING for 3 seconds... SPEAK NOW!")
                audio = recognizer.listen(source, timeout=3, phrase_time_limit=3)

                # Check if audio was actually captured
                audio_data = audio.get_raw_data()
                audio_size = len(audio_data)

                print(f"   ✓ Audio captured: {audio_size} bytes")

                if audio_size < 1000:
                    print(f"   ⚠️  Very little audio captured (may be too quiet)")
                    continue

                # Try to recognize
                try:
                    print(f"   🔄 Recognizing with Google API...")
                    text = recognizer.recognize_google(audio)
                    print(f"   ✅ SUCCESS! Recognized: '{text}'")
                    working_devices.append((i, device_name, "Working - Voice Recognized"))
                except sr.UnknownValueError:
                    print(f"   ⚠️  Audio captured but not recognized")
                    working_devices.append((i, device_name, "Audio Captured - Not Recognized"))
                except sr.RequestError as e:
                    print(f"   ❌ API Error: {e}")
                    if audio_size > 1000:
                        working_devices.append((i, device_name, "Audio Captured - API Error"))

        except sr.WaitTimeoutError:
            print(f"   ❌ Timeout: No audio detected")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    p.terminate()

    # Summary
    print("\n" + "="*70)
    print("📊 WORKING MICROPHONES FOUND")
    print("="*70)

    if working_devices:
        for device_id, name, status in working_devices:
            print(f"✅ Device {device_id}: {name}")
            print(f"   Status: {status}")
    else:
        print("❌ No working microphones found")
        print("\nPossible causes:")
        print("  1. Microphone is muted in Windows Sound Settings")
        print("  2. Microphone volume is too low")
        print("  3. No microphone plugged in")
        print("  4. Drivers need update")

    return working_devices


def test_with_different_thresholds(device_id):
    """Test microphone with different sensitivity settings."""
    print("\n" + "="*70)
    print(f"🔊 TESTING SENSITIVITY LEVELS (Device {device_id})")
    print("="*70)

    recognizer = sr.Recognizer()
    thresholds = [300, 1000, 2000, 4000, 8000]

    for threshold in thresholds:
        recognizer.energy_threshold = threshold

        print(f"\n📍 Testing with sensitivity: {threshold}")
        try:
            with sr.Microphone(device_index=device_id) as source:
                print(f"   Calibrating...")
                recognizer.adjust_for_ambient_noise(source, duration=1)

                print(f"   🔴 RECORDING (speak now)...")
                audio = recognizer.listen(source, timeout=3, phrase_time_limit=3)

                audio_data = audio.get_raw_data()
                audio_size = len(audio_data)

                if audio_size > 1000:
                    print(f"   ✓ Captured {audio_size} bytes")
                    try:
                        text = recognizer.recognize_google(audio)
                        print(f"   ✅ Recognized: '{text}'")
                        print(f"   💡 BEST SETTING: Use sensitivity {threshold}")
                        return threshold
                    except sr.UnknownValueError:
                        print(f"   ⚠️  Audio captured but not clear")
                else:
                    print(f"   ❌ Too little audio ({audio_size} bytes)")
        except sr.WaitTimeoutError:
            print(f"   ❌ No audio detected")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    return None


def main():
    print("\n" + "="*70)
    print("🎤 ADVANCED MICROPHONE DIAGNOSTIC")
    print("="*70)

    # Step 1: Test all devices
    working = test_each_device()

    # Step 2: If we found working devices, test sensitivity
    if working:
        best_device = working[0][0]
        print(f"\n\n💡 Will test sensitivity with Device {best_device}")
        best_threshold = test_with_different_thresholds(best_device)

        if best_threshold:
            print(f"\n\n✅ RECOMMENDED SETTINGS:")
            print(f"   Device: {best_device}")
            print(f"   Sensitivity: {best_threshold}")
            print(f"\n   In app: Click '🔊 Mic Sensitivity' and enter {best_threshold}")

    # Step 3: Instructions
    print("\n" + "="*70)
    print("📋 NEXT STEPS")
    print("="*70)

    if not working:
        print("\n❌ No working microphone found")
        print("\nFix microphone issues:")
        print("  1. Check Windows Sound Settings (Settings → Sound)")
        print("  2. Verify microphone is not muted")
        print("  3. Check microphone volume is high enough")
        print("  4. Try different microphone if available")
        print("  5. Update audio drivers")
        print("  6. Restart computer")
        print("\nOr use TEXT INPUT instead (no microphone needed)!")
    else:
        print("\n✅ Microphone is working!")
        print("\n1. Run: python gui_app.py")
        print("2. Click '🎤 Start Listening'")
        print("3. Speak clearly when it says 'Speak now!'")

        if best_threshold and best_threshold != 300:
            print(f"\n💡 TIP: Use sensitivity setting {best_threshold} for better results")

    print("\n")


if __name__ == "__main__":
    main()
