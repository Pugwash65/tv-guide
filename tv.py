#!/usr/bin/python

import re
import sys
import tvguide

# target = 'castle' or 'ncis'

try:
    tv = tvguide.TvGuide()
    tv.load_feed()
    tv.load_channels()
    tv.search()

except Exception as e:
    print e
    sys.exit(1)

sys.exit(0)

