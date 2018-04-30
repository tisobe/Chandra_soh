#!/usr/bin/env /proj/sot/ska/bin/python

#####################################################################################
#                                                                                   #
#           check_msid_exist.py: check whether msid can be extracted with maude     #
#                                                                                   #
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
    msid = sys.argv[1].strip()
else:
    print "\n\tUsage: check_msid_exist.py <msid>\n"
    exit(1)

start  = '2018:001:00:00:00'
stop   = '2018:001:00:05:00'

try:
    out   = maude.get_msids(msid, start, stop)
    print "in the database"
except:
    print "not in the database"
