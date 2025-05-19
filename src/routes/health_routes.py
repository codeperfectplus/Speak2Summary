import redis
from flask import jsonify

from . import audio_bp
from src.config import redis_client
from src.models import TranscriptEntry, db

@audio_bp.route('/health', methods=['GET'])
def health():
    try:
        redis_client.ping()
        return jsonify({'status': 'healthy'}), 200
    except redis.ConnectionError:
        return jsonify({'status': 'unhealthy'}), 503


@audio_bp.route('/health/redis', methods=['GET'])
def health_redis():
    try:
        redis_client.ping()
        return jsonify({'status': 'healthy'}), 200
    except redis.ConnectionError:
        return jsonify({'status': 'unhealthy'}), 503

@audio_bp.route('/health/db', methods=['GET'])
def health_db():
    try:
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        return jsonify({'status': 'healthy'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503
    
@audio_bp.route('/health/all', methods=['GET'])
def health_all():
    try:
        redis_client.ping()
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        return jsonify({'status': 'healthy'}), 200
    except redis.ConnectionError:
        return jsonify({'status': 'unhealthy', 'error': 'Redis connection error'}), 503
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503
    # return jsonify({'status': 'healthy'}), 200