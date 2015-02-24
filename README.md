# socket-executor
Execute a shell command and watch it's progress Tornado backend, websocket+angular frontend.

Great for tracking the progress of long-running processes on remote servers.

#### Web UI
Has a neat responsive web UI that looks like this:
![alt img](https://raw.githubusercontent.com/hospadar/socket-executor/master/screen.png)

#### Installation
You need to 'bower install' before you install the python package, this will pull in the js and css dependencies for the web UI.  The easiest way is to simply use the install script:
```bash
./install.sh
```

#### Running a Process
Use the 'socket-server.py' script (this will be installed to your path with the package)
```bash
$ socket-server.py -h 
usage: Start up a process with a tornado web-socket-ey wrapper
       [-h] [-p PORT] [--no-terminate] [--autoreload] [--history HISTORY] [-v]
       command [command ...]

positional arguments:
  command               Command to execute. Will be run in bash, you should
                        quote your command, otherwise only the first token
                        will be used.

optional arguments:
  -h, --help            show this help message and exit
  -p PORT, --port PORT  Port number to bind to, port 0 (the default) chooses a random open
                        port
  --no-terminate        Keep the server alive after child process has
                        terminated
  --autoreload          Should we autoreload the server if this script
                        changes? (for dev only)
  --history HISTORY     Number of lines of history to store
  -v, --verbose         More verbose logging
```

#### Example
Try a simple long-running command to get a good idea of what it looks like.

```bash
$ socket-server.py -v -p 8888 'ping www.google.com' #on linux, add '-c 99999' to make ping keep pinging 
starting webserver on 8888
sending: PING www.google.com (216.58.216.228): 56 data bytes
sending: 64 bytes from 216.58.216.228: icmp_seq=0 ttl=56 time=13.423 ms
sending: 64 bytes from 216.58.216.228: icmp_seq=1 ttl=56 time=15.617 ms
sending: 64 bytes from 216.58.216.228: icmp_seq=2 ttl=56 time=15.292 ms
sending: 64 bytes from 216.58.216.228: icmp_seq=3 ttl=56 time=15.453 ms
sending: 64 bytes from 216.58.216.228: icmp_seq=4 ttl=56 time=15.490 ms
sending: 64 bytes from 216.58.216.228: icmp_seq=5 ttl=56 time=13.019 ms
sending: 64 bytes from 216.58.216.228: icmp_seq=6 ttl=56 time=12.616 ms
sending: 64 bytes from 216.58.216.228: icmp_seq=7 ttl=56 time=27.414 ms
WebSocket opened
sending: 64 bytes from 216.58.216.228: icmp_seq=8 ttl=56 time=18.577 ms
sending: 64 bytes from 216.58.216.228: icmp_seq=9 ttl=56 time=13.532 ms
```

Then point your browser at http://localhost:8888/
