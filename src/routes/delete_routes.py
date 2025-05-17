import os
from flask import jsonify

from src.config import redis_client
from src.models import db, TranscriptEntry
from . import audio_bp


@audio_bp.route('/delete/<file_id>', methods=['POST'])
def delete_file(file_id):
    file = TranscriptEntry.query.get(file_id)
    if not file:
        return jsonify({'error': 'File not found'}), 404

    if os.path.exists(file.file_path):
        os.remove(file.file_path)

    redis_client.delete(f"file:{file_id}:progress")
    db.session.delete(file)
    db.session.commit()

    return jsonify({'success': True})
