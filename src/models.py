from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class AudioFile(db.Model):
    __tablename__ = 'audio_files'
    
    id = db.Column(db.String(36), primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    status = db.Column(db.String(50), default='queued')  # queued, processing, completed, failed
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    completion_time = db.Column(db.DateTime, nullable=True)
    
    # Store processing results
    transcript = db.Column(db.Text, nullable=True)
    minutes = db.Column(db.Text, nullable=True)
    
    # Error handling
    error_message = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<AudioFile {self.filename}>'
        
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'status': self.status,
            'upload_time': self.upload_time.isoformat(),
            'completion_time': self.completion_time.isoformat() if self.completion_time else None,
            'transcript_available': self.transcript is not None,
            'minutes_available': self.minutes is not None,
            'error_message': self.error_message
        }