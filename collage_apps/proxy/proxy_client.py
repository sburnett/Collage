#!/usr/bin/env python

import threading
import Queue
import datetime
import sqlite3
from optparse import OptionParser
import webbrowser
import pkgutil
import os.path
import urllib
import re

from selenium.firefox.webdriver import WebDriver
import wx
import wx.html
import wx.calendar

from collage.messagelayer import MessageLayer, MessageLayerError

from collage_apps.providers.local import NullVectorProvider
from collage_apps.instruments import create_logger

import proxy_common as common

import pdb

class DownloadThread(threading.Thread):
    def __init__(self, log_queue, db_filename, address):
        super(DownloadThread, self).__init__()
        self.log_queue = log_queue
        self.db_filename = db_filename
        self.address = address
        self.data = None
    
    def run(self):
        self.driver = WebDriver()

        database = Database(self.db_filename)
        modules = database.get_loaded_task_modules()
        all_tasks = database.get_tasks()
        snippets = filter(lambda s: s.get_module() in modules, all_tasks)
        tasks = map(lambda s: s.execute(self.driver), snippets)

        vector_provider = NullVectorProvider()
        message_layer = MessageLayer(vector_provider,
                                     common.BLOCK_SIZE,
                                     common.MAX_UNIQUE_BLOCKS,
                                     tasks,
                                     common.TASKS_PER_MESSAGE,
                                     create_logger(self.log_queue),
                                     mac=True)
        try:
            self.data = message_layer.receive(self.address)
        except MessageLayerError:
            pass

        self.driver.close()

    def get_data(self):
        return self.data

    def close(self):
        self.driver.close()

class FetchFrame(wx.Dialog):
    def __init__(self, parent, db_filename, address):
        wx.Dialog.__init__(self, parent,
                           title='Fetching %s' % address,
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

        self.db_filename = db_filename
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
        self.Bind(wx.EVT_CLOSE, self.OnClose, self)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

        self.log_queue = Queue.Queue(100)

        self.thread = DownloadThread(self.log_queue, db_filename, address)
        self.thread.daemon = True
        self.thread.start()

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTick, self.timer)
        self.timer.Start(milliseconds=100, oneShot=False)

    def OnCancel(self, event):
        self.thread.close()
        self.EndModal(wx.CANCEL)

    def OnClose(self, event):
        self.thread.close()

    def OnTick(self, event):
        while True:
            try:
                item = self.log_queue.get(False)
                self.control.AppendAndEnsureVisible(item)
            except Queue.Empty:
                break

        if not self.thread.is_alive():
            self.data = self.thread.get_data()
            self.timer.Stop()
            self.EndModal(wx.OK)

    def GetData(self):
        return self.data

class OpenFrame(wx.Dialog):
    def __init__(self, parent, db_filename):
        wx.Dialog.__init__(self, parent,
                           title='Open censored document',
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

        self.database = Database(db_filename)

        self.dates = []
        for (address, fetched) in self.database.get_addresses().items():
            self.dates.append(common.parse_address(address))

        self.sizer = wx.FlexGridSizer(wx.VERTICAL)
        self.sizer.AddGrowableRow(1)
        self.sizer.AddGrowableCol(0)

        label = wx.StaticText(self, label='Select a date from the calendar.\nNews for dates in bold has already been downloaded.', style=wx.ALIGN_CENTRE)
        self.sizer.Add(label, flag=wx.TOP|wx.ALIGN_CENTER)

        self.control = wx.calendar.CalendarCtrl(self)
        self.sizer.Add(self.control, flag=wx.EXPAND)
        self.Bind(wx.calendar.EVT_CALENDAR, self.OnOpen, self.control)
        self.Bind(wx.calendar.EVT_CALENDAR_MONTH, self.OnChange, self.control)
        self.Bind(wx.calendar.EVT_CALENDAR_YEAR, self.OnChange, self.control)
        
        button_panel = wx.Panel(self)
        self.sizer.Add(button_panel, flag=wx.EXPAND)
        panel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        panel_sizer.AddStretchSpacer()

        cancel_button = wx.Button(button_panel, id=wx.ID_CANCEL)
        panel_sizer.Add(cancel_button, flag=wx.ALIGN_RIGHT)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, cancel_button)

        self.open_button = wx.Button(button_panel, id=wx.ID_OPEN)
        panel_sizer.Add(self.open_button, flag=wx.ALIGN_RIGHT)
        self.Bind(wx.EVT_BUTTON, self.OnOpen, self.open_button)

        button_panel.SetSizer(panel_sizer)
        button_panel.SetAutoLayout(1)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

        self.OnChange(None)

    def OnOpen(self, event):
        date = self.control.PyGetDate()
        if date is None:
            return
        self.address = common.format_address(date)
        self.need_to_fetch = date not in self.dates
        self.EndModal(wx.OK)

    def OnChange(self, event):
        for i in range(1, 32):
            self.control.ResetAttr(i)
        current = self.control.PyGetDate()
        for date in self.dates:
            if date.year == current.year and date.month == current.month:
                avail_style = wx.calendar.CalendarDateAttr(font=wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD))
                self.control.SetAttr(date.day, avail_style)

        self.control.Refresh()

    def GetAddress(self):
        return self.address

    def NeedToFetch(self):
        return self.need_to_fetch

    def OnCancel(self, event):
        self.EndModal(wx.CANCEL)

