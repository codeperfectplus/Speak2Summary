# cython: language_level=3
import traceback
from datetime import datetime

from celery import Celery
from transmeet import transcribe_audio_file
from transmeet.utils.general_utils import get_logger

from src.config import app, REDIS_URI, redis_client
from src.models import db, TranscriptEntry

logger = get_logger(__name__)

# Initialize Celery
celery = Celery('transmeet_tasks', broker=REDIS_URI, backend=REDIS_URI)

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
    file_record = TranscriptEntry.query.get(file_id)
    if file_record:
        file_record.status = status
        if error_message:
            file_record.error_message = error_message
        db.session.commit()

def update_progress(file_id, progress_value):
    """Update the progress of a file processing task in Redis."""
    redis_client.set(f"file:{file_id}:progress", progress_value)

@celery.task(bind=True)
def process_audio_file(self, file_id, file_path, transcription_client, transcription_model):
    """Process audio file and generate transcript and minutes."""
    with app.app_context():
        try:
            # Retrieve the file record and update its status to 'processing'
            file_record = TranscriptEntry.query.get(file_id)
            if not file_record:
                return {'error': 'File record not found'}
            
            logger.info(f"Processing file: {file_record.filename}")
            update_file_status(file_id, 'processing')
            update_progress(file_id, 20)

            if transcription_client == "groq":
                audio_chunk_size_mb = 18
            elif transcription_client == "openai":
                audio_chunk_size_mb = 24
            else:
                audio_chunk_size_mb = 18

            transcript = transcribe_audio_file(
                file_path,
                transcription_client,
                transcription_model,
                audio_chunk_size_mb=audio_chunk_size_mb
            )
            update_progress(file_id, 50)
            update_progress(file_id, 60)

            # if transcription starts with "Error:", update status and return
            if transcript.startswith("Error:"):
                logger.error(f"Transcription error for file {file_id}: {transcript}")
                error_message = transcript
                update_file_status(file_id, 'failed', error_message)
                update_progress(file_id, 0)
                return {'status': 'error', 'file_id': file_id, 'error_message': error_message}

            update_progress(file_id, 70)

            update_progress(file_id, 80)
            
            # Update file record with results and mark as completed
            update_progress(file_id, 90)
            file_record.transcript = transcript
            file_record.minutes = None
            file_record.status = 'completed'
            file_record.completion_time = datetime.utcnow()
            file_record.mind_map = None
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
            logger.error(f"Error processing file {file_id}: {error_message}\n{stack_trace}")

            # Update file record to 'failed' and store the error
            update_file_status(file_id, 'failed', f"{error_message}\n\n{stack_trace}")
            
            # Clear progress in Redis
            redis_client.delete(f"file:{file_id}:progress")
            
            return {
                'status': 'error',
                'file_id': file_id,
                'error_message': error_message
            }


@celery.task(bind=True)
def process_transcript_file(self, file_id):
    """Process transcript file and generate meeting minutes."""
    with app.app_context():
        try:
            # Retrieve the file record and update its status to 'processing'
            file_record = TranscriptEntry.query.get(file_id)
            if not file_record:
                return {'error': 'File record not found'}

            update_file_status(file_id, 'processing')
            update_progress(file_id, 20)
            
            # Update file record with results and mark as completed
            file_record.minutes = None
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
            logger.error(f"Error processing transcript file {file_id}: {error_message}\n{stack_trace}")

            # Update file record to 'failed' and store the error
            update_file_status(file_id, 'failed', f"{error_message}\n\n{stack_trace}")
            
            # Clear progress in Redis
            redis_client.delete(f"file:{file_id}:progress")
            
            return {
                'status': 'error',
                'file_id': file_id,
                'error_message': error_message
            }