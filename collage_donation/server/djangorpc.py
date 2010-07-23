from django.http import HttpResponse
from SimpleXMLRPCServer import SimpleXMLRPCDispatcher
dispatcher = SimpleXMLRPCDispatcher()

def call_xmlrpc(request):
    """Dispatch XML-RPC requests."""
    if request.method == 'POST':
        # Process XML-RPC call
        response = HttpResponse(mimetype='text/xml')
        response.write(dispatcher._marshaled_dispatch(request.raw_post_data))
        response['Content-length'] = str(len(response.content))
        return response
    else:
        # Show documentation on available methods
        response = HttpResponse()
        t = loader.get_template('xmlrpc.html')
        c = Context({'methods': dispatcher.system_listMethods()})
        response.write(t.render(c))
        return response

def xmlrpc(uri):
    """A decorator for XML-RPC functions."""
    def register_xmlrpc(fn):
        dispatcher.register_function(fn, uri)
        return fn
    return register_xmlrpc
