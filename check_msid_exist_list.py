#!/usr/bin/env /proj/sot/ska/bin/python

#####################################################################################
#                                                                                   #
#   check_msid_exist_list.py: find msids which are not in maude from the given list #
#           author: t. isobe (tisobe@cfa.harvard.edu)                               #
#                                                                                   #
#           last update: Apr 26, 2018                                               #
#                                                                                   #
#####################################################################################

import os
import sys
import re
import string
import math
import time
import Chandra.Time
import maude

if len(sys.argv) > 1:
    infile = sys.argv[1].strip()
else:
    print "\n\tUsage: check_msid_exist_list.py <msid_list>\n"
    exit(1)


f    = open(infile, 'r')
data = [line.strip() for line in f.readlines()]
f.close()

start  = '2018:001:00:00:00'
stop   = '2018:001:00:05:00'

for ent in data:
    if ent[0] == '#':
        continue
    else:
        atemp = re.split(':', ent)
        msid  = atemp[0]

        try:
            out   = maude.get_msids(msid, start, stop)
        except:
            print msid
