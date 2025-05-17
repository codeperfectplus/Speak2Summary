
import os
import uuid
from datetime import datetime
from flask import request, jsonify
from werkzeug.utils import secure_filename

from src.models import db, AudioFile
from src.celery_worker import process_audio_file, process_transcript_file
from src.config import app
from . import audio_bp

def save_file(file, tracking_id):
    filename = secure_filename(file.filename)
    unique_name = f"{tracking_id}_{filename}"
    path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
    file.save(path)
    return path, filename

def create_audio_file_entry(tracking_id, original_filename, filepath, t_client, t_model, llm_client, llm_model):
    new_file = AudioFile(
        id=tracking_id, #type: ignore
        filename=original_filename, #type: ignore
        file_path=filepath, #type: ignore
        status="queued", #type: ignore
        transcription_client=t_client, #type: ignore
        transcription_model=t_model, #type: ignore
        llm_client=llm_client, #type: ignore
        llm_model=llm_model #type: ignore
    )
    db.session.add(new_file)
    db.session.commit()

def create_text_file_entry(tracking_id, original_filename, filepath, llm_client, llm_model, transcription):
    new_file = AudioFile(
        id=tracking_id, #type: ignore
        filename=original_filename, #type: ignore
        file_path=filepath, #type: ignore
        status="queued", #type: ignore
        llm_client=llm_client, #type: ignore
        llm_model=llm_model, #type: ignore
        transcript=transcription #type: ignore
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
        create_audio_file_entry(tracking_id, original_name, path, t_client, t_model, llm_client, llm_model)
        add_to_audio_processing_queue(tracking_id, path, t_client, t_model, llm_client, llm_model)
        results.append({
            'id': tracking_id,
            'filename': original_name,
            'status': 'queued'
        })

    return jsonify(results)

#process_transcript_file(self, file_id, transcription_content, llm_client, llm_model):
@audio_bp.route('/upload_transcript', methods=['POST'])
def upload_transcript():
    if 'transcript_file' not in request.files and 'transcript_text' not in request.form:
        return jsonify({'error': 'No file or text provided'}), 400
    
    content = None
    # get file or text from request and generate a unique tracking ID and save it
    tracking_id = str(uuid.uuid4())
    if 'transcript_file' in request.files:
        file = request.files['transcript_file']
        
        # open text file and read the content
        if file.filename.endswith('.txt'): # type: ignore
            content = file.read().decode('utf-8')
    elif 'transcript_text' in request.form:
        content = request.form['transcript_text']

    #save in the uploads folder\

    llm_client = request.form.get('llm-client')
    llm_model = request.form.get('llm-model')

    if content is None or content == '':
        return jsonify({'error': 'No content provided'}), 400
    
    # tracking_id, original_filename, filepath, llm_client, llm_model, transcription):
    create_text_file_entry(tracking_id, 'transcript.txt', '', 'openai', 'gpt-3.5-turbo', content) #type: ignore
                                 
    process_transcript_file.delay(tracking_id, content, llm_client, llm_model) #type: ignore
    
    print(f"Transcript ID: {tracking_id}")
    print(f"Transcript Content: {content}")

    return jsonify({
        'id': tracking_id,
        'status': 'queued',    
    })

