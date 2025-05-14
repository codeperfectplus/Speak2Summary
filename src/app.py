from src.config import app
from src.models import db
from src.routes import audio_bp


with app.app_context():
    db.create_all()

app.register_blueprint(audio_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
