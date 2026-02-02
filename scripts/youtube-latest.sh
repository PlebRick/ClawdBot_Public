#!/bin/bash
# Fetch latest videos from a YouTube channel
# Usage: youtube-latest.sh <channel_name_or_id> [max_results]
#
# Examples:
#   youtube-latest.sh "Trading Fraternity" 3
#   youtube-latest.sh UCsfp0zw1hNxpy_wDig8oExA 5

QUERY=$(echo "$1" | sed 's/ /+/g')
MAX="${2:-3}"
API_KEY=$(cat /home/ubuntu76/.config/clawd/youtube-api-key.json | grep api_key | cut -d'"' -f4)

if [ -z "$QUERY" ]; then
  echo "Usage: youtube-latest.sh <channel_name_or_query> [max_results]"
  exit 1
fi

curl -s "https://www.googleapis.com/youtube/v3/search?part=snippet&q=${QUERY}&order=date&maxResults=${MAX}&type=video&key=${API_KEY}" | \
  python3 -c "
import sys, json
data = json.load(sys.stdin)
for item in data.get('items', []):
    s = item['snippet']
    vid = item['id']['videoId']
    print(f\"📺 {s['title']}\")
    print(f\"   Channel: {s['channelTitle']}\")
    print(f\"   Published: {s['publishedAt'][:10]}\")
    print(f\"   https://youtube.com/watch?v={vid}\")
    print()
"
