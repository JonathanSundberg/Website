import os
import subprocess
from flask import Flask, render_template, request, redirect, session, abort, flash
from werkzeug.utils import secure_filename
from ffmpy import FFmpeg
app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
THUMBNAIL_FOLDER = os.path.join(os.path.dirname(__file__), "thumbnails")
ALLOWED_EXTENSIONS = {'.mp4'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



@app.route('/')
def index():
    return render_template('test.html')


if __name__ == '__main__':
    app.run(debug=True)