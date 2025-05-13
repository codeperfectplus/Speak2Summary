import os
import redis
from flask import Flask
from configparser import ConfigParser

from src.models import db

# Read from config.ini
config_parser = ConfigParser()
config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
config_parser.read(config_path)

# Flask config values
UPLOAD_FOLDER = config_parser.get('flask', 'UPLOAD_FOLDER')
MAX_CONTENT_LENGTH_MB = config_parser.getint('flask', 'MAX_CONTENT_LENGTH_MB')
DB_NAME = config_parser.get('flask', 'SQLALCHEMY_DB_NAME')
SQLALCHEMY_TRACK_MODIFICATIONS = config_parser.getboolean('flask', 'SQLALCHEMY_TRACK_MODIFICATIONS')

SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(os.path.abspath(os.path.dirname(__file__)), DB_NAME)}'

# Redis config values
REDIS_HOST = config_parser.get('redis', 'HOST')
REDIS_PORT = config_parser.getint('redis', 'PORT')
REDIS_DB = config_parser.getint('redis', 'DB')

REDIS_URI = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

app = Flask(__name__)
app.config.from_mapping(
    UPLOAD_FOLDER=UPLOAD_FOLDER,
    MAX_CONTENT_LENGTH=MAX_CONTENT_LENGTH_MB * 1024 * 1024,
    SQLALCHEMY_DATABASE_URI=SQLALCHEMY_DATABASE_URI,
    SQLALCHEMY_TRACK_MODIFICATIONS=SQLALCHEMY_TRACK_MODIFICATIONS,
)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)
