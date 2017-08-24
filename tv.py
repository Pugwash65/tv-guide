#!/usr/bin/python

import re
import sys
import tvguide

# target = 'castle' or 'ncis'

### TODO: castle target
### TODO: Filter out non-Freeview channels
### TODO: search for new: if no series info

try:
    tv = tvguide.TvGuide()
    tv.load_feed()
    tv.load_channels()

    target = tv.args[tvguide.ARG_TARGET]
    season = tv.args[tvguide.ARG_SEASON]
    tv.search(target, season)

except Exception as e:
    print e
    sys.exit(1)

sys.exit(0)

