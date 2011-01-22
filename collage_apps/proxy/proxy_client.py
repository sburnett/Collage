#!/usr/bin/env python2
"""Demo Collage application that reads news articles published by the server.

We call this application a "proxy", because it could be used to serve any Web
content.

"""

import threading
import Queue
import sqlite3
from optparse import OptionParser
import webbrowser
import urllib
import re
import datetime
import logging
import time

from selenium.firefox.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException

import wx
import wx.html
import wx.calendar
from wx.lib.pubsub import Publisher

from collage.messagelayer import MessageLayer, MessageLayerError

from collage_apps.providers.local import NullVectorProvider
from collage_apps.instruments import Logger

import proxy_common as common

class BetterWebDriver(WebDriver):
    def patient_find_element_by_xpath(self, path, timeout=60):
        """Sleep for 1 second increments until the provided XPath
        query matches on the current page. This should take care of
        weird AJAX loading issues."""

        for i in range(timeout):
            try:
                el = self.find_element_by_xpath(path)
                time.sleep(1)
                return el
            except NoSuchElementException:
                time.sleep(1)
        raise NoSuchElementException

    def wait_for_xpath(self, path, timeout=60):
        """A non-returning version of the above, with a more intuitive name."""
        self.patient_find_element_by_xpath(path, timeout)

    def real_back(self):
        """Keep clicking the back button until the URL changes. This should
        take care of Picasa's injection of extra history elements."""

        orig_url = self.get_current_url()
        while self.get_current_url() == orig_url:
            self.back()

