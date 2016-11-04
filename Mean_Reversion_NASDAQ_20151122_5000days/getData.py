#!/usr/bin/python

# This code is to screen all the stocks to make sure they are all active
# Active stocks will be printed to a new file

import sys
import urllib2
import socket
import math
from array import array

# This codes asks for one parameter, which is the time range for backtesting
time = int(sys.argv[1])

period = 'd'

tLast = []

# Calibrate Yahoo Finance with AAPL and MSFT
for stock in ['AAPL', 'MSFT']:
    response = urllib2.urlopen('http://table.finance.yahoo.com/table.csv?s='+stock+'&d=12&e=29&f=3014&g='+period+'&a=3&b=23&c=1000&ignore=.csv')
    tLast.append( response.read().splitlines()[1].split(',')[0] ) # Store the last date

if tLast[0] != tLast[1]:
    sys.exit("Calibration fails with AAPL and MSFT.")

print "Calibration passes with AAPL and MSFT.\n"
print "Now Starts to screen the stocks with more than", time, period


# Open NASDAQ Website to get all the stock names
response = urllib2.urlopen('http://www.nasdaq.com/screening/companies-by-name.aspx?letter=0&exchange=nasdaq&render=download')
output = response.read().splitlines()

nStocks = len([row.split('"')[1] for row in output][1:])


# Files to write to
stockFile = open("stock_screened.dat", "w") # Stock names
priceFile = open("price_relative.dat", "wb") # Price relative: today's price / yesterday's price
volumeFile = open("volume.dat", "wb") # Stock volumes
dateFile = open("date.dat", "wb") # The dates in time range

i = 0
count = 0
for stock in [row.split('"')[1] for row in output][1:]:
    i += 1
    req = urllib2.Request('http://table.finance.yahoo.com/table.csv?s='+stock+'&d=12&e=29&f=3014&g='+period+'&a=3&b=23&c=1000&ignore=.csv')
    try:
        output = urllib2.urlopen(req, timeout=5).read().splitlines() # !!!!!!!!!!!!!! Timeout???
    except urllib2.URLError:
        print i,"/",nStocks, stock, "   Bad URL"
        continue # skips to the next iteration of the loop    
    except socket.timeout:
        print i,"/",nStocks, stock, "   Timeout"
        continue # skips to the next iteration of the loop 
    try:
        output = output[1:]
    except IndexError:
        print i,"/",nStocks, stock, "   Good", nPeriod, "No data"
        continue
    nPeriod = len(output)
    print i,"/",nStocks, stock, "   Good", nPeriod, output[0].split(',')[0]
    if nPeriod >= time + 1 and output[0].split(',')[0] == tLast[0]:
        allPositive = True
        for line in output[0:time]:
            oldPrice = float(line.split(',')[6])
            if oldPrice <= 0.0:
                allPositive = False
                break
        if allPositive == False:
            continue
        
        count += 1
        stockFile.write(stock+'\n')
        stockFile.flush()

        priceRelative = []
        newPrice = float(output[0].split(',')[6])
        for line in output[1:time+1]:
            oldPrice = float(line.split(',')[6])
            priceRelative = [ newPrice / oldPrice ] + priceRelative  # Append new priceRelative to the front of list
            newPrice = oldPrice
        floatArray = array('d', priceRelative)
        floatArray.tofile(priceFile)
        volumeArray = array('i', [int(row.split(',')[5]) for row in output[0:time]][::-1])
        volumeArray.tofile(volumeFile)
        if count == 1:
            dateArray = array('i', [int(row.split(',')[0].translate(None, '-')) for row in output[0:time]][::-1])
            dateArray.tofile(dateFile)
#            print dateArray
            #    print sys.getsizeof(floatArray), len(floatArray)
            #    print sys.getsizeof(volumeArray), len(volumeArray)
            #    print >> file, priceRelative
            #    print '\n'.join([row.split('"')[1] for row in output][1:time+1])

stockFile.close()
priceFile.close()
volumeFile.close()
dateFile.close()
