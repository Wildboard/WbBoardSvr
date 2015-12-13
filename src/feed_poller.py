import random
from lockfile import FileLock
import os
from datetime import datetime
import os.path
import urlparse
import simplejson
from copy import deepcopy
import feedparser
import urllib
import traceback
import time
from copy import deepcopy
import common

# TODO config read from file
# TODO logging

PATH = "kaffeehaus/sanmateo/board1";

FEED = 'http://ads.wildboard.net/rss/'

BIG_JSON = { 
"feed_start_date" : "2013-06-16",
"feed_end_date"   : "2013-06-25",
"inventory_start_date" : "2013-06-16",
"inventory_end_date"   : "2013-06-25",

"flyers" : 
[],
"premium" : [
             {
              "vastUrl" : "http://localhost/default/vast_companion.xml", 
              "qr" : "http://localhost/default/wildboardqr.png"
             }
            ],

"news" :   [
             { 
                "summary" : "Wildboard unveiled at Kaffeehaus!",
                "url"  : "http://www.wildboard.net/"
             }
           ]
}

SAMPLE_FLYER = {
  "id"         : "1",
  "category"   : ["events"], 
  "sticky"     : 0,
  "titleArea"  : { 
     "title"    :  "NorCal Auto Swap Meet",
     "subtitle" : [ 
                    "Saturday, July 21st, 2013", 
                    "San Mateo Event Center",
                    "2 miles away"
                  ],
     "posted"    :  "2013-06-25",
     "sort_date" :  "2013-07-21"
                },


 "bodyArea" :    { 
          "description" : "A traditional automotive swap meet for car people, by car people. Over 2,000 vendor spaces. Rod, Classic and Collector Car Corral. Collector Motorcycles Too! Great food. Entry only $8.00. Under 12 free. Tons of parking."
                 }, 

 "mediaArea"   : [
                  "http://feed.wildboard.net/sample/norcal-auto-swap-meet.jpg"
                 ],

 "contactArea" : [  
                    {
                      "img"  : "http://feed.wildboard.net/sample/norcal-auto-swap-meet-qr.png", 
                      "text" : "Saturday, July 21st, 2013 San Mateo Event Center"
                    }
                  ]
  }
 
 
new_items = False

IMAGE_DIR = os.path.join(common.WORKDIR, 'images')

def fetch_image(img_url):
    parsed_url = urlparse.urlparse(img_url)
    fname = os.path.basename(parsed_url.path)
    dest = os.path.join(IMAGE_DIR, fname)
    if os.path.exists(dest):
        # print "%s already exists" % dest
        pass
    else:
        global new_items
        new_items = True
        log("Fetching %s into %s" % (img_url, dest))
        urllib.urlretrieve(img_url, dest)
    
    new_url = 'http://localhost/images/%s' % fname
    return new_url

my_feed = None

ids = []
"""IDs of flyers fetched previously."""

valid_ids = []
"""IDs of flyers fetched presently."""

ids_to_flyers = {}

def log(msg):
    t = datetime.now()
    ts = t.strftime('%y/%m/%d %H:%M:%S')
    try:
        print '%s %s' % (ts, msg)
    except UnicodeEncodeError:
        print 'Oops'
	# '%s %s' % (ts, msg.encode('ascii'))

