#!/usr/bin/python

# Trend Following Method

import sys
import urllib2
import socket
import math
import heapq
import numpy as np
from matplotlib import pyplot
import operator
from array import array

period = 'd'
avgTime = 1

# The portfolio's performance in the previous day must be above some threshold
# 1.0 means no win no loss 
# 0.8 means you only get 80% as daily return 
# 1.2 means you get 120% as daily return
performanceThreshold = 1.5

volumeRankThreshold = 200

def projectOnToSimplex(portfolioVector):

    sortedVector = np.sort(portfolioVector)[::-1]

    nStocks = len(portfolioVector)
    rho = 0

    sum = 0.0
    for i in range(0, nStocks):
        # I used a trick here, sum here does not include the current sortedVector[i]
        if sum - sortedVector[i] * i <= 1.0:
            rho = i + 1
        else:
            break
        sum = sum + sortedVector[i]
    
    theta = (sum - 1) / rho
    for i in range(0, nStocks):
        portfolioVector[i] = max(portfolioVector[i] - theta, 0.0)

np.set_printoptions(threshold='nan') # Otherwise we see ellipses when print out np array

stockList = open('stock_screened.dat').read().splitlines()
nStocks = len(stockList)

file = open('price_relative.dat', 'r')
floatArray = array('d')
floatArray.fromstring(file.read())
time = len(floatArray) / nStocks
priceRelative = np.reshape(floatArray, (nStocks, time))

volumeFile = open('volume.dat', 'r')
volumeArray = array('i')
volumeArray.fromstring(volumeFile.read())
volume = np.reshape(volumeArray, (nStocks, time))

dateFile = open('date.dat', 'r')
dateArray = array('i')
dateArray.fromstring(dateFile.read())
print dateArray

cmlReturn = [1] # Cumulative returns on every day
gainList = []

volumeThreshold = sorted(volume[:, time - 1], reverse=True)[volumeRankThreshold-1]
newPriceRelative = np.empty([volumeRankThreshold, time])
newStockList = []
j = 0
for i in range(0, nStocks):
    if volume[i, time - 1] >= volumeThreshold:
        newPriceRelative[j] = priceRelative[i]
        print 
        newStockList = newStockList + [stockList[i]]
        j = j + 1
        if j == volumeRankThreshold:
            break
        
priceRelative = newPriceRelative
nStocks = len(priceRelative)

portfolioVector = np.ones(nStocks) / nStocks
ASADportfolioVector = np.ones(nStocks) / nStocks
UCRPportfolioVector = np.ones(nStocks) / nStocks

ASADcmlReturn = [1]
ASADgainList = []


UCRPcmlReturn = [1]
UCRPgainList = []

print nStocks

for i in range(0, time):

    # Cumulative Return
    cmlReturn.append(np.dot(priceRelative[:, i], portfolioVector) * cmlReturn[-1])
    ASADcmlReturn.append(np.dot(priceRelative[:, i], ASADportfolioVector) * ASADcmlReturn[-1])
    UCRPcmlReturn.append(np.dot(priceRelative[:, i], UCRPportfolioVector) * UCRPcmlReturn[-1])

    # Performance Everyday
    gainList.append(np.dot(priceRelative[:, i], portfolioVector) - 1)
    ASADgainList.append(np.dot(priceRelative[:, i], ASADportfolioVector) - 1)
    UCRPgainList.append(np.dot(priceRelative[:, i], UCRPportfolioVector) - 1)

    # Calculate Lagrange Multiplier related to loss function
    numeratorOfLagrangeMultiplier = performanceThreshold - np.dot(portfolioVector, priceRelative[:, i])
    denominatorOfLagrangeMultiplier = np.sum(np.square(priceRelative[:, i] - np.average(priceRelative[:, i]) * np.ones(nStocks)))
    lagrangeMultiplier = numeratorOfLagrangeMultiplier / denominatorOfLagrangeMultiplier
    
    # Loss Function is set to zero if performance is below the threshold
    lagrangeMultiplier = max(0, lagrangeMultiplier)

    # Update Portfolio Vector for the next trading day
    portfolioVector = portfolioVector + lagrangeMultiplier * (priceRelative[:, i] - np.average(priceRelative[:, i]) * np.ones(nStocks))

    # Project Portfolio Vector to the simplex domain
    projectOnToSimplex(portfolioVector)

    ASADportfolioVector = np.zeros(nStocks)
    singleStockIndex = 0
    for j in range(0, nStocks):
        if priceRelative[j, i] < 1.0 and portfolioVector[j] > portfolioVector[singleStockIndex]:
            singleStockIndex = j
    if singleStockIndex == 0 and priceRelative[0, i] >= 1.0:
        singleStockIndex = np.argmax(portfolioVector)

    ASADportfolioVector[singleStockIndex] = 1

    print i, "Cumulative Return: ", cmlReturn[-1]

#print priceRelative.index(min(priceRelative)) # Not a good way to find index_min

del cmlReturn[0]
del ASADcmlReturn[0]
del UCRPcmlReturn[0]

xindex = []
xdate = []
nxinterval = 5
for i in range(0, nxinterval):
    idate = int ( math.ceil( float(i) * ( time - 1 ) / nxinterval ) )
    xindex.append( idate )
    xdate.append( str(dateArray[idate]) )
xindex.append(time - 1)
xdate.append( str(dateArray[time - 1]) )

pyplot.subplot(2,1,1)
pyplot.xlabel('Date', fontsize=20)
pyplot.ylabel('Cumulative Return', fontsize=20)
pyplot.xticks(xindex, xdate, fontsize=12)
pyplot.yscale('log')
pyplot.plot(range(0, time), cmlReturn, 'k', label = 'Trend Following')
pyplot.plot(range(0, time), ASADcmlReturn, 'g', label = 'ASAD Trend Following')
pyplot.plot(range(0, time), UCRPcmlReturn, 'r', label = 'Uniform Constant Rebalanced Portfolios')
pyplot.legend(loc='upper left')
pyplot.grid()

pyplot.subplot(2,1,2)
pyplot.xlabel('Date', fontsize=20)
pyplot.ylabel('Daily Performance', fontsize=20)
pyplot.ylim((-1,1)) 
pyplot.axhline(y=0.0, xmin=0, xmax=time-1, linestyle='dashed')
pyplot.plot(range(0, time), gainList, 'k', label = 'Trend Following')
pyplot.plot(range(0, time), ASADgainList, 'g', label = 'ASAD Trend Following')
pyplot.plot(range(0, time), UCRPgainList, 'r', label = 'Uniform Constant Rebalanced Portfolios')
pyplot.legend(loc='upper left')
pyplot.grid()

pyplot.show()
