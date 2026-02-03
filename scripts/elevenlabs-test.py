#!/usr/bin/env python3
"""
ElevenLabs API Test Script
Tests voice listing and audio generation using Rick's cloned voice.
"""

import os
import sys
import argparse
import requests
from pathlib import Path

BASE_URL = "https://api.elevenlabs.io/v1"
DEFAULT_VOICE_ID = "VetLYaRsPXWId0NB3QSJ"  # Chaplain2
DEFAULT_MODEL = "eleven_multilingual_v2"
TEST_TEXT = "This is a test of the ElevenLabs text-to-speech system using Rick's cloned voice."


def get_api_key(args_key=None):
    """Get API key from arg or environment."""
    key = args_key or os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        print("Error: No API key provided. Set ELEVENLABS_API_KEY or use --api-key")
        sys.exit(1)
    return key


def list_voices(api_key):
    """List all available voices."""
    resp = requests.get(
        f"{BASE_URL}/voices",
        headers={"xi-api-key": api_key}
    )
    resp.raise_for_status()
    voices = resp.json().get("voices", [])
    
    print("\n=== Available Voices ===")
    print(f"{'Name':<40} {'ID':<25} {'Category':<15}")
    print("-" * 80)
    
    for v in voices:
        name = v.get("name", "Unknown")[:38]
        vid = v.get("voice_id", "")[:23]
        cat = v.get("category", "")[:13]
        print(f"{name:<40} {vid:<25} {cat:<15}")
    
    print(f"\nTotal: {len(voices)} voices")
    return voices


def generate_audio(api_key, text, voice_id=DEFAULT_VOICE_ID, model=DEFAULT_MODEL):
    """Generate audio from text."""
    print(f"\n=== Generating Audio ===")
    print(f"Voice ID: {voice_id}")
    print(f"Model: {model}")
    print(f"Text ({len(text)} chars): {text[:60]}...")
    
    resp = requests.post(
        f"{BASE_URL}/text-to-speech/{voice_id}",
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        },
        json={
            "text": text,
            "model_id": model,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
    )
    resp.raise_for_status()
    return resp.content


def get_subscription(api_key):
    """Get subscription info for character usage."""
    resp = requests.get(
        f"{BASE_URL}/user/subscription",
        headers={"xi-api-key": api_key}
    )
    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description="Test ElevenLabs API")
    parser.add_argument("--api-key", help="ElevenLabs API key")
    parser.add_argument("--voice-id", default=DEFAULT_VOICE_ID, help="Voice ID to use")
    parser.add_argument("--text", default=TEST_TEXT, help="Text to synthesize")
    parser.add_argument("--output", default=None, help="Output file path")
    parser.add_argument("--list-only", action="store_true", help="Only list voices")
    args = parser.parse_args()
    
    api_key = get_api_key(args.api_key)
    
    # List voices
    voices = list_voices(api_key)
    
    if args.list_only:
        return
    
    # Generate audio
    audio_data = generate_audio(api_key, args.text, args.voice_id)
    
    # Save output
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    output_path = Path(args.output) if args.output else output_dir / "test-audio.mp3"
    
    with open(output_path, "wb") as f:
        f.write(audio_data)
    
    print(f"\n=== Output ===")
    print(f"Saved to: {output_path}")
    print(f"Size: {len(audio_data):,} bytes")
    
    # Show subscription info
    try:
        sub = get_subscription(api_key)
        used = sub.get("character_count", 0)
        limit = sub.get("character_limit", 0)
        print(f"\n=== Usage ===")
        print(f"Characters used: {used:,} / {limit:,} ({100*used/limit:.1f}%)")
    except Exception as e:
        print(f"Could not fetch usage: {e}")
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    main()
