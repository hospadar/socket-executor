#!/usr/bin/env python3
from tornado import gen
import json, re, os
import tornado.netutil
import tornado.httpserver
import tornado.websocket
import tornado.process
import tornado.web
import tornado.ioloop
import tornado.iostream
import traceback

'''
var ws = new WebSocket("ws://localhost:8888/websocket")
ws.onmessage = function(msg){console.log(msg.data);}
'''

listeners = set([])

partial = {}


def send_output(application, key, stream_name, out):
    out = out.decode("utf-8", errors="replace")
    if len(out) > 0:
        lines = re.split("([^\n]*\n)", out)
        to_print = application.partial_lines.setdefault(key, {}).get(stream_name, "")
        for line in lines:
            to_print += line
            if len(to_print) > 0 and to_print[-1] == "\n":
                print("sending: " + to_print.strip())
                for listener in application.socket_listeners.get(key, []):
                    listener.write_message(json.dumps({"type":"output", "stream":stream_name, "msg":str(to_print.strip())}))
                to_print = ""
        
        
        application.partial_lines[key][stream_name] = to_print

def make_handler(key, command):
    
    class CommandWebSocket(tornado.websocket.WebSocketHandler):
        setup = False
        
        def init(self):
            if not self.setup:
                self.key = key
                self.command = command
                if "sub_procs" not in dir(self.application):
                    self.application.sub_procs = {}
                if "socket_listeners" not in dir(self.application):
                    self.application.socket_listeners = {}
                if "partial_lines" not in dir(self.application):
                    self.application.partial_lines = {}
                
                #don't start the process twice
                if self.key not in self.application.sub_procs:
                    self.application.sub_procs[self.key]= tornado.process.Subprocess(["python", "test_proc.py"],
                            stdout=tornado.process.Subprocess.STREAM, stderr=tornado.process.Subprocess.STREAM, shell=False)
                    
                    #set callbacks for stdout
                    self.application.sub_procs[self.key].stdout.read_until_close(
                            callback=lambda x: send_output(self.application, self.key, "stdout", x),
                                streaming_callback=lambda x: send_output(self.application, self.key, "stdout", x))
                    
                    
                    #set callbacks for stderr
                    self.application.sub_procs[self.key].stderr.read_until_close( 
                            callback=lambda x: send_output(self.application, self.key, "stderr", x),
                               streaming_callback=lambda x: send_output(self.application, self.key, "stderr", x))
            self.setup = True
            
        def open(self):
            self.init()
            self.application.socket_listeners.setdefault(self.key, set([])).add(self)
            print("WebSocket opened")
    
        def on_message(self, message):
            self.init()
            try:
                parsed = json.loads(message)
            except:
                self.write_message(json.dumps({"type":"error", "msg":"Got invalid JSON message: " + message}))
            else:
                try:
                    if "directive" in message:
                        
                        #Termination
                        if parsed["directive"] == "terminate":
                            if self.application.sub_procs.get(self.key, None) != None:
                                self.application.sub_procs[self.key].proc.terminate()
                                self.write_message(json.dumps({"type":"info", "msg":"Sent SIGTERM to process"}))
                            else:
                                self.write_message(json.dumps({"type":"info", "msg":"Tried to terminate, but process not started or already ended"}))
                        #Fetch Status
                        elif parsed["directive"] == "status":
                            
                            if self.application.sub_procs.get(self.key, None) == None:
                                self.write_message(json.dumps({"type":"error", "msg":"Process has not been started yet, or has been terminated."}))
                            elif self.application.sub_procs[self.key].proc.poll() == None:
                                self.write_message(json.dumps({"type":"status", "value": False, "msg":"Not finished yet"}))
                            else:
                                self.write_message(json.dumps({"type":"status", "value": self.application.sub_procs[self.key].proc.returncode, "msg":"Process terminated"}))
                        
                                
                        else:
                            self.write_message(json.dumps({"type":"error", "msg":"Unknown directive in message: " + str(message["command"])}))
                    else:
                        self.write_message(json.dumps({"type":"error", "msg":"Message missing 'directive': " + str(message)}))
                except Exception:
                    exc = traceback.format_exc()
                    self.write_message(json.dumps({"type":"error", "msg":"Failed to process command:\n"+exc}))

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

def start_server(port=0, command=None, terminate_on_completion=False, autoreload=False):
    static_path = os.path.join(os.path.dirname(__file__), "static")
    
    
    application =  tornado.web.Application([
        (r'/', Redirector),
        (r'/static.*', CachelessStaticFileHandler, {"path":static_path}),
        (r'/websocket', make_handler("my_thing", "./test_proc.py"))
    ], static_path=static_path, autoreload=autoreload)
    
    application.listen(8888)
    application.proc = None
    print("starting webserver")
    import pdb
    
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    start_server(port=8888, autoreload=True)