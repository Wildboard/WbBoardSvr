import os
import sys

cur_dir = os.getcwd()

WORKDIR = None

if sys.platform in ['win32', 'cygwin']:
    cur_dir = cur_dir.lower()
    WORKDIR="c:/users/wildboard/main/boardsvr/work"
elif sys.platform == 'darwin':
    WORKDIR = '/Users/grisha/dev/boardsvr/work'
elif sys.platform == 'linux2':
    WORKDIR = '/opt/wb_svn_main/boardsvr/work'
else:
    raise Exception("Unsupported platform: %s" % sys.platform)

print "We are in %s, checking that we are in %s" % (cur_dir, WORKDIR)
if cur_dir != WORKDIR:
    try:
        os.chdir(WORKDIR)
    except OSError, e:
        print "Cannot change directory to %s: %s" % (WORKDIR, e)
        sys.exit(1)

print "We are in %s..." % (os.getcwd())

LOCK_FILE = os.path.join(WORKDIR, 'lock.txt')

FEED_FILE = os.path.join(WORKDIR, 'feed.json')
