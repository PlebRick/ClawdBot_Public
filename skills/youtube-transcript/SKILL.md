---
name: youtube-transcript
description: >
  Fetch and transcribe YouTube videos using yt-dlp + OpenAI Whisper.
  Use when asked to transcribe, summarize, or extract content from YouTube videos.
  Runs entirely local - no API keys or VPN required.
---

# YouTube Transcript

Fetch transcripts from YouTube videos using local tools (yt-dlp + Whisper).

## Quick Start

```bash
# Basic usage - returns JSON with transcript
python3 scripts/yt-transcript.py <video_url_or_id>

# Specify whisper model (tiny|base|small|medium|large)
python3 scripts/yt-transcript.py <video_url_or_id> --model base

# Specify language hint
python3 scripts/yt-transcript.py <video_url_or_id> --language en

# Output plain text instead of JSON
python3 scripts/yt-transcript.py <video_url_or_id> --format text

# Keep audio file after transcription
python3 scripts/yt-transcript.py <video_url_or_id> --keep-audio
```

## Examples

```bash
# Transcribe a video
python3 scripts/yt-transcript.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Short video ID works too
python3 scripts/yt-transcript.py dQw4w9WgXcQ

# Use smaller model for speed
python3 scripts/yt-transcript.py dQw4w9WgXcQ --model tiny

# Use larger model for accuracy
python3 scripts/yt-transcript.py dQw4w9WgXcQ --model medium
```

## Output

**JSON format (default):**
```json
{
  "video_id": "dQw4w9WgXcQ",
  "title": "Video Title",
  "channel": "Channel Name",
  "duration": 212,
  "model": "base",
  "language": "en",
  "full_text": "Full transcript text...",
  "segments": [
    {"start": 0.0, "end": 4.2, "text": "First segment..."},
    ...
  ]
}
```

**Text format (`--format text`):**
Plain transcript text only.

## Model Selection Guide

| Model | Speed | Accuracy | VRAM | Use Case |
|-------|-------|----------|------|----------|
| tiny | ~10x realtime | Fair | ~1GB | Quick previews |
| base | ~7x realtime | Good | ~1GB | Default, good balance |
| small | ~4x realtime | Better | ~2GB | Important content |
| medium | ~2x realtime | Great | ~5GB | Accuracy matters |
| large | ~1x realtime | Best | ~10GB | Critical transcripts |

## Workflow Integration

For sermon research or study:
```bash
# 1. Transcribe
python3 scripts/yt-transcript.py <url> --model small > transcript.json

# 2. Extract just the text
jq -r '.full_text' transcript.json > transcript.txt

# 3. Summarize with Claude/Gemini as needed
```

## Dependencies

- `yt-dlp` - YouTube download
- `whisper` - OpenAI Whisper transcription  
- `ffmpeg` - Audio processing

Install: `pip3 install yt-dlp openai-whisper`

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| Video unavailable | Region/age restricted | Try with cookies or different video |
| CUDA out of memory | Model too large | Use smaller model (`--model base`) |
| Slow transcription | Large model on CPU | Use `tiny` or `base` model |

## Notes

- First run downloads the Whisper model (~140MB for base)
- Transcription runs on GPU if CUDA available, CPU otherwise
- Temp audio files auto-cleanup unless `--keep-audio` specified
