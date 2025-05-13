import redis
from flask import jsonify

from . import audio_bp
from src.config import redis_client

@audio_bp.route('/health', methods=['GET'])
def health():
    try:
        redis_client.ping()
        return jsonify({'status': 'healthy'}), 200
    except redis.ConnectionError:
        return jsonify({'status': 'unhealthy'}), 503
