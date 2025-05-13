from flask import Flask, render_template, request, jsonify, url_for
import os
import uuid
from werkzeug.utils import secure_filename
from src.celery_worker import process_audio_file
from src.models import db, AudioFile
import redis

# Initialize Flask app and configurations
app = Flask(__name__)

# Constants
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 1000 * 1024 * 1024  # 100MB max upload
SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(os.path.abspath(os.path.dirname(__file__)), "transmeet.db")}'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# App Configuration
app.config.from_mapping(
    UPLOAD_FOLDER=UPLOAD_FOLDER,
    MAX_CONTENT_LENGTH=MAX_CONTENT_LENGTH,
    SQLALCHEMY_DATABASE_URI=SQLALCHEMY_DATABASE_URI,
    SQLALCHEMY_TRACK_MODIFICATIONS=SQLALCHEMY_TRACK_MODIFICATIONS,
)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database and Redis connection
db.init_app(app)
redis_client = redis.Redis(host='redis', port=6379, db=0)

# Create database tables
with app.app_context():
    db.create_all()


@app.route('/', methods=['GET'])
def index():
    # Get all audio files from database
    files = AudioFile.query.order_by(AudioFile.upload_time.desc()).all()
    return render_template('index.html', files=files)

# Helper function to handle file saving
def save_file(file, tracking_id):
    original_filename = file.filename
    secure_name = secure_filename(original_filename)
    unique_filename = f"{tracking_id}_{secure_name}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(filepath)
    return filepath, original_filename

# Helper function to create a new AudioFile entry
def create_audio_file_entry(tracking_id, original_filename, filepath):
    new_file = AudioFile(
        id=tracking_id,
        filename=original_filename,
        file_path=filepath,
        status="queued"
    )
    db.session.add(new_file)
    db.session.commit()

# Helper function to handle audio processing queue
def add_to_audio_processing_queue(tracking_id, filepath, transcription_client, transcription_model, llm_client, llm_model):
    process_audio_file.delay(tracking_id, filepath, transcription_client, transcription_model, llm_client, llm_model)

# Route to handle file upload
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
            
            # Save the file and create a new audio file entry
            filepath, original_filename = save_file(file, tracking_id)
            create_audio_file_entry(tracking_id, original_filename, filepath)
            
            # Add to queue for processing
            add_to_audio_processing_queue(tracking_id, filepath, transcription_client, transcription_model, llm_client, llm_model)
            
            results.append({
                'id': tracking_id,
                'filename': original_filename,
                'status': 'queued'
            })
    
    return jsonify(results)

# Route to fetch the status of a file
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

# Route to view the minutes of a file
@app.route('/view/<file_id>', methods=['GET'])
def view_minutes(file_id):
    file_record = AudioFile.query.get(file_id)
    if not file_record or file_record.status != 'completed':
        return render_template('error.html', message="File not found or processing not complete"), 404
    
    return render_template('view.html', file=file_record)

# Route to delete a file from the system
@app.route('/delete/<file_id>', methods=['POST'])
def delete_file(file_id):
    file_record = AudioFile.query.get(file_id)
    if not file_record:
        return jsonify({'error': 'File not found'}), 404
    
    # Delete the physical file and Redis data
    if os.path.exists(file_record.file_path):
        os.remove(file_record.file_path)
    
    redis_client.delete(f"file:{file_id}:progress")
    
    # Delete DB record
    db.session.delete(file_record)
    db.session.commit()
    
    return jsonify({'success': True})

# Route to list all files in the system
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

# Health check route
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
