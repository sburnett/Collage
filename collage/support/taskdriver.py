import threading

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from jsonrpc import handleCGI, ServiceMethod

class TaskDriver(object):
    client_timeout = 30

    def __init__(self):
        self.processing = threading.Condition()

    def run_snippet(self, snippet):
        self.processing.acquire()
        self.current_snippet = snippet
        try:
            self.processing.wait(self.client_timeout)
        except RuntimeError:
            raise RuntimeError('Timeout contacting task driver. Ensure task driver is running.')
        retval = self.result
        self.processing.release()

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
        self.waiting_for_result = False
        self.processing.notify()
        self.processing.release()
    
task_driver = TaskDriver()

class JsonRpcHttpRequestHandler(BaseHTTPRequestHandler):
    """This is a very simple HTTP request handler. It handles
    all requests as JSON-RPC calls, regardless of the URL."""

    def do_POST(self):
        length = self.headers.getheader('content-length')
        env = {'CONTENT_LENGTH': length}
        handleCGI(task_driver, self.rfile, self.wfile, env)

def rpc_server(self):
    address = ('127.0.0.1', 8000)
    server = HTTPServer(address, JsonRpcHttpRequestHandler)

    while True:
        server.handle_request()

threading.Thread(target=rpc_server).start()
