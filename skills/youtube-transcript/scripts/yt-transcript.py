#!/usr/bin/env python3
"""
YouTube Transcript - Local transcription using yt-dlp + Whisper.
No API keys or VPN required.
"""

import sys
import os
import json
import argparse
import tempfile
import subprocess
import re
from pathlib import Path

def extract_video_id(url_or_id: str) -> str:
    """Extract video ID from URL or return as-is."""
    patterns = [
        r"(?:v=|/v/|youtu\.be/|/embed/|/shorts/|/live/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$"
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return url_or_id

def get_video_info(video_id: str) -> dict:
    """Get video metadata via yt-dlp."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        result = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-download", url],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                "title": data.get("title", "Unknown"),
                "channel": data.get("channel", data.get("uploader", "Unknown")),
                "duration": data.get("duration", 0),
                "description": data.get("description", "")[:500]
            }
    except Exception as e:
        pass
    return {"title": "Unknown", "channel": "Unknown", "duration": 0, "description": ""}

def download_audio(video_id: str, output_path: str) -> bool:
    """Download audio from YouTube video."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        result = subprocess.run([
            "yt-dlp",
            "-x",  # Extract audio
            "--audio-format", "mp3",
            "--audio-quality", "0",  # Best quality
            "-o", output_path,
            "--no-playlist",
            "--no-warnings",
            url
        ], capture_output=True, text=True, timeout=300)
        return result.returncode == 0 and os.path.exists(output_path)
    except Exception as e:
        print(json.dumps({"error": f"Download failed: {e}"}), file=sys.stderr)
        return False

def transcribe_audio(audio_path: str, model: str = "base", language: str = None) -> dict:
    """Transcribe audio using Whisper."""
    try:
        import whisper
        
        # Load model
        whisper_model = whisper.load_model(model)
        
        # Transcribe
        options = {"fp16": False}  # CPU-safe default
        if language:
            options["language"] = language
            
        result = whisper_model.transcribe(audio_path, **options)
        
        return {
            "text": result.get("text", "").strip(),
            "language": result.get("language", "unknown"),
            "segments": [
                {
                    "start": round(seg["start"], 2),
                    "end": round(seg["end"], 2),
                    "text": seg["text"].strip()
                }
                for seg in result.get("segments", [])
            ]
        }
    except Exception as e:
        return {"error": f"Transcription failed: {e}"}

def main():
    parser = argparse.ArgumentParser(description="Transcribe YouTube videos locally")
    parser.add_argument("video", help="YouTube URL or video ID")
    parser.add_argument("--model", "-m", default="base", 
                       choices=["tiny", "base", "small", "medium", "large"],
                       help="Whisper model size (default: base)")
    parser.add_argument("--language", "-l", help="Language hint (e.g., 'en', 'es')")
    parser.add_argument("--format", "-f", default="json", choices=["json", "text"],
                       help="Output format (default: json)")
    parser.add_argument("--keep-audio", "-k", action="store_true",
                       help="Keep downloaded audio file")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    
    args = parser.parse_args()
    
    # Extract video ID
    video_id = extract_video_id(args.video)
    
    # Get video info
    info = get_video_info(video_id)
    
    # Create temp directory for audio
    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = os.path.join(tmpdir, f"{video_id}.mp3")
        
        # Download audio
        sys.stderr.write(f"Downloading audio for {video_id}...\n")
        if not download_audio(video_id, audio_path):
            print(json.dumps({"error": "Failed to download audio", "video_id": video_id}))
            sys.exit(1)
        
        # Transcribe
        sys.stderr.write(f"Transcribing with {args.model} model...\n")
        transcript = transcribe_audio(audio_path, args.model, args.language)
        
        if "error" in transcript:
            print(json.dumps({"error": transcript["error"], "video_id": video_id}))
            sys.exit(1)
        
        # Keep audio if requested
        if args.keep_audio:
            keep_path = f"{video_id}.mp3"
            subprocess.run(["cp", audio_path, keep_path])
            sys.stderr.write(f"Audio saved to {keep_path}\n")
    
    # Build output
    if args.format == "text":
        output = transcript["text"]
    else:
        output = json.dumps({
            "video_id": video_id,
            "title": info["title"],
            "channel": info["channel"],
            "duration": info["duration"],
            "model": args.model,
            "language": transcript["language"],
            "full_text": transcript["text"],
            "segments": transcript["segments"]
        }, indent=2)
    
    # Write output
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        sys.stderr.write(f"Output written to {args.output}\n")
    else:
        print(output)

if __name__ == "__main__":
    main()
