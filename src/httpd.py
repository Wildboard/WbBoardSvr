import sys
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
import urllib2
from SimpleHTTPServer import SimpleHTTPRequestHandler
import SocketServer
from cgi import parse_qs
import time
from lockfile import FileLock
import common

BOARD_ID = "1"

register_openers()

#PORT = 8888
PORT=80

MAIN_STATS_FNAME = "./log/stats.log"

stats_lock = FileLock(MAIN_STATS_FNAME)

main_stats = None

class MyHandler(SimpleHTTPRequestHandler):

    def __init__(self,req,client_addr,server):
        SimpleHTTPRequestHandler.__init__(self,req,client_addr,server)
    
    def sendOk(self):
        self.sendResponse("OK")
    
    def sendResponse(self, txt, code=200):
        self.send_response(code)
        self.send_header("Content-length", len(txt))
        self.end_headers()
        self.wfile.write(txt)
        self.wfile.flush()

    def do_GET(self):
        if self.path.startswith('/assets'):	
            with FileLock(common.LOCK_FILE):
                SimpleHTTPRequestHandler.do_GET(self)
        elif self.path.startswith('/addrag'):
            self.sendOk()
        elif self.path == '/statsrotate':
            statsrotate()
            self.sendOk()
        elif self.path.startswith('/log'):
            qs = self.path[self.path.index('?')+1:]
            parsed = parse_qs(qs)
            parsed['ts'] = str(int(time.time()))
            # Remove cachebuster
	    if '_' in parsed:
                del parsed['_']
            try:
                fields_to_write = [
                                   BOARD_ID,
                                   parsed['ts'], 
                                   parsed['id'][0],
                                   parsed['event'][0],
                                   parsed['state'][0]
                                   ]
            except Exception, e:
                print "Oops", e
                self.sendResponse("Stuff missing", 400)
                return
            line = ','.join(fields_to_write)
            with stats_lock:
                main_stats.write(line)
                main_stats.write("\n")
                main_stats.flush()
            self.sendOk()
        else:
            SimpleHTTPRequestHandler.do_GET(self)

def statsrotate():
    global main_stats
    if not main_stats:
        main_stats = open(MAIN_STATS_FNAME, 'a')
    else:
	with stats_lock:
            main_stats.close()
            datagen, headers = multipart_encode({"stats": open(MAIN_STATS_FNAME)}) 
            headers['User-Agent'] = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
            request = urllib2.Request("http://www.wildboard.net/statsrotate.php", datagen, headers)
            request.unverifiable = True 
            resp = urllib2.urlopen(request)
            # TODO log this locally somewhere
            resp_val = resp.read()
            print resp_val

def main():
    statsrotate()
    handler = MyHandler # SimpleHTTPRequestHandler
    global PORT
    if len(sys.argv) > 1:
        PORT = int(sys.argv[1])
    httpd = SocketServer.TCPServer(("", PORT), handler)
    print "Serving at port", PORT
    httpd.serve_forever()

if __name__ == "__main__":
    main()
