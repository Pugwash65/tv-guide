import os
import re
import time
import datetime
import requests
import argparse
import xml.etree.ElementTree as ET

FEED_DEFAULT = 'FEED72'

FEED_DATA = {
            'FEED24': 'http://www.xmltv.co.uk/feed/6549',
            'FEED72': 'http://www.xmltv.co.uk/feed/6550',
            'FEED7DAYS': 'http://www.xmltv.co.uk/feed/6582'
}

XML_CHANNEL = 'channel'
XML_PROGRAMME = 'programme'
XML_ID = 'id'
XML_DISPLAY_NAME = 'display-name'
XML_TITLE = 'title'
XML_START = 'start'
XML_EPISODE = 'episode-num'
XML_DESCRIPTION = 'desc'
CACHE_TIMEOUT = 43200
CACHE_DIR = 'cache'

ARG_FEED = 'feed'
ARG_FILE = 'file'
ARG_QUIET = 'quiet'
ARG_TARGET = 'target'
ARG_SEASON = 'season'


class TvGuide:

    def __init__(self):
        self.quiet = False
        self.args = vars(self.parse_args())
        self.feedname = None
        self.xml = None
        self.channels = None

        self.basedir = os.path.dirname(os.path.dirname(__file__))
        self.cache_dir = os.path.join(self.basedir, CACHE_DIR)

        if not os.path.isdir(self.cache_dir):
            os.mkdir(self.cache_dir)

        if not os.path.isdir(self.cache_dir):
            raise Exception('Unable to create cache directory')

    def parse_args(self):

        parser = argparse.ArgumentParser(description='Process TV Guide Arguments')
        parser.add_argument('-q', '--quiet', action='store_true')
        parser.add_argument('--feed', action='store', dest=ARG_FEED, metavar='<Feed Name>', help='Feed Shortname')
        parser.add_argument('--file', action='store', dest=ARG_FILE, metavar='<Filename>', help='File containing search target information')
        parser.add_argument('-t', '--target', action='store', dest=ARG_TARGET, metavar='<Search Target>',
                            help='Search Target', required=True)
        parser.add_argument('-s', '--season', action='store', dest=ARG_SEASON, metavar='<Season Number>',
                            help='Season ' 'Number')

        args = parser.parse_args()

        return args

    def out_print(self, msg):

        if not self.args[ARG_QUIET]:
            print msg

        return True

    def cache_feed(self, cache_name, feedname):

        feed_url = FEED_DATA[feedname]

        self.out_print('Fetching feed {0}'.format(feedname))

        r = requests.get(feed_url)

        if r.status_code != requests.codes.ok:
            r.raise_for_status()

        f = open(cache_name, 'w')
        f.write(r.text)
        f.close

        self.out_print('Cached feed {0}'.format(feedname))
        return True

    def load_feed(self):

        feedname = self.args[ARG_FEED]

        if feedname is not None:

            if feedname not in FEED_DATA:
                feeds = FEED_DATA.keys()
                raise Exception('{0}: Unknown Feed - Valid feeds: {1}'.format(feedname, ', '.join(feeds)))

        else:
            feedname = FEED_DEFAULT

        self.feedname = feedname

        feedfile = feedname + '.xml'
        cache_name = os.path.join(self.cache_dir, feedfile)

        if not os.path.exists(cache_name):
            self.cache_feed(cache_name, feedname)
        else:
            now = time.time()
            t = os.path.getmtime(cache_name)

            if (now - t) > CACHE_TIMEOUT:
                self.cache_feed(cache_name, feedname)

        f = open(cache_name, 'r')
        xml_text = f.read()
        f.close()

        self.xml = ET.fromstring(xml_text)

        return True

    def load_channels(self):

        self.channels = {}

        for child in self.xml:
            if child.tag == XML_CHANNEL:
                channel_id = child.get(XML_ID)
                channel_name = child.find(XML_DISPLAY_NAME)

                if channel_id is None or channel_name is None:
                    print
                    ET.dump(child)
                    raise Exception('Missing channel id or name')

                self.channels[channel_id] = channel_name.text

        return True

    def search(self, target_title, target_season=None):

        if target_season is not None and len(target_season) == 1:
            target_season = target_season.zfill(2)

        regexp = re.compile(target_title, re.IGNORECASE)

        for child in self.xml:

            if child.tag == XML_PROGRAMME:
                title = child.find(XML_TITLE)

                if title is None:
                    print
                    ET.dump(child)
                    raise Exception('Missing programme title')

                ### TODO
                print title.text
                desc = child.find(XML_DESCRIPTION)
                print desc.text
                continue

                if not regexp.match(title.text):
                    continue

                start = child.get(XML_START)
                (start_time, timezone) = start.split(' ')
                start_str = datetime.datetime.strptime(start_time, '%Y%m%d%H%M%S').strftime('%H:%M:%S %d/%m/%y (%a)')

                channel_id = child.get(XML_CHANNEL)
                episode = child.find(XML_EPISODE)
                desc = child.find(XML_DESCRIPTION)

                if channel_id not in self.channels:
                    raise Exception('{0}: Not in channel list'.format(channel_id))

                channel = self.channels[channel_id]

                if target_season is not None:
                    if episode is None:

                        # Check description for Season

                        m = re.match('.+\s*S(\d)+,\s*Ep(\d+)$', desc.text)
                        if m is not None:
                            episode_season = m.group(1)
                            episode_str = 's{0}.e{1}'.format(m.group(1).zfill(2), m.group(2).zfill(2))
                        else:
                            episode_season = None
                    else:
                        m = re.match('^s(\d+)\.e\d+$', episode.text)
                        episode_season = m.group(1)
                        episode_str = episode.text
                else:
                    episode_season = None

                episode_str = ' ' + episode_str if episode_season is not None else ''
                programme_text = '{0}{1} ({2}) - {3}'.format(title.text, episode_str, channel, start_str)

                if episode_season is None:
                    print 'No series info: {0}'.format(programme_text)
                    continue

                if episode_season != target_season:
                    continue

                print programme_text

        return True
