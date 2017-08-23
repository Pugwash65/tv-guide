#!/usr/bin/python

import requests
import xml.etree.ElementTree as ET

FEED24 = 'http://www.xmltv.co.uk/feed/6549'
FEED72= 'http://www.xmltv.co.uk/feed/6550'
FEED7DAYS = 'http://www.xmltv.co.uk/feed/6582'


#link = FEED72
#f = requests.get(link)
# xml_text = f.text
# Error checking

f = open('6550', 'r')
xml_text = f.read()
f.close()

root = ET.fromstring(xml_text)
print root
print xml_text