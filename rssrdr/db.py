import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext

import opml

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


def traverse_opml(node, parent, visit):
    visit(node, parent)
    for child in node:
        traverse_opml(child, node, visit)

def visit_opml(node, parent):
    if hasattr(node, 'type') and node.type == 'rss':
        db = get_db()
        title = node.title
        url = node.xmlUrl
        topic = parent.title
        try:
            db.execute("INSERT INTO feed (title, url, topic) VALUES (?, ?, ?)", (title, url, topic))
            db.commit()
        except db.IntegrityError:
            pass


def import_opml(filename):
    outline = opml.parse(filename)
    traverse_opml(outline, None, visit_opml)
                
                
@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)