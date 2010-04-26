#!/usr/bin/env python

import threading
import Queue
from datetime import datetime
import sqlite3
import tempfile
from optparse import OptionParser
import time

from selenium.firefox.webdriver import WebDriver
import wx
import wx.html

from collage.messagelayer import MessageLayer

from tasks import WebTagPairFlickrTask
from vectors import OutguessVector
from providers import NullVectorProvider, DirectoryVectorProvider
from instruments import create_logger

import proxy_common as common

TAGS_FILE = 'flickr_tags'

class OpenFrame(wx.Dialog):
    def __init__(self, parent, db_filename):
        wx.Dialog.__init__(self, parent, title='Open censored document', style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

        self.database = Database(db_filename)

        addresses = []
        for (address, fetched) in self.database.get_addresses().items():
            addresses.append(address)

        self.sizer = wx.FlexGridSizer(wx.VERTICAL)
        self.sizer.AddGrowableRow(1)
        self.sizer.AddGrowableCol(0)

        label = wx.StaticText(self, label='Select a censored document from the list below.')
        self.sizer.Add(label, flag=wx.TOP|wx.ALIGN_CENTER)

        self.control = wx.ListBox(self, choices=addresses, style=wx.LB_SINGLE)
        self.sizer.Add(self.control, flag=wx.EXPAND)
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.OnOpen, self.control)
        
        button_panel = wx.Panel(self)
        self.sizer.Add(button_panel, flag=wx.EXPAND)
        panel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        panel_sizer.AddStretchSpacer()

        cancel_button = wx.Button(button_panel, id=wx.ID_CANCEL)
        panel_sizer.Add(cancel_button, flag=wx.ALIGN_RIGHT)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, cancel_button)

        open_button = wx.Button(button_panel, id=wx.ID_OPEN)
        panel_sizer.Add(open_button, flag=wx.ALIGN_RIGHT)
        self.Bind(wx.EVT_BUTTON, self.OnOpen, open_button)

        button_panel.SetSizer(panel_sizer)
        button_panel.SetAutoLayout(1)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

    def OnOpen(self, event):
        self.address = self.control.GetStringSelection()
        if len(self.address) > 0:
            self.EndModal(wx.OK)

    def GetAddress(self):
        return self.address

    def OnCancel(self, event):
        self.EndModal(wx.CANCEL)

class FetchFrame(wx.Dialog):
    def __init__(self, parent, address):
        wx.Dialog.__init__(self, parent, title='Fetching %s' % address, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

        self.address = address
        self.data = None

        self.sizer = wx.FlexGridSizer(wx.VERTICAL)
        self.sizer.AddGrowableRow(1)
        self.sizer.AddGrowableCol(0)

        status_str = 'Currently fetching %s\n' % address + \
                     'This program will open new Firefox windows. ' + \
                     'Do not interfere with these windows.'
        label = wx.StaticText(self, label=status_str, style=wx.ALIGN_CENTER)
        self.sizer.Add(label, flag=wx.ALIGN_CENTER)

        self.control = wx.ListBox(self, style=wx.LB_SINGLE)
        self.sizer.Add(self.control, flag=wx.ALIGN_CENTER|wx.EXPAND)

        cancel_button = wx.Button(self, id=wx.ID_CANCEL)
        self.sizer.Add(cancel_button, flag=wx.ALIGN_RIGHT)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, cancel_button)

        self.Bind(wx.EVT_IDLE, self.OnIdle)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

        self.log_queue = Queue.Queue(100)

        self.thread = threading.Thread(target=self.DownloadFile)
        self.thread.daemon = True
        self.thread.start()

    def OnCancel(self, event):
        self.EndModal(wx.CANCEL)

    def OnIdle(self, event):
        while True:
            try:
                item = self.log_queue.get(False)
                self.control.AppendAndEnsureVisible(item)
            except Queue.Empty:
                break

        if not self.thread.is_alive():
            self.EndModal(wx.OK)

    def GetData(self):
        return self.data

    def DownloadFile(self):
        driver = WebDriver()

        tags = []
        for line in open(TAGS_FILE, 'r'):
            tags.append(line.strip())
        tag_pairs = [(a, b) for a in tags for b in tags if a < b]
        tasks = map(lambda pair: WebTagPairFlickrTask(driver, pair), tag_pairs)

        vector_provider = NullVectorProvider()
        message_layer = MessageLayer(vector_provider,
                                     common.BLOCK_SIZE,
                                     common.MAX_UNIQUE_BLOCKS,
                                     tasks,
                                     common.TASKS_PER_MESSAGE,
                                     create_logger(self.log_queue),
                                     mac=True)
        self.data = message_layer.receive(self.address)

        driver.close()

