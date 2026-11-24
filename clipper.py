import os
import sys
import subprocess
from faster_whisper import WhisperModel


def format_ass_time(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis == 100:
        secs += 1
        centis = 0
    return f"{hrs}:{mins:02d}:{secs:02d}.{centis:02d}"


def find_best_clip_window(words, target_duration=45.0):
    """Finds the densest spoken window of `target_duration` seconds."""
    if not words:
        return 0.0, target_duration
    total_end = words[-1]["end"]
    if total_end <= target_duration:
        return 0.0, total_end

    best_start = 0.0
    max_words = 0
    for i, w in enumerate(words):
        start_t = w["start"]
        end_t = start_t + target_duration
        if end_t > total_end:
            break
        count = sum(1 for x in words[i:] if x["end"] <= end_t)
        if count > max_words:
            max_words = count
            best_start = start_t

    return best_start, min(best_start + target_duration, total_end)


def generate_hormozi_ass(words, clip_start, clip_end, ass_path):
    """Generates an .ass file with 3-word chunks and active yellow word highlight."""
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,78,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,8,3,2,60,60,340,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    clip_words = [
        {
            "word": w["word"].strip().upper(),
            "start": max(0.0, w["start"] - clip_start),
            "end": max(0.0, w["end"] - clip_start),
        }
        for w in words
        if w["end"] > clip_start and w["start"] < clip_end
    ]

    events = []
    chunk_size = 3
    for i in range(0, len(clip_words), chunk_size):
        chunk = clip_words[i : i + chunk_size]
        for active_idx, active_word in enumerate(chunk):
            ev_start = active_word["start"]
            ev_end = (
                chunk[active_idx + 1]["start"]
                if active_idx + 1 < len(chunk)
                else active_word["end"]
            )
            if ev_end <= ev_start:
                ev_end = ev_start + 0.12

            styled_tokens = []
            for idx, token in enumerate(chunk):
                clean = token["word"].replace("{", "").replace("}", "")
                if idx == active_idx:
                    styled_tokens.append(
                        r"{\c&H0000FFFF&\fscx112\fscy112}"
                        + clean
                        + r"{\c&H00FFFFFF&\fscx100\fscy100}"
                    )
                else:
                    styled_tokens.append(clean)

            line_text = " ".join(styled_tokens)
            events.append(
                f"Dialogue: 0,{format_ass_time(ev_start)},{format_ass_time(ev_end)},Default,,0,0,0,,{line_text}"
            )

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events) + "\n")


def process_video(
    input_video: str,
    output_video: str = "viral_clip.mp4",
    clip_duration: float = 45.0,
    start_time: float | None = None,
):
    if not os.path.exists(input_video):
        print(f"Error: File '{input_video}' not found.")
        return

    print("[1/3] Transcribing audio with word-level timestamps...")
    model = WhisperModel("base.en", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(
        input_video,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=400),
    )

    words = []
    for seg in segments:
        if seg.words:
            for w in seg.words:
                words.append({"word": w.word, "start": w.start, "end": w.end})

    if not words:
        print("No speech detected in video.")
        return

    if start_time is not None and start_time >= 0:
        total_end = words[-1]["end"]
        clip_start = min(float(start_time), max(0.0, total_end - 1.0))
        clip_end = min(clip_start + float(clip_duration), total_end + 2.0)
        print(f"[2/3] Manual start time set: {clip_start:.1f}s -> {clip_end:.1f}s ({clip_end - clip_start:.1f}s)")
    else:
        clip_start, clip_end = find_best_clip_window(words, target_duration=clip_duration)
        print(f"[2/3] Best viral window found: {clip_start:.1f}s -> {clip_end:.1f}s ({clip_end - clip_start:.1f}s)")

    actual_duration = max(1.0, clip_end - clip_start)
    ass_file = "captions.ass"
    generate_hormozi_ass(words, clip_start, clip_end, ass_file)

    print("[3/3] Cropping 9:16 vertical & burning animated captions via FFmpeg...")
    vf_filter = f"crop=ih*9/16:ih,scale=1080:1920,ass={ass_file}"
    cmd = [
        "ffmpeg",
        "-y",
        "-ss", f"{clip_start:.3f}",
        "-i", input_video,
        "-t", f"{actual_duration:.3f}",
        "-vf", vf_filter,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        output_video,
    ]
    subprocess.run(cmd, check=True)
    print(f"Done! Saved watermark-free vertical clip to: {output_video}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python clipper.py <path_to_video.mp4> [clip_duration_seconds] [start_time_seconds]")
        sys.exit(1)
    video_file = sys.argv[1]
    duration = float(sys.argv[2]) if len(sys.argv) > 2 else 45.0
    manual_start = float(sys.argv[3]) if len(sys.argv) > 3 else None
    process_video(video_file, "viral_clip.mp4", duration, start_time=manual_start)