#Michael Craig
#October 12, 2016
#Remove hydro (normal + pumped storage) units from fleet and subtract their monthly average generation
#from demand profile.

import copy, operator, os
from AuxFuncs import *

def setKeyParameters(runLoc):
    if runLoc == 'pc': eia923dir = 'C:\\Users\\mtcraig\\Desktop\\EPP Research\\Databases\\EIAForm923\\2011to2015Compiled'
    else: eia923dir = os.path.join('Data','EIAForm923')
    eia923years = list(range(2011,2015))
    return (eia923years,eia923dir)

########### MASTER FUNCTION ####################################################
#Inputs: gen fleet, demand profile (1d list of hourly demand values)
#Outputs: gen fleet w/out hydro units, demand profile w/ average monthly 
#hydro generation subtracted (1d list of hourly values)
def removeHydroFromFleetAndDemand(genFleet,demandProfile,runLoc):
    (eia923years,eia923dir) = setKeyParameters(runLoc)
    (hydroFleetRows,genFleetNoHydro) = getHydroRows(genFleet) #hydroFleetRows has fleet header & full fleet rows w/ hydro plants
    demandMinusHydroGen = removeHydroGenFromDemand(hydroFleetRows,demandProfile,eia923years,eia923dir)
    return (genFleetNoHydro,demandMinusHydroGen)
################################################################################

########### GET HYDRO ROWS #####################################################
#Returns hydro units in separate fleet, and fleet without hydro units
def getHydroRows(fleet):
    genFleetNoHydro = copy.deepcopy(fleet)
    heads = copy.copy(genFleetNoHydro[0])
    fuelTypeCol = heads.index('Modeled Fuels')
    hydroFleetRows = [heads]
    idxs = []
    for idx in range(len(genFleetNoHydro)-1,0,-1):
        if genFleetNoHydro[idx][fuelTypeCol] == 'Hydro': 
            hydroRow = genFleetNoHydro.pop(idx)
            hydroFleetRows.append(hydroRow)
    return (hydroFleetRows,genFleetNoHydro)
################################################################################

########### REMOVE HYDRO GENERATION FROM DEMAND ################################
#Returns 1d list of demand minus average monthly hydro generation
def removeHydroGenFromDemand(hydroFleetRows,demandProfile,eia923years,eia923dir):
    orisIDtoCapac = getHydroOrisIdsAndCapacs(hydroFleetRows)
    hydroAvgMonthlyGen = getTotalHydroAvgMonthlyGen(orisIDtoCapac,eia923years,eia923dir)
    hourlyHydroGen = expandMonthlyGenToHourly(hydroAvgMonthlyGen)
    return list(map(operator.sub,demandProfile,hourlyHydroGen))

#Return dictionary mapping ORIS ID to capacity
def getHydroOrisIdsAndCapacs(hydroFleetRows):
    (orisCol,capacCol) = (hydroFleetRows[0].index('ORIS Plant Code'),hydroFleetRows[0].index('Capacity (MW)'))
    orisIDtoCapac = dict()
    for row in hydroFleetRows[1:]:
        if row[orisCol] in orisIDtoCapac: orisIDtoCapac[row[orisCol]] += float(row[capacCol])
        else: orisIDtoCapac[row[orisCol]] = float(row[capacCol])
    return orisIDtoCapac

#Get total average monthly hydro generation by getting monthly generation per year
#for each unit, then adding average values.
#Inputs: dict mapping ORIS id to capac of all hydro units, years of EIA 923
#data to use, & dir of that data.
#Outputs: 1d list (len=12) of average total hydro generation per month
def getTotalHydroAvgMonthlyGen(orisIDtoCapac,eia923years,eia923dir):
    (orisIDtoMonthlyGen,orisIDtoMonthlyGenCount) = (dict(),dict())
    for orisId in orisIDtoCapac: 
        orisIDtoMonthlyGen[orisId] = []
        orisIDtoMonthlyGenCount[orisId] = []
    for year in eia923years:
        (orisIDtoMonthlyGen,orisIDtoMonthlyGenCount) = getMonthlyGenInYear(orisIDtoMonthlyGen,
                                                        orisIDtoMonthlyGenCount,year,eia923dir)
    return getCombinedAverageMonthlyGen(orisIDtoMonthlyGen,orisIDtoMonthlyGenCount)
     