class TasksFrame(wx.Dialog):
    my_title = 'Collage task modules'
    def __init__(self, parent, db_filename):
        wx.Dialog.__init__(self, parent, title=self.my_title)

        self.db_filename = db_filename
        self.database = Database(db_filename)

        self.sizer = wx.FlexGridSizer(wx.VERTICAL)
        self.sizer.AddGrowableRow(1)
        self.sizer.AddGrowableCol(0)

        label = wx.StaticText(self, label='This is a list of available task modules.')
        self.sizer.Add(label, flag=wx.TOP|wx.ALIGN_CENTER)

        modules = []
        modules_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'taskmodules')
        for _, name, _ in pkgutil.iter_modules([modules_dir]):
            fh = open(os.path.join(modules_dir, '%s.py' % name), 'r')
            try:
                desc = fh.readline()[1:].strip()
            except:
                desc = ''
            loaded = self.database.is_task_module_loaded(name)
            modules.append((name, desc, loaded))
            fh.close()

        self.control = wx.CheckListBox(self)
        for (idx, (name, desc, loaded)) in enumerate(modules):
            self.control.Append('%s: %s' % (name, desc), name)
            self.control.Check(idx, loaded)
        self.sizer.Add(self.control, flag=wx.EXPAND)

        close_button = wx.Button(self, id=wx.ID_CLOSE)
        self.sizer.Add(close_button, flag=wx.ALIGN_RIGHT)
        self.Bind(wx.EVT_BUTTON, self.OnClose, close_button)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

    def OnClose(self, event):
        self.loaded = []
        for idx in self.control.GetChecked():
            self.loaded.append(self.control.GetClientData(idx))
        self.EndModal(wx.OK)

    def GetLoaded(self):
        return self.loaded

