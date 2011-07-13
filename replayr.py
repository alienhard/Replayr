"""Replayr -- a realtime HTTP log replay script.

Copyright(c) 2011 Adrian Lienhard <adrian@cmsbox.com>
MIT Licensed
"""

import sys
import time
import urllib2
from datetime import datetime
from optparse import OptionParser
import time
import re

# Apache log format -- you may need to adapt regex to your custom format!
# This pattern matches the Apache format
#"%{Host}i %h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-agent}i\"" vcombined
LOGLINE_RE = re.compile(\
    r'(?P<host>\S+) (?P<ip>\S+) (\S+) (\S+) \[(?P<time>.*?)\] "(?P<method>\S+) (?P<path>\S+) (?P<version>\S+)" (?P<code>\S+) (?P<size>\S+) "(?P<useragent>\S+)"')

# HTTP client timeout in seconds
TIMEOUT = 10


class RedirectHandler(urllib2.HTTPRedirectHandler):
    """Custom redirect handler that does not follow 301/302 responses"""
    
    def http_error_301(self, req, fp, code, msg, headers):  
        result = urllib2.HTTPRedirectHandler.http_error_301( 
            self, req, fp, code, msg, headers)
        result.status = code
    
    def http_error_302(self, req, fp, code, msg, headers):
        result = urllib2.HTTPRedirectHandler.http_error_302(
            self, req, fp, code, msg, headers)
        result.status = code
    
    
def main(f, proxy, exclude):
    """Setup HTTP client and generator pipe for requests"""
    setup_http_client(proxy)
    loglines = follow(f)
    requests = (parse(line) for line in loglines)
    requests = (r for r in requests if r is not None)
    if exclude:
        pattern = re.compile(exclude)
        requests = (r for r in requests if not pattern.search(r['path']))
    requests = (r for r in requests if is_get_or_head_request(r))
    for r in requests:
        send_request(r)

def parse(line):
    """Parse a log line, return None if regex does not match."""
    match = LOGLINE_RE.match(line)
    if match:
        return match.groupdict()
    return None

def is_get_or_head_request(r):
    """Filter GET and HEAD requests."""
    return r['method'] == 'GET' or r['method'] == 'HEAD'
    
def send_request(r):
    """Send the request r"""
    url = "http://" + r['host'] + r['path']
    req_result = None
    req_start = datetime.now()
    code = '200'
    try:
        # protect against "CONNECTION RESET BY PEER PROBLEM"
        time.sleep(0.01)
        f = urllib2.urlopen(url, timeout=TIMEOUT)
        f.read()
    except urllib2.HTTPError, e:
        code = str(e.code)
    except urllib2.URLError, e:
        req_result = 'FAILED[URLError: ' + str(e.reason) + ']'
    
    # treat 304 as a 200 status code since it depends on client cache 
    expected_code = r['code'] if r['code'] != '304' else '200'
    if not req_result and code != expected_code:
        req_result = 'FAILED[' + code + ' but expected ' + expected_code + ']'
    else:
        req_result = 'OK[' + code + ']' 

    req_delta = datetime.now() - req_start
    req_msecs = req_delta.seconds * 1000 + req_delta.microseconds / 1000
    print ("%s %5i   %s" % (req_result, req_msecs, url))


def setup_http_client(proxy):
    """Configure proxy server and register redirect handler."""
    proxy_config = {'http': proxy} if proxy else {}
    proxy_handler = urllib2.ProxyHandler(proxy_config)
    opener = urllib2.build_opener(proxy_handler, RedirectHandler)
    urllib2.install_opener(opener)
   
def follow(f):
    """A generator that yields new lines in file f."""
    while True:
        line = f.readline()
        if not line:
            time.sleep(0.1)
            continue
        yield line

if __name__ == "__main__":
    """Parse command line options."""
    usage = "usage: %prog [options] [logfile]"
    parser = OptionParser(usage)
    parser.add_option('-s', '--server',
        help='send requests to HOST',
        dest='host',
        default=None)
    parser.add_option('-e', '--exclude',
        help='ignore requests with paths that match REGEX',
        dest='regex',
        default=None)
    (options, args) = parser.parse_args()
    if len(args) == 1:
        # open file and move to end -- behaves like "tail -f"
        f = open(args[0])
        f.seek(0,2)
        main(f, options.host, options.regex)
    elif len(args) == 0:
        main(sys.stdin, options.host, options.regex)
    else:
        parser.error("incorrect number of arguments")
