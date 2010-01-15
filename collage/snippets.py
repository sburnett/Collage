""" The technique for executing dynamic python code is as follows:

    * We provide two types of dynamic code execution: "primitive" and "assisted".
    * In "primitive" execution, we execute a python module from disk. It is
        executed only once, and the results of its execution are stored for use in
        assisted execution. (i.e., we save the dictionary of global variables
        created by the module.)
    * In "assisted" execution, we execute a snippet of python code in the context
        of the "primitive" modules. Because these snippets can run multiple times,
        they are precompiled using python's 'compile' function.
"""

import os.path

class Snippet(object):
    """Abstract class of executable code snippets"""

    def __init__(self, code, environment):
        self._code = code

    def execute(self, params):
        raise NotImplementedError

    def get_code(self):
        return self._code

class PythonSnippet(Snippet):
    """Support for arbitrary executable code snippets."""

    def __init__(self, code, compiled, environment, modulename='<unknown>'):
        self._code = code
        self._compiled = compiled
        self._environment = environment

    def execute(self, params):
        my_env = dict(self._environment)
        my_env.update(params)
        return eval(self._compiled, my_env)

python_send_snippet = 'send_vector(data)'
python_receive_snippet = 'receive_vector()'
python_can_embed_snippet = 'can_embed()'

def load_snippets(directories):
    snippets = []
    snippets.extend(load_python_snippets(directories))
    return snippets

def load_python_snippets(directories):
    primitive_modules = {}
    for directory in directories:
        for filename in os.listdir(directory):
            (modulename, ext) = os.path.splitext(filename)
            if ext == '.py':
                globals = {}
                try:
                    execfile(os.path.join('primitives', filename), globals)
                except Exception as exception:
                    print 'Error loading primitive module "%s"' % modulename
                    print 'Exception: %s' % (str(exception),)
                else:
                    primitive_modules[modulename] = globals

    assisted_modules = []
    assisted_code = [('send', python_send_snippet),
                     ('receive', python_receive_snippet),
                     ('can_embed', python_can_embed_snippet)]
    for name, code in assisted_code:
        try:
            compiled = compile(code, name, 'eval')
        except Exception as exception:
            print 'Error loading assisted module "%s"' % name
            print 'Exception: %s' % (str(exception),)
        else:
            assisted_modules.append((name, code, compiled))

    all_snippets = {}
    for pname, environment in primitive_modules.items():
        snippets = []
        for (aname, code, compiled) in assisted_modules:
            module_name = '%s in %s' % (aname, pname)
            snippet = PythonSnippet(code, compiled, environment, module_name)
            snippets.append(snippet)
        all_snippets[pname] = tuple(snippets)

    return all_snippets

del load_python_snippets

if __name__ == '__main__':
    all_snippets = load_python_snippets()

    for aname, snippets in all_snippets.items():
        print 'Snippets from assisted module %s:' % aname

        for (pname, snippet) in snippets:
            print 'Executing snippet %s in %s' % (aname, pname)
            snippet.execute({})
