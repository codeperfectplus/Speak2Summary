from flask import Flask, render_template, request
import os
from werkzeug.utils import secure_filename
from transmeet import generate_meeting_transcript_and_minutes
from markdown import markdown

from utils import render_minutes_with_tailwind

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route('/', methods=['GET', 'POST'])
def index():
    transcript = minutes = None

    if request.method == 'POST':
        file = request.files.get('audio')
        if file and file.filename:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Generate the transcript and meeting minutes
            transcript, meeting_minutes = generate_meeting_transcript_and_minutes(
                meeting_audio_file=filepath,
                transcription_client="groq",
                transcription_model="whisper-large-v3-turbo",
                llm_client="groq",
                llm_model="llama-3.3-70b-versatile"
            )
            
            MARKDOWN_EXTENSIONS = [
                'fenced_code',     # Enables GitHub-style triple backtick code blocks
                'codehilite',      # Syntax highlighting for code blocks
                'tables',          # GitHub-style tables
                'nl2br',           # Converts newlines to <br>
                'sane_lists',      # Fixes list parsing issues
                'attr_list',       # Allows setting attributes like classes on elements
                'toc'              # Adds table of contents generation (optional use)
            ]
            minutes = markdown(meeting_minutes, extensions=MARKDOWN_EXTENSIONS)
            minutes = render_minutes_with_tailwind(meeting_minutes)
    
    return render_template('index.html', transcript=transcript, minutes=minutes)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
