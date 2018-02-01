#!/usr/bin/python

import re
import sys
import tvguide

# target = 'castle' or 'ncis'

### TODO: Filter out non-Freeview channels

try:
    tv = tvguide.TvGuide()
    tv.load_feed()
    tv.load_channels()

    channels = tv.args[tvguide.ARG_CHANNELS]
    file = tv.args[tvguide.ARG_FILE]
    target = tv.args[tvguide.ARG_TARGET]
    season = tv.args[tvguide.ARG_SEASON]

    if channels:
        tv.channel_data()
    elif file is not None:
        tv.load_targets(file)
        tv.search_targets()
    else:
        tv.search(target, season)

    tv.results()

    sys.exit(0)

except Exception as e:
    print e
    sys.exit(1)
