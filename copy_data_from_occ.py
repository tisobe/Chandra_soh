#!/usr/bin/env /proj/sot/ska/bin/python

#####################################################################################
#                                                                                   #
#   copy_data_from_occ.py: extract current SOH data from occ side                   #
#                                                                                   #
#           author: t. isobe (tisobe@cfa.harvard.edu)                               #
#                                                                                   #
#           last update: May 11, 2018                                               #
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
#
#---- occ msididx location
#
url    = 'https://occweb.cfa.harvard.edu/occweb/web/fot_web/software/sandbox/SOT_area/msididx.json'
#
#---- local directory path
#
outdir        = '/data/mta4/www/CSH/'
house_keeping = '/data/mta/Script/SOH_TI/house_keeping/'

#-------------------------------------------------------------------------------
#-- copy_data_from_occs: run infinite loop to extract blob and msididx data from occ side
#-------------------------------------------------------------------------------

def copy_data_from_occs():
    """
    run infinite loop to extract blob and msididx data from occ side
    input: none
    output: blob.json
            msididx.json
    """
#
#--- check whether a long blob extraction is currently running; if so, stop
#
    ifile   = house_keeping + 'running'
    running = read_file_data(ifile)

    if running[0] == '1':
        exit(1)
#
#--- read msid list
#
    ifile     = house_keeping + 'msid_list'
    msid_list = read_file_data(ifile)
#
#--- msid <--> id dict
#
    ifile     = house_keeping + 'msid_id_list'
    data      = read_file_data(ifile)

    mdict     = {}
    for ent in data:
        atemp  = re.split(':', ent)
        mdict[atemp[0]] = atemp[1]
#
#--- extract blob.json
#
    try:
        hold = run_extract_blob_data(msid_list, mdict )
    except:
        hold = 0
        write_run_file('0')

    if hold == 1:
#
#--- if the data are comming in (under comm), update msididx.json
#
        copy_msididx_data()

#-------------------------------------------------------------------------------
#-- run_extract_blob_data: extract current SOH data from occ side                 --
#-------------------------------------------------------------------------------

def run_extract_blob_data(msid_list, mdict):
    """
    extract current SOH data from occ side
    input:  msid_list   --- a list of soh related msids
            mdict       --- a dictionary of msid <--> id #
    output: blob.json   --- SOH data in json format
            hold        --- an indicator of whether the data is hold position: 0: no/1:yes
    """
    hold = 0
#
#--- check current time and set start and stop time
#
    stday = time.strftime("%Y:%j:%H:%M:%S", time.gmtime())
    stop  = Chandra.Time.DateTime(stday).secs
    start = stop - 300
#
#--- check whether the data are currently coming from comm
#--- if not expand the data extraction period so that we can
#--- the last valid data value
#
    try:
        out   = maude.get_msids('AOPCADMD', start, stop)
        val   = str((list(out['data'][0]['values']))[-1])
        start = stop - 30

        if val == 'NaN':
#
#--- it seems that we are out of the comm; find the last valid data
#
            hold = long_blob_extraction(msid_list, mdict, stop)

        else:
#
#--- if it is currently in comm, run the loop for slightly shorter than 10 mins
#
            timeout = time.time() + 280
            while time.time() < timeout:
                stday = time.strftime("%Y:%j:%H:%M:%S", time.gmtime())
                stop  = Chandra.Time.DateTime(stday).secs
                start = stop - 30
                chk   = extract_blob_data(msid_list, mdict, start, stop)
#
#--- if comm stops, check the last 5 mins to find valid data
#
                if chk == 'stop':
                    start = stop - 300
                    chk   = extract_blob_data(msid_list, mdict, start, stop)
                    break
    except:
#
#--- currently we are outside of comm. if the last blob.json does not contain
#--- valid data, update
#
        hold = long_blob_extraction(msid_list, mdict, stop)

    return hold

#-------------------------------------------------------------------------------
#-- long_blob_extraction: extract current SOH data from occ side but outside of comm link
#-------------------------------------------------------------------------------

def long_blob_extraction(msid_list, mdict, stop):
    """
    extract current SOH data from occ side but outside of comm link
            ---- basically try to find the last valid data from the database
    input:  msid_list   --- a list of soh related msids
            mdict       --- a dictionary of msid <--> id #
            stop        --- stop time in seconds from 1998.1.1
    output: blob.json   --- SOH data in json format
            hold        --- an indicator of whether the data is hold position: 0: no/1:yes
    """
#
#--- telling the data extractiion is going on to the script which may start 
#--- while this extraction is still going on so that the other script won't start
#
    write_run_file('1')
#
#--- check blob.json has non-"NaN" values
#
    if check_blob_state() == 1:             #---- 1 means that blob.json needs update
        hold = 1
#
#--- if the blob.json is "empty" check 10 mins ago
#
        start = stop - 600 
        chk   =  extract_blob_data(msid_list, mdict, start, stop)
