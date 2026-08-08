#!/usr/bin/env python3
"""
Transcribe audio/video to timestamped text using faster-whisper.

Usage:
    python transcribe.py <input>               # local file
    python transcribe.py <url>                 # download via yt-dlp, then transcribe
    python transcribe.py <folder> --batch      # transcribe all media in folder

Output: plain text with timestamps, one segment per line.
"""

import argparse
import glob
import os
import subprocess
import sys
import tempfile
from pathlib import Path

MEDIA_EXTENSIONS = {".mp4", ".mkv", ".webm", ".avi", ".mov", ".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac"}


def is_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://") or s.startswith("www.")


def download_video(url: str, output_dir: str) -> str:
    """Download video/audio from URL using yt-dlp. Returns local file path."""
    try:
        import yt_dlp
    except ImportError:
        print("Error: yt-dlp not installed. Run: pip install yt-dlp", file=sys.stderr)
        sys.exit(1)

    output_template = os.path.join(output_dir, "%(title)s.%(ext)s")
    ydl_opts = {
        "outtmpl": output_template,
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "quiet": False,
        "no_warnings": False,
    }

    print(f"Downloading: {url}", file=sys.stderr)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        # yt-dlp may change extension after download
        if not os.path.exists(filename):
            # Find the actual downloaded file
            base = os.path.splitext(filename)[0]
            for ext in MEDIA_EXTENSIONS:
                candidate = base + ext
                if os.path.exists(candidate):
                    filename = candidate
                    break
        print(f"Downloaded: {filename}", file=sys.stderr)
        return filename


def extract_audio(input_path: str, output_path: str) -> bool:
    """Extract audio from video to WAV 16kHz mono using ffmpeg."""
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ffmpeg error: {result.stderr}", file=sys.stderr)
        return False
    return True


def transcribe(audio_path: str, model_size: str = "base", language: str = None) -> list:
    """Transcribe audio file, return list of (start, end, text) tuples."""
    from faster_whisper import WhisperModel

    print(f"Loading model '{model_size}'...", file=sys.stderr)
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    print(f"Transcribing '{audio_path}'...", file=sys.stderr)
    segments, info = model.transcribe(
        audio_path,
        language=language,
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500)
    )

    results = []
    for seg in segments:
        results.append((seg.start, seg.end, seg.text.strip()))

    print(f"Detected language: {info.language} (prob: {info.language_probability:.2f})", file=sys.stderr)
    print(f"Segments: {len(results)}", file=sys.stderr)

    return results


def format_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def write_output(segments: list, output_path: str):
    with open(output_path, "w", encoding="utf-8") as f:
        for start, end, text in segments:
            ts = format_timestamp(start)
            f.write(f"[{ts}] {text}\n")
    print(f"Written to: {output_path}", file=sys.stderr)


def process_single(input_path: str, model_size: str, language: str, output_path: str = None) -> str:
    """Process one file. Returns output path."""
    input_path = Path(input_path)
    if not input_path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        return None

    if not output_path:
        output_path = str(input_path.with_suffix("")) + "_transcript.txt"

    # Check if transcript already exists
    if os.path.exists(output_path):
        print(f"Transcript already exists: {output_path} (skipping)", file=sys.stderr)
        return output_path

    # Detect video vs audio
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-select_streams", "v:0",
         "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(input_path)],
        capture_output=True, text=True
    )
    is_video = "video" in probe.stdout

    if is_video:
        print("Input is video, extracting audio...", file=sys.stderr)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_audio = tmp.name
        if not extract_audio(str(input_path), tmp_audio):
            return None
        audio_to_transcribe = tmp_audio
    else:
        audio_to_transcribe = str(input_path)

    try:
        segments = transcribe(audio_to_transcribe, model_size, language)
        write_output(segments, output_path)

        for start, end, text in segments:
            ts = format_timestamp(start)
            print(f"[{ts}] {text}")

        return output_path
    finally:
        if is_video and os.path.exists(tmp_audio):
            os.unlink(tmp_audio)


def main():
    parser = argparse.ArgumentParser(description="Transcribe audio/video to text")
    parser.add_argument("input", help="Input file, URL, or folder (with --batch)")
    parser.add_argument("--model", default="base",
                        choices=["tiny", "base", "small", "medium", "large-v3"],
                        help="Whisper model size (default: base)")
    parser.add_argument("--language", default=None,
                        help="Language code (e.g., en, zh, ja). Auto-detect if not set.")
    parser.add_argument("--output", default=None,
                        help="Output file path (default: <input>_transcript.txt)")
    parser.add_argument("--batch", action="store_true",
                        help="Process all media files in the input folder")
    args = parser.parse_args()

    downloaded_file = None

    try:
        if args.batch:
            # Batch mode: process all media files in folder
            folder = Path(args.input)
            if not folder.is_dir():
                print(f"Error: not a directory: {folder}", file=sys.stderr)
                sys.exit(1)

            media_files = sorted([
                f for f in folder.iterdir()
                if f.suffix.lower() in MEDIA_EXTENSIONS and not f.stem.endswith("_transcript")
            ])

            if not media_files:
                print(f"No media files found in {folder}", file=sys.stderr)
                sys.exit(1)

            print(f"Found {len(media_files)} media files", file=sys.stderr)
            for i, f in enumerate(media_files, 1):
                print(f"\n[{i}/{len(media_files)}] {f.name}", file=sys.stderr)
                process_single(str(f), args.model, args.language)

        elif is_url(args.input):
            # URL mode: download then transcribe
            with tempfile.TemporaryDirectory() as tmpdir:
                downloaded_file = download_video(args.input, tmpdir)
                output_path = args.output or (str(Path(downloaded_file).with_suffix("")) + "_transcript.txt")
                process_single(downloaded_file, args.model, args.language, output_path)

        else:
            # Single file mode
            process_single(args.input, args.model, args.language, args.output)

    finally:
        # Cleanup downloaded file if it was in a temp dir
        pass


if __name__ == "__main__":
    main()
