#Michael Craig
#October 4, 2016
#Create fleet for current CE loop by removing retired units from fleet. 
#Determines which units retire due to age, and also accounts for past retirements
#for age and economic reasons.

import os, copy
from AuxFuncs import *
from GAMSAuxFuncs import createGenSymbol

################## CREATE FLEET FOR CURRENT CE LOOP ############################
#Inputs: gen fleet (2d list), current CE year, list of units retired each year (2d list)
#Outputs: gen fleet w/ retired units removed (2d list)
def createFleetForCurrentCELoop(genFleet,currYear,capacExpRetiredUnitsByAge,runLoc,scenario):
    markAndSaveRetiredUnitsFromAge(genFleet,currYear,capacExpRetiredUnitsByAge,runLoc,scenario)
    genFleetForCE = [genFleet[0]] + [row for row in genFleet[1:] if onlineAndNotRetired(row,genFleet[0],currYear)]
    return genFleetForCE
################################################################################

#################### RETIRE UNITS BY AGE #######################################
#Marks units that retire in gen fleet and saves them in list
def markAndSaveRetiredUnitsFromAge(genFleet,currYear,capacExpRetiredUnitsByAge,runLoc,scenario):
    lifetimeByPlantTypeDict = importPlantTypeLifetimes(runLoc,scenario)
    renewablePlantTypes = ['Geothermal','Hydro','Pumped Storage','Wind','Solar PV',
                            'Biomass']
    onlineYearCol = genFleet[0].index('On Line Year')
    plantTypeCol = genFleet[0].index('PlantType')
    retiredByAgeCol = genFleet[0].index('YearRetiredByAge')
    retiredByCECol = genFleet[0].index('YearRetiredByCE')
    retiredUnitsByAge = []
    for row in genFleet[1:]:
        if row[retiredByAgeCol] == '' and row[retiredByCECol] == '': #if not already retired by age or CE
            (onlineYear,plantType) = (row[onlineYearCol],row[plantTypeCol])
            lifetimePlantType = lifetimeByPlantTypeDict[plantType]
            if int(onlineYear) + lifetimePlantType < currYear: 
                if plantType in renewablePlantTypes: readdRenewablePlant(genFleet,row,currYear) #readd to fleet before add retired year!
                row[retiredByAgeCol] = currYear
                retiredUnitsByAge.append(createGenSymbol(row,genFleet[0]))
    capacExpRetiredUnitsByAge.append(['UnitsRetiredByAge' + str(currYear)] + retiredUnitsByAge)

#Import lifetimes for each plant type
def importPlantTypeLifetimes(runLoc,scenario):
    if runLoc == 'pc': lifetimeDir = 'C:\\Users\\mtcraig\\Desktop\\EPP Research\\NewPlantData'
    else: lifetimeDir = 'Data'
    if scenario == 'coalret': lifetimeFilename = 'LifetimeValuesExistingPlants4Aug2016EarlyCoalRet.csv'
    else: lifetimeFilename = 'LifetimeValuesExistingPlants4Aug2016.csv'
    lifetimeData = readCSVto2dList(os.path.join(lifetimeDir,lifetimeFilename))
    lifetimeByPlantTypeDict = convert2dListToDictionaryWithIntVals(lifetimeData,
                                                        'PlantType','Lifetime(yrs)')
    return lifetimeByPlantTypeDict

#Converts Zx2 2d list to dictionary
#Inputs: 2d list (2 cols), header of col w/ keys, header of col w/ vals
#Outputs: dictionary
def convert2dListToDictionaryWithIntVals(list2d,keyHeader,valHeader):
    dictResult = dict()
    (keyCol,valCol) = (list2d[0].index(keyHeader),list2d[0].index(valHeader))
    for row in list2d[1:]: dictResult[row[keyCol]] = int(row[valCol])
    return dictResult
################################################################################

################# READD RENEWABLES THAT RETIRE DUE TO AGE ######################
#If renewable retires due to age, automatically adds new unit to end of fleet
#that is same as old unit except for unit ID & online year.
#Inputs: gen fleet, row of generator fleet of retired RE unit, curr CE year
def readdRenewablePlant(genFleet,row,currYear):
    (unitIdCol,onlineCol) = (genFleet[0].index('Unit ID'),genFleet[0].index('On Line Year'))
    newRow = copy.deepcopy(row)
    newRow[unitIdCol] += 'Replaced'
    newRow[onlineCol] = currYear
    genFleet.append(newRow)
################################################################################

################ REMOVE UNITS RETIRED FROM FLEET ###############################
#Checks if unit has already gone online and is not retired
#Inputs: row of gen fleet (1d list), headers of gen fleet (1d list), current year
#Outputs: True if online & not retired, False otherwise
def onlineAndNotRetired(genRow,headers,currYear):
    (ipmRetiredCol,ceRetiredCol) = (headers.index('Retirement Year'),headers.index('YearRetiredByCE'))
    retiredByAgeCol = headers.index('YearRetiredByAge')
    onlineCol = headers.index('On Line Year')
    if int(genRow[onlineCol]) > currYear: return False #some units don't come online until 2020
    elif int(genRow[ipmRetiredCol]) < currYear: return False #units flagged as retiring by IPM
    elif genRow[retiredByAgeCol] != '' and genRow[retiredByAgeCol] <= currYear: return False #units retired due to age
    elif genRow[ceRetiredCol] != '' and genRow[ceRetiredCol] <= currYear: return False #units retired by CE
    else: return True
################################################################################