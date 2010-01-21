import threading

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from jsonrpc import handleCGI, ServiceMethod

import pdb

class TaskDriver(object):
    def __init__(self):
        self.processing = threading.Condition()
        self.waiting_for_result = False

    def run_snippet(self, snippet):
        print 'Running snippet...',

        self.processing.acquire()
        self.current_snippet = snippet
        self.running_a_snippet = True
        self.processing.wait()
        retval = self.result
        is_error = self.is_error
        self.processing.release()

        print 'done'

        if is_error:
            raise RuntimeError(retval)
        else:
            return retval

    @ServiceMethod
    def fetch_snippet(self):
        self.processing.acquire()
        if self.waiting_for_result:
            raise RuntimeError('Snippet result pending')
        retval = self.current_snippet
        self.current_snippet = None
        self.waiting_for_result = True
        self.processing.release()

        return retval

    @ServiceMethod
    def snippet_return(self, result, is_error):
        self.processing.acquire()
        if not self.waiting_for_result:
            raise RuntimeError('No result pending')
        self.result = result
        self.is_error = is_error
        self.waiting_for_result = False
        self.running_a_snippet = False
        self.processing.notify()
        self.processing.release()
    
task_driver = TaskDriver()

class JsonRpcHttpRequestHandler(BaseHTTPRequestHandler):
    """This is a very simple HTTP request handler. It handles
    all requests as JSON-RPC calls, regardless of the URL."""

    def do_POST(self):
        self.send_response(200, 'Script output follows')

        length = self.headers.getheader('content-length')
        env = {'CONTENT_LENGTH': length}
        handleCGI(task_driver, self.rfile, self.wfile, env)

    def log_message(self, format, *args):
        pass

def rpc_server():
    address = ('127.0.0.1', 8000)
    server = HTTPServer(address, JsonRpcHttpRequestHandler)

    while True:
        server.handle_request()

rpc_thread = threading.Thread(target=rpc_server)
rpc_thread.daemon = True
rpc_thread.start()
