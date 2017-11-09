#Michael Craig
#October 4, 2016
#Functions that process demand data for CE model - select which days are 
#included in CE, calculate seasonal weights, get peak demand hour, and calculate
#planning reserve margin. 

import copy, os
from AuxFuncs import *

########### SELECT WEEKS FOR EXPANSION #########################################
#Inputs: demand for current CE run (1d list w/out head), net demand for current CE run (1d list w/out head),
#hourly wind and solar gen (1d lists w/out heads), num representative days per season,
#current CE year.
#Outputs: hourly demand, wind and solar values for CE (1d lists w/out headers),
#and hour numbers for whole CE, representative per season, special days, and 
#all other season hours (1d lists, all 1-8760 basis). 
def selectWeeksForExpansion(demandWithGrowth,netDemand,hourlyWindGen,hourlySolarGen,
                            daysPerSeason,currYear,resultsDir):
    specialDayHours = []
    #Get hours for peak demand day
    (peakNetDemandDayHours,netDemandMinusPeak) = getPeakNetDemandDayHours(netDemand) #1-8760 basis
    specialDayHours.extend(peakNetDemandDayHours)
    #Get hours for day w/ max ramp up or down
    (maxRampDayHours,netDemandMinusMaxRamp) = getMaxRampDayHours(netDemand,specialDayHours) #1-8760 basis
    specialDayHours.extend(maxRampDayHours)
    #Get representative hours by NLDC
    (repSeasonalHours,repHrsBySeason,regHrsBySeason) = getRepSeasonalHoursByNLDC(netDemand,
                                                            daysPerSeason,specialDayHours)
    #Combine representative w/ special hours
    hoursForCE = copy.copy(specialDayHours) + copy.copy(repSeasonalHours)
    hrsByBlock = copy.copy(repHrsBySeason)
    hrsByBlock['demand'] = peakNetDemandDayHours
    hrsByBlock['ramp'] = maxRampDayHours
    (demandCE,hourlyWindGenCE,hourlySolarGenCE) = isolateDemandAndREGenForCE(hoursForCE,
                                demandWithGrowth,hourlyWindGen,hourlySolarGen)
    return (demandCE,hourlyWindGenCE,hourlySolarGenCE,hoursForCE,repHrsBySeason,
                peakNetDemandDayHours,maxRampDayHours,regHrsBySeason,hrsByBlock)

##### SELECT CE HOURS FOR DAY WITH PEAK DEMAND
#Input: net demand (1d lits w/out head)
#Output: hours of day w/ peak net demand (1d list, 1-8760 basis),
#net demand without peak demand day (1d list)
def getPeakNetDemandDayHours(netDemand):
    peakDemandDayHour = netDemand.index(max(netDemand))
    peakNetDemandDayHours = getHoursOfDayForGivenHour(peakDemandDayHour) #1-8760 basis
    netDemandMinusPeak = removeHoursFrom1dList(netDemand,peakNetDemandDayHours) 
    return (peakNetDemandDayHours,netDemandMinusPeak) #1-8760 basis

#Get all hours for day for a given hour of year. 
#Inputs: single hour
#Outputs: hours for entire day (Returns value on 1-8760 basis)
def getHoursOfDayForGivenHour(inputHour):
    hoursPerDay = 24
    dayInYear = (inputHour)//hoursPerDay 
    return getHoursOfDayForGivenDay(dayInYear)

#Get all hours for day for a given day
#Input: day in 0-364 basis. Output: hour in 1-8760 basis.
def getHoursOfDayForGivenDay(numDay): 
    hoursPerDay = 24
    (dayStartHour,dayEndHour) = (numDay*hoursPerDay,(numDay+1)*hoursPerDay)
    return [hr+1 for hr in range(dayStartHour,dayEndHour)] 

#Remove given list of hours from a 1d list, where hours are in 1-8760 format
def removeHoursFrom1dList(list1d,hoursToRemove):
    list1dCopy = copy.copy(list1d)
    for hr in reversed(hoursToRemove): list1dCopy.pop(hr-1) 
    return list1dCopy

##### SELECT CE HOURS FOR DAY WITH MAX RAMP
#Take day w/ max ramp up or down, since have same ramp up & down rates for generators
#Inputs: net demand (1d list), set of hours already incluced as special days in CE (1d list, 1-8760 basis).
#Output: hours of day w/ max ramp (1d list, 1-8760 basis), net demand without max ramp day (1d list).
def getMaxRampDayHours(netDemand,peakDemandDayHours):
    netDemandRamp = [0] + [abs(netDemand[hr]-netDemand[hr-1]) for hr in range(1,len(netDemand))] 
    foundMaxRamp = False
    while foundMaxRamp == False:
        maxRampHour = netDemandRamp.index(max(netDemandRamp))
        if maxRampHour+1 not in peakDemandDayHours: foundMaxRamp = True #+1 converts from 0-8759 idx to 1-8760 hour
        else: netDemandRamp[maxRampHour] = 0 #set to zero so don't pick it up again
    maxRampDayHours = getHoursOfDayForGivenHour(maxRampHour) #1-8760 basis
    netDemandMinusMaxRamp = removeHoursFrom1dList(netDemand,maxRampDayHours) 
    return (maxRampDayHours,netDemandMinusMaxRamp) #1-8760 basis

##### SELECT CE HOURS FOR REPRESENTATIVE DAYS PER SEASON
#Inputs: net demand (1d list), num representative days per season to select,
#set of hours already incluced as special days in CE (1d list, 1-8760 basis)
#Outputs: rep hours for each season (1d list no head, 1-8760 basis), dictionaries mapping
#seasons to representative and regular hours 
def getRepSeasonalHoursByNLDC(netDemand,daysPerSeason,specialDayHours):
    seasons = ['winter','spring','summer','fall']
    seasonMonths = {'winter':[1,2,12],'spring':[3,4,5],'summer':[6,7,8],'fall':[9,10,11]}
    (repHrsBySeason,regHrsBySeason,allRepSeasonalHours) = (dict(),dict(),[])
    for season in seasons:
        monthsInSeason = seasonMonths[season]
        (seasonRepHours,otherSeasonHours) = getSeasonRepHoursByNLDC(netDemand,
                                                    daysPerSeason,monthsInSeason,specialDayHours) #1-8760
        allRepSeasonalHours.extend(seasonRepHours)
        repHrsBySeason[season] = seasonRepHours
        regHrsBySeason[season] = otherSeasonHours
    return (allRepSeasonalHours,repHrsBySeason,regHrsBySeason)

#Get representative hours for given season
#Inputs: net demand (1d list), rep days per season to select, months in season (1d list, 1-8760 basis),
#hours already included in CE model as special days (1d list, 1-8760 basis)
#Outputs: rep hours for given season (1d list), all other hours for given season (1d list) 
#(both sets of hours start at 1) 
def getSeasonRepHoursByNLDC(netDemand,daysPerSeason,monthsInSeason,specialDayHours):
    hoursInMonths = getHoursInMonths(monthsInSeason) #starting @ 1
    hoursInMonthsNotSpecial = [hour for hour in hoursInMonths if hour not in specialDayHours] #starting at 1
    netDemandInMonths = [netDemand[hr-1] for hr in hoursInMonthsNotSpecial] #index backwards so hour 1 = idx 0
    print('Months in season:',monthsInSeason)
    seasonRepHours = selectRepresentativeHours(netDemandInMonths,hoursInMonthsNotSpecial,daysPerSeason) #starting at 1
    otherSeasonHours = [hr for hr in hoursInMonthsNotSpecial if hr not in seasonRepHours] #starting at 1
    return (seasonRepHours,otherSeasonHours) #starting at 1

#Get 1d list of hours (starting at 1) in given list of months
#Input: 1d list of months
#Output: hours in given months (1d list, hours start at 1 in year)
def getHoursInMonths(months):
    daysPerMonth = [(1,31),(2,28),(3,31),(4,30),(5,31),(6,30),(7,31),(8,31),(9,30),(10,31),(11,30),(12,31)]
    firstDayInMonthsAsDayInYear = getFirstDayInMonthsAsDayInYear(daysPerMonth)
    daysInMonths = []
    for month in months:
        firstDayInMonth = firstDayInMonthsAsDayInYear[month-1]
        daysInMonth = [day for day in range(firstDayInMonth,firstDayInMonth+daysPerMonth[month-1][1])]
        daysInMonths.extend(daysInMonth)
    hoursInMonths = []
    for day in daysInMonths: hoursInMonths.extend([val+1 for val in range(day*24,(day+1)*24)])
    return hoursInMonths #starts @ 1

#Get 1d list of first day each month as day in year (starting at 0)
#Inputs: num days each month (list of tuples)
#Outputs: first day in each month (1d list) (days start at 0)
def getFirstDayInMonthsAsDayInYear(daysPerMonth):
    firstDayInMonthsAsDayInYear = []
    for idx in range(len(daysPerMonth)):
        if idx == 0: 
            firstDayInMonthsAsDayInYear.append(0)
        else: 
            firstDayInMonthsAsDayInYear.append(firstDayInMonthsAsDayInYear[idx-1]+daysPriorMonth)
        (lastMonth,daysPriorMonth) = (daysPerMonth[idx][0],daysPerMonth[idx][1])
    return firstDayInMonthsAsDayInYear #starts at 0