def loop():
    global my_feed
    global new_items
    new_items = False
    del valid_ids[:]
    feed = feedparser.parse(FEED)
    if not feed.entries:
	print 'Error occurred fetching feed: %s' % feed
    if not my_feed:
        my_feed = deepcopy(BIG_JSON)
    flyers = my_feed['flyers']
    fetched_cnt = 0
    added = []
    for f in feed.entries:
        fetched_cnt += 1
        new_f = {}
	url_id = f['id']
	num_id = url_id.replace('http://ads.wildboard.net/','')
        fid = new_f['id'] = num_id
        valid_ids.append(fid)
        if 'title' not in f:
            print 'No title in %s' % f
            continue
        if fid in ids:
            # print "Already have ID %s" % id
            continue
        else:
            ids_to_flyers[fid] = new_f
            ids.append(fid)
            added.append("%s: %s" % (fid, f['title']))
        
        # TODO will allow multiple later
        new_f['category'] = [ f['category'] ]
        new_f['sticky'] = 0
        titleArea = new_f['titleArea'] = {}
        
        titleArea['title'] = f['title']
        
        subtitle = titleArea['subtitle'] = []
        if f['price']:
            subtitle.append(f['price'])
        if f['address']:
            subtitle.append(f['address'])
        # TODO
        # new_f['distance'] = ""
        
	titleArea['posted'] = f['published']

        # TODO
        pubParsed = f['published_parsed']
        sortDate = "%04d-%02d-%02d" % (pubParsed.tm_year, pubParsed.tm_mon, pubParsed.tm_mday)

        cf_ends = False
	if 'cf_ends' in f:
            cf_ends = True
	    sortDate = f['cf_ends'][:10]
              
	titleArea['sort_date'] =  sortDate
        print 'cf_ends: %s, posted %s, sort_date %s' % (cf_ends, titleArea['posted'], sortDate)
  
        bodyArea = new_f['bodyArea'] = {}
        bodyArea['description'] = f['description']
        
        mediaArea = new_f['mediaArea'] = []
        img_cnt = 0
        while True:
            img_key = 'image%d' % img_cnt
            if img_key in f:
                img_url = f[img_key]
                local_img_url = fetch_image(img_url)
                mediaArea.append(local_img_url)
                img_cnt += 1
            else:
                break
        
        contactArea = new_f['contactArea'] = []
        
	# TODO Create proper contacts based on QR - or
	# this is done server-side?
        if 'qr_calendar' in f:
            d= {'text'  : ''}
            d['img'] = f['qr_calendar']
            contactArea.append(d)
        if 'qr_website' in f:
	    d= {'text'  : ''}
            d['img'] = f['qr_website']
            contactArea.append(d)      
        if 'qr_contact' in f:
	    d= {'text'  : ''}
            d['img'] = f['qr_contact']
            contactArea.append(d)
        flyers.append(new_f)
    
    if True:
        ids_set = set(ids) 
	print 'IDs fetched previously: %s' % ids_set
        valid_ids_set = set(valid_ids)
	print 'Valid IDs (fetched currently): %s' % valid_ids_set
        invalid_ids = list(ids_set - valid_ids_set)
	print 'Invalid IDs: %s' % invalid_ids
        removed = []
        for inv_id in invalid_ids:
            inv_f = ids_to_flyers[inv_id]
	    if 'title' not in inv_f:
	        print 'No title found in %s' % inv_f
            else:
                removed.append("%s: %s" % (inv_id, inv_f['titleArea']['title']))
            flyers.remove(inv_f)
            del ids_to_flyers[inv_id]
        del ids[:]
        ids.extend(valid_ids)
    else:
        # Test the deletion functionality
        idx = random.randint(0, len(ids)-1)
        print "Deleting %s" % flyers[idx]['id']
        del ids[idx]
        del flyers[idx]
    log("Waiting for lock...")
    with FileLock(common.LOCK_FILE):
        feed_file = open(common.FEED_FILE, 'w')
	log("Writing to %s" % feed_file)
        simplejson.dump(my_feed, feed_file, indent="\t")
        feed_file.close()
    if added or removed:
        log("Total fetched: %s" % fetched_cnt)
    if added:
        log("%s added: %s" % (len(added), "; ".join(added)  ))
    if removed:
        log("%s removed: %s" % (len(removed), "; ".join(removed)  ))
        

def main():
    print "Starting..."
    while True:
        try:
            loop()
            time.sleep(10)
        except Exception, e:
            traceback.print_exc()
	    

if __name__ == "__main__":
    main()