class DownloadThread(threading.Thread):
    def __init__(self, log_queue, db_filename, address):
        super(DownloadThread, self).__init__()
        self.log_queue = log_queue
        self.db_filename = db_filename
        self.address = address
        self.data = None
        self.error = None
        self.logger = logging.getLogger('collage_proxy')

    def run(self):
        self.driver = BetterWebDriver()

        self.logger.info('Starting download thread')

        database = Database(self.db_filename)
        task_list = database.get_active_task_list()
        modules = database.get_loaded_task_modules(task_list)
        snippets = database.get_tasks(task_list)

        def dummy_receive(self, id):
            print 'Task module not loaded'
        def dummy_can_embed(self, id, data):
            return False
        def get_task_from_snippet(snippet):
            task = snippet.execute(self.driver)
            if snippet.get_module() not in modules:
                task.receive = dummy_receive
                task.can_embed = dummy_can_embed
            return task

        tasks = map(get_task_from_snippet, snippets)

        vector_provider = NullVectorProvider()
        message_layer = MessageLayer(vector_provider,
                                     common.BLOCK_SIZE,
                                     common.MAX_UNIQUE_BLOCKS,
                                     tasks,
                                     common.TASKS_PER_MESSAGE,
                                     Logger(self.log_queue),
                                     mac=True)
        try:
            self.logger.info('Download thread fetching address "%s"' % self.address)
            self.data = message_layer.receive(self.address)
        except Exception as inst:
            self.logger.info('Download thread had error "%s"' % inst.message)
            self.error = inst

        self.driver.close()

    def get_data(self):
        return self.data

    def get_error(self):
        return self.error

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
        self.vectors_downloaded = 0
        self.chunks_decoded = 0
        self.cover_received = 0
        self.data_decoded = 0

        self.logger = logging.getLogger('collage_proxy')
        self.logger.info('Building fetch window')

        self.sizer = wx.FlexGridSizer(wx.VERTICAL)
        self.sizer.AddGrowableRow(1)
        self.sizer.AddGrowableCol(0)

        status_str = 'Currently fetching %s\n' % address + \
                     'This program will open new Firefox windows. ' + \
                     'Do not interfere with these windows.'
        label = wx.StaticText(self, label=status_str, style=wx.ALIGN_CENTER)
        self.sizer.Add(label, flag=wx.ALIGN_CENTER)
        self.sizer.Add(wx.StaticLine(self, style=wx.LI_HORIZONTAL), flag=wx.EXPAND)

        status_sizer = wx.BoxSizer(wx.VERTICAL)

        self.status_label = wx.StaticText(self, label='Opening Firefox', style=wx.ALIGN_LEFT)
        defFont = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        self.status_label.SetFont(wx.Font(defFont.GetPointSize()+2, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
        status_sizer.Add(self.status_label, flag=wx.ALIGN_LEFT)
        self.vectors_label = wx.StaticText(self, label='0 vectors downloaded', style=wx.ALIGN_LEFT)
        status_sizer.Add(self.vectors_label, flag=wx.ALIGN_LEFT)
        self.chunks_label = wx.StaticText(self, label='0 chunks decoded', style=wx.ALIGN_LEFT)
        status_sizer.Add(self.chunks_label, flag=wx.ALIGN_LEFT)
        self.efficiency_label = wx.StaticText(self, label=' ', style=wx.ALIGN_LEFT)
        status_sizer.Add(self.efficiency_label, flag=wx.ALIGN_LEFT)

        self.sizer.Add(status_sizer, flag=wx.ALL, border=4)

        cancel_button = wx.Button(self, id=wx.ID_CANCEL)
        self.sizer.Add(cancel_button, flag=wx.ALIGN_RIGHT)
        self.Bind(wx.EVT_BUTTON, self.on_cancel, cancel_button)
        self.Bind(wx.EVT_CLOSE, self.on_close, self)

        self.SetAutoLayout(True)
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)
        self.Layout()

        self.log_queue = Queue.Queue(100)

        self.thread = DownloadThread(self.log_queue, db_filename, address)
        self.thread.daemon = True
        self.thread.start()

        Publisher().subscribe(self.update_status, 'status')
        Publisher().subscribe(self.update_vector, 'vector')
        Publisher().subscribe(self.update_chunk, 'chunk')
        Publisher().subscribe(self.log_message, 'message')
        Publisher().subscribe(self.log_error, 'error')

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_tick, self.timer)
        self.timer.Start(milliseconds=1000, oneShot=False)

    def on_cancel(self, event):
        self.logger.info('User canceled fetch')
        self.thread.close()
        self.EndModal(wx.CANCEL)

    def on_close(self, event):
        self.logger.info('Closing fetch thread')
        self.thread.close()

    def update_status(self, msg):
        self.logger.info('Received status update from download thread: %s', msg.data)
        self.status_label.SetLabel(msg.data)

    def update_vector(self, msg):
        self.logger.info('Received %d byte vector', int(msg.data))
        self.vectors_downloaded += 1
        self.cover_received += int(msg.data)
        if self.vectors_downloaded == 1:
            message = '%d vector downloaded' % self.vectors_downloaded
            self.vectors_label.SetLabel(message)
            self.logger.info(message)
        else:
            message = '%d vectors downloaded' % self.vectors_downloaded
            self.vectors_label.SetLabel(message)
            self.logger.info(message)
        if self.cover_received > 0:
            message = '%2.2f%% recovery efficiency' % (100*float(self.data_decoded)/float(self.cover_received),)
            self.efficiency_label.SetLabel(message)
            self.logger.info(message)

    def update_chunk(self, msg):
        self.logger.info('Decoded %d chunks from a vector', int(msg.data))
        self.chunks_decoded += 1
        self.data_decoded += int(msg.data)
        if self.chunks_decoded == 1:
            message = '%d chunk decoded' % self.chunks_decoded
            self.chunks_label.SetLabel(message)
            self.logger.info(message)
        else:
            message = '%d chunks decoded' % self.chunks_decoded
            self.chunks_label.SetLabel(message)
            self.logger.info(message)
        if self.cover_received > 0:
            message = '%2.2f%% recovery efficiency' % (100*float(self.data_decoded)/float(self.cover_received),)
            self.efficiency_label.SetLabel(message)
            self.logger.info(message)

    def log_message(self, msg):
        self.logger.info('Collage message: %s', msg)

    def log_error(self, msg):
        self.logger.error('Collage error: %s', msg)

    def on_tick(self, arg):
        if not self.thread.is_alive():
            self.logger.info('Download thread has exited')
            self.data = self.thread.get_data()
            self.error = self.thread.get_error()
            self.timer.Stop()
            self.EndModal(wx.OK)

    def get_data(self):
        return self.data

    def get_error(self):
        return self.error