#Select representiative hours for months in a season
#Inputs: net demand in months (1d list), hours in months not already included
#as special hours (1d list, hours start @ 1), num rep days per season to select
#Outputs: rep hours for season (1d list) (hours start @ 1)
def selectRepresentativeHours(netDemandInMonths,hoursInMonthsNotSpecial,daysPerSeason):
    hoursPerDay = 24
    hoursLowestRmse,lowestRmse = [],sum(netDemandInMonths)**2
    for firstHourInDay in range(0,len(netDemandInMonths)-hoursPerDay*(daysPerSeason-1),hoursPerDay):
        hrInNetDemandSample = [hr for hr in range(firstHourInDay,firstHourInDay + hoursPerDay*daysPerSeason)]
        actualHrsSample = [hoursInMonthsNotSpecial[hr] for hr in hrInNetDemandSample]
        maxDiffHrs = max([actualHrsSample[idx]-actualHrsSample[idx-1] for idx in range(1,len(actualHrsSample))])
        if maxDiffHrs == 1: 
            netDemandInDay = [netDemandInMonths[hr] for hr in hrInNetDemandSample]
            netDemandInDayForAllMonths = netDemandInDay * (len(netDemandInMonths)//len(netDemandInDay))
            truncatedNetDemandInMonths = netDemandInMonths[:len(netDemandInDayForAllMonths)]
            rmse = getRMSE(netDemandInDayForAllMonths,truncatedNetDemandInMonths)
            if rmse < lowestRmse: 
                lowestRmse = rmse
                hoursLowestRmse = copy.copy(actualHrsSample)
    print('Lowest NRMSE:',lowestRmse/(max(netDemandInMonths)-min(netDemandInMonths)))
    return hoursLowestRmse
    
#Calculate RMSE b/wn 2 sets of data
def getRMSE(sampleData,originalData):
    sampleNLDC = sorted(sampleData)
    originalNLDC = sorted(originalData)
    squaredErrors = [(sampleNLDC[idx]-originalNLDC[idx])**2 for idx in range(len(sampleData))]
    rmse = (sum(squaredErrors)/len(squaredErrors))**0.5
    return rmse

##### ISOLATE DEMAND AND RE GENERATION FOR HOURS FOR CE
#Inputs: hours for CE model (1-8760 basis, 1d list), hourly demand, wind and solar
#for whole year for curr CE year (1d lists)
#Outputs: hourly demand, wind & solar for next CE run (1d lists)
def isolateDemandAndREGenForCE(hoursForCE,demandScaled,hourlyWindGen,hourlySolarGen):
    demandCE = [demandScaled[hr-1] for hr in hoursForCE] #-1 b/c hours in year start @ 1, not 0 like Python idx
    hourlyWindGenCE = [hourlyWindGen[hr-1] for hr in hoursForCE] #-1 b/c hours in year start @ 1, not 0 like Python idx
    hourlySolarGenCE = [hourlySolarGen[hr-1] for hr in hoursForCE] #-1 b/c hours in year start @ 1, not 0 like Python idx
    return (demandCE,hourlyWindGenCE,hourlySolarGenCE) 

########### CALCULATE SEASONAL WEIGHTS TO SCALE REP. DEMAND TO SEASON VALUE ####
#Inputs: hourly demand in curr CE year (1d list w/out headers), 1d list of 
#representative hours per season (1-8760 basis), 1d list of regular (i.e. non-rep) 
#hours per season (1-8760 basis)
#Outputs: map of season to weight to scale rep demand to full season demand (scalar)
def calculateSeasonalWeights(demandWithGrowth,repHrsBySeason,regHrsBySeason):
    seasonDemandWeights,weightsList = dict(),[['Season','SeasonWeight']]
    for season in repHrsBySeason:
        (repHrs,regHrs) = (repHrsBySeason[season],regHrsBySeason[season])
        (repHourlyDemand,regHourlyDemand) = ([demandWithGrowth[hr-1] for hr in repHrs],
                                             [demandWithGrowth[hr-1] for hr in regHrs])
        seasonWeight = (sum(regHourlyDemand)+sum(repHourlyDemand))/sum(repHourlyDemand)
        seasonDemandWeights[season] = seasonWeight
        weightsList.append([season,seasonWeight])
    return seasonDemandWeights,weightsList

########### GET PEAK DEMAND HOUR AND PLANNING RESERVE CAPACITY #################
#Inputs: 1d list of demand values for CE model, 1d list of hour vals for CE mdoel
#Outputs: hour that corresponds to peak demand
def getPeakDemandHourCE(demandCE,hoursForCE):
    idx = demandCE.index(max(demandCE))
    return hoursForCE[idx]

#Return planning reserve margin given peak demand
def calculatePlanningReserve(demandCE,planningReserveMargin):
    return max(demandCE)*(1+planningReserveMargin)

########### TEST FUNCTIONS #####################################################
def testGetRMSE():
    print('testing getRMSE')
    assert(almostEqual(getRMSE([1,1,1],[1,1,1]),0))
    assert(almostEqual(getRMSE([1,2,10],[1,2,10]),0))
    assert(almostEqual(getRMSE([1,2,0],[1,2,4]),((1+1+4)/3)**0.5))
    assert(almostEqual(getRMSE([1,1,10],[5,5,5]),((16+16+25)/3)**0.5))

def almostEqual(num1,num2):
    return abs(num2-num1)<0.005