#!/usr/bin/env python

# sudo apt-get install python-picamera python-pip python-rpi.gpio
# sudo pip install pibrella

import threading
import pibrella
import time
import BaseHTTPServer
import mjpeg6
import signal

dovideo = False

class ControlHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def redirect(s, location):
        s.send_response(302)
        s.send_header('Location', location)
        s.end_headers()

    def do_GET(s):
#        s.wfile.write("test")
#        print s.path

        # video feed control (this forces a refresh of the page)
        global dovideo
        if s.path == "/video1":
            dovideo = True
            s.redirect("/")
            return
        if s.path == "/video0":
            dovideo = False
            s.redirect("/")
            return

        # interactive page elements
        if s.path != "/":

            # forward for a short period
            if s.path == "/forward":
                pibrella.output.on()
                time.sleep(0.5)
                pibrella.output.off()

            # turn for a short period
            elif s.path == "/left":
                pibrella.output.f.on()
                time.sleep(0.5)
                pibrella.output.f.off()
            elif s.path == "/right":
                pibrella.output.e.on()
                time.sleep(0.5)
                pibrella.output.e.off()

            # forward indefinetely
            elif s.path == "/forwardstart":
                pibrella.output.on()
            elif s.path == "/forwardstop":
                pibrella.output.off()

            # turn indefinetely
            elif s.path == "/leftstart":
                pibrella.output.f.on()
            elif s.path == "/rightstart":
                pibrella.output.e.on()
            elif s.path == "/leftstop":
                pibrella.output.f.off()
            elif s.path == "/rightstop":
                pibrella.output.e.off()
            s.send_response(200)
            s.end_headers()
            s.wfile.write("done");
            return

#       otherwise s.path == "/"...
        s.send_response(200)
        s.end_headers()
        s.wfile.write('<html><head>\n')
        s.wfile.write('<style>body { font-size: x-large; } h1 { text-align: center } h3 { text-align: center }\n')
        s.wfile.write('p.control a { color: black; border: 3px solid black; padding: 1em; }\n')
        s.wfile.write('p { text-align:center; }\n')
        s.wfile.write('p.control { padding: 3px; margin-bottom: 2.5em; }</style>\n')
        s.wfile.write('</head><body><h1>A simple, open robot</h1>\n')

        s.wfile.write('<h3>Video Feed</h3>')
        if dovideo == False:
            s.wfile.write('<p class="control"><a href="/video1">Turn On</a></p>\n')
        else:
            s.wfile.write('<p class="control"><a href="/video0">Turn Off</a></p>\n')
            myip = s.request.getsockname();
            s.wfile.write('<p><img src="http://' + myip[0] + ':8080/t.mjpg" width="480" height="360"></p>')

        s.wfile.write('<h3>Quick Control</h3>')
        s.wfile.write('<p class="control"><a href="/left" target="myframe">Left</a> \n')
        s.wfile.write('<a href="/forward" target="myframe">Forward</a> \n')
        s.wfile.write('<a href="/right" target="myframe">Right</a></p>\n')

        s.wfile.write('<h3>Full Control</h3>')
        s.wfile.write('<p class="control"><a href="/leftstart" target="myframe">Go Left</a> \n')
        s.wfile.write('<a href="/forwardstart" target="myframe">Go Forward</a> \n')
        s.wfile.write('<a href="/rightstart" target="myframe">Go Right</a></p>\n')

        s.wfile.write('<p class="control"><a href="/leftstop" target="myframe">Stop Left</a> \n')
        s.wfile.write('<a href="/forwardstop" target="myframe">Stop Forward</a>\n')
        s.wfile.write('<a href="/rightstop" target="myframe">Stop Right</a></p>\n')

#        s.wfile.write('<p><br/><p align="center"><iframe src="/test.html" width="680" height="520"></iframe></p>')
        s.wfile.write('<iframe src="/blank" name="myframe" style="display: none"></iframe>\n')
        s.wfile.write('</body></html>\n')


class ServerThread(threading.Thread):
    def __init__(self, aserver):
        threading.Thread.__init__(self)
        self.aserver = aserver

    def run(self):
        self.aserver.serve_forever()

recorder=mjpeg6.VideoRecorder()
videohttpd=mjpeg6.ThreadedVideoServer(recorder, ("0.0.0.0", 8080), mjpeg6.VideoServerHandler)
videohttpdthread = ServerThread(videohttpd)

controlhttpd=BaseHTTPServer.HTTPServer(("0.0.0.0", 80), ControlHandler)
controlhttpdthread=ServerThread(controlhttpd)

print "Starting Video Capture..."
recorder.start()
print "Starting Video Server..."
videohttpdthread.start()
print "Starting Control Server..."
controlhttpdthread.start()

sleeping = 1

def quit_nicely():
    print "Stopping Video Capture..."
    recorder.running = False
    print "Stopping Video Server..."
    videohttpd.shutdown()
    print "Stopping Control Server..."
    controlhttpd.shutdown()

def signal_term_handler(signal, frame):
    print "SIGTERM recieved, shutting down..."
    global sleeping
    sleeping = 0
 
signal.signal(signal.SIGTERM, signal_term_handler)

try:
    print "Waiting for requests..."
    while sleeping:
        time.sleep(1)
except (KeyboardInterrupt, SystemExit) as e:
    pass
quit_nicely()