class ProxyFrame(wx.Frame):
    my_title = 'Collage proxy client'
    def __init__(self, parent, db_filename):
        wx.Frame.__init__(self, parent, title=self.my_title)

        self.db_filename = db_filename
        self.database = Database(db_filename)

        filemenu = wx.Menu()
        item = filemenu.Append(wx.ID_OPEN, '&Open...', 'View censored documents')
        self.Bind(wx.EVT_MENU, self.OnOpen, item)
        item = filemenu.Append(wx.ID_ANY, '&Fetch news', 'Download the latest news')
        self.Bind(wx.EVT_MENU, self.OnFetch, item)
        item = filemenu.Append(wx.ID_ANY, '&Update task database', 'Fetch the latest task database')
        self.Bind(wx.EVT_MENU, self.OnUpdate, item)
        filemenu.AppendSeparator()
        item = filemenu.Append(wx.ID_EXIT, 'E&xit', 'Terminate the program')
        self.Bind(wx.EVT_MENU, self.OnExit, item)

        menubar = wx.MenuBar()
        menubar.Append(filemenu, '&File')
        self.SetMenuBar(menubar)

        self.CreateStatusBar()

        self.control = wx.html.HtmlWindow(self)

        self.Show(True)

    def OnOpen(self, event):
        dlg = OpenFrame(self, self.db_filename)
        if dlg.ShowModal() == wx.OK:
            address = dlg.GetAddress()
            self.SetTitle('%s - %s' % (address, self.my_title))
            contents = self.database.get_file(address)
            self.control.SetPage(contents)
        dlg.Destroy()

    def OnFetch(self, event):
        today = datetime.utcnow()
        address = common.format_address(today)

        for seen in self.database.get_addresses():
            if address == seen:
                wx.MessageDialog(self,
                                 'You have already downloaded the latest news',
                                 'Download complete')
                return

        dlg = FetchFrame(self, address)
        rc = dlg.ShowModal()
        data = dlg.GetData()
        if rc == wx.OK and data is not None:
            self.database.add_file(address, data)

    def OnUpdate(self, event):
        dlg = FetchFrame(self, common.UPDATE_ADDRESS)
        rc = dlg.ShowModal()
        data = dlg.GetData()
        if rc == wx.OK and data is not None:
            tags = data.split()
            self.database.set_tags(tags)

    def OnExit(self, event):
        self.Close(True)

class Database:
    def __init__(self, filename):
        self.conn = sqlite3.connect(filename)
        self.conn.row_factory = sqlite3.Row

        self.conn.execute('''CREATE TABLE IF NOT EXISTS downloads
                             (address TEXT, contents TEXT, fetched DEFAULT CURRENT_TIMESTAMP)''')
        self.conn.execute('''CREATE TABLE IF NOT EXISTS tags
                             (tag TEXT)''')
        self.conn.commit()

    def add_file(self, address, contents):
        self.conn.execute('''DELETE FROM downloads WHERE address = ?''', (contents,))
        self.conn.execute('''INSERT INTO downloads (address, contents)
                             VALUES (?, ?)''', (address, contents))
        self.conn.commit()

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

        self.conn.commit()

def main():
    usage = 'usage: %s [options]'
    parser = OptionParser(usage=usage)
    parser.set_defaults(database='proxy_client.sqlite')
    parser.add_option('-d', '--database', dest='database', action='store', type='string', help='SQLite database')
    (options, args) = parser.parse_args()

    app = wx.App(False)
    frame = ProxyFrame(None, options.database)
    app.MainLoop()

if __name__ == '__main__':
    main()
