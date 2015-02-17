#!/usr/bin/env python3
from tornado import gen
import json, re, os, sys, socket
import tornado.netutil
import tornado.httpserver
import tornado.websocket
import tornado.process
import tornado.web
import tornado.ioloop
import tornado.iostream
import traceback
from collections import deque
from argparse import ArgumentParser

'''
var ws = new WebSocket("ws://localhost:8888/websocket")
ws.onmessage = function(msg){console.log(msg.data);}
'''


def send_output(application, key, stream_name, history, out):
    out = out.decode("utf-8", errors="replace")
    if len(out) > 0:
        lines = re.split("([^\n]*\n)", out)
        to_print = application.partial_lines.setdefault(key, {}).get(stream_name, "")
        for line in lines:
            to_print += line
            if len(to_print) > 0 and to_print[-1] == "\n":
                print("sending: " + to_print.strip())
                to_remove = []
                for listener in application.socket_listeners.get(key, set()):
                    try:
                        message = json.dumps({"type":"output", "stream":stream_name, "msg":str(to_print.strip()), "index":application.out_indexes[key]})
                        application.out_indexes[key] += 1
                        application.history.setdefault(key, deque(maxlen=history)).append(message)
                        listener.write_message(message)
                    except tornado.websocket.WebSocketClosedError:
                        to_remove.append(listener)
                for listener in to_remove:
                    try:
                        application.socket_listeners.get(key, set()).remove(listener)
                        print("removed dead listener")
                    except KeyError:
                        pass
                to_print = ""
        
        application.partial_lines[key][stream_name] = to_print
        
def cleanup(application):
    print("Stopping IOLoop")
    tornado.ioloop.IOLoop.current().stop()

def make_handler(key, command, terminate_on_completion = False, history=1000):
    
    class CommandWebSocket(tornado.websocket.WebSocketHandler):
        setup = False
        
        def start_proc(application ):
            if "sub_procs" not in dir(application):
                application.sub_procs = {}
            if "socket_listeners" not in dir(application):
                application.socket_listeners = {}
            if "partial_lines" not in dir(application):
                application.partial_lines = {}
            if "history" not in dir(application):
                application.history = {}
            if "out_indexes" not in dir(application):
                application.out_indexes = {}
                application.out_indexes[key] = 0
    
            #don't start the process twice
            if key not in application.sub_procs:
                application.sub_procs[key]= tornado.process.Subprocess(["python", "test_proc.py"],
                        stdout=tornado.process.Subprocess.STREAM, stderr=tornado.process.Subprocess.STREAM, shell=False)
                
                #set callbacks for stdout
                application.sub_procs[key].stdout.read_until_close(
                        callback=lambda x: send_output(application, key, "stdout", history, x),
                            streaming_callback=lambda x: send_output(application, key, "stdout", history, x))
                
                #when the stdout stream closes we can assume the process is terminated
                if terminate_on_completion:
                    application.sub_procs[key].stdout.set_close_callback(lambda : cleanup(application))
                
                #set callbacks for stderr
                application.sub_procs[key].stderr.read_until_close( 
                        callback=lambda x: send_output(application, key, "stderr", history, x),
                           streaming_callback=lambda x: send_output(application, key, "stderr", history, x))
        
        def init(self):
            if not self.setup:
                
                self.key = key
                self.command = command
                self.terminate_on_completion = terminate_on_completion
                self.history = history
                
                self.status_index = 0
                
                
            self.setup = True
            
        def open(self):
            self.init()
            self.application.socket_listeners.setdefault(self.key, set([])).add(self)
            print("WebSocket opened")
    
    
        def send_status(self, ty, msg, **kwargs):
            message = kwargs
            message.update({"type": ty, "msg":msg, "index":self.status_index})
            self.status_index += 1
            self.write_message(json.dumps(message))
            
            
        def on_message(self, message):
            self.init()
            try:
                parsed = json.loads(message)
            except:
                self.send_status("error", "Got invalid JSON message: " + message)
            else:
                try:
                    if "directive" in message:
                        
                        #Termination
                        if parsed["directive"] == "terminate":
                            if self.application.sub_procs.get(self.key, None) != None:
                                self.application.sub_procs[self.key].proc.terminate()
                                self.send_status("info", "Sent SIGTERM to process")
                            else:
                                self.send_status("info","Tried to terminate, but process not started or already ended")
                        #Fetch Status
                        elif parsed["directive"] == "status":
                            
                            if self.application.sub_procs.get(self.key, None) == None:
                                self.send_status("error", "Process has not been started yet, or has been terminated.")
                            elif self.application.sub_procs[self.key].proc.poll() == None:
                                self.send_status("status", "Not finished yet", running=True)
                            else:
                                self.send_status("status", "Process finished with exit code: "+str(self.application.sub_procs[self.key].proc.returncode), running=False)
                        
                        elif parsed["directive"] == "history":
                            for item in self.application.history.setdefault(self.key, deque(maxlen=self.history)):
                                self.write_message(item)
                                
                        else:
                            self.send_status("error", "Unknown directive in message: " + str(message["command"]))
                    else:
                        self.self.send_status("error", "Message missing 'directive': " + str(message))
                except Exception:
                    exc = traceback.format_exc()
                    sys.stderr.write(exc + "\n")
                    self.send_status("error", "Failed to process command:\n"+exc)

    def on_close(self):
        self.init()
        self.application.socket_listeners[self.key].remove(self)
        print("WebSocket closed")


    return CommandWebSocket

class Redirector(tornado.web.RequestHandler):
    def get(self):
        self.redirect("/static/index.html")
        
class CachelessStaticFileHandler(tornado.web.StaticFileHandler):
    def set_extra_headers(self, path):
        # Disable cache
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')

def start_server(command, key="default", port=0, terminate_on_completion=False, autoreload=False, history=1000):
    static_path = os.path.join(os.path.dirname(__file__), "static")
    
    handler = make_handler("my_thing", command, terminate_on_completion=terminate_on_completion, history=history)
    application =  tornado.web.Application([
            (r'/', Redirector),
            (r'/static.*', CachelessStaticFileHandler, {"path":static_path}),
            (r'/websocket', handler)
        ], static_path=static_path, autoreload=autoreload)
    
    
    sockets = tornado.netutil.bind_sockets(port, '')
    server = tornado.httpserver.HTTPServer(application)
    server.add_sockets(sockets)
    print("starting webserver on " + str(sockets[0].getsockname()[1]))
    
    handler.start_proc(application)
    
    loop = tornado.ioloop.IOLoop.instance()
    loop.start()
    print("closing IOLoop")
    loop.close()

if __name__ == "__main__":
    parser = ArgumentParser("Start up a process with a tornado web-socket-ey wrapper")
    parser.add_argument("-p", "--port", default=0, type=int, help="Port number to bind to, port 0 chooses a random open port")
    parser.add_argument("-t", "--no-terminate", help="Keep the server alive after child process has terminated", action="store_true")
    parser.add_argument("-a", "--autoreload", help="Should we autoreload the server if this script changes?", action="store_true")
    parser.add_argument("-s", "--history", default=1000, type=int, help="Number of lines of history to store")
    parser.add_argument("command", nargs=1, help="Command to execute.  will be run in bash")
    
    options = parser.parse_args()
    start_server(options.command, port=options.port, autoreload=options.autoreload, terminate_on_completion=not options.no_terminate, history=options.history)