# grab_gamefaqs.py

# TODO:
# - does not grab images yet

import cStringIO
import os
import re
import sgmllib
import string
import sys
import time
import urllib

__usage__ = """\
grab_gamefaqs.py faq_page_url [output_dir]
"""

BASE_URL = "http://www.gamefaqs.com"
re_url = re.compile("/faqs/\d+$")
re_real_name = re.compile("%2F([^%]*?)\">View/Download Original")

def grab_url(url, max_size=None):
    print 'Reading', url, '...',
    u = urllib.urlopen(url)
    if max_size is None:
        data = u.read()
    else:
        data = u.read(max_size)
    u.close()
    print 'OK'
    return data

class URLFinder(sgmllib.SGMLParser):
    def __init__(self, *args, **kwargs):
        sgmllib.SGMLParser.__init__(self, *args, **kwargs)
        self.urls = []
    def start_a(self, attributes):
        # collect URLs that refer to FAQs.
        d = dict(attributes)
        url = d.get('href', None)
        if url and re_url.search(url):
            #print 'URL found:', url
            self.urls.append(url)
            
class PreFinder(sgmllib.SGMLParser):
    # XXX may need to convert entities...
    def __init__(self, *args, **kwargs):
        sgmllib.SGMLParser.__init__(self, *args, **kwargs)
        self._pre = False
        self.raw_text = []
    def start_pre(self, attributes):
        self._pre = True
    def end_pre(self):
        self._pre = False
    def handle_data(self, data):
        if self._pre:
            self.raw_text.append(data)

def grab_index_page(url):
    if url.startswith('http:'):
        return grab_url(url)
    else:
        print 'Reading local file...',
        # assume it's a local file
        f = open(url, 'rb')
        data = f.read()
        f.close()
        print 'OK'
        return data
    
def scan_index_page(data):
    parser = URLFinder()
    parser.feed(data)
    return parser.urls
    
def grab_faq(url):
    url = BASE_URL + url
    data = grab_url(url)
    parser = PreFinder()
    parser.feed(data)
    m = re_real_name.search(data)
    if m:
        real_name = m.group(1)
    else:
        real_name = "faq_%s" % time.time() # use a dummy name
    raw_text = string.join(parser.raw_text, "")
    
    return raw_text, real_name
    
def write_faq(out_dir, filename, data):
    print "Writing:", filename, "...",
    path = os.path.join(out_dir, filename)
    f = open(path, 'wb')
    f.write(data)
    f.close()
    print "OK (%dK)" % (len(data) / 1024)

def grab_gamefaqs(url, out_dir):
    try:
        os.makedirs(out_dir)
    except:
        pass
        
    data = grab_index_page(url)
    print len(data), "bytes read"
    urls = scan_index_page(data)
    print len(urls), "URLs found"
    for url in urls:
        data, filename = grab_faq(url)
        write_faq(out_dir, filename, data)

if __name__ == "__main__":
    
    url = sys.argv[1]
    if sys.argv[2:]:
        out_dir = sys.argv[2]
    else:
        out_dir = "gamefaqs"
        
    grab_gamefaqs(url, out_dir)
    