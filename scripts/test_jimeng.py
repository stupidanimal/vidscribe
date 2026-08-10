#!/usr/bin/env python3
"""Test Jimeng API via jimeng-free-api-all service."""

import json
import os
import requests
import sys

SESSION_ID = os.environ.get("JIMENG_SESSION_ID", "")  # Set via: export JIMENG_SESSION_ID=your_sessionid
API_URL = "https://jimeng.duckcloud.fun"

def test_generate(prompt: str, ratio: str = "9:16"):
    """Generate image from text."""
    url = f"{API_URL}/v1/images/generations"
    
    headers = {
        "Authorization": f"Bearer {SESSION_ID}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": "jimeng-4.5",
        "prompt": prompt,
        "ratio": ratio,
        "resolution": "2k",
        "n": 1,
    }
    
    print(f"Request: {url}", file=sys.stderr)
    print(f"Prompt: {prompt}", file=sys.stderr)
    
    response = requests.post(url, headers=headers, json=payload, timeout=120)
    
    print(f"Status: {response.status_code}", file=sys.stderr)
    
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # Download image if URL provided
        if "data" in data and len(data["data"]) > 0:
            img_url = data["data"][0].get("url")
            if img_url:
                print(f"\nDownloading image...", file=sys.stderr)
                img_resp = requests.get(img_url)
                with open(r"C:\Sandbox\mimocode\test_jimeng.png", "wb") as f:
                    f.write(img_resp.content)
                print(f"Saved: C:\\Sandbox\\mimocode\\test_jimeng.png", file=sys.stderr)
        return data
    else:
        print(f"Error: {response.text}", file=sys.stderr)
        return None


if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else "一个穿着西装的AI机器人站在未来城市前，赛博朋克风格，高质量，4K"
    test_generate(prompt)