#
#--- if it is still "empty" try the last 12 hrs
#
        if chk == 'stop':
            start = stop - 43200
            chk = extract_blob_data(msid_list, mdict, start, stop)
#
#--- telling the long extraction is finished
#
    else:
        hold = 0

    write_run_file('0')
        
    return hold

#-------------------------------------------------------------------------------
#-- write_run_file: update running file to indicates data extraction is going on 
#-------------------------------------------------------------------------------

def write_run_file(chk, rfile='running'):
    """
    update running file to indicates data extraction is going on
    input:  chk     --- indicator: 0: not running/1: data extraction is going on
            rfile   --- indicator file name: defalut: running
    output: <house_keeping>/running --- udated file
    """
    out   = chk + '\n'
    ofile = house_keeping + rfile
    fo    = open(ofile, 'w')
    fo.write(out)
    fo.close()

#-------------------------------------------------------------------------------
#-- check_blob_state: check whether blob.jzon has none "NaN" values           --
#-------------------------------------------------------------------------------

def check_blob_state():
    """
    check whether blob.jzon has none "NaN" values
    input: none, but read from <data_dir>/blob.json
    ouput:  run --- 1: need update / 0: blob has non-"NaN" values
    """
    run = 0
    try:
        bfile = outdir + 'blob.json'
        data  = read_file_data(bfile)
    
        chk   = 0
        for ent in data:
            mc1 = re.search('AOPCADMD', ent)
            mc2 = re.search('CIUB',     ent)
            mc3 = re.search('EB1K1',    ent)
            if (mc1 is not None) or (mc2 is not None) or (mc3 is not None):
                mcv  = re.search('"value":"NaN"', ent)
                chk += 1
                if mcv is not None:
                    run = 1
                    break
                else:
#
#--- even if the msid has a valid value, if the file is not updated more than 3 hrs
#--- update blob.json, just in a case, for some unknown reasons, it is not updated
#
                    if find_last_upate(bfile) == 1:
                        run = 1

                    else:
                        run = 0
                        if chk < 2:
                            continue
                    break
            else:
                run = 1
    except:
        run = 1

    return run

#-------------------------------------------------------------------------------
#-- find_last_upate: check the last update and if it is more than tsapn sec ago, notify 
#-------------------------------------------------------------------------------

def find_last_upate(tfile, tspan=10800):
    """
    check the last update and if it is more than tspan secs ago, notify
    input:  tfile   --- a file to be checked; 
            tspan   --- a time span in seconds; default is 3 hrs
    ouptput:    0 or 1. 1 indicates that more than tsapn secs passed from the last update
    """
#
#--- current time
#
    ctime = time.strftime("%Y:%j:%H:%M:%S", time.gmtime())
    ctime = Chandra.Time.DateTime(ctime).secs
#
#--- last fine update time
#
    btime = time.strftime("%Y:%j:%H:%M:%S", time.gmtime(os.path.getmtime(tfile)))
    btime = Chandra.Time.DateTime(btime).secs

    tdiff = ctime - btime

    if tdiff > tspan:
        return 1
    else:
        return 0

#-------------------------------------------------------------------------------
#-- extract_blob_data: extract current SOH data from occ side                 --
#-------------------------------------------------------------------------------

def extract_blob_data(msid_list, mdict, start, stop):
    """
    extract current SOH data from occ side
    input:  msid_list   --- a list of soh related msids
            mdict       --- msid <---> id dicct
            start       --- starting time
            stop        --- stopping time
    output: blob.json   --- SOH data in json format
    """
#
#--- check the most recent data and see whether it is a valid data
#--- if not just go back
#
    try:
        out   = maude.get_msids('AOPCADMD', start, stop)
        val   = str((list(out['data'][0]['values']))[-1])
        if val == 'NaN':
            return 'stop'
#
#--- find the most rescent updated time
#
        ctime = str((list(out['data'][0]['times']))[-1])
        ctime = Chandra.Time.DateTime(ctime).date
        ctime = ctime.replace(':', '')
    except:
        ###ctime = time.strftime("%Y%j%H%M%S", time.gmtime())
        return 'stop'

    mlen  = len(msid_list)
    mlst  = int(mlen/100) + 1
    mstp  = mlen -1
#
#--- extract data using maude tool; 100 msids at a time
#
    line  = '[\n'
    for  k in range(0, mlst):
        mstart     = k * 100
        mstop      = mstart + 100
#
#--- the last round has fewer than 100 msids
#
        if mstop > mlen:
            mstop  = mlen

        msid_short = msid_list[mstart:mstop]
#
#---- maude tool
#
        try:
            mdata = maude.get_msids(msid_short, start, stop)
        except:
            continue
#
#--- now extract data and put into json data format
#
        for m in range(mstart, mstop):
            msid = msid_list[m]
            nk   = m - mstart
            try:
                val = str((list(mdata['data'][nk]['values']))[-1])
                val = '"' + val + '"'
            except:
                val = '"NaN"'
            try:
                index  = mdict[msid]
            except:
                index  = '"0000"'
    
            out = '{"msid":"' + msid + '",'
            out = out + '"index":"' + index + '",'
            out = out + '"time":"'  + ctime + '",'
            out = out + '"value":'  + val  + ','
