import os
import re
import time
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

CACHE_TIMEOUT = 14400
CACHE_DIR = 'cache'

ARG_FEED = 'feed'
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

    def search(self):

        target = self.args[ARG_TARGET]
        regexp = re.compile(target, re.IGNORECASE)

        for child in self.xml:

            if child.tag == 'programme':
                title = child.find('title')

                if title is None:
                    print
                    ET.dump(child)
                    raise Exception('Missing programme title')

                if not regexp.match(title.text):
                    continue

                start = child.get('start')
                channel_id = child.get('channel')
                episode = child.find('episode-num')

                if channel_id not in self.channels:
                    # check desc for Sx
                    raise Exception('{0}: Not in channel list'.format(channel_id))

                channel = self.channels[channel_id]

                if episode is None:
                    print 'No series info: ', title.text, channel

                print title.text, channel
                print episode.text


