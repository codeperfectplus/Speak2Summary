# cython: language_level=3
from flask import render_template

from src.models import TranscriptEntry
from . import audio_bp

@audio_bp.route('/view/<file_id>', methods=['GET'])
def view_minutes(file_id):
    file = TranscriptEntry.query.get(file_id)
    if not file or file.status != 'completed':
        return render_template('error.html', message="File not found or processing not complete"), 404

    return render_template('view.html', file=file)