#
#--- if it is the last entry, do without ','
#
#            if m == mstp:
#                out = out + '"f": '     + '"1"}'
#            else:
#                out = out + '"f": '     + '"1"},'
     
            out  = out + '"f": '     + '"1"},'
            line = line  + out + "\n"
#
#---- special computed values
#
    [aoacfid, aoacfct] = get_aoacomputed(start, stop, ctime)
             
    line = line + aoacfid + '\n'
    line = line + aoacfct + '\n'

    line = line + ']'

    out  = outdir + 'blob.json'
    fo   = open(out, 'w')
    fo.write(line)
    fo.close()

    return 'run'

#-------------------------------------------------------------------------------
#-- get_aoacomputed: adding computerd AOACFID and AOACFCT to the database     --
#-------------------------------------------------------------------------------

def get_aoacomputed(start, stop, ctime):
    """
    adding computerd AOACFID and AOACFCT to the database
    input:  start   --- start time
            stop    --- stop time
            ctime   --- time to be display
    output: aoacfid --- AOACFID output in blob format
            aoacfct --- AOACFCT output in blob format
    """

    msid_short = ['AOACFID0', 'AOACFID1','AOACFID2','AOACFID3','AOACFID4','AOACFID5','AOACFID6','AOACFID7']
    aoacfid    = create_aoaline(msid_short, start, stop, 'AOACFIDC', 99999, ctime, mlast=0)

    msid_short = ['AOACFCT0', 'AOACFCT1','AOACFCT2','AOACFCT3','AOACFCT4','AOACFCT5','AOACFCT6','AOACFCT7']
    aoacfct    = create_aoaline(msid_short, start, stop, 'AOACFCTC', 98989, ctime, mlast=1)


    return [aoacfid, aoacfct]

#-------------------------------------------------------------------------------
#-- create_aoaline: create a combined blob data line                         ---
#-------------------------------------------------------------------------------

def create_aoaline(msid_short,start, stop, msid, index, ctime, mlast=0):
    """
    create a combined blob data line 
    input:  msid_short  --- a list of msids to be sued
            start       --- start time
            stop        --- stop time
            ctime       --- time to be display
            msid        --- msid to be used
            index       --- index of the msid
            mlast       --- indicator of whether this is the last of the blob entry
                            if so, it cannot have "," at the end
    output: out         --- blob data line
    """

    mdata = maude.get_msids(msid_short, start, stop)
    line = ''
    for k in range(0, 8):
        val = str((list(mdata['data'][k]['values']))[-1])
        line = line + str(val)[0]

    out = '{"msid":"' + msid + '",'
    out = out + '"index":"' + str(index) + '",'
    out = out + '"time":"'  + ctime + '",'
    out = out + '"value":"'  + line  + '",'
    if mlast == 1:
        out = out + '"f": '     + '"1"}'
    else:
        out = out + '"f": '     + '"1"},'


    return out

#-------------------------------------------------------------------------------
#-- copy_msididx_data: copy msididx.json from occ side                        --
#-------------------------------------------------------------------------------

def copy_msididx_data():
    """
    copy msididx.json from occ side
    input: none but read from <url>
    output: <outdir>/msididx.json
    """
    [usr, pwd] = get_u_p()

    cmd = 'rm ./msididx.json'
    os.system(cmd)
    cmd = 'wget --user='+usr + ' --password=' + pwd + '  ' + url
    os.system(cmd)
#
#--- special addtions
#
    line = '[{"name": "AOACFIDC", "idx": 99999, "description": "ACA Fiducial Object 0-7  (OBC)", "sc": [""]},'
    line = line + '{"name": "AOACFCTC", "idx": 98989, "description": "ACA Image Func 0-7 (OBC)", "sc": [""]},{"name"'

    f    = open('msididx.json', 'r')
    data = f.read()

    out = data.replace('[{"name"', line)

    outfile = outdir + 'msididx.json'
    fo      = open(outfile, 'w')
    fo.write(out)
    fo.close()


#-------------------------------------------------------------------------------
#-- get_u_p: get login information                                            --
#-------------------------------------------------------------------------------

def get_u_p():
    """
    get login information
    input: none
    output: user    --- user name
            pawd    --- password
    """

    data = read_file_data('/home/isobe/.netrc')

    for line in data:
        mc1 = re.search('login', line)
        mc2 = re.search('pass', line)
        if mc1 is not None:
            atemp = re.split('\s+', line)
            user  = atemp[1]
        elif mc2 is not None:
            atemp = re.split('\s+', line)
            pwd   = str(atemp[1].strip())

    return [user, pwd]

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------

def read_file_data(file):

    f    = open(file, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()

    return data

#-------------------------------------------------------------------------------

if __name__ == '__main__':

    copy_data_from_occs()

