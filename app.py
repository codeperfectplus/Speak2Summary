from flask import Flask, render_template, request, jsonify, url_for, redirect
import os
import uuid
from werkzeug.utils import secure_filename
from celery_worker import process_audio_file
from models import db, AudioFile
import redis

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 1000 * 1024 * 1024  # 100MB max upload
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'transmeet.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
db.init_app(app)

# Initialize Redis connection
redis_client = redis.Redis(host='redis', port=6379, db=0)

with app.app_context():
    db.create_all()

@app.route('/', methods=['GET'])
def index():
    # Get all audio files from database
    files = AudioFile.query.order_by(AudioFile.upload_time.desc()).all()
    return render_template('index.html', files=files)

@app.route('/upload', methods=['POST'])
def upload():
    if 'audio' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    uploaded_files = request.files.getlist('audio')

    transcription_client = request.form.get('transcription-client')
    transcription_model = request.form.get('transcription-model')
    llm_client = request.form.get('llm-client')
    llm_model = request.form.get('llm-model')
    
    if not uploaded_files or uploaded_files[0].filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    results = []
    
    for file in uploaded_files:
        if file and file.filename:
            # Generate a unique ID for tracking
            tracking_id = str(uuid.uuid4())
            original_filename = file.filename
            secure_name = secure_filename(original_filename)
            
            # Create unique filename with UUID to prevent collisions
            unique_filename = f"{tracking_id}_{secure_name}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            # Save the file
            file.save(filepath)
            
            # Create database entry
            new_file = AudioFile(
                id=tracking_id,
                filename=original_filename,
                file_path=filepath,
                status="queued"
            )
            db.session.add(new_file)
            db.session.commit()
            
            # Add to queue - send to Celery task
            process_audio_file.delay(tracking_id, filepath, transcription_client, transcription_model, llm_client, llm_model)
            
            results.append({
                'id': tracking_id,
                'filename': original_filename,
                'status': 'queued'
            })
    
    return jsonify(results)

@app.route('/status/<file_id>', methods=['GET'])
def status(file_id):
    file_record = AudioFile.query.get(file_id)
    
    if not file_record:
        return jsonify({'error': 'File not found'}), 404
    
    # Get progress from Redis if available
    progress = redis_client.get(f"file:{file_id}:progress")
    progress_value = int(progress) if progress else 0
    
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
        response['view_url'] = url_for('view_minutes', file_id=file_record.id)
    
    return jsonify(response)

@app.route('/view/<file_id>', methods=['GET'])
def view_minutes(file_id):
    file_record = AudioFile.query.get(file_id)
    
    if not file_record:
        return render_template('error.html', message="File not found"), 404
    
    if file_record.status != 'completed':
        return render_template('error.html', message="Processing not complete"), 400
    
    return render_template('view.html', file=file_record)

@app.route('/delete/<file_id>', methods=['POST'])
def delete_file(file_id):
    file_record = AudioFile.query.get(file_id)
    
    if not file_record:
        return jsonify({'error': 'File not found'}), 404
    
    # Delete the physical file if it exists
    if os.path.exists(file_record.file_path):
        os.remove(file_record.file_path)
    
    # Delete Redis keys
    redis_client.delete(f"file:{file_id}:progress")
    
    # Delete DB record
    db.session.delete(file_record)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/files', methods=['GET'])
def list_files():
    files = AudioFile.query.order_by(AudioFile.upload_time.desc()).all()
    return jsonify([{
        'id': f.id,
        'filename': f.filename,
        'status': f.status,
        'upload_time': f.upload_time.isoformat(),
        'transcript_available': f.transcript is not None,
        'minutes_available': f.minutes is not None
    } for f in files])

#health
@app.route('/health', methods=['GET'])
def health():
    try:
        # Check Redis connection
        redis_client.ping()
        return jsonify({'status': 'healthy'}), 200
    except redis.ConnectionError:
        return jsonify({'status': 'unhealthy'}), 503

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')