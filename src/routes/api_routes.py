from flask import jsonify
from datetime import datetime
from flask import request, jsonify
from src.models import TranscriptEntry, db
from transmeet import generate_mind_map_from_transcript, generate_meeting_minutes_from_transcript
from src.utils import render_minutes_with_tailwind
from transmeet.utils.general_utils import get_logger
from src.models import TranscriptEntry
from . import audio_bp

logger = get_logger(__name__)

@audio_bp.route('/api/files', methods=['GET'])
def list_files():
    files = TranscriptEntry.query.order_by(TranscriptEntry.upload_time.desc()).all()
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
        'mind_map': f.mind_map is not None,
        'topic': f.mind_map.get('Root Topic') if f.mind_map else None,

    } for f in files])


@audio_bp.route("/api/generate_mindmap", methods=["POST"])
def generate_mindmap_api():
    """API to generate mind map from transcript"""
    data = request.get_json()
    file_id = data.get("id")

    llm_client = data.get("llm-client")
    llm_model = data.get("llm-model")
    

    if not file_id:
        return jsonify({"error": "Missing 'id' in request body"}), 400

    file_record = TranscriptEntry.query.filter_by(id=file_id).first()

    if not file_record:
        return jsonify({"error": f"No record found for id: {file_id}"}), 404

    if file_record.mind_map:
        return jsonify({"message": "Mind map already exists", "mind_map": file_record.mind_map}), 200

    if not file_record.transcript:
        return jsonify({"error": "Transcript not found for this file"}), 400

    if not llm_client or not llm_model:
        return jsonify({"error": "Missing 'llm_client' or 'llm_model' in request body"}), 400

    # Generate the mind map
    mindmap_data = generate_mind_map_from_transcript(
        file_record.transcript,
        llm_client=llm_client,
        llm_model=llm_model
    )

    file_record.mind_map = mindmap_data
    file_record.status = "completed"
    file_record.completion_time = datetime.utcnow()
    db.session.commit()

    return jsonify({"message": "Mind map generated successfully", "mind_map": mindmap_data}), 200


@audio_bp.route("/api/generate_meeting_minutes", methods=["POST"])
def generate_meeting_minutes_api():
    """API to generate meeting minutes from transcript"""
    data = request.get_json()

    file_id = data.get("id")
    llm_client = data.get("llm-client")
    llm_model = data.get("llm-model")

    if not file_id:
        return jsonify({"error": "Missing 'id' in request body"}), 400

    file_record = TranscriptEntry.query.filter_by(id=file_id).first()

    if not file_record:
        return jsonify({"error": f"No record found for id: {file_id}"}), 404

    if file_record.minutes:
        return jsonify({"message": "Meeting minutes already exist", "minutes": file_record.minutes}), 200
    
    if not file_record.transcript:
        return jsonify({"error": "Transcript not found for this file"}), 400

    if not llm_client or not llm_model:
        return jsonify({"error": "Missing 'llm_client' or 'llm_model' in request body"}), 400
    
    # Generate the meeting minutes
    meeting_minutes_markdown = generate_meeting_minutes_from_transcript(
        file_record.transcript,
        llm_client=llm_client,
        llm_model=llm_model
    )
    
    # minutes_raw
    meeting_minutes_html = render_minutes_with_tailwind(meeting_minutes_markdown)

    file_record.minutes_raw = meeting_minutes_markdown
    file_record.minutes = meeting_minutes_html
    file_record.status = "completed"
    file_record.completion_time = datetime.utcnow()
    db.session.commit()
    return jsonify({"message": "Meeting minutes generated successfully", "minutes": meeting_minutes_html}), 200

