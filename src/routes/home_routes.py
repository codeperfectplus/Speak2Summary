from flask import render_template

from src.models import AudioFile
from . import audio_bp

@audio_bp.route('/', methods=['GET'])
def index():
    files = AudioFile.query.order_by(AudioFile.upload_time.desc()).all()
    return render_template('index.html', files=files)
