# cython: language_level=3
import subprocess
from pathlib import Path
from typing import Optional


def extract_audio(video_file: str, output_file: Optional[str] = None) -> str:
    """Extract mono 16kHz WAV audio from a video file using ffmpeg."""
    video_path = Path(video_file)

    if output_file is None:
        output_path = video_path.with_suffix(".wav")
    else:
        output_path = Path(output_file)

    command = [
        "ffmpeg",
        "-i",
        str(video_path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        str(output_path),
        "-y",
    ]

    subprocess.run(command, check=True)
    return str(output_path)


if __name__ == "__main__":
    extract_audio("videos/sample.mp4")
