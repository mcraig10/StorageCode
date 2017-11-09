#Michael Craig
#October 4, 2016
#Project CPP CO2 emissions cap to given year (forward or backward) based on 2022
#& 2030 limits.  

from AuxFuncs import *
import os

#Get CO2 cap for given scenario. Refs: 
#For emissions limits, see: see Databases, CO2EmissionERCOT, UCBaseCase2015Output9April2017 folder,
#baseCaseCo2Emissions9April2017.xlsx.
def getCo2Cap(co2CapScenario):
    if co2CapScenario == 'cpp': capYear,capEms = 2050,87709115 #50% redux
    #35083646 #80% redux  #43854557 #75% redux #52625469 #70% redux
    elif co2CapScenario == 'deep': capYear,capEms = 2050,52625469 #70% redux
    elif co2CapScenario == 'none': capYear,capEms = 2050,175418230*10 #set to arbitrarily large value so effectively no cap
    return capYear,capEms #short tons!

#Inputs: current year and end year and emissions quantity for cap.
#Outputs: project co2 emissions cap (short tons)
#Data soruce for 2015 emissions: UC run w/out co2 price or storage. See xls file above.
#(data from EIA, "Texas electricity profile 2017", Table 7, electric power industry emissions estimates, 1990-2014).s
def interpolateCO2Cap(currYear,endYr,endLimit):
    startYr,startEms = 2015,175418230
    if currYear == startYr: startEms *= 10 #if first year, don't want to enforce co2 cap, so just scale up
    (deltaYear,deltaEms) = (endYr-startYr,startEms-endLimit)
    emsReduxPerYear = deltaEms/deltaYear
    diffCurrYearFromStart = currYear - startYr
    return startEms - diffCurrYearFromStart*emsReduxPerYear     
################################################################################







##################### OLD FUNCTIONS #############################################
#Inputs: year to project cap to, 2022 and 2030 CPP CO2 emissions cap (short tons)
#Outputs: projected CO2 emissions cap (short tons)
def setCppCapBasedOnCurrYear(currYear,co2Cpp2022Limit,co2Cpp2030Limit):
    (deltaYear,deltaEms) = (2030-2022,co2Cpp2022Limit-co2Cpp2030Limit)
    emsReduxPerYear = deltaEms/deltaYear
    diffCurrYearFrom2022 = currYear-2022
    return co2Cpp2022Limit - diffCurrYearFrom2022*emsReduxPerYear

#Import 2022 & 2030 regional CPP mass limit for all states in region
#Output emissions are in short tons/yr, and include new source complement.
def calcRegionCPPLimits(states,runLoc):
    if runLoc=='pc': cppLimitDir = 'C:\\Users\\mtcraig\\Desktop\\EPP Research\\Power Plant Rules\\Clean Power Plan\\FinalRule'
    else: cppLimitDir = 'Data'
    cppLimitName = 'StateCPPCO2EmsCaps5Oct2016.csv'
    stateCppLimits = readCSVto2dList(os.path.join(cppLimitDir,cppLimitName))
    stateCol = stateCppLimits[0].index('State')
    startYr,endYr = 2022,2030
    (limit2022Col,limit2030Col) = (stateCppLimits[0].index(str(startYr)),stateCppLimits[0].index(str(endYr)))
    state2022Limits = [float(row[limit2022Col]) for row in stateCppLimits[1:] if row[stateCol] in states]
    state2030Limits = [float(row[limit2030Col]) for row in stateCppLimits[1:] if row[stateCol] in states]
    return (startYr,endYr,sum(state2022Limits),sum(state2030Limits)) #short tons/yr; includes new source complement

#Output emissions are in short tons/yr.
#Data source: see 'C:\Users\mtcraig\Desktop\EPP Research\Databases\DeepDecarbCO2LimitsTX'
def calcDeepDecarbLimits():
    startYr,endYr = 2014,2050
    startEms,endEms = 280582138, 46980374
    return startYr,endYr,startEms,endEms