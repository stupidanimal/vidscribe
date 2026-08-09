#!/usr/bin/env python3
"""
Video narrator: transcribe → LLM rewrite → TTS → combine.

Usage:
    python narrate.py <video>                  # auto: summarize + translate to Chinese
    python narrate.py <video> --lang zh        # force Chinese narration
    python narrate.py <video> --lang en        # force English narration
    python narrate.py <video> --full           # full translation (not summarized)
"""

import argparse
import asyncio
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def transcribe_video(video_path: str, model: str = "auto", language: str = None) -> str:
    """Transcribe video using transcribe.py, return transcript text."""
    script_dir = Path(__file__).parent
    transcribe_script = script_dir / "transcribe.py"
    
    transcript_path = str(Path(video_path).with_suffix("")) + "_transcript.txt"
    if os.path.exists(transcript_path):
        print(f"Transcript exists: {transcript_path}", file=sys.stderr)
        with open(transcript_path, "r", encoding="utf-8") as f:
            return f.read()
    
    cmd = ["python", str(transcribe_script), video_path, "--model", model, "--no-srt"]
    if language:
        cmd.extend(["--language", language])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Transcription failed: {result.stderr}", file=sys.stderr)
        return None
    
    with open(transcript_path, "r", encoding="utf-8") as f:
        return f.read()


def detect_language(text: str) -> str:
    """Detect language from transcript text."""
    cjk_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    total = len(text)
    if total > 0 and cjk_count / total > 0.1:
        return "zh"
    return "en"


def clean_transcript(raw_text: str) -> str:
    """Remove timestamps from transcript."""
    lines = []
    for line in raw_text.strip().split("\n"):
        if line.startswith("[") and "]" in line:
            line = line[line.index("]")+1:].strip()
        if line:
            lines.append(line)
    return " ".join(lines)


def rewrite_with_llm(transcript: str, target_lang: str = "zh", style: str = "summary") -> str:
    """Use LLM to rewrite transcript into narration script.
    
    This function prints the prompt for the agent to process.
    The agent should call this with the actual LLM.
    """
    if style == "summary":
        if target_lang == "zh":
            prompt = f"""请将以下视频内容总结为一段中文解说稿。要求：
1. 提炼核心观点，不要逐字翻译
2. 用播音员的口吻，流畅自然
3. 控制在200-300字
4. 保留关键数据和人名
5. 去掉口语化表达（嗯、啊、那个）

原始内容：
{transcript[:3000]}

请直接输出解说稿，不要加任何前缀说明。"""
        else:
            prompt = f"""Summarize the following video content into a concise narration script. Requirements:
1. Extract key points, don't translate word-for-word
2. Professional news anchor tone
3. 150-250 words
4. Keep key data and names
5. Remove filler words (um, uh, like, you know)

Original content:
{transcript[:3000]}

Output the narration script directly, no prefix."""
    else:  # full translation
        if target_lang == "zh":
            prompt = f"""请将以下视频内容翻译为中文解说稿。要求：
1. 完整翻译，不要遗漏重要内容
2. 用播音员的口吻，流畅自然
3. 保留关键数据和人名
4. 去掉口语化表达

原始内容：
{transcript[:5000]}

请直接输出解说稿。"""
        else:
            prompt = f"""Rewrite the following transcript as a professional narration. Requirements:
1. Keep all important content
2. Professional news anchor tone
3. Keep key data and names
4. Remove filler words

Original content:
{transcript[:5000]}

Output the narration script directly."""
    
    # Write prompt to temp file for agent to process
    prompt_path = str(Path(transcript[:50].split()[0] if transcript else "narration").parent / "_narration_prompt.txt")
    prompt_path = os.path.join(tempfile.gettempdir(), "vidscribe_narration_prompt.txt")
    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write(prompt)
    
    print(f"LLM prompt written to: {prompt_path}", file=sys.stderr)
    print(f"Agent should read this file and generate narration.", file=sys.stderr)
    
    return prompt_path


