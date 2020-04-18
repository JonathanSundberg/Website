import os
import subprocess
from flask import Flask, render_template, request, redirect, session, abort, flash, url_for
from werkzeug.utils import secure_filename
from ffmpy import FFmpeg
import difflib
import re
app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__),"static", "uploads")
THUMBNAIL_FOLDER = os.path.join(os.path.dirname(__file__), "static", "thumbnails")
ALLOWED_EXTENSIONS = {'.mp4', '.mkv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def mkv_to_mp4_convert(og_file_path, filename):
    print("og_file_path:" ,og_file_path)
    print("filename:", filename)
    filename = filename.replace(" ", "§")
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    os.rename(og_file_path, file_path)

    mp4_file_path = file_path.split(".")[0]
    mp4_file_path += ".mp4"
    subprocess.call(['ffmpeg', '-i', file_path, '-codec', 'copy', mp4_file_path])
    os.remove(file_path)
    mp4_file_path_new = mp4_file_path.replace("§", " ")
    os.rename(mp4_file_path, mp4_file_path_new)
    return os.path.basename(mp4_file_path_new)

def merge_vids_thumbnails(all_movies, all_thumbnails):
    movie_dict = {}
    found=False 
    for item in all_movies:
        for image in all_thumbnails:
            img = image.split(".")[0]
            title = item.split(".")[0]
            title_ext = item.split(".")[1]

            if img == title:
                title+="."+title_ext
                movie_dict.update({title: image})
                found=True
                continue
        
        # if no image was found
        if not found:
            movie_dict.update({title: "placeholder"})
    return movie_dict


def allowed_file(filename):
    for ending in ALLOWED_EXTENSIONS:
        if filename.endswith(ending):
            return True
    return False


def collect_all_movies(search_word=""):
    all_items = os.listdir(UPLOAD_FOLDER)
    if search_word:
        all_items = difflib.get_close_matches(search_word,all_items,cutoff=0)
    return all_items


def collect_all_thumbnails(search_word=""):
    all_items = os.listdir(THUMBNAIL_FOLDER)
    if search_word:
        all_items = difflib.get_close_matches(search_word, all_items, cutoff=0)
    return all_items


def delete_existing_thumbnail(file_name):
    all_items = os.listdir(THUMBNAIL_FOLDER)

    for item in all_items:
        no_ext = item.split(".")[0]

        if no_ext == file_name:
            #delete the existing picture
            item = os.path.join(THUMBNAIL_FOLDER, item)
            os.remove(item)
            return


@app.route('/')
def index():
    if not session.get('logged_in'):
        return render_template('log_in.html')
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    if request.form['password'] == 'password' and request.form['username'] == 'admin':
        session['logged_in'] = True
        return redirect('/')
    else:
        flash('wrong password!')
        return index()


@app.route("/logout")
def logout():
    session['logged_in'] = False
    return index()


@app.route("/show_all")
def show_all():
    all_movies = collect_all_movies()
    all_thumbnails = collect_all_thumbnails()

    movie_dict = merge_vids_thumbnails(all_movies, all_thumbnails)

    print(movie_dict)
    return render_template('show_all.html', movie_dict=movie_dict)


@app.route('/view/<string:title>')
def view(title):
    if not session.get('logged_in'):
        return render_template('log_in.html')
    return render_template('view.html', title=title)


@app.route('/upload_success')
def upload_success():
    if not session.get('logged_in'):
        return render_template('log_in.html')
    return render_template('upload_success.html')


@app.route('/upload_failed/<Error_msg>')
def upload_failed(Error_msg):
    if not session.get('logged_in'):
        return render_template('log_in.html')
    return render_template('upload_failed.html', Error_msg=Error_msg)


@app.route('/search', methods=['POST'])
def search():
    search_str = request.form['search_value']
    print("search string:", search_str)
    all_movies = collect_all_movies(search_str)
    all_thumbnails = collect_all_thumbnails(search_str)
    movie_dict = merge_vids_thumbnails(all_movies, all_thumbnails)

    print(movie_dict)
    return render_template('show_all.html', movie_dict=movie_dict)


@app.route('/upload', methods=['POST'])
def upload_file():
    if not session.get('logged_in'):
        return render_template('log_in.html')

    # check if the post request has the file part
    if 'file' not in request.files:
        print("No file!")   
        return redirect(url_for('upload_failed', Error_msg="No file in package"))
    
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        print(file.filename)
        print("No selected file")
        return redirect(url_for('upload_failed', Error_msg="No selected file"))
    
    if file and allowed_file(file.filename):
        print(file.filename)
        original_filename = file.filename

        filename_ext = original_filename.split(".")[1]
        filename = original_filename.split(" ",1)[1]
        filename = filename.rsplit(" ",1)[0]
        filename += "." + filename_ext

        all_items = collect_all_movies()
        for item in all_items:
            if item == filename:
                return redirect(url_for('upload_failed', Error_msg="That file already exists"))

        # Check if thumbnail exists but not video and delete it if it do
        no_ext_filename = original_filename.split(".")[0]
        delete_existing_thumbnail(no_ext_filename)

        og_file_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
        
        file.save(og_file_path)
        filename = mkv_to_mp4_convert(og_file_path, filename)

        video_input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        img_extension = filename.split(".")[0] + ".png"
        print("img_extension:", img_extension)
        img_path = os.path.join(THUMBNAIL_FOLDER, img_extension)
        subprocess.call(['ffmpeg', '-i', video_input_path, '-ss', '00:00:10.000', '-vframes', '1', img_path])

        return redirect("/upload_success")
    return redirect(url_for('upload_failed', Error_msg="That file extension is not allowed"))


if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(debug=True)