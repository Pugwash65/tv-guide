#!/usr/bin/python

import re
import sys
import requests
import xml.etree.ElementTree as ET

FEED24 = 'http://www.xmltv.co.uk/feed/6549'
FEED72= 'http://www.xmltv.co.uk/feed/6550'
FEED7DAYS = 'http://www.xmltv.co.uk/feed/6582'

if len(sys.argv) != 2:
    raise Exception('Missing search target')

# target = 'castle' or 'ncis'

target = sys.argv[1]

#link = FEED72
#f = requests.get(link)
# xml_text = f.text
# Error checking

f = open('6550', 'r')
xml_text = f.read()
f.close()

root = ET.fromstring(xml_text)

regstr = '{0}'.format(target)
regexp = re.compile(regstr, re.IGNORECASE)

channels = {}

for child in root:
    if child.tag == 'channel':
        id = child.get('id')
        name = child.find('display-name').text
        channels[id] = name

    if child.tag == 'programme':
         title = child.find('title')

         if not regexp.match(title.text):
             continue

         start =  child.get('start')
         channel_id =  child.get('channel')
         episode = child.find('episode-num')

         if channel_id not in channels:
             raise Exception('{0}: Not in channel list'.format(channel_id))

         channel = channels[channel_id]

         if episode is None:
             print 'No series info: ', title.text, channel
             sys.exit()

         print title.text, channel
         print episode.text


