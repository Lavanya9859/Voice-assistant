# Microphone troubleshooting

The assistant supports typed commands even when microphone input is
unavailable. Speech recognition through Google requires an internet connection.

## Check the microphone

1. Confirm the microphone is connected, enabled, and selected as the system
   input device.
2. Check that the application has permission to use the microphone.
3. Install the project dependencies, including SpeechRecognition and PyAudio.
4. Run the diagnostic script:

   ```bash
   python diagnostic.py
   ```

   The script checks audio-device access and makes a short recording. It may
   send that recording to Google's speech-recognition service.
5. Start `python gui_app.py`, select **Start Listening**, and speak after the
   listening status appears.

## Common errors

| Message or symptom | What to check |
| --- | --- |
| PyAudio or microphone initialization error | Confirm PyAudio is installed and the input device is available to the OS. |
| No audio detected | Check the selected input device, system input level, and microphone permissions. |
| Audio captured but not recognized | Reduce background noise, speak clearly, or try typed input. |
| Speech service request error | Check internet access, firewall settings, and service availability. |

Use `check_audio.py` to record and inspect a sample, or
`advanced_mic_test.py` to compare available input devices. These scripts require
access to microphone hardware; they are manual diagnostics, not automated
tests.

See the [Quick Start](QUICKSTART.md) for running the application and
[LLM setup](LLM_SETUP.md) for optional provider configuration.
