"""Record microphone input to file and check if speech is captured."""

import os

try:
    import speech_recognition as sr
except ImportError:
    print("❌ Required libraries not installed")
    exit(1)


def record_to_file(device_id, duration=5, filename="test_audio.wav"):
    """Record audio from microphone to a WAV file."""
    print(f"\n🎙️  Recording from Device {device_id} for {duration} seconds...")
    print("   🔴 SPEAK NOW! (loudly and clearly)")

    recognizer = sr.Recognizer()

    try:
        with sr.Microphone(device_index=device_id) as source:
            print("   📊 Calibrating for ambient noise (1 second)...")
            recognizer.adjust_for_ambient_noise(source, duration=1)

            print(f"   🔴 RECORDING...")
            audio = recognizer.listen(source, timeout=duration, phrase_time_limit=duration)

            # Save to file
            audio_data = audio.get_wav_data()

            os.makedirs("recordings", exist_ok=True)
            filepath = f"recordings/{filename}"

            with open(filepath, "wb") as f:
                f.write(audio_data)

            print(f"   ✓ Saved: {filepath}")
            print(f"   Size: {len(audio_data)} bytes")

            return filepath, audio_data

    except sr.WaitTimeoutError:
        print("   ❌ Timeout: No audio detected within time limit")
        return None, None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None, None


def check_audio_level(audio_data):
    """Check if the audio file has actual sound or just silence."""
    print("\n📊 AUDIO ANALYSIS:")

    if not audio_data:
        print("   ❌ No audio data")
        return False

    # Convert bytes to 16-bit integers
    import struct
    samples = struct.unpack(f"<{len(audio_data)//2}h", audio_data)

    # Calculate RMS (Root Mean Square) - a measure of audio loudness
    import math
    if len(samples) > 0:
        rms = math.sqrt(sum(s**2 for s in samples) / len(samples))
        print(f"   Audio Level (RMS): {rms:.0f}")

        if rms < 100:
            print("   ⚠️  Audio is VERY QUIET (almost silent)")
            print("      Possible causes:")
            print("        - Microphone not plugged in properly")
            print("        - Microphone muted in Windows")
            print("        - Speaking too quietly")
            return False
        elif rms < 500:
            print("   ⚠️  Audio is QUIET")
            print("      Try speaking LOUDER")
            return False
        elif rms < 2000:
            print("   📊 Audio level is OK but somewhat low")
            return True
        else:
            print("   ✅ Audio level is GOOD")
            return True

    return False


def test_playback(filepath):
    """Try to play back the recorded audio."""
    print(f"\n🔊 Testing playback of: {filepath}")
    try:
        import winsound
        print("   Playing audio...")
        winsound.PlaySound(filepath, winsound.SND_FILENAME)
        print("   ✓ Playback complete")
    except Exception as e:
        print(f"   Note: Could not play audio ({e})")
        print(f"   But file was saved: {filepath}")


def try_recognize(filepath):
    """Try to recognize speech from the saved file."""
    print(f"\n🔄 Attempting speech recognition on saved file...")

    recognizer = sr.Recognizer()

    try:
        with sr.AudioFile(filepath) as source:
            audio = recognizer.record(source)

        print("   Sending to Google API...")
        text = recognizer.recognize_google(audio)
        print(f"   ✅ Recognized: '{text}'")
        return True
    except sr.UnknownValueError:
        print("   ⚠️  Could not understand audio")
        print("   This could mean:")
        print("     - Audio contains noise, not speech")
        print("     - Speech is not clear enough")
        print("     - Background noise is too loud")
        print("\n   Try speaking LOUDER and more CLEARLY")
        return False
    except sr.RequestError as e:
        print(f"   ⚠️  API Error: {e}")
        print("   Check internet connection")
        return False
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        return False


def main():
    print("\n" + "="*70)
    print("🎤 MICROPHONE AUDIO CHECK")
    print("="*70)
    print("\nThis test will record your voice and check if it's being captured correctly")

    # Use the device that was working (Device 4 or 5)
    print("\n📍 Using Device 4 (Primary Sound Capture Driver)")
    device_id = 4

    # Record
    filepath, audio_data = record_to_file(device_id, duration=5)

    if not audio_data:
        print("\n❌ Failed to record audio")
        print("\nTroubleshooting:")
        print("  1. Check if microphone is plugged in")
        print("  2. Check Windows Sound Settings")
        print("  3. Unmute microphone if muted")
        print("  4. Try Device 5 instead: python advanced_mic_test.py")
        return

    # Check audio level
    has_sound = check_audio_level(audio_data)

    # Try playback
    if filepath:
        test_playback(filepath)

    # Try recognition
    if filepath:
        recognized = try_recognize(filepath)

    # Summary
    print("\n" + "="*70)
    print("📋 SUMMARY")
    print("="*70)

    if has_sound and recognized:
        print("✅ Everything is working! Use the app now.")
    elif has_sound:
        print("⚠️  Audio is captured but not recognized as speech")
        print("\nSolutions:")
        print("  1. Speak LOUDER and CLEARER")
        print("  2. Reduce background noise")
        print("  3. Move microphone closer to mouth")
        print("  4. Try using TEXT INPUT instead (click in text box)")
    else:
        print("❌ Microphone is not capturing sound")
        print("\nSolutions:")
        print("  1. Check if microphone is plugged in")
        print("  2. Go to Windows Settings → Sound")
        print("  3. Check microphone is selected and not muted")
        print("  4. Check microphone volume is high")
        print("  5. Update audio drivers")
        print("\nOr use TEXT INPUT instead (no microphone needed)!")

    print("\n" + "="*70)
    print("💡 IMPORTANT: You can ALWAYS use TEXT INPUT")
    print("   No microphone needed! Just type in the text box.")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
