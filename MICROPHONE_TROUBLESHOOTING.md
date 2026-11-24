# Microphone & Listening Troubleshooting Guide

## Issue: Assistant Not Listening to Words

### ✅ Diagnosis Passed!
Your system has all the required components:
- ✓ PyAudio installed (16 audio devices found)
- ✓ SpeechRecognition library working
- ✓ Google Speech API accessible
- ✓ Multiple microphone arrays available

### Possible Issues & Solutions

#### 1. **Wrong Microphone Selected**
**Symptom:** Microphone works in other apps, but not with voice assistant

**Solution:**
1. Open **Sound Settings** (Windows Settings → Sound)
2. Find "Input devices" section
3. Select the correct microphone
4. Check volume is not muted
5. Test recording with Voice Recorder

**In App:**
- Click "🔊 Mic Sensitivity" button
- Try values between 200-400 (lower = more sensitive)

#### 2. **Microphone Not Speaking Clearly**
**Symptom:** App says "Could not understand audio"

**Solutions:**
- Speak **slowly and clearly**
- Speak **louder**
- Reduce background noise
- Move closer to microphone
- Avoid speaking at same time as audio output

#### 3. **Ambient Noise Too High**
**Symptom:** App triggers even when silent

**Solutions:**
- Lower microphone sensitivity (use higher number: 400-600)
- Move away from fans, AC, background noise
- Close windows and doors
- Try in a quieter room

#### 4. **No Audio Devices Showing**
**Symptom:** Error "No audio devices found"

**Solutions:**
```bash
# Check if microphone is detected
python diagnostic.py

# If not detected:
# 1. Plug in microphone (if external)
# 2. Update audio drivers
# 3. Check Windows Sound settings
# 4. Restart computer
```

#### 5. **Google API Errors**
**Symptom:** Error "Speech Recognition API Error"

**Possible Causes:**
- ❌ No internet connection (required for Google API)
- ❌ Network firewall blocking API
- ❌ Google API quota exceeded
- ❌ Rate limiting (too many requests)

**Solutions:**
- Check internet connection
- Try using text input (no internet needed)
- Wait a few minutes and retry
- Check Windows firewall settings

#### 6. **Silent Failures (No Feedback)**
**Symptom:** App says "I did not catch that" repeatedly

**Why This Happens:**
- Ambient noise is being detected
- Microphone volume too low
- Google API rejecting the audio

**What to Try:**
1. Speak **louder and clearer**
2. Adjust sensitivity with "🔊 Mic Sensitivity" button
3. Use text input for testing: Just type in the text box!
4. Try in a quieter environment

---

## Quick Fixes

### Test Text Input (No Microphone)
Type commands in the text box instead:
- "What time is it?"
- "Open YouTube"
- "What's the weather?"

### Lower Sensitivity (If Too Sensitive)
- Click "🔊 Mic Sensitivity"
- Try: 500-1000 (for noisy environments)

### Increase Sensitivity (If Not Detecting Speech)
- Click "🔊 Mic Sensitivity"
- Try: 100-200 (for quiet environments)

### Default: 300 (Balanced)

---

## How to Test Microphone

### Method 1: Use Windows Voice Recorder
1. Win + R → `soundrecorder.exe`
2. Click Record
3. Speak for 5 seconds
4. Click Stop
5. Play back and verify audio

### Method 2: Run Diagnostic
```bash
python diagnostic.py
```

### Method 3: Test in App
1. Click "🎤 Start Listening"
2. Wait for: "🎤 Listening... Speak now!"
3. Say a word clearly
4. Check the chat window for feedback

---

## Microphone Features

### Automatic Noise Adjustment
The app automatically adjusts for background noise when you:
1. Click "🎤 Start Listening"
2. It calibrates for ~0.5 seconds
3. Then listens for your voice

### Timeout Settings
- **Listen timeout:** 10 seconds
- **Phrase limit:** 10 seconds
- If you don't speak, it stops automatically

### Error Messages & What They Mean

| Message | Meaning | Solution |
|---------|---------|----------|
| "Listening... Speak now!" | Ready for voice input | Speak clearly |
| "Could not hear you. Retry..." | No speech detected | Speak louder |
| "Could not understand audio" | Speech too unclear | Speak more clearly |
| "API Error" | Internet/API issue | Check connection |
| "Microphone Error" | Microphone not available | Check device |

---

## Using Text Instead (No Microphone Needed)

If microphone isn't working, just **type commands** in the text box:
1. Type your command: "Open Google"
2. Press Enter or click Send
3. The assistant responds

**All features work with text:**
- Website opening ✓
- Weather queries ✓
- Time/date ✓
- Wikipedia ✓
- General questions ✓

---

## Performance Tips

1. **Use quieter environment** → Better recognition
2. **Speak at normal pace** → Not too fast, not too slow
3. **Close background apps** → Less CPU usage
4. **Use default sensitivity** → Start at 300, adjust from there
5. **Good internet** → Faster API responses

---

## Still Having Issues?

1. **Run diagnostic:** `python diagnostic.py`
2. **Check Windows settings:** Sound → Input devices
3. **Try text input:** Type instead of speaking
4. **Restart app:** Close and reopen `gui_app.py`
5. **Restart computer:** May fix audio driver issues

---

## Important Notes

⚠️ **Internet Required:** Google Speech API needs internet connection
📱 **Microphone Required:** For voice input (text input doesn't need mic)
🔊 **Volume Matters:** Speak at reasonable volume, not whisper
🎙️ **Clear Speech:** The clearer you speak, the better recognition

Good luck! 🎯
