#!/usr/bin/env python

import Tkinter
import webbrowser
import threading
import Queue
from datetime import datetime
import sqlite3
import tempfile
from optparse import OptionParser

from selenium.firefox.webdriver import WebDriver

from collage.messagelayer import MessageLayer

from tasks import WebTagPairFlickrTask
from vectors import OutguessVector
from providers import NullVectorProvider, DirectoryVectorProvider
from instruments import create_logger

BLOCK_SIZE = 8
MAX_UNIQUE_BLOCKS = 2**16
TASKS_PER_MESSAGE = 3
TAGS_FILE = 'flickr_tags'

class DownloadWindow:
    def __init__(self, address, callback):
        self.address = address
        self.callback = callback

        self.root = Tkinter.Tk()
        self.root.title(string='Collage downloader')
        try:
            self.root.call('console', 'hide')
        except:
            pass

        frame = Tkinter.Frame(self.root)
        Tkinter.Label(frame, text='Downloading ').pack(side=Tkinter.LEFT)
        Tkinter.Label(frame, text=address, font=('Courier', 12)).pack(side=Tkinter.LEFT)
        Tkinter.Label(frame, text=' using Collage. Please be patient.').pack(side=Tkinter.LEFT)
        frame.pack()
        Tkinter.Label(self.root, text='This program will open new Firefox windows. Do not interfere with these windows.').pack()

        self.log_list = Tkinter.Listbox(self.root, selectmode=Tkinter.SINGLE)
        self.log_list.pack(fill=Tkinter.BOTH, expand=1)

        Tkinter.Button(self.root, text='Cancel', command=self.cancel).pack()
        self.root.protocol('WM_DELETE_WINDOW', self.cancel)
        
        self.log_queue = Queue.Queue(100)

        self.thread = threading.Thread(target=self.download_file)
        self.thread.start()

        self.root.after(500, self.update_status)
        self.root.mainloop()

    def update_status(self):
        while True:
            try:
                item = self.log_queue.get(False)
                self.log_list.insert(0, item)
            except Queue.Empty:
                break

        self.root.after_idle(self.update_status)

    def download_file(self):
        driver = WebDriver()

        tags = []
        for line in open(TAGS_FILE, 'r'):
            tags.append(line.strip())
        tag_pairs = [(a, b) for a in tags for b in tags if a < b]
        tasks = map(lambda pair: WebTagPairFlickrTask(driver, pair), tag_pairs)

        vector_provider = NullVectorProvider()
        message_layer = MessageLayer(vector_provider,
                                     BLOCK_SIZE,
                                     MAX_UNIQUE_BLOCKS,
                                     tasks,
                                     TASKS_PER_MESSAGE,
                                     create_logger(self.log_queue))
        data = message_layer.receive(self.address)

        self.callback(data)

    def cancel(self):
        self.root.destroy()
        ProxyApp()

class ProxyApp:
    def __init__(self):
        self.root = Tkinter.Tk()
        self.root.title(string='Collage proxy client')
        try:
            self.root.call('console', 'hide')
        except:
            pass

        self.document_list = Tkinter.Listbox(self.root, selectmode=Tkinter.SINGLE)
        self.document_list.bind('<Double-Button-1>', self.view_article)
        self.document_list.pack(fill=Tkinter.BOTH, expand=1)

        button_frame = Tkinter.Frame(self.root)
        Tkinter.Button(button_frame, text='Download the latest news', command=self.download).pack(side=Tkinter.LEFT)
        Tkinter.Button(button_frame, text='Update task database', command=self.update).pack(side=Tkinter.LEFT)
        button_frame.pack()

        for (address, fetched) in database.get_addresses():
            self.document_list.insert(Tkinter.END, address)

        self.root.mainloop()

    def view_article(self, event=None):
        sel = self.document_list.curselection()
        if len(sel) == 0:
            return

        address = self.document_list.get(sel[0])
        data = database.get_file(address)

        fh = tmpfile.NamedTemporaryFile(suffix='.html', prefix='collage_proxy_', delete=False)
        fh.write(data)
        fh.close()

        webbrowser.open_new(fh.name)

    def download(self, event=None):
        self.root.destroy()

        today = datetime.utcnow()
        address = 'proxy://news/%.4d/%.2d/%.2d' % (today.year, today.month, today.day)
        DownloadWindow(address, download_complete)

    def download_complete(address, data):
        database.add_file(address, data)

    def update(self, event=None):
        self.root.destroy()

        DownloadWindow('proxy://update', update_complete)

    def update_complete(address, data):
        tags = data.split()
        database.set_tags(tags)

class Database:
    def __init__(self, filename):
        self.conn = sqlite3.connect(filename)
        self.conn.row_factory = sqlite3.Row

        self.conn.execute('''CREATE TABLE IF NOT EXISTS downloads
                             (address TEXT, contents TEXT, fetched DEFAULT CURRENT_TIMESTAMP)''')
        self.conn.execute('''CREATE TABLE IF NOT EXISTS tags
                             (tag TEXT)''')

    def add_file(self, address, contents):
        self.conn.execute('''DELETE FROM downloads WHERE address = ?''', (contents,))
        self.conn.execute('''INSERT INTO downloads (address, contents)
                             VALUES (?, ?)''', (address, contents))

    def get_file(self, address):
        row = self.conn.execute('''SELECT contents FROM downloads WHERE address = ?''',
                                (address,)).fetchone()
        if row is None:
            return None
        else:
            return row['contents']

    def get_addresses(self):
        addresses = {}

        cur = self.conn.execute('SELECT address,fetched FROM downloads')
        for row in cur:
            addresses[row['address']] = row['fetched']

        return addresses

    def get_tags(self):
        tags = set()
        for row in self.conn.execute('SELECT tag FROM tags'):
            tags.add(row['tag'])
        return tags

    def set_tags(self, tags):
        self.conn.execute('DELETE FROM tags')

        for tag in tags:
            self.conn.execute('INSERT INTO tags (tag) VALUES (?)', (tag,))

def main():
    usage = 'usage: %s [options]'
    parser = OptionParser(usage=usage)
    parser.set_defaults(database='proxy_client.sqlite')
    parser.add_option('-d', '--database', dest='database', action='store', type='string', help='SQLite database')
    (options, args) = parser.parse_args()

    global database
    database = Database(options.database)
    ProxyApp()

if __name__ == '__main__':
    main()
