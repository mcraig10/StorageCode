#Michael Craig
#October 6, 2014
#Import hourly ERCOT demand data from CSVs, return in 1d list w/out header

import os, csv
from AuxFuncs import *

#Extract hourly ERCOT demand from given year, and return it in 1d list w/out headers
def importHourlyERCOTDemand(demandYear,runLoc):
    baseFilename = '_ERCOT_Hourly_Load_Data.csv'
    if runLoc == 'pc': demandDir = 'C:\\Users\\mtcraig\\Desktop\\EPP Research\\Databases\\ERCOTDemand'
    else: demandDir = os.path.join('Data','ERCOTDemand')
    hourlyDemand = importSingleYearDemand(demandYear,demandDir,baseFilename)
    # write2dListToCSV([hourlyDemand],'hourlyERCOTDemand' + str(demandYear) + '.csv')
    return hourlyDemand

#For given year, return hourly demand for ERCOT in 1d list w/out header.
def importSingleYearDemand(year,demandDir,baseFilename):
    filename = str(year)+baseFilename
    rawDemand = readCSVto2dList(os.path.join(demandDir,filename))
    demandCol = rawDemand[0].index('ERCOT')
    hourlyDemand = [float(row[demandCol]) for row in rawDemand[1:]]
    return hourlyDemand


################### DATA EXPLORATION ###########################################
def exploreDemand():
    (demandDir,demandYear,baseFilename) = setKeyParameters()
    demandYears = [2013,2014,2015] #replace demand years w/ multiple years
    (demandAllYears,yearToDemand) = ([],dict())
    for year in demandYears:
        yearDemand = importSingleYearDemand(year,demandDir,baseFilename)
        print('sum of ' + str(year) + ':',sum(yearDemand))
        yearToDemand[year] = yearDemand
        demandAllYears.append(yearDemand)
    write2dListToCSV(demandAllYears,'hourlyDemandAllYears.csv')
    return yearDemand