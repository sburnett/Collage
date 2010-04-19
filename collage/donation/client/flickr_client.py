#!/usr/bin/env python

import Tkinter
from tkFileDialog import askopenfilename
from tkMessageBox import showinfo
import os.path
import subprocess
import datetime
import tempfile
import sys
import time

import pdb

import flickrapi

api_key = 'ebc4519ce69a3485469c4509e8038f9f'
api_secret = '083b2c8757e2971f'

class MyApp:
    def __init__(self, myParent):
        self.flickr = self.init_flickr()

        self.parent = myParent

        self.filenameVar = Tkinter.StringVar()
        self.filenameVar.set('(Click to choose)')
        self.titleVar = Tkinter.StringVar()
        self.tagsVar = Tkinter.StringVar()
        self.timeVar = Tkinter.IntVar()
        self.timeVar.set(24)

        myParent.title(string='Collage Flickr Photo Donation')
        self.myFrame = Tkinter.Frame(myParent, padx=2, pady=2)
        self.myFrame.grid(row=0, column=0)

        Tkinter.Label(self.myFrame, text='File:').grid(row=0, column=0, sticky=Tkinter.E)
        Tkinter.Button(self.myFrame, textvariable=self.filenameVar, command=self.choose_file).grid(row=0, column=1, sticky=Tkinter.W)

        Tkinter.Label(self.myFrame, text='Title:').grid(row=1, column=0, sticky=Tkinter.E)
        Tkinter.Entry(self.myFrame, textvariable=self.titleVar).grid(row=1,column=1, sticky=Tkinter.W)
        
        Tkinter.Label(self.myFrame, text='Description:').grid(row=2, column=0, sticky=Tkinter.E)
        self.descText = Tkinter.Text(self.myFrame, width=40, height=4)
        self.descText.grid(row=2, column=1, sticky=Tkinter.W)

        Tkinter.Label(self.myFrame, text='Tags:').grid(row=3, column=0, sticky=Tkinter.E)
        Tkinter.Entry(self.myFrame, textvariable=self.tagsVar).grid(row=3, column=1, sticky=Tkinter.W)

        Tkinter.Label(self.myFrame, text='Max. donation hours:').grid(row=4, column=0, sticky=Tkinter.E)
        Tkinter.Entry(self.myFrame, textvariable=self.timeVar).grid(row=4, column=1, sticky=Tkinter.W)

        Tkinter.Button(self.myFrame, text='Upload', command=self.on_submit).grid(row=5, column=1, sticky=Tkinter.E)

    def init_flickr(self):
        flickr = flickrapi.FlickrAPI(api_key, api_secret)
        (token, frob) = flickr.get_token_part_one(perms='write')
        if not token:
            showinfo('Flickr Authorization', 'Click OK once you have authorized this application')
        flickr.get_token_part_two((token, frob))

        return flickr

    def choose_file(self, event=None):
        filetypes = [('JPEG', '.jpeg'), ('JPEG', '.jpg')]
        filename = askopenfilename(title='Choose Photo', filetypes=filetypes)
        if len(filename) > 0:
            self.filename = filename
            self.filenameVar.set(os.path.basename(self.filename))

    def upload_progress(self, progress, done):
        if done:
            print 'Done uploading'
            sys.exit(0)
        else:
            print 'Uploading %d%% done' % progress

    def upload(self, filename, title, description, tags):
        self.flickr.upload(filename=filename, title=title, description=description, tags=tags, callback=self.upload_progress)

    def on_submit(self, event=None):
        showinfo('Upload message', 'Your photo will be uploaded to Flickr within the next %d hours' % self.timeVar.get())

        self.parent.withdraw()

        filename = self.filename
        title = self.titleVar.get()
        description = self.descText.get(1.0, Tkinter.END)
        tags = self.tagsVar.get()

        wait_start = datetime.datetime.utcnow()
        (days, seconds) = divmod(self.timeVar.get()*3600, 86400)
        max_wait = datetime.timedelta(days, seconds)
        poll_period = 3
        
        pdb.set_trace()

        handle = open(filename, 'r')
        atl = map(lambda t: '--attribute=tag:%s' % t, tags.split())
        atl.append('--attribute=title:%s' % title)
        atl.append('--attribute=description:%s' % description)
        atl.append('--lifetime=%d' % (max_wait.days*86400 + max_wait.seconds))
        submit_path = ['python', 'submit.py', 'flickr'] + atl
        proc = subprocess.Popen(submit_path, stdin=handle, stdout=subprocess.PIPE)
        rc = proc.wait()
        key = proc.stdout.read()

        if key is None \
                or len(key) == 0 \
                or rc != 0:
            print 'Could not donate. Uploading...'
            self.upload(filename, title, description, tags)

        print 'Processing donation...'

        while True:
            time.sleep(poll_period)

            if datetime.datetime.utcnow() - wait_start > max_wait:
                break

            retrieve_path = ['python', 'retrieve.py', key]
            outfile = tempfile.NamedTemporaryFile(suffix='.jpeg', delete=False)
            proc = subprocess.Popen(retrieve_path, stdout=outfile)
            rc = proc.wait()
            if rc == 0:
                pdb.set_trace()

                outfile.close()
                self.upload(outfile.name, title, description, tags)
                os.unlink(outfile.name)
                return
            else:
                outfile.close()
                os.unlink(outfile.name)
    
        self.upload(filename, title, description, tags)

def main():
    root = Tkinter.Tk()
    app = MyApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
