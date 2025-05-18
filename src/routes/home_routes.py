from flask import render_template

from src.models import TranscriptEntry
from . import audio_bp

import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

models_path = ROOT_DIR / 'src/models.json'

with open(models_path, 'r') as f:
    model_config = json.load(f)

transcription_model_to_client = model_config['transcription_model_to_client']
llm_model_to_client = model_config['llm_model_to_client']
transcription_model_list = list(transcription_model_to_client.keys())
llm_model_list = list(llm_model_to_client.keys())


@audio_bp.route('/', methods=['GET'])
def index():
    files = TranscriptEntry.query.order_by(TranscriptEntry.upload_time.desc()).all()
    return render_template('index.html', files=files,         transcription_model_to_client=transcription_model_to_client,
        llm_model_to_client=llm_model_to_client,
        transcription_model_list=transcription_model_list,
        llm_model_list=llm_model_list)
