import subprocess
from pathlib import Path


def extract_audio(video_file, output_file=None):
    video_path = Path(video_file)

    if output_file is None:
        output_file = video_path.with_suffix(".wav")

    command = [
        "ffmpeg",
        "-i", str(video_path),
        "-vn",                # no video
        "-acodec", "pcm_s16le",
        "-ar", "16000",       # 16 kHz sample rate
        "-ac", "1",           # mono audio
        str(output_file),
        "-y"
    ]

    subprocess.run(command, check=True)
    print(f"Audio saved to: {output_file}")


if __name__ == "__main__":
    extract_audio("")