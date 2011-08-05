# Replayr -- a realtime HTTP log replay script

A simple Python script that reads log lines from an Apache access log file and resends the GET and HEAD requests to a given host. Compares HTTP status codes and measures response times. Useful for testing.

Note: requests are replayed synchronously (only one request at a time), hence this script (as it is implemented now) does not reproduce a realistic high load scenario.


## Installation

Requires Python >= 2.6

Simply download the file.

If you have a different log format, adjust the regex LOGLINE_RE.


## Basic usage

    Usage: replayr.py [options] [logfile]
    
    Options:
      -h, --help            show this help message and exit
      -s HOST, --server=HOST
                            send requests to HOST
      -e REGEX, --exclude=REGEX
                            ignore requests with paths that match REGEX

Example:
`python -u replayr.py --server test.com access.log`

This reads new lines from access.log and sends them to `test.com`. You can also pipe logs to stdin:
`tail -f access.log | python -u replayr.py --server test.com`

Log output (written to stdout):

- A line like `OK[200] 88 http://somehost.com/path` indicates that the replayed request succeeded. It returned the same status code as the original request (200) and the request took 88ms to complete.
- In turn, `FAILED[404 but expected 200]` indicates that the status code received does not match the original status code.
- Timeouts and other errors are logged as `FAILED[<error message>]`.


## Exclude certain type of requests (e.g., static assets):
The option `--exclude` expects a regular expression that is matched against the path of a request.

Example:
`python -u replayr.py --server localhost --exclude '(\.jpe?g|\.png|\.gif|\.ico|\.js|\.css)$'`


## Replay requests from a production server on a remote test server

It's better not to replay logs directly from a production system (e.g., this doubles network traffic). A better solution is to first pipe log statements via netcat to the test server and replay them there:

On test host:
`nc -l -p 13992 | python -u replayr.py -s localhost`

On production host:
`tail -f access.log | nc remote.com 13992`


## License 

(The MIT License)

Copyright (c) 2011 Adrian Lienhard adrian@cmsbox.com;

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
'Software'), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.