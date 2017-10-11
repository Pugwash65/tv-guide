import os
import re
import sys
import yaml
import time
import textwrap
import datetime
import requests
import argparse
import xml.etree.ElementTree as ET

FEED_DEFAULT = 'FEED7DAYS'

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
DATA_DIR = 'data'
DATA_CHANNELS = 'channels.yaml'

YAML_UNCLASSIFIED = 'unclassified'
YAML_INCLUDE = 'include'
YAML_EXCLUDE = 'exclude'

ARG_FEED = 'feed'
ARG_FILE = 'file'
ARG_DESC = 'desc'
ARG_QUIET = 'quiet'
ARG_TITLE = 'title'
ARG_TARGET = 'target'
ARG_SEASON = 'season'
ARG_CHANNELS = 'channels'


class TvGuide:

    def __init__(self):
        self.quiet = False
        self.args = vars(self.parse_args())
        self.feedname = None
        self.xml = None
        self.channels = None
        self.targets = None

        self.basedir = os.path.dirname(os.path.dirname(__file__))
        self.cache_dir = os.path.join(self.basedir, CACHE_DIR)
        self.data_dir = os.path.join(self.basedir, DATA_DIR)

        if not os.path.isdir(self.cache_dir):
            os.mkdir(self.cache_dir)

        if not os.path.isdir(self.cache_dir):
            raise Exception('Unable to create cache directory')

        self.channel_file = os.path.join(self.data_dir, DATA_CHANNELS)

    def parse_args(self):

        parser = argparse.ArgumentParser(description='Process TV Guide Arguments')
        parser.add_argument('-q', '--quiet', action='store_true')
        parser.add_argument('--channels', action='store_true', dest=ARG_CHANNELS, help='Generate Channel YAML')
        parser.add_argument('--feed', action='store', dest=ARG_FEED, metavar='<Feed Name>', help='Feed Shortname')
        parser.add_argument('--file', action='store', dest=ARG_FILE, metavar='<Filename>', help='File containing search target information')
        parser.add_argument('--desc', action='store_true', dest=ARG_DESC, help='Show description as well')
        parser.add_argument('-t', '--target', action='store', dest=ARG_TARGET, metavar='<Search Target>',
                            help='Search Target')
        parser.add_argument('-s', '--season', action='store', dest=ARG_SEASON, metavar='<Season Number>',
                            help='Season ' 'Number')

        args = parser.parse_args()

        if args.target is None and args.file is None and args.channels is False:
            raise Exception('--channels, --target or --file is required')

        return args

    def out_print(self, msg, flush=False):

        if not self.args[ARG_QUIET]:
            sys.stderr.write(msg)
            if flush:
                sys.stderr.flush()

        return True

    def cache_feed(self, cache_name, feedname):

        feed_url = FEED_DATA[feedname]

        self.out_print("Fetching feed {0}\n".format(feedname))

        r = requests.get(feed_url)

        if r.status_code != requests.codes.ok:
            r.raise_for_status()

        f = open(cache_name, 'w')
        f.write(r.text)
        f.close

        self.out_print("{0}: Feed cached\n".format(feedname), True)

        return True

    def load_feed(self):

        feedname = self.args[ARG_FEED]

        if feedname is not None:

            if feedname not in FEED_DATA:
                feeds = FEED_DATA.keys()
                raise Exception('{0}: Unknown Feed - Valid feeds: {1}'.format(feedname, ', '.join(feeds)))

        else:
            feedname = FEED_DEFAULT
            self.args[ARG_FEED] = feedname

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

        self.out_print('{0}: Loading cached feed....'.format(feedname), True)

        f = open(cache_name, 'r')
        xml_text = f.read()
        f.close()

        self.out_print("done\n")

        self.out_print('{0}: Parsing XML....'.format(feedname), True)

        self.xml = ET.fromstring(xml_text)

        self.out_print("done\n")

        return True

    def load_targets(self, file):

        f = open(file, 'r')
        yaml_data = f.read()
        f.close()

        targets = yaml.load(yaml_data)

        self.targets = targets

        return True

    def load_channels(self):

        feedname = self.args[ARG_FEED]

        self.out_print('{0}: Loading Channel Data...'.format(feedname), True)

        self.channels = {}

        if not os.path.isfile(self.channel_file):
            raise Exception('{0}: Channel classification file missing'.format(self.channel_file))

        f = open(self.channel_file, 'r')
        yaml_data = f.read()
        f.close()

        data = yaml.load(yaml_data, Loader=yaml.loader.BaseLoader)

        for child in self.xml:
            if child.tag == XML_CHANNEL:
                channel_id = child.get(XML_ID)
                channel_name = child.find(XML_DISPLAY_NAME)

                if channel_id is None or channel_name is None:
                    print
                    ET.dump(child)
                    raise Exception('Missing channel id or name')

                if channel_name.text in data[YAML_INCLUDE]:
                    self.channels[channel_id] = channel_name.text

        self.out_print("done\n")

        return True

    def channel_data(self):

        # Load existing channel map

        if os.path.isfile(self.channel_file):
            f = open(self.channel_file, 'r')
            yaml_data = f.read()
            f.close()

            data = yaml.load(yaml_data, Loader=yaml.loader.BaseLoader)

            if YAML_UNCLASSIFIED in data and len(data[YAML_UNCLASSIFIED]) > 0:
                c = len(data[YAML_UNCLASSIFIED])
                print "{0} unclassified channels in {1}".format(c, self.channel_file)
                return True

            data[YAML_UNCLASSIFIED] = []

            for name in self.channels.values():

                if name not in data[YAML_EXCLUDE] and name not in data[YAML_INCLUDE]:
                    print '{0}: Unclassified channel in feed'.format(name)
                    data[YAML_UNCLASSIFIED].append(name)

        # Write updated channel map

        f = open(self.channel_file, 'w')

        for key in [YAML_INCLUDE, YAML_EXCLUDE, YAML_UNCLASSIFIED]:
            f.write("{0}: \n".format(key))

            channels = sorted(data[key])
            for channel in channels:
                f.write("  - {0}\n".format(channel))

        f.close()

        return True

    def search_targets(self):

        for target in self.targets:

            if ARG_TITLE not in target and ARG_SEASON not in target:
                raise Exception('Invalid target data: Missing title or season')

            title = target[ARG_TITLE]
            season = str(target[ARG_SEASON]) if ARG_SEASON in target else None

            self.search(title, season)

        sys.exit()

    def search(self, target_title, target_season=None):

        feedname = self.args[ARG_FEED]

        if target_season is not None and len(target_season) == 1:
            target_season = int(target_season)

        target_regexp = '{0}|new:\s*{0}'.format(target_title)
        regexp = re.compile(target_regexp, re.IGNORECASE)

        count = 0

        for child in self.xml:

            if child.tag == XML_PROGRAMME:
                title = child.find(XML_TITLE)

                if title is None:
                    print
                    ET.dump(child)
                    raise Exception('Missing programme title')

                count += 1

                if count % 10 == 0:
                    self.out_print("{0}: Searching - {1}\r".format(feedname, count), True)

                if not regexp.match(title.text):
                    continue

                start = child.get(XML_START)
                (start_time, timezone) = start.split(' ')
                start_str = datetime.datetime.strptime(start_time, '%Y%m%d%H%M%S').strftime('%H:%M:%S %d/%m/%y (%a)')

                channel_id = child.get(XML_CHANNEL)
                episode = child.find(XML_EPISODE)
                desc = child.find(XML_DESCRIPTION)

                # Channel isn't one we're interested in - or perhaps is undefined in XML

                if channel_id not in self.channels:
                    continue

                channel = self.channels[channel_id]

                if episode is None:

                    # Check description for Season

                    m = re.match('.+\s*\(?S\s*(\d+),?\s*Ep\s*(\d+)\)?$', desc.text)
                    if m is not None:
                        episode_season = int(m.group(1))
                        episode_str = 's{0}.e{1}'.format(m.group(1).zfill(2), m.group(2).zfill(2))
                    else:
                        episode_season = None
                else:
                    m = re.match('^s(\d+)\.e\d+$', episode.text)
                    episode_season = int(m.group(1))
                    episode_str = episode.text

                episode_str = ' ' + episode_str if episode_season is not None else ''
                programme_text = '{0}{1} ({2}) - {3}'.format(title.text, episode_str, channel, start_str)

                if episode_season is None:
                    print 'No series info: {0}'.format(programme_text)
                    print "\t" + "\n\t".join(textwrap.wrap(desc.text, 60))
                    continue

                if target_season is not None and episode_season != target_season:
                    continue

                print programme_text
                if self.args[ARG_DESC]:
                    print "\t" + "\n\t".join(textwrap.wrap(desc.text, 60))

        self.out_print("\n")

        return True
