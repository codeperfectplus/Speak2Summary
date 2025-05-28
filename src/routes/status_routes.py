# cython: language_level=3
from flask import jsonify, url_for

from src.config import redis_client
from src.models import TranscriptEntry
from . import audio_bp


@audio_bp.route('/status/<file_id>', methods=['GET'])
def status(file_id):
    file_record = TranscriptEntry.query.get(file_id)
    if not file_record:
        return jsonify({'error': 'File not found'}), 404

    progress = redis_client.get(f"file:{file_id}:progress")
    progress_value = int(progress) if progress else 0 #type: ignore

    response = {
        'id': file_record.id,
        'filename': file_record.filename,
        'status': file_record.status,
        'progress': progress_value,
        'error': file_record.error_message,
        'transcript_available': file_record.transcript is not None,
        'minutes_available': file_record.minutes is not None,
        'upload_time': file_record.upload_time.isoformat(),
    }

    if file_record.status == 'completed':
        response['view_url'] = url_for('audio.view_minutes', file_id=file_record.id)

    return jsonify(response)
