# cython: language_level=3
# need to move into transmeet package
from pydub import AudioSegment
import noisereduce as nr
import numpy as np
from scipy.io import wavfile
import os

def reduce_noise(input_path: str, output_path: str):
    audio = AudioSegment.from_file(input_path)    
    temp_wav = "temp_audio.wav"
    audio.export(temp_wav, format="wav")

    rate, data = wavfile.read(temp_wav)
    if len(data.shape) == 2:
        data = data.mean(axis=1).astype(data.dtype)

    reduced_noise = nr.reduce_noise(y=data, sr=rate)
    wavfile.write(output_path, rate, reduced_noise.astype(np.int16))
    os.remove(temp_wav)
    # print(f"Noise-reduced audio saved to: {output_path}")


if __name__ == "__main__":
    reduce_noise("/home/admin/Downloads/meeting.wav", "clean_meeting_audio.wav")
