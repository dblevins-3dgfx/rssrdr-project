import os
from flask import Blueprint, render_template, flash, request, redirect, current_app, url_for
from werkzeug.utils import secure_filename
from rssrdr.auth import login_required
from rssrdr.db import import_opml, get_db
import feedparser

bp = Blueprint('index', __name__)

@bp.route('/')
@login_required
def index():
    db = get_db()
    feeds = db.execute("SELECT id, title FROM feed")
    return render_template('index.html', feeds=feeds)


def allowed_file(filename):
    allowed_extensions = {'opml'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


@bp.route('/import', methods=['GET', 'POST'])
@login_required
def handle_import():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            localpath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(localpath)
            import_opml(localpath)
            return redirect(url_for('index'))

    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''    
    
@bp.route('/feed/<int:feed_id>')
@login_required
def feed(feed_id):
    db = get_db()
    feedUrl = db.execute("SELECT url FROM feed WHERE id == ?", (feed_id,)).fetchone()
    rssFeed = feedparser.parse(feedUrl['url'])
    return render_template('feed.html', articles=rssFeed.entries)