class ProxyFrame(wx.Frame):
    my_title = 'Collage proxy client'
    def __init__(self, parent, db_filename, local_dir=None):
        wx.Frame.__init__(self, parent, title=self.my_title)

        self.db_filename = db_filename
        self.database = Database(db_filename)
        self.local_dir = local_dir

        filemenu = wx.Menu()
        item = filemenu.Append(wx.ID_OPEN, '&Open...', 'View censored documents')
        self.Bind(wx.EVT_MENU, self.OnOpen, item)
        item = filemenu.Append(wx.ID_ANY, '&Update task database', 'Fetch the latest task database')
        self.Bind(wx.EVT_MENU, self.OnUpdate, item)
        item = filemenu.Append(wx.ID_ANY, '&Task modules', 'Select task modules')
        self.Bind(wx.EVT_MENU, self.OnModules, item)
        filemenu.AppendSeparator()
        item = filemenu.Append(wx.ID_EXIT, 'E&xit', 'Terminate the program')
        self.Bind(wx.EVT_MENU, self.OnExit, item)

        menubar = wx.MenuBar()
        menubar.Append(filemenu, '&File')
        self.SetMenuBar(menubar)

        self.control = wx.html.HtmlWindow(self)
        self.Bind(wx.html.EVT_HTML_LINK_CLICKED, self.OnLinkClick, self.control)

        self.Show(True)

    def OnOpen(self, event):
        dlg = OpenFrame(self, self.db_filename)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.OK:
            address = dlg.GetAddress()
            if dlg.NeedToFetch():
                self.Fetch(address)
            contents = self.database.get_file(address)
            if contents is not None:
                self.SetTitle('%s - %s' % (address, self.my_title))
                self.control.SetPage(contents)

    def Fetch(self, address):
        dlg = FetchFrame(self, self.db_filename, address)
        rc = dlg.ShowModal()
        data = dlg.GetData()
        if rc == wx.OK:
            if data is None:
                dlg = wx.MessageDialog(self,
                                       'Cannot download the news from %s. Try activating additional task modules.' % address,
                                       'Fetch error',
                                       style=wx.OK|wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
            else:
                self.database.add_file(address, data)

    def OnUpdate(self, event):
        pagedata = urllib.urlopen('http://flickr.com/photos/tags').read()
        match = re.search('<p id="TagCloud">(.*?)</p>', pagedata, re.S|re.I)
        block = match.group(1)
        block = re.sub(r'<a href=".*?".*?>', '', block)
        block = re.sub(r'</a>', '', block)
        block = re.sub(r'&nbsp;', '', block)

        tags = block.split()
        tag_pairs = [(a, b) for a in tags for b in tags if a < b] 

        tasks = []
        for pair in tag_pairs:
            tasks.append(('flickr', 'WebTagPairFlickrTask(driver, %s)' % repr(pair)))
        if self.local_dir is not None:
            tasks.append(('local', 'ReadDirectory(%s)' % repr(self.local_dir)))
        self.database.delete_tasks()
        self.database.add_tasks(tasks)

#        dlg = FetchFrame(self, self.db_filename, common.UPDATE_ADDRESS)
#        rc = dlg.ShowModal()
#        data = dlg.GetData()
#        if rc == wx.OK and data is not None:
#            tags = data.split()
#            self.database.set_tags(tags)

    def OnModules(self, event):
        dlg = TasksFrame(self, self.db_filename)
        if dlg.ShowModal() == wx.OK:
            self.database.set_loaded_task_modules(dlg.GetLoaded())
        dlg.Destroy()

    def OnExit(self, event):
        self.Close(True)

    def OnLinkClick(self, event):
        dlg = wx.MessageDialog(self,
                               'This link will be opened in your regular Web browser and will not be fetched using Collage. Are you sure you want to continue?',
                               'Warning: %s' % event.GetLinkInfo().GetHref(),
                               style=wx.YES_NO|wx.ICON_EXCLAMATION)
        rc = dlg.ShowModal()
        dlg.Destroy()
        if rc == wx.ID_YES:
            webbrowser.open(event.GetLinkInfo().GetHref())

class Snippet(object):
    def __init__(self, module, command):
        self.module = module
        self.command = command

    def get_module(self):
        return self.module

    def execute(self, driver):
        pkg = __import__('collage_apps.proxy.taskmodules', fromlist=[str(self.module)])
        mod = pkg.__getattribute__(self.module)
        return eval(self.command, mod.__dict__, {'driver': driver})

class Database(object):
    def __init__(self, filename):
        self.conn = sqlite3.connect(filename)
        self.conn.row_factory = sqlite3.Row

        self.conn.execute('''CREATE TABLE IF NOT EXISTS downloads
                             (address TEXT, contents TEXT, fetched DEFAULT CURRENT_TIMESTAMP)''')
        self.conn.execute('''CREATE TABLE IF NOT EXISTS task_modules
                             (name TEXT)''')
        self.conn.execute('''CREATE TABLE IF NOT EXISTS tasks
                             (module TEXT, command TEXT)''')
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

    def is_task_module_loaded(self, module):
        cur = self.conn.execute('''SELECT name FROM task_modules
                                   WHERE name = ?''',
                                (module,))
        return cur.fetchone() is not None

    def set_loaded_task_modules(self, modules):
        self.conn.execute('DELETE FROM task_modules')
        for module in modules:
            self.conn.execute('INSERT INTO task_modules (name) VALUES (?)', (module,))
        self.conn.commit()

    def get_loaded_task_modules(self):
        cur = self.conn.execute('SELECT name FROM task_modules')
        modules = []
        for row in cur:
            modules.append(row['name'])
        return modules

    def get_tasks(self):
        cur = self.conn.execute('SELECT module,command FROM tasks')
        tasks = []
        for row in cur:
            tasks.append(Snippet(row['module'], row['command']))
        return tasks

    def add_tasks(self, tasks):
        for (module, command) in tasks:
            self.conn.execute('INSERT INTO tasks (module, command) VALUES (?, ?)',
                              (module, command))
        self.conn.commit()

    def delete_tasks(self):
        self.conn.execute('DELETE FROM tasks')
        self.conn.commit()

def main():
    usage = 'usage: %s [options]'
    parser = OptionParser(usage=usage)
    parser.set_defaults(database='proxy_client.sqlite', localdir=None)
    parser.add_option('-d', '--database',
                      dest='database',
                      action='store',
                      type='string',
                      help='SQLite database')
    parser.add_option('-l', '--local-dir',
                      dest='localdir',
                      action='store',
                      type='string',
                      help='Local content host directory (testing)')
    (options, args) = parser.parse_args()

    app = wx.App(False)
    frame = ProxyFrame(None, options.database, options.localdir)
    app.MainLoop()

if __name__ == '__main__':
    main()
