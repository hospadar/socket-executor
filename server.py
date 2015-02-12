#!/usr/bin/env python3
from tornado import gen
import json, re, os
import tornado.netutil
import tornado.httpserver
import tornado.websocket
import tornado.process
import tornado.web
import tornado.ioloop

'''
var ws = new WebSocket("ws://localhost:8888/websocket")
ws.onmessage = function(msg){console.log(msg.data);}
'''

listeners = set([])

partial = {}

def send_output(stream_name, out):
    import pdb
    pdb.set_trace()
    out = out.decode("utf-8", errors="replace")
    if len(out) > 0:
        lines = re.split("([^\n]*\n)", out)
        
        to_print = partial.get(stream_name, "")
        for line in lines:
            to_print += line
            if len(to_print) > 0 and to_print[-1] == "\n":
                for listener in listeners:
                    listener.write_message(json.dumps({"type":"output", "stream":stream_name, "msg":str(to_print.strip())}))
                to_print = ""
                
        partial["stream_name"] = to_print

class EchoWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        listeners.add(self)
        print("WebSocket opened")

    def on_message(self, message):
        try:
            parsed = json.loads(message)
        except:
            self.write_message(json.dumps({"type":"error", "msg":"Got invalid JSON message: " + message}))
        else:
            if "directive" in message:
                if parsed["directive"] == "start":
                    if "command" in parsed:
                        self.write_message(json.dumps({"type":"info", "msg":"Running command: " + json.dumps(parsed["command"])}))
                        self.application.proc= tornado.process.Subprocess(parsed["command"], stdout=tornado.process.Subprocess.STREAM, stderr=tornado.process.Subprocess.STREAM)
                        self.application.proc.stdout.read_until_close(callback=lambda x: send_output("stdout", x), streaming_callback=lambda x: send_output("stdout", x))
                        self.application.proc.stderr.read_until_close(callback=lambda x: send_output("stderr", x), streaming_callback=lambda x: send_output("stderr", x))
                    else:
                        self.write_message(json.dumps({"type":"error", "msg":"Missing 'command' from message: " + message}))
                elif parsed["directive"] == "terminate":
                    if self.application.proc != None:
                        self.application.proc.terminate()
                        self.write_message(json.dumps({"type":"info", "msg":"Sent SIGTERM to process"}))
                elif parsed["directive"] == "status":
                    if self.application.proc == None:
                        self.write_message(json.dumps({"type":"error", "msg":"Process has not been started"}))
                    elif self.application.proc.proc.poll() == None:
                        self.write_message(json.dumps({"type":"status", "value": False, "msg":"Not finished yet"}))
                    else:
                        self.write_message(json.dumps({"type":"status", "value": self.application.proc.proc.returncode, "msg":"Process terminated"}))
                else:
                    self.write_message(json.dumps({"type":"error", "msg":"Unknown directive in message: " + str(message["command"])}))
            else:
                self.write_message(json.dumps({"type":"error", "msg":"Message missing 'directive': " + str(message)}))

    def on_close(self):
        listeners.remove(self)
        print("WebSocket closed")

def start_server(port=0, command=None, terminate_on_completion=False):
    static_path = os.path.join(os.path.dirname(__file__), "static")
    application =  tornado.web.Application([
        (r'/static.*', tornado.web.StaticFileHandler, {"path":static_path}),
        (r'/websocket', EchoWebSocket)
    ], static_path=static_path)
    
    application.listen(8888)
    application.proc = None
    print("starting webserver")
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    start_server