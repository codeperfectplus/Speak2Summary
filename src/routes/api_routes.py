from flask import jsonify

from src.models import AudioFile
from . import audio_bp

@audio_bp.route('/api/files', methods=['GET'])
def list_files():
    files = AudioFile.query.order_by(AudioFile.upload_time.desc()).all()
    return jsonify([{
        'id': f.id,
        'filename': f.filename,
        'status': f.status,
        'upload_time': f.upload_time.isoformat(),
        'transcript_available': f.transcript is not None,
        'minutes_available': f.minutes is not None,
        'error_message': f.error_message,
        'transcription_client': f.transcription_client,
        'transcription_model': f.transcription_model,
        'llm_client': f.llm_client,
        'llm_model': f.llm_model,
        'mind_map': f.mind_map,

    } for f in files])
