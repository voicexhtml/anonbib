# Make rankings of papers and authors for automatic classification of content hotness

# Google Scholar address
# http://scholar.google.com/scholar?as_epq=

# Take care of the caching setup
cache_expire = 60*60*24*30 # 30 days

# Checks
import config
import os
import sys
from os.path import exists, isdir, join, getmtime
from os import listdir, remove

def remove_old():
   # Remove all old cached files
   filenames = listdir(cache_folder())
   from time import time
   now = time()
   for f in filenames:
      pf = join(cache_folder(), f)
      time_mt =  getmtime(pf)
      if now - time_mt > cache_expire: # 30 days
         remove(pf)

def cache_folder():
   r = join(config.OUTPUT_DIR, config.CITE_CACHE_DIR)
   if not exists(r):
      os.makedirs(r)
   assert isdir(r)
   return r

import md5
import re
from urllib2 import urlopen, build_opener
from datetime import date

# A more handy hash
def md5h(s):
   m = md5.new()
   m.update(s)
   return m.digest().encode('hex_codec')

format_tested = 0

def getCite(title, cache=True, update=True):
   #Returns (citation-count, scholar url) tuple, or (None,None)
   global format_tested
   if not format_tested and update:
      format_tested = 1
      TestScholarFormat()

   # Do not assume that the title is clean
   title = re.sub("\s+", " ", title)
   title = re.sub("[^'a-zA-Z0-9\. \-\/:]", "", title)
   title = re.sub("'\/", " ", title)

   # Make a custom user agent (so that we are not filtered by Google)!
   opener = build_opener()
   opener.addheaders = [('User-agent', 'Anon.Bib.0.1')]

   # We rely on google scholar to return the article with this exact title
   gurl = "http://scholar.google.com/scholar?as_epq=%s&as_occt=title"
   from urllib import quote
   url = gurl % quote(title)

   # Access cache or network
   if exists(join(cache_folder(), md5h(url))) and cache:
      page = file(join(cache_folder(), md5h(url)),'r').read()
   elif update:
      print "Downloading rank for %r."%title
      page = opener.open(url).read()
      file(join(cache_folder(), md5h(url)),'w').write(page)
   else:
      return (None, None)

   # Check if it finds any articles
   if len(re.findall("did not match any articles", page)) > 0:
      return (None, None)

   # Kill all tags!
   cpage = re.sub("<[^>]*>", "", page)

   # Add up all citations
   s = sum([int(x) for x in re.findall("Cited by ([0-9]*)", cpage)])
   return (s, url)

def get_rank_html(title, years=None, base_url=".", update=True,
                  velocity=False):
   s,url = getCite(title, update=update)

   # Paper cannot be found
   if s is None:
      return ''

   html = ''

   # Hotness
   H,h = 50,5
   if s >= H:
      html += '<a href="%s"><img src="%s/gold.gif" alt="More than %s citations on Google Scholar" title="More than %s citations on Google Scholar" /></a>' % (url,base_url,H,H)
   elif s >= h:
      html += '<a href="%s"><img src="%s/silver.gif" alt="More than %s citations on Google Scholar" title="More than %s citations on Google Scholar" /></a>' % (url,base_url,h,h)

   # Only include the velocity if asked.
   if velocity:
      # Velocity
      d = date.today().year - int(years)
      if d >= 0:
         if 2 < s / (d +1) < 10:
            html += '<img src="%s/ups.gif" />' % base_url
         if 10 <= s / (d +1):
            html += '<img src="%s/upb.gif" />' % base_url

   return html

def TestScholarFormat():
   # We need to ensure that Google Scholar does not change its page format under our feet
   # Use some cases to check if all is good
   assert(getCite("Stop-and-Go MIXes: Providing Probabilistic Anonymity in an Open System", False)[0] > 0)
   assert(getCite("Mixes protected by Dragons and Pixies: an empirical study", False)[0] == None)

if __name__ == '__main__':
   # First download the bibliography file.
   import BibTeX
   config.load(sys.argv[1])
   bib = BibTeX.parseFile(config.MASTER_BIB)
   remove_old()
   print "Downloading missing ranks."
   for ent in bib.entries:
      getCite(ent['title'], cache=True, update=True)
