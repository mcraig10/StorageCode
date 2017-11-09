#Michael Craig
#October 4, 2016
#Combine all wind and solar units in fleet together (separately for
#each plant type), then remove all but combined unit from fleet. 

from SetupGeneratorFleet import *
from AuxFuncs import *

#Inputs: gen fleet (2d list)
def combineWindAndSolarToSinglePlant(fleetUC,runLoc):
    combineWindOrSolarPlants(fleetUC,'Wind','Wind',runLoc)
    combineWindOrSolarPlants(fleetUC,'Solar','Solar PV',runLoc)

#Adds new combined unit, then removes other units
#Inputs: gen fleet (2d list), fuel type to combine, plant type to combine
def combineWindOrSolarPlants(fleetUC,fuelType,plantType,runLoc):
    plantCol = fleetUC[0].index('PlantType')
    rowIdxs = [idx for idx in range(len(fleetUC)) if fleetUC[idx][plantCol] == plantType]
    newRow = ['']*len(fleetUC[0])
    addParametersToNewWindOrSolarRow(fleetUC,newRow,rowIdxs,fuelType,plantType,runLoc)
    fleetUC.append(newRow)
    for idx in reversed(rowIdxs): fleetUC.pop(idx)

#Adds parameters to new wind or solar row
#Inputs: gen fleet, new gen row (fill values in), row indices of units
#that are being combined into new gen row, fuel & plant type of units being
#combined.
def addParametersToNewWindOrSolarRow(fleetUC,newRow,rowIdxs,fuelType,plantType,runLoc):
    addStateOrisFuelOnlineYearAndPlantType(fleetUC,newRow,fuelType,plantType)
    addRegEligAndCost(fleetUC,newRow,rowIdxs[0])
    (capacCol,hrCol) = (fleetUC[0].index('Capacity (MW)'),fleetUC[0].index('Heat Rate (Btu/kWh)'))
    fuelPriceCol = fleetUC[0].index('FuelPrice($/MMBtu)')
    totalCapac = sum([float(fleetUC[idx][capacCol]) for idx in rowIdxs])
    (newRow[capacCol],newRow[hrCol],newRow[fuelPriceCol]) = (totalCapac,0,0)
    (noxCol,so2Col,co2Col) = (fleetUC[0].index('NOxEmRate(lb/MMBtu)'), 
                          fleetUC[0].index('SO2EmRate(lb/MMBtu)'),
                          fleetUC[0].index('CO2EmRate(lb/MMBtu)'))
    (newRow[noxCol],newRow[so2Col],newRow[co2Col]) = (0,0,0)
    #Fill in rand adder col w/ average of other rows
    randAdderCol = fleetUC[0].index('RandOpCostAdder($/MWh)')
    randAdders = [float(fleetUC[idx][randAdderCol]) for idx in rowIdxs]
    capacs = [float(fleetUC[idx][capacCol]) for idx in rowIdxs]
    capacFracs = [val/sum(capacs) for val in capacs]
    avgRandAdder = sum([randAdders[idx] * capacFracs[idx] for idx in range(len(randAdders))])
    newRow[randAdderCol] = avgRandAdder
    #Add UC, VOM & FOM parameters
    tempFleet = [fleetUC[0],newRow]
    ucHeaders = ['MinDownTime(hrs)','RampRate(MW/hr)','MinLoad(MW)','StartCost($)']
    addUCValues(tempFleet,ucHeaders,importPhorumData(runLoc))
    addVomAndFomValues(tempFleet,importVomAndFomData(runLoc))

#Copy down reg eligibility & cost from first wind and solar row
def addRegEligAndCost(fleetUC,newRow,firstOtherRow):
    regElig,regCost = fleetUC[0].index('RegOfferElig'),fleetUC[0].index('RegOfferCost($/MW)')
    newRow[regElig] = fleetUC[firstOtherRow][regElig]
    newRow[regCost] = fleetUC[firstOtherRow][regCost]