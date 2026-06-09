# cython: language_level=3
from datetime import datetime

from flask import jsonify, request
from transmeet.utils.general_utils import get_logger

from src.llm_clients import (
    generate_meeting_minutes_with_provider,
    generate_mind_map_with_provider,
)
from src.models import TranscriptEntry, db
from src.utils import render_minutes_with_tailwind
from . import audio_bp

logger = get_logger(__name__)


@audio_bp.route('/api/files', methods=['GET'])
def list_files():
    files = TranscriptEntry.query.order_by(TranscriptEntry.upload_time.desc()).all()
    return jsonify([
        {
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
            'mind_map': f.mind_map is not None,
            'topic': f.mind_map.get('Root Topic') if f.mind_map else None,
        }
        for f in files
    ])


@audio_bp.route('/api/generate_mindmap', methods=['POST'])
def generate_mindmap_api():
    """API to generate mind map from transcript."""
    data = request.get_json(silent=True) or {}
    file_id = data.get('id')
    force_regenerate = bool(data.get('force'))

    if not file_id:
        return jsonify({'error': "Missing 'id' in request body"}), 400

    file_record = TranscriptEntry.query.filter_by(id=file_id).first()

    if not file_record:
        return jsonify({'error': f'No record found for id: {file_id}'}), 404

    if file_record.mind_map and not force_regenerate:
        return jsonify({'message': 'Mind map already exists', 'mind_map': file_record.mind_map}), 200

    if not file_record.transcript:
        return jsonify({'error': 'Transcript not found for this file'}), 400

    llm_client = (data.get('llm-client') or '').strip()
    llm_model = (data.get('llm-model') or '').strip()
    llm_base_url = data.get('llm-base-url')
    llm_api_key = data.get('llm-api-key')

    if not llm_client or not llm_model:
        return jsonify({'error': "Missing 'llm-client' or 'llm-model' in request body"}), 400

    try:
        mindmap_data = generate_mind_map_with_provider(
            file_record.transcript,
            llm_client=llm_client,
            llm_model=llm_model,
            llm_base_url=llm_base_url,
            llm_api_key=llm_api_key,
        )
    except Exception as exc:
        logger.error(f'Mind map generation failed for {file_id}: {exc}')
        return jsonify({'error': str(exc)}), 500

    file_record.mind_map = mindmap_data
    file_record.llm_client = llm_client
    file_record.llm_model = llm_model
    file_record.status = 'completed'
    file_record.completion_time = datetime.utcnow()
    db.session.commit()

    return jsonify({'message': 'Mind map generated successfully', 'mind_map': mindmap_data}), 200


@audio_bp.route('/api/generate_meeting_minutes', methods=['POST'])
def generate_meeting_minutes_api():
    """API to generate meeting minutes from transcript."""
    data = request.get_json(silent=True) or {}

    file_id = data.get('id')
    force_regenerate = bool(data.get('force'))

    if not file_id:
        return jsonify({'error': "Missing 'id' in request body"}), 400

    file_record = TranscriptEntry.query.filter_by(id=file_id).first()

    if not file_record:
        return jsonify({'error': f'No record found for id: {file_id}'}), 404

    if file_record.minutes and not force_regenerate:
        return jsonify({'message': 'Meeting minutes already exist', 'minutes': file_record.minutes}), 200

    if not file_record.transcript:
        return jsonify({'error': 'Transcript not found for this file'}), 400

    llm_client = (data.get('llm-client') or '').strip()
    llm_model = (data.get('llm-model') or '').strip()
    llm_base_url = data.get('llm-base-url')
    llm_api_key = data.get('llm-api-key')

    if not llm_client or not llm_model:
        return jsonify({'error': "Missing 'llm-client' or 'llm-model' in request body"}), 400

    try:
        meeting_minutes_markdown = generate_meeting_minutes_with_provider(
            file_record.transcript,
            llm_client=llm_client,
            llm_model=llm_model,
            llm_base_url=llm_base_url,
            llm_api_key=llm_api_key,
        )
    except Exception as exc:
        logger.error(f'Meeting minutes generation failed for {file_id}: {exc}')
        return jsonify({'error': str(exc)}), 500

    meeting_minutes_html = render_minutes_with_tailwind(meeting_minutes_markdown)

    file_record.minutes_raw = meeting_minutes_markdown
    file_record.minutes = meeting_minutes_html
    file_record.llm_client = llm_client
    file_record.llm_model = llm_model
    file_record.status = 'completed'
    file_record.completion_time = datetime.utcnow()
    db.session.commit()

    return jsonify({'message': 'Meeting minutes generated successfully', 'minutes': meeting_minutes_html}), 200