def get_default_voice(language: str) -> str:
    """Get default voice based on language."""
    voices = {
        "zh": "zh-CN-YunyangNeural",
        "en": "en-US-BrianNeural",
        "ja": "ja-JP-KeitaNeural",
    }
    return voices.get(language, "en-US-BrianNeural")


async def generate_narration(text: str, voice: str, output_path: str, rate: str = "+0%"):
    """Generate narration audio using edge-tts."""
    import edge_tts
    
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_path)
    print(f"Narration audio: {output_path}", file=sys.stderr)


def combine_audio_video(video_path: str, narration_path: str, output_path: str, 
                        lower_original: bool = True) -> bool:
    """Combine narration audio with video."""
    if lower_original:
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", narration_path,
            "-filter_complex",
            "[0:a]volume=0.2[orig];[1:a]volume=1.0[narr];[orig][narr]amix=inputs=2:duration=first[out]",
            "-map", "0:v",
            "-map", "[out]",
            "-c:v", "copy",
            "-shortest",
            output_path
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", narration_path,
            "-map", "0:v",
            "-map", "1:a",
            "-c:v", "copy",
            "-shortest",
            output_path
        ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ffmpeg error: {result.stderr}", file=sys.stderr)
        return False
    print(f"Narrated video: {output_path}", file=sys.stderr)
    return True


async def main():
    parser = argparse.ArgumentParser(description="Generate video narration")
    parser.add_argument("input", help="Input video file")
    parser.add_argument("--voice", default=None, help="TTS voice")
    parser.add_argument("--lang", default=None, choices=["zh", "en", "ja"],
                        help="Target narration language (default: auto-detect)")
    parser.add_argument("--style", default="summary", choices=["summary", "full"],
                        help="Narration style (default: summary)")
    parser.add_argument("--rate", default="+0%", help="Speech rate")
    parser.add_argument("--replace", action="store_true", help="Replace original audio")
    parser.add_argument("--model", default="auto", help="Whisper model")
    parser.add_argument("--output", default=None, help="Output file path")
    parser.add_argument("--narration-text", default=None,
                        help="Path to narration text file (skip LLM step)")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    # Step 1: Transcribe
    print("Step 1: Transcribing...", file=sys.stderr)
    raw_text = transcribe_video(str(input_path), args.model)
    if not raw_text:
        sys.exit(1)
    
    source_lang = detect_language(raw_text)
    target_lang = args.lang or ("zh" if source_lang != "zh" else "en")
    print(f"Source: {source_lang}, Target: {target_lang}", file=sys.stderr)
    
    # Step 2: Get narration text
    if args.narration_text:
        # Use provided narration text
        with open(args.narration_text, "r", encoding="utf-8") as f:
            narration_text = f.read().strip()
        print(f"Using provided narration text ({len(narration_text)} chars)", file=sys.stderr)
    else:
        # Generate LLM prompt
        print("Step 2: Generating LLM prompt...", file=sys.stderr)
        prompt_path = rewrite_with_llm(raw_text, target_lang, args.style)
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"Please generate narration using LLM:", file=sys.stderr)
        print(f"  1. Read: {prompt_path}", file=sys.stderr)
        print(f"  2. Generate narration text", file=sys.stderr)
        print(f"  3. Save to a file", file=sys.stderr)
        print(f"  4. Run: python narrate.py \"{input_path}\" --narration-text <file> --lang {target_lang}", file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr)
        return
    
    # Step 3: Generate TTS
    voice = args.voice or get_default_voice(target_lang)
    print(f"Step 3: Generating narration (voice: {voice})...", file=sys.stderr)
    
    narration_path = str(input_path.with_suffix("")) + "_narration.mp3"
    await generate_narration(narration_text, voice, narration_path, args.rate)
    
    # Step 4: Combine
    if args.output:
        output_path = args.output
    else:
        output_path = str(input_path.with_suffix("")) + "_narrated" + input_path.suffix
    
    print("Step 4: Combining audio...", file=sys.stderr)
    combine_audio_video(str(input_path), narration_path, output_path, 
                        lower_original=not args.replace)
    
    print(f"\nDone! Output: {output_path}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
