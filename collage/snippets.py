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

import pdb
class Snippet(object):
    """Arbitrary executable code snippets."""

    def __init__(self, code, compiled, environment, modulename='<unknown>'):
        self._code = code
        self._compiled = compiled
        self._environment = environment

    def execute(self, params):
        my_env = dict(self._environment)
        my_env.update(params)
        return eval(self._compiled, my_env)

send_snippet = 'send_vector(id, vector)'
receive_snippet = 'receive_vector(id)'
can_embed_snippet = 'can_embed(id, vector)'

def load_snippets(directories, params):
    """Load all primitive snippets in a set of directories, and
    execute each assisted snippet in the context of each of the
    primtive snippets."""

    # Evaluate and store primitive snippets
    primitive_modules = {}
    for directory in directories:
        for filename in os.listdir(directory):
            (modulename, ext) = os.path.splitext(filename)
            if os.path.isfile(os.path.join(directory, filename)) \
                    and ext == '.py':
                globals = params
                try:
                    execfile(os.path.join(directory, filename), globals)
                except Exception as exception:
                    print 'Error loading primitive module "%s"' % modulename
                    print 'Exception: %s' % (str(exception),)
                else:
                    primitive_modules[modulename] = globals

    # Compile assisted snippets
    assisted_modules = []
    assisted_code = [('send', send_snippet),
                     ('receive', receive_snippet),
                     ('can_embed', can_embed_snippet)]
    for name, code in assisted_code:
        try:
            compiled = compile(code, name, 'eval')
        except Exception as exception:
            print 'Error loading assisted module "%s"' % name
            print 'Exception: %s' % (str(exception),)
        else:
            assisted_modules.append((name, code, compiled))

    # Associate each assisted snippet with each primtive snippet
    all_snippets = {}
    for pname, environment in primitive_modules.items():
        snippets = []
        for (aname, code, compiled) in assisted_modules:
            module_name = '%s in %s' % (aname, pname)
            snippet = Snippet(code, compiled, environment, module_name)
            snippets.append(snippet)
        all_snippets[pname] = tuple(snippets)

    return all_snippets

if __name__ == '__main__':
    all_snippets = load_snippets()

    for aname, snippets in all_snippets.items():
        print 'Snippets from assisted module %s:' % aname

        for (pname, snippet) in snippets:
            print 'Executing snippet %s in %s' % (aname, pname)
            snippet.execute({})
