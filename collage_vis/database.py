import sqlite3
import sys
import os
import os.path

def get_database():
    vdb_filename = os.getenv('COLLAGE_VIS')
    if vdb_filename is None:
        return None
    else:
        return VisDatabase(vdb_filename)

class VisDatabase(object):
    def __init__(self, db_file):
        self._conn = sqlite3.connect(db_file)
        self._conn.row_factory = sqlite3.Row
        self._conn.text_factory = str

        self._conn.execute('''CREATE TABLE IF NOT EXISTS stories
                              (rowid INTEGER PRIMARY KEY AUTOINCREMENT,
                               timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                               story TEXT,
                               state TEXT)''')
        self._conn.execute('''CREATE TABLE IF NOT EXISTS photos_queued
                              (rowid INTEGER PRIMARY KEY AUTOINCREMENT,
                               identifier TEXT,
                               thumbnail TEXT)''')
        self._conn.execute('''CREATE TABLE IF NOT EXISTS photos_embedding
                              (rowid INTEGER PRIMARY KEY AUTOINCREMENT,
                               identifier TEXT,
                               thumbnail TEXT)''')
        self._conn.execute('''CREATE TABLE IF NOT EXISTS photos_uploaded
                              (rowid INTEGER PRIMARY KEY AUTOINCREMENT,
                               identifier TEXT,
                               thumbnail TEXT)''')
        self._conn.execute('''CREATE TABLE IF NOT EXISTS photos_downloaded
                              (rowid INTEGER PRIMARY KEY AUTOINCREMENT,
                               thumbnail TEXT)''')
        self._conn.commit()

    def add_article_sender(self, story):
        self._conn.execute('''INSERT INTO stories (story, state) VALUES (?, ?)''', (story, 'sender'))
        self._conn.commit()

    def enqueue_photo(self, identifier, thumbnail):
        self._conn.execute('''INSERT INTO photos_queued (identifier, thumbnail) VALUES (?, ?)''', (identifier, thumbnail))
        self._conn.commit()

    def embed_photo(self, identifier):
        self._conn.execute('''INSERT INTO photos_embedding (identifier,thumbnail)
                              SELECT identifier,thumbnail FROM photos_queued WHERE identifier = ?''', (identifier,))
        self._conn.execute('''DELETE FROM photos_queued WHERE identifier = ?''', (identifier,))
        self._conn.commit()

    def upload_photo(self, identifier):
        self._conn.execute('''INSERT INTO photos_uploaded (identifier,thumbnail)
                              SELECT identifier,thumbnail FROM photos_embedding WHERE identifier = ?''', (identifier,))
        self._conn.execute('''DELETE FROM photos_embedding WHERE identifier = ?''', (identifier,))
        self._conn.commit()

    def remove_photo(self, identifier):
        self._conn.execute('''DELETE FROM photos_queued WHERE identifier = ?''', (identifier,))
        self._conn.execute('''DELETE FROM photos_embedding WHERE identifier = ?''', (identifier,))
        self._conn.execute('''DELETE FROM photos_uploaded WHERE identifier = ?''', (identifier,))
        self._conn.commit()

    def download_photo(self, thumbnail):
        self._conn.execute('''INSERT INTO photos_downloaded (thumbnail) VALUES (?)''', (thumbnail,))
        self._conn.commit()

    def add_article_receiver(self, story):
        self._conn.execute('''INSERT INTO stories (story, state) VALUES (?, ?)''', (story, 'receiver'))
        self._conn.commit()
