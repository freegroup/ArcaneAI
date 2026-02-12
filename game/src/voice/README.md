# Voice/TTS System

Text-to-Speech system with multiple provider support.

## Providers

### 1. Console (Default)
No audio output, just for testing.

```yaml
voice:
  enabled: false  # or use console provider
  provider: "console"
```

### 2. Google Cloud TTS
High-quality cloud TTS with many voices.

```yaml
voice:
  enabled: true
  provider: "google"
  api_key: "YOUR_API_KEY"  # or use Application Default Credentials
  language_code: "de-DE"
  voice_name: "de-DE-Journey-D"
  sample_rate: 24000
```

**Installation:**
```bash
pip install google-cloud-texttospeech
```

### 3. OpenAI TTS
High-quality cloud TTS with streaming.

```yaml
voice:
  enabled: true
  provider: "openai"
  api_key: "YOUR_API_KEY"
  voice: "onyx"  # alloy, echo, fable, onyx, nova, shimmer
  speed: 1.2
  model: "tts-1"  # or tts-1-hd
```

**Installation:**
```bash
pip install openai
```

### 4. XTTS v2 (Coqui) - **RECOMMENDED FOR CUSTOM VOICES**
Local TTS with voice cloning support!

#### Default Voice (No Cloning)
```yaml
voice:
  enabled: true
  provider: "xtts"
  language: "de"  # de, en, es, fr, it, pt, pl, tr, ru, nl, cs, ar, zh-cn, ja, hu, ko, hi
  use_gpu: true   # Much faster with GPU
```

#### Voice Cloning (Custom Pirate Voice!)
```yaml
voice:
  enabled: true
  provider: "xtts"
  language: "de"
  speaker_wav: "voices/pirate.wav"  # 6-10 seconds of audio
  use_gpu: true
```

**Installation:**
```bash
pip install TTS
```

**First run:** Model will be downloaded automatically (~2GB)

## Voice Cloning Guide

### Step 1: Get Audio Sample
You need 6-10 seconds of clean audio:

**Option A: Record yourself**
```bash
# Record with ffmpeg
ffmpeg -f avfoundation -i ":0" -t 10 pirate.wav
```

**Option B: Extract from video**
```bash
# Extract audio from YouTube video
yt-dlp -x --audio-format wav "VIDEO_URL"
# Cut to 6-10 seconds
ffmpeg -i input.wav -ss 00:00:05 -t 10 pirate.wav
```

**Option C: Use existing audio**
- Find pirate voice samples online
- Use movie/game audio clips
- Generate with other TTS (e.g., ElevenLabs free tier)

### Step 2: Prepare Audio
Audio should be:
- ✅ 6-10 seconds long
- ✅ Clear speech (no background noise)
- ✅ Single speaker
- ✅ WAV or MP3 format
- ✅ Any sample rate (will be resampled)

### Step 3: Configure
```yaml
voice:
  enabled: true
  provider: "xtts"
  language: "de"
  speaker_wav: "game_v2/voices/pirate.wav"  # Path to your audio
  use_gpu: true
```

### Step 4: Test
```bash
cd game_v2
python src/main.py
```

## Audio Sinks

Configure where audio is played:

```yaml
audio:
  output: "auto"  # auto, pyaudio, websocket, null
  sample_rate: 24000
```

- **auto**: Detect based on session (websocket for web, pyaudio for console)
- **pyaudio**: Local audio playback
- **websocket**: Stream to browser
- **null**: No audio output

## Performance Tips

### XTTS v2
- **GPU**: ~1-2 seconds for synthesis
- **CPU**: ~10-30 seconds for synthesis
- **First run**: Downloads model (~2GB)
- **Memory**: ~4GB RAM, ~2GB VRAM (GPU)

### Speed Comparison
1. **Piper** (not implemented yet): Fastest (~0.1s)
2. **Google/OpenAI**: Fast (~0.5s, cloud)
3. **XTTS v2**: Medium (~1-2s GPU, ~10-30s CPU)

## Troubleshooting

### XTTS: "CUDA out of memory"
```yaml
voice:
  use_gpu: false  # Use CPU instead
```

### XTTS: Slow synthesis
- Use GPU if available
- Reduce text length
- Consider Google/OpenAI for real-time

### Google: Authentication error
```bash
# Set up Application Default Credentials
gcloud auth application-default login
```

### OpenAI: Rate limit
- Use `tts-1` instead of `tts-1-hd`
- Add delays between requests

## Examples

### Change voice at runtime
```python
# In game code
controller.voice_provider.set_speaker("voices/pirate2.wav")
controller.voice_provider.set_language("en")
```

### Disable TTS temporarily
```yaml
voice:
  enabled: false
```

### Multiple voices for different characters
```python
# Create multiple providers
pirate_voice = XTTSProvider(audio_sink, speaker_wav="pirate.wav")
narrator_voice = XTTSProvider(audio_sink, speaker_wav="narrator.wav")

# Use different voices
pirate_voice.speak(session, "Arrgh!")
narrator_voice.speak(session, "The pirate said...")