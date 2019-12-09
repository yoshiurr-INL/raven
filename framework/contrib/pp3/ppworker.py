# Parallel Python Software: http://www.parallelpython.com
# Copyright (c) 2005-2012, Vitalii Vanovschi
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the author nor the names of its contributors
#      may be used to endorse or promote products derived from this software
#      without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
# THE POSSIBILITY OF SUCH DAMAGE.
"""
Parallel Python Software, PP Worker

http://www.parallelpython.com - updates, documentation, examples and support
forums
"""
import sys
import os
import atexit
try:
    import io
    ioStringIO = io.StringIO
   #ioStringIO = io.BytesIO
except ImportError:
    import StringIO as io
    ioStringIO = io.StringIO
#RAVEN CHANGE: switching to cloudpickle
import cloudpickle as pickle
import six
import pptransport
import ppcommon as ppc

copyright = "Copyright (c) 2005-2012 Vitalii Vanovschi. All rights reserved"
__version__ = version = "1.6.4.4"


def preprocess(msg):
    fname, fsources, imports = pickle.loads(ppc.b_(msg))
    fobjs = [compile(fsource, '<string>', 'exec') for fsource in fsources]
    for module in imports:
        try:            
            if not module.startswith("from ") and not module.startswith("import "):
                module = "import " + module
            six.exec_(module)
            globals().update(locals())
        except:
            print("An error has occured during the module import")
            sys.excepthook(*sys.exc_info())
    return fname, fobjs

class _WorkerProcess(object):

    def __init__(self):
        self.hashmap = {}
        self.e = sys.__stderr__
        self.sout = ioStringIO()
#        self.sout = open("/tmp/pp.debug","a+")
        sys.stdout = self.sout
        sys.stderr = self.sout
        self.t = pptransport.CPipeTransport(sys.stdin, sys.__stdout__)
       #open('/tmp/pp.debug', 'a+').write('Starting _WorkerProcess\n')
       #open('/tmp/pp.debug', 'a+').write('send... \n')
        self.t.send(str(os.getpid()))
       #open('/tmp/pp.debug', 'a+').write('send: %s\n' % str(os.getpid()))
       #open('/tmp/pp.debug', 'a+').write('receive... \n')
        self.pickle_proto = int(self.t.receive())
       #open('/tmp/pp.debug', 'a+').write('receive: %s\n' % self.pickle_proto)

    def run(self):
        try:
            #execution cycle
            while 1:
                open(ppc._debug_file, 'a+').write('run_10\n')
                __fname, __fobjs = self.t.creceive(preprocess)
                open(ppc._debug_file, 'a+').write('run_20\n')
                __sargs = self.t.receive()
                open(ppc._debug_file, 'a+').write('run_30\n')
                for __fobj in __fobjs:
                    try:
                        six.exec_(__fobj)
                        globals().update(locals())
                    except:
                        print("An error has occured during the " + \
                              "function import")
                        sys.excepthook(*sys.exc_info())
                open(ppc._debug_file, 'a+').write('run_40\n')
                __args = pickle.loads(ppc.b_(__sargs))
                open(ppc._debug_file, 'a+').write('run_50\n')
                __f = locals()[ppc.str_(__fname)]
                open(ppc._debug_file, 'a+').write('run_60\n')
                try:
                    __result = __f(*__args)
                except:
                    print("An error has occured during the function execution")
                    sys.excepthook(*sys.exc_info())
                    __result = None
                open(ppc._debug_file, 'a+').write('run_70\n')
                __sresult = pickle.dumps((__result, self.sout.getvalue()),
                        self.pickle_proto)
                open(ppc._debug_file, 'a+').write('run_80\n')
                self.t.send(__sresult)
                open(ppc._debug_file, 'a+').write('run_90\n')
                self.sout.truncate(0)
                open(ppc._debug_file, 'a+').write('run_100\n')
        except:
            print("A fatal error has occured during the function execution")
            sys.excepthook(*sys.exc_info())
            __result = None
            __sresult = pickle.dumps((__result, self.sout.getvalue()),
                    self.pickle_proto)
            self.t.send(__sresult)

def exit_handler():
    open(ppc._debug_file, 'a+').write("exit_handler ending ppworker\n")

if __name__ == "__main__":
    open(ppc._debug_file, 'a+').write("starting ppworker\n")
    atexit.register(exit_handler)
    # add the directory with ppworker.py to the path
    sys.path.append(os.path.dirname(__file__))
    wp = _WorkerProcess()
    wp.run()
    open(ppc._debug_file, 'a+').write("ending ppworker\n")

# Parallel Python Software: http://www.parallelpython.com
