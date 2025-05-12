import os
import traceback
from datetime import datetime

import redis
from flask import Flask
from celery import Celery
from models import db, AudioFile
from utils import render_minutes_with_tailwind
from transmeet import generate_meeting_transcript_and_minutes

# Constants for configuration
REDIS_URI = 'redis://redis:6379/0'
SQLALCHEMY_DATABASE_URI = 'sqlite:///transmeet.db'

# Initialize Flask app
def create_app():
    app = Flask(__name__)
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'transmeet.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

# Initialize Celery
celery = Celery('transmeet_tasks', broker=REDIS_URI, backend=REDIS_URI)

# Initialize Redis client for progress tracking
redis_client = redis.Redis(host='redis', port=6379, db=0)

# Celery configuration
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Reusable functions to handle progress and file updates
def update_file_status(file_id, status, error_message=None):
    """Update file record status in the database."""
    file_record = AudioFile.query.get(file_id)
    if file_record:
        file_record.status = status
        if error_message:
            file_record.error_message = error_message
        db.session.commit()

def update_progress(file_id, progress_value):
    """Update the progress of a file processing task in Redis."""
    redis_client.set(f"file:{file_id}:progress", progress_value)

@celery.task(bind=True)
def process_audio_file(self, file_id, file_path, transcription_client, transcription_model, llm_client, llm_model):
    """Process audio file and generate transcript and minutes."""
    app = create_app()
    with app.app_context():
        try:
            # Retrieve the file record and update its status to 'processing'
            file_record = AudioFile.query.get(file_id)
            if not file_record:
                return {'error': 'File record not found'}
            
            print(f"Processing file: {file_record.filename}")
            update_file_status(file_id, 'processing')
            update_progress(file_id, 20)

            # Generate transcript and meeting minutes
            transcript, meeting_minutes = generate_meeting_transcript_and_minutes(
                meeting_audio_file=file_path,
                transcription_client=transcription_client,
                transcription_model=transcription_model,
                llm_client=llm_client,
                llm_model=llm_model
            )

            update_progress(file_id, 70)
            meeting_minutes = render_minutes_with_tailwind(meeting_minutes)
            
            # Update file record with results and mark as completed
            update_progress(file_id, 90)
            file_record.transcript = transcript
            file_record.minutes = meeting_minutes
            file_record.status = 'completed'
            file_record.completion_time = datetime.utcnow()
            db.session.commit()

            update_progress(file_id, 100)

            return {
                'status': 'success',
                'file_id': file_id,
                'message': 'Processing completed successfully',
            }

        except Exception as e:
            error_message = str(e)
            stack_trace = traceback.format_exc()
            print(f"Error processing file {file_id}: {error_message}\n{stack_trace}")

            # Update file record to 'failed' and store the error
            update_file_status(file_id, 'failed', f"{error_message}\n\n{stack_trace}")
            
            # Clear progress in Redis
            redis_client.delete(f"file:{file_id}:progress")
            
            return {
                'status': 'error',
                'file_id': file_id,
                'error': error_message
            }
