# grab_gamefaqs.py

import cStringIO
import getopt
import os
import re
import sgmllib
import string
import sys
import time
import urllib

__version__ = "1.1"

__usage__ = """\
grab_gamefaqs.py [options] faq_page_url [output_dir]

Options:
    -n N    Download at most N files. (mostly for testing)
"""

BASE_URL = "http://www.gamefaqs.com"
re_url = re.compile("/faqs/\d+$")
re_real_name = re.compile("%2F([^%]*?)\">View/Download Original")
re_url_info = re.compile(r"www\.gamefaqs\.com/\w+/(\S+?)/faqs/(\d+)")

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
        self._image = None
        self.raw_text = []
    def start_pre(self, attributes):
        self._pre = True
    def end_pre(self):
        self._pre = False
    def start_img(self, attributes):
        if self._pre and not self._image:
            attrs = dict(attributes)
            img_url = attrs.get('src', None)
            if img_url:
                self._image = img_url
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
    
    if parser._image:
        image_data = grab_url(parser._image)
        shortname = os.path.split(parser._image)[1]
        return image_data, shortname
    
    m = re_real_name.search(data)
    if m:
        real_name = m.group(1)
        raw_text = string.join(parser.raw_text, "")
    else:
        # assume this in HTML format... grab the URL again
        new_url = url + "?print=2"
        raw_text = grab_url(new_url) # we don't remove any HTML 
        #real_name = "faq_%s.html" % time.time() # FIXME use a dummy name
        real_name = make_up_filename(url)
    
    return raw_text, real_name

def make_up_filename(url, ext="html"):
    m = re_url_info.search(url)
    if m:
        return "%s-%s.%s" % (m.group(1), m.group(2), ext)
    
def write_faq(out_dir, filename, data):
    print "Writing:", filename, "...",
    path = os.path.join(out_dir, filename)
    f = open(path, 'wb')
    f.write(data)
    f.close()
    print "OK (%dK)" % (len(data) / 1024)

def grab_gamefaqs(url, out_dir, max_urls):
    try:
        os.makedirs(out_dir)
    except:
        pass
        
    data = grab_index_page(url)
    print len(data), "bytes read"
    urls = scan_index_page(data)
    print len(urls), "URLs found"
    if max_urls > -1: urls = urls[:max_urls]
    for url in urls:
        data, filename = grab_faq(url)
        write_faq(out_dir, filename, data)

if __name__ == "__main__":

    max_urls = -1
    opts, args = getopt.getopt(sys.argv[1:], "n:")

    if not args:
        print __usage__
        sys.exit(1)

    for o, a in opts:
        if o == "-n":
            max_urls = int(a)
    
    url = args[0]
    if args[1:]:
        out_dir = args[1]
    else:
        out_dir = "gamefaqs"
        
    grab_gamefaqs(url, out_dir, max_urls)
    
