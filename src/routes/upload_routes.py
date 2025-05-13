
import os
import uuid
from flask import request, jsonify
from werkzeug.utils import secure_filename

from src.models import db, AudioFile
from src.celery_worker import process_audio_file
from src.config import app
from . import audio_bp

def save_file(file, tracking_id):
    filename = secure_filename(file.filename)
    unique_name = f"{tracking_id}_{filename}"
    path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
    file.save(path)
    return path, filename

def create_audio_file_entry(tracking_id, original_filename, filepath):
    new_file = AudioFile(
        id=tracking_id, #type: ignore
        filename=original_filename, #type: ignore
        file_path=filepath, #type: ignore
        status="queued" #type: ignore
    )
    db.session.add(new_file)
    db.session.commit()

def add_to_audio_processing_queue(tracking_id, filepath, t_client, t_model, llm_client, llm_model):
    process_audio_file.delay(tracking_id, filepath, t_client, t_model, llm_client, llm_model) #type: ignore

@audio_bp.route('/upload', methods=['POST'])
def upload():
    if 'audio' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    uploaded_files = request.files.getlist('audio')
    t_client = request.form.get('transcription-client')
    t_model = request.form.get('transcription-model')
    llm_client = request.form.get('llm-client')
    llm_model = request.form.get('llm-model')

    if not uploaded_files or uploaded_files[0].filename == '':
        return jsonify({'error': 'No selected file'}), 400

    results = []
    for file in uploaded_files:
        tracking_id = str(uuid.uuid4())
        path, original_name = save_file(file, tracking_id)
        create_audio_file_entry(tracking_id, original_name, path)
        add_to_audio_processing_queue(tracking_id, path, t_client, t_model, llm_client, llm_model)
        results.append({
            'id': tracking_id,
            'filename': original_name,
            'status': 'queued'
        })

    return jsonify(results)
