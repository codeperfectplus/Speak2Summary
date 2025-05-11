from celery import Celery
import os
import time
import redis
from datetime import datetime
import traceback
from flask import Flask
from models import db, AudioFile
from utils import render_minutes_with_tailwind

# Create a minimal Flask app for DB context
def create_app():
    app = Flask(__name__)
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'transmeet.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

# Initialize Celery
celery = Celery('transmeet_tasks',
                broker='redis://localhost:6379/0',
                backend='redis://localhost:6379/0'
)

# Initialize Redis for progress tracking
redis_client = redis.Redis(host='localhost', port=6379, db=0)


# Configure Celery
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

@celery.task(bind=True)
def process_audio_file(self, file_id, file_path):
    """Process audio file and generate transcript and minutes"""
    app = create_app()
    with app.app_context():
        try:
            # Update status to processing
            file_record = AudioFile.query.get(file_id)
            if not file_record:
                return {'error': 'File record not found'}
            
            print(f"Processing file: {file_record.filename}")
            file_record.status = 'processing'
            db.session.commit()

            update_progress(file_id, 10)
            time.sleep(3)

            update_progress(file_id, 20)
            time.sleep(3)

            # Simulate file processing
            print(f"Processing audio file: {file_path}")
            update_progress(file_id, 50)
            time.sleep(3)

            from transmeet import generate_meeting_transcript_and_minutes
            # Call the actual transcript and minutes generator
            transcript, meeting_minutes = generate_meeting_transcript_and_minutes(
                meeting_audio_file=file_path,
                transcription_client="groq",
                transcription_model="whisper-large-v3-turbo",
                llm_client="groq",
                llm_model="llama-3.3-70b-versatile"
            )

            update_progress(file_id, 70)
            meeting_minutes = render_minutes_with_tailwind(meeting_minutes)
            
            update_progress(file_id, 90)
            
            # Update database with results
            file_record.transcript = transcript
            file_record.minutes = meeting_minutes
            file_record.status = 'completed'
            file_record.completion_time = datetime.utcnow()
            db.session.commit()
            
            # Final progress update
            update_progress(file_id, 100)
            
            return {
                'status': 'success',
                'file_id': file_id,
                'message': 'Processing completed successfully'
            }
            
        except Exception as e:
            # Log the error
            error_message = str(e)
            stack_trace = traceback.format_exc()
            print(f"Error processing file {file_id}: {error_message}")
            print(stack_trace)
            
            # Update database with error
            file_record = AudioFile.query.get(file_id)
            if file_record:
                file_record.status = 'failed'
                file_record.error_message = f"{error_message}\n\n{stack_trace}"
                db.session.commit()
            
            # Clear progress
            redis_client.delete(f"file:{file_id}:progress")
            
            return {
                'status': 'error',
                'file_id': file_id,
                'error': error_message
            }

def update_progress(file_id, progress_value):
    """Update the progress of a file processing task"""
    redis_client.set(f"file:{file_id}:progress", progress_value)