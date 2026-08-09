#!/usr/bin/env python3
"""
Image slideshow video generator: combine images + audio into video.

Usage:
    python slideshow.py --audio narration.mp3 --images img1.png img2.png ... --output video.mp4
    python slideshow.py --audio narration.mp3 --image-dir ./images/ --output video.mp4
    python slideshow.py --audio narration.mp3 --segments segments.json --output video.mp4
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def get_audio_duration(audio_path: str) -> float:
    """Get audio duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "csv=p=0", audio_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def create_slideshow(images: list, durations: list, output_path: str, audio_path: str = None):
    """Create video from images with durations, optionally add audio."""
    if not images:
        print("Error: no images provided", file=sys.stderr)
        return False
    
    # Create temporary concat file for ffmpeg
    concat_path = output_path + ".concat.txt"
    with open(concat_path, "w", encoding="utf-8") as f:
        for img, dur in zip(images, durations):
            f.write(f"file '{os.path.abspath(img)}'\n")
            f.write(f"duration {dur}\n")
        # Last image needs to be repeated for ffmpeg concat
        f.write(f"file '{os.path.abspath(images[-1])}'\n")
    
    if audio_path:
        # With audio
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_path,
            "-i", audio_path,
            "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k",
            "-shortest",
            output_path
        ]
    else:
        # Without audio (silent)
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_path,
            "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            output_path
        ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    os.unlink(concat_path)
    
    if result.returncode != 0:
        print(f"ffmpeg error: {result.stderr}", file=sys.stderr)
        return False
    
    print(f"Video created: {output_path}", file=sys.stderr)
    return True


def equal_split(total_duration: float, num_images: int) -> list:
    """Split total duration equally among images."""
    duration_each = total_duration / num_images
    return [duration_each] * num_images


def from_segments(segments_file: str) -> tuple:
    """Load segments from JSON file.
    
    Format: [{"image": "path.png", "duration": 10.5}, ...]
    """
    with open(segments_file, "r", encoding="utf-8") as f:
        segments = json.load(f)
    
    images = [s["image"] for s in segments]
    durations = [s["duration"] for s in segments]
    return images, durations


def main():
    parser = argparse.ArgumentParser(description="Create slideshow video from images + audio")
    parser.add_argument("--audio", help="Audio file (narration)")
    parser.add_argument("--images", nargs="+", help="Image files (in order)")
    parser.add_argument("--image-dir", help="Directory containing images (sorted by name)")
    parser.add_argument("--segments", help="JSON file with image+duration pairs")
    parser.add_argument("--output", required=True, help="Output video file")
    parser.add_argument("--fps", type=int, default=30, help="Output video FPS (default: 30)")
    args = parser.parse_args()
    
    # Collect images
    if args.segments:
        images, durations = from_segments(args.segments)
    elif args.images:
        images = args.images
        if args.audio:
            total_dur = get_audio_duration(args.audio)
            durations = equal_split(total_dur, len(images))
        else:
            durations = [5.0] * len(images)  # default 5 seconds each
    elif args.image_dir:
        image_dir = Path(args.image_dir)
        images = sorted([
            str(f) for f in image_dir.iterdir()
            if f.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
        ])
        if not images:
            print(f"No images found in {image_dir}", file=sys.stderr)
            sys.exit(1)
        if args.audio:
            total_dur = get_audio_duration(args.audio)
            durations = equal_split(total_dur, len(images))
        else:
            durations = [5.0] * len(images)
    else:
        parser.error("Provide --images, --image-dir, or --segments")
    
    # Validate images exist
    for img in images:
        if not os.path.exists(img):
            print(f"Error: image not found: {img}", file=sys.stderr)
            sys.exit(1)
    
    print(f"Images: {len(images)}", file=sys.stderr)
    print(f"Total duration: {sum(durations):.1f}s", file=sys.stderr)
    for i, (img, dur) in enumerate(zip(images, durations)):
        print(f"  [{i+1}] {Path(img).name} — {dur:.1f}s", file=sys.stderr)
    
    create_slideshow(images, durations, args.output, args.audio)


if __name__ == "__main__":
    main()