class OpenFrame(wx.Dialog):
    def __init__(self, parent, db_filename):
        wx.Dialog.__init__(self, parent,
                           title='Open censored document',
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

        self.database = Database(db_filename)
        self.logger = logging.getLogger('collage_proxy')

        self.logger.info('Building open dialog')

        self.dates = []
        for (address, fetched) in self.database.get_addresses().items():
            self.logger.info('Date "%s" available', address)
            self.dates.append(common.parse_address(address))

        self.sizer = wx.FlexGridSizer(wx.VERTICAL)
        self.sizer.AddGrowableRow(1)
        self.sizer.AddGrowableCol(0)

        label = wx.StaticText(self, label='Select a date from the calendar.\nNews for dates in bold has already been downloaded.', style=wx.ALIGN_CENTRE)
        self.sizer.Add(label, flag=wx.TOP|wx.ALIGN_CENTER)

        self.control = wx.calendar.CalendarCtrl(self)
        self.sizer.Add(self.control, flag=wx.EXPAND)
        self.Bind(wx.calendar.EVT_CALENDAR, self.on_open, self.control)
        self.Bind(wx.calendar.EVT_CALENDAR_MONTH, self.on_change, self.control)
        self.Bind(wx.calendar.EVT_CALENDAR_YEAR, self.on_change, self.control)

        button_panel = wx.Panel(self)
        self.sizer.Add(button_panel, flag=wx.EXPAND)
        panel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        panel_sizer.AddStretchSpacer()

        cancel_button = wx.Button(button_panel, id=wx.ID_CANCEL)
        panel_sizer.Add(cancel_button, flag=wx.ALIGN_RIGHT)
        self.Bind(wx.EVT_BUTTON, self.on_cancel, cancel_button)

        self.open_button = wx.Button(button_panel, id=wx.ID_OPEN)
        panel_sizer.Add(self.open_button, flag=wx.ALIGN_RIGHT)
        self.Bind(wx.EVT_BUTTON, self.on_open, self.open_button)

        button_panel.SetSizer(panel_sizer)
        button_panel.SetAutoLayout(1)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

        self.on_change(None)

    def on_open(self, event):
        date = self.control.PyGetDate()
        if date is None:
            return
        self.address = common.format_address(date)
        if date not in self.dates:
            self.logger.info('User attempted to open "%s", which hasn\'t been downloaded yet', self.address)
            dlg = wx.MessageDialog(self,
                                   'News for this date has not been downloaded.',
                                   'Invalid date',
                                   style=wx.OK|wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            self.logger.info('User wants to view news from "%s"', self.address)
            self.EndModal(wx.OK)

    def on_change(self, event):
        for i in range(1, 32):
            self.control.ResetAttr(i)
            unavail_style = wx.calendar.CalendarDateAttr(colText='#a0a0a0')
            self.control.SetAttr(i, unavail_style)

        current = self.control.PyGetDate()
        for date in self.dates:
            if date.year == current.year and date.month == current.month:
                self.control.ResetAttr(date.day)

        self.control.Refresh()

    def get_address(self):
        return self.address

    def on_cancel(self, event):
        self.logger.info('User canceled date selection')
        self.EndModal(wx.CANCEL)

welcome_page_source = '''<h1>Collage News Reader</h1>
<p>This application fetches news articles stored inside user-generated media, such as photos on Flickr.</p>
<p>To begin you can <a href="fetch">fetch the latest news</a>. You can also <a href="open">read your old news</a>.
<p>This program is a proof-of-concept of Collage, a new censorship circumvention technique from Georgia Tech. For more information on Collage, please go to <a href="http://www.gtnoise.net/collage">http://www.gtnoise.net/collage</a>.</p>
'''

class ProxyFrame(wx.Frame):
    my_title = 'Collage news reader client'
    my_min_update_time = datetime.timedelta(1)

    def __init__(self, parent, db_filename, local_dir=None, custom=False):
        wx.Frame.__init__(self, parent, title=self.my_title)

        self.db_filename = db_filename
        self.database = Database(db_filename)
        self.local_dir = local_dir
        self.custom = custom
        self.logger = logging.getLogger('collage_proxy')

        my_lists = ['centralized', 'community', 'local', 'custom']
        task_lists = self.database.get_task_lists()
        for task_list in task_lists:
            if task_list not in my_lists:
                self.database.del_task_list(task_list)
        for task_list in my_lists:
            if task_list not in task_lists:
                self.database.add_task_list(task_list)
        self.database.set_loaded_task_modules('centralized', ['flickr_user'])
        self.database.set_loaded_task_modules('community', ['flickr_new'])
        self.database.set_loaded_task_modules('local', ['local'])
        self.database.set_loaded_task_modules('custom', ['picasa'])

        self.logger.info('Building main window')

        filemenu = wx.Menu()
        item = filemenu.Append(wx.ID_ANY, '&Fetch latest news...', 'Fetch the latest news')
        self.Bind(wx.EVT_MENU, self.on_fetch, item)
        item = filemenu.Append(wx.ID_OPEN, '&Open old news...', 'View censored documents')
        self.Bind(wx.EVT_MENU, self.on_open, item)
        filemenu.AppendSeparator()
        item = filemenu.Append(wx.ID_EXIT, 'E&xit', 'Terminate the program')
        self.Bind(wx.EVT_MENU, self.on_exit, item)

        menubar = wx.MenuBar()
        menubar.Append(filemenu, '&File')
        self.SetMenuBar(menubar)

        self.control = wx.html.HtmlWindow(self)
        self.control.SetPage(welcome_page_source)
        self.showing_welcome_page = True
        self.Bind(wx.html.EVT_HTML_LINK_CLICKED, self.on_link_click, self.control)

        self.Show(True)

    def on_open(self, event):
        self.logger.info('Showing "open" window')
        dlg = OpenFrame(self, self.db_filename)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.OK:
            self.open(dlg.get_address())
        else:
            self.logger.info('User canceled document open')

    def open(self, address):
        self.logger.info('Opening document "%s"', address)
        contents = self.database.get_file(address)
        if contents is not None:
            self.logger.info('Loading previously fetched document') 
            self.SetTitle('%s - %s' % (address, self.my_title))
            self.control.SetPage(contents)
            self.showing_welcome_page = False

    def on_fetch(self, event):
        address = common.format_address(datetime.datetime.utcnow())
        self.logger.info('User wants to fetch document "%s"', address)

        if not self.database.have_address(address):
            descriptions = {}
            descriptions['Quickly but with little deniability'] = 'centralized'
            descriptions['Slowely and with more deniability'] = 'community'
            if self.local_dir is not None:
                descriptions['With a local testing directory'] = 'local'
            if self.custom:
                descriptions['Using advanced tasks'] = 'custom'

            self.logger.info('Asking user how he wants to fetch the message')
            dlg = wx.SingleChoiceDialog(self, 'How do you want to fetch the news?\n\nThere is a tradeoff between deniability and speed:\nThe faster you download the news, the it will be easier\nfor a censor to identify your activity.', 'Task modules', sorted(descriptions.keys()))
            if dlg.ShowModal() != wx.ID_OK:
                dlg.Destroy()
                return
            task_list = descriptions[dlg.GetStringSelection()]
            dlg.Destroy()

            self.logger.info('User has elected to fetch using method "%s"' % task_list)

            self.database.set_active_task_list(task_list)
            self.update_task_list(task_list)

            self.fetch(address)
        else:
            self.logger.info('Address "%s" has already been fetched' % address)

        self.open(address)

    def fetch(self, address):
        self.logger.info('Fetching document "%s"', address)

        dlg = FetchFrame(self, self.db_filename, address)
        rc = dlg.ShowModal()
        data = dlg.get_data()
        if rc == wx.OK:
            if data is None:
                self.logger.error('There was an error downloading address "%s"' % address)
                dlg = wx.MessageDialog(self,
                                       'Cannot download the news from %s.' % address,
                                       'Fetch error',
                                       style=wx.OK|wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
            else:
                self.logger.info('Successfully fetched "%s"' % address)
                self.database.add_file(address, data)

    def update_task_list(self, task_list):
        self.logger.info('Upating task list "%s"', task_list)

        last_update = self.database.get_task_list_updated(task_list)
        #if last_update is not None \
        #        and datetime.datetime.utcnow() - last_update < self.my_min_update_time:
        #    return

        tasks = []
        if task_list == 'centralized':
            tasks.append(('flickr_user', 'WebUserFlickrTask(driver, %s)' % repr('srburnet')))
        elif task_list == 'community':
            #pagedata = urllib.urlopen('http://flickr.com/photos/tags').read()
            #match = re.search('<p id="TagCloud">(.*?)</p>', pagedata, re.S|re.I)
            #block = match.group(1)
            #block = re.sub(r'<a href=".*?".*?>', '', block)
            #block = re.sub(r'</a>', '', block)
            #block = re.sub(r'&nbsp;', '', block)

            #tags = block.split()
            #tag_pairs = [(a, b) for a in tags for b in tags if a < b] 
            tasks.append(('flickr_new', 'WebTagPairFlickrTask(driver, %s)' % repr(('nature', 'vacation'))))
        elif task_list == 'local':
            tasks.append(('local', 'ReadDirectory(%s)' % repr(self.local_dir)))
        elif task_list == 'custom':
            adv_tasks = []

            # Add your own advanced tasks here.
            adv_tasks.append(('picasa', 'WebTagsPicasaTask(driver, %s)' % repr(('nature', 'mountains'))))

            dlg = wx.SingleChoiceDialog(self, 'Select the task you want to use', 'Advanced tasks', map(lambda t: t[1], adv_tasks))
            if dlg.ShowModal() != wx.ID_OK:
                dlg.Destroy()
                raise ValueError()
            task = adv_tasks[dlg.GetSelection()]
            tasks.append(task)

        self.logger.info('Updating tasks: %s', str(tasks))

        self.database.delete_tasks(task_list)
        self.database.add_tasks(task_list, tasks)
        self.database.updated_task_list(task_list)

    def on_exit(self, event):
        self.logger.info('User closed application')
        self.Close(True)

    def on_link_click(self, event):
        href = event.GetLinkInfo().GetHref()
        self.logger.info('User clicked link "%s"', href)
        if self.showing_welcome_page:
            if href == 'fetch':
                self.on_fetch(event)
            elif href == 'open':
                self.on_open(event)
            else:
                self.logger.info('Opening link in external Web browser')
                webbrowser.open(href)
        else:
            dlg = wx.MessageDialog(self,
                                   'This link will be opened in your regular Web browser and will not be fetched using Collage. Are you sure you want to continue?',
                                   'Warning: %s' % event.GetLinkInfo().GetHref(),
                                   style=wx.YES_NO|wx.ICON_EXCLAMATION)
            rc = dlg.ShowModal()
            dlg.Destroy()
            if rc == wx.ID_YES:
                self.logger.info('Opening link in external Web browser')
                webbrowser.open(href)

class Snippet(object):
    def __init__(self, module, command):
        self.module = module
        self.command = command
        self.logger = logging.getLogger('collage_proxy')

    def get_module(self):
        return self.module

    def execute(self, driver):
        self.logger.info('Executing snippet "%s"' % self.module)

        pkg = __import__('collage_apps.proxy.taskmodules', fromlist=[str(self.module)])
        mod = pkg.__getattribute__(self.module)
        return eval(self.command, mod.__dict__, {'driver': driver})

class Database(object):
    def __init__(self, filename):
        self.conn = sqlite3.connect(filename, detect_types=sqlite3.PARSE_COLNAMES)
        self.conn.row_factory = sqlite3.Row
        self.conn.text_factory = str

        self.conn.execute('''PRAGMA foreign_keys = ON''')
        self.conn.execute('''CREATE TABLE IF NOT EXISTS downloads
                             (address TEXT, contents TEXT, fetched DEFAULT CURRENT_TIMESTAMP)''')
        self.conn.execute('''CREATE TABLE IF NOT EXISTS task_modules
                             (name TEXT, task_list TEXT, FOREIGN KEY (task_list) REFERENCES task_lists (name))''')
        self.conn.execute('''CREATE TABLE IF NOT EXISTS tasks
                             (module TEXT, task_list TEXT, command TEXT, FOREIGN KEY (task_list) REFERENCES task_lists (name))''')
        self.conn.execute('''CREATE TABLE IF NOT EXISTS task_lists
                             (name TEXT PRIMARY KEY, active INTEGER, last_update TEXT)''')
        self.conn.commit()

    def add_file(self, address, contents):
        self.conn.execute('''DELETE FROM downloads WHERE address = ?''', (address,))
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

    def have_address(self, address):
        cur = self.conn.execute('SELECT rowid FROM downloads WHERE address = ?', (address,))
        return cur.fetchone() is not None

    def is_task_module_loaded(self, task_list, module):
        cur = self.conn.execute('''SELECT name FROM task_modules
                                   WHERE name = ?
                                   AND task_list = ?''',
                                (module, task_list))
        return cur.fetchone() is not None

    def set_loaded_task_modules(self, task_list, modules):
        self.conn.execute('DELETE FROM task_modules WHERE task_list = ?', (task_list,))
        for module in modules:
            self.conn.execute('INSERT INTO task_modules (task_list, name) VALUES (?, ?)', (task_list, module))
        self.conn.commit()

    def get_loaded_task_modules(self, task_list):
        cur = self.conn.execute('SELECT name FROM task_modules WHERE task_list = ?', (task_list,))
        modules = []
        for row in cur:
            modules.append(row['name'])
        return modules

    def get_tasks(self, task_list):
        cur = self.conn.execute('SELECT module,command FROM tasks WHERE task_list = ?', (task_list,))
        tasks = []
        for row in cur:
            tasks.append(Snippet(row['module'], row['command']))
        return tasks

    def add_tasks(self, task_list, tasks):
        for (module, command) in tasks:
            self.conn.execute('INSERT INTO tasks (module, command, task_list) VALUES (?, ?, ?)',
                              (module, command, task_list))
        self.conn.commit()

    def delete_tasks(self, task_list):
        self.conn.execute('DELETE FROM tasks WHERE task_list = ?', (task_list,))
        self.conn.commit()

    def add_task_list(self, name):
        self.conn.execute('INSERT INTO task_lists (name) VALUES (?)', (name,))
        self.conn.commit()

    def get_task_lists(self):
        task_lists = []
        for row in self.conn.execute('SELECT name FROM task_lists'):
            task_lists.append(row['name'])
        return task_lists

    def get_active_task_list(self):
        cur = self.conn.execute('SELECT name FROM task_lists WHERE active = 1')
        row = cur.fetchone()

        assert cur.fetchone() is None     # Make sure there is exactly one active task

        if row is None:
            return None
        else:
            return row['name']

    def set_active_task_list(self, name):
        self.conn.execute('UPDATE task_lists SET active = (CASE name WHEN ? THEN 1 ELSE 0 END)', (name,))
        self.conn.commit()

    def del_task_list(self, name):
        self.conn.execute('DELETE FROM tasks WHERE task_list = ?', (name,))
        self.conn.execute('DELETE FROM task_modules WHERE task_list = ?', (name,))
        self.conn.execute('DELETE FROM task_lists WHERE name = ?', (name,))
        self.conn.commit()

    def get_task_list_updated(self, name):
        cur = self.conn.execute('SELECT last_update as "last_update [timestamp]" FROM task_lists WHERE name = ?', (name,))
        row = cur.fetchone()
        return row[0]

    def updated_task_list(self, name):
        self.conn.execute('UPDATE task_lists SET last_update = CURRENT_TIMESTAMP WHERE name = ?', (name,))
        self.conn.commit()

def main():
    usage = 'usage: %s [options]'
    parser = OptionParser(usage=usage)
    parser.set_defaults(database='proxy_client.sqlite', localdir=None, logging=False, custom=False)
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
    parser.add_option('-L', '--logging',
                      dest='logging',
                      action='store_true',
                      help='Enable debug logging to proxy_client.log')
    parser.add_option('-a', '--advanced',
                      dest='custom',
                      action='store_true',
                      help='Enable advanced tasks (not recommended)')
    (options, args) = parser.parse_args()

    logger = logging.getLogger('collage_proxy')
    if options.logging:
        handler = logging.FileHandler('proxy_client.log', 'w')
        formatter = logging.Formatter("[%(asctime)s] (%(name)s) %(levelname)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

    logger.info('Starting logging')

    app = wx.App(False)
    frame = ProxyFrame(None, options.database, options.localdir, options.custom)
    app.MainLoop()

if __name__ == '__main__':
    main()