#For each hydro unit in fleet, get monthly generation in a given year.
#Inputs: dict mapping oris ID to list of monthly gen, dict mapping ORIS ID to 
#list of count of gen values per month, year of analysis, dir w/ EIA 923 data
#Outputs: dict mapping oris ID to list of monthly gen, dict mapping ORIS ID to 
#list of count of gen values per month
def getMonthlyGenInYear(orisIDtoMonthlyGen,orisIDtoMonthlyGenCount,year,eia923dir):
    numMonths = 12
    (idCol,idLabel) = (0,'Plant Id')
    genFile = 'gen' + str(year) + '.csv'
    genData = readCSVto2dList(os.path.join(eia923dir,genFile))
    firstColVals = [row[idCol] for row in genData]
    headsRow = firstColVals.index(idLabel) #this has detailed header rows; 1 row up are overarching headers, hence -1 in next line
    netGenFirstCol = genData[headsRow-1].index('Electricity Net Generation (MWh)')
    if 'Reported Fuel Type Code' in genData[headsRow]: fuelCol = genData[headsRow].index('Reported Fuel Type Code') 
    else: fuelCol = genData[headsRow].index('Reported\nFuel Type Code') 
    for row in genData[headsRow+1:]:
        (orisId,fuel) = (row[idCol],row[fuelCol])
        if orisId in orisIDtoMonthlyGen and fuel == 'WAT':
                monthlyGen = [toNum(row[idx]) for idx in range(netGenFirstCol,netGenFirstCol+numMonths)]
                if orisIDtoMonthlyGen[orisId]==[]:
                    orisIDtoMonthlyGen[orisId] = monthlyGen
                    orisIDtoMonthlyGenCount[orisId] = [1]*len(monthlyGen)
                else:
                    orisIDtoMonthlyGen[orisId] = list(map(operator.add,orisIDtoMonthlyGen[orisId],monthlyGen))
                    orisIDtoMonthlyGenCount[orisId] = list(map(operator.add,orisIDtoMonthlyGenCount[orisId],[1]*len(monthlyGen)))
    return (orisIDtoMonthlyGen,orisIDtoMonthlyGenCount)

#For each unit, calculate average monthly gen, then add value to 
#running total of hydro gen for all units. 
#Inputs: dict mapping oris ID to list of monthly gen, dict mapping ORIS ID to 
#list of count of gen values per month
#Outputs: 1d list of total hydro average monthly gen (len=12)
def getCombinedAverageMonthlyGen(orisIDtoMonthlyGen,orisIDtoMonthlyGenCount):
    combinedAverageGen = []
    for orisId in orisIDtoMonthlyGen:
        (monthlyGen,count) = (orisIDtoMonthlyGen[orisId],orisIDtoMonthlyGenCount[orisId])
        averageMonthlyGen = [monthlyGen[idx]/count[idx] for idx in range(len(monthlyGen))]
        if monthlyGen != []:
            if combinedAverageGen==[]: combinedAverageGen = copy.copy(averageMonthlyGen)
            else: combinedAverageGen = list(map(operator.add,combinedAverageGen,averageMonthlyGen))
    return combinedAverageGen

#Expand average monthly generation from 1d list of len=12 to 1d list of n=8760.
#Also spreads out average monthly generation to hourly generation values,
#assuming equal generation per hour. 
def expandMonthlyGenToHourly(hydroAvgMonthlyGen):
    hoursPerDay = 24
    daysPerMonth = [31,28,31,30,31,30,31,31,30,31,30,31]
    hydroAvgMonthlyGenHourly = []
    for idx in range(len(hydroAvgMonthlyGen)):
        (days,avgMonthlyGen) = (daysPerMonth[idx],hydroAvgMonthlyGen[idx])
        hourlyGen = avgMonthlyGen/(hoursPerDay*days)
        hydroAvgMonthlyGenHourly += [hourlyGen]*(hoursPerDay*days)
    return hydroAvgMonthlyGenHourly
################################################################################

########### HELPER FUNCTION ####################################################
#Converts a string w/ commas in it to a float
def toNum(s):
    numSegments = s.split(',')
    result = ""
    for segment in numSegments:
        result += segment
    return float(result)
################################################################################