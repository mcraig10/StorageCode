#Michael Craig
#Compare results between fleets w/ and w/out storage

from AuxFuncs import *
from GAMSAuxFuncs import createGenSymbol,createHourSymbol
from SetupGeneratorFleet import isolateFirstFuelType,mapFleetFuelToPhorumFuels
import matplotlib.pyplot as plt
import os, csv

plt.style.use('ggplot')

def masterFunction():
    baseFolder = 'ResultsFullYearNoStorageCoopt'
    stoFolder = 'ResultsFullYearStorageEnergy'
    baseGen = readCSVto2dList(os.path.join(baseFolder,'genByPlantUC2015.csv'))
    stoGen = readCSVto2dList(os.path.join(stoFolder,'genByPlantUC2015.csv'))
    a,b,genToFuelBase,genToCo2Base = getGenDicts(baseFolder)
    a,b,genToFuelSto,genToCo2Sto = getGenDicts(stoFolder)
    compareGenByFuelType(baseGen,stoGen,genToFuelBase,genToFuelSto)
    compareCo2Emissions(baseGen,stoGen,genToCo2Base,genToCo2Sto)
    plt.show()

def getGenDicts(fleetDir):
    lbToTon = 2000
    fleet = readCSVto2dList(os.path.join(fleetDir,'genFleetUC2015.csv'))
    orisCol,genIdCol = fleet[0].index('ORIS Plant Code'), fleet[0].index('Unit ID')
    fuelCol = fleet[0].index('Modeled Fuels')
    capacCol = fleet[0].index('Capacity (MW)')
    plantTypeCol = fleet[0].index('PlantType')
    co2Col = fleet[0].index('CO2EmRate(lb/MMBtu)')
    hrCol = fleet[0].index('Heat Rate (Btu/kWh)')
    genToCapac,genToPlantType,genToFuel = dict(),dict(),dict()
    genToCo2Ems = dict()
    for row in fleet[1:]:
        genToCapac[createGenSymbol(row,fleet[0])] = float(row[capacCol])
        genToPlantType[createGenSymbol(row,fleet[0])] = row[plantTypeCol]
        genToFuel[createGenSymbol(row,fleet[0])] = row[fuelCol]
        genToCo2Ems[createGenSymbol(row,fleet[0])] = float(row[co2Col])/lbToTon * float(row[hrCol]) #ton/GWh
    return (genToCapac,genToPlantType,genToFuel,genToCo2Ems)

def compareGenByFuelType(baseGen,stoGen,genToFuelBase,genToFuelSto):
    baseGenByFuel,baseGenByFuelFrac = calcGenByFuel(baseGen,genToFuelBase)
    stoGenByFuel,stoGenByFuelFrac = calcGenByFuel(stoGen,genToFuelSto)
    diffGenByFuel = dict()
    for fuel in stoGenByFuel:
        if fuel not in baseGenByFuel: baseGenByFuel[fuel] = 0 #add storage fuel type
        diffGenByFuel[fuel] = stoGenByFuel[fuel] - baseGenByFuel[fuel]
    plotGenByFuelType(baseGenByFuel,stoGenByFuel,diffGenByFuel)     

def calcGenByFuel(genData,genToFuel):
    genByFuel,totalGen = dict(),0
    for row in genData[1:]:
        if isolateFirstFuelType(genToFuel[row[0]]) == 'Storage': fuel = 'Storage'
        else: fuel = mapFleetFuelToPhorumFuels(isolateFirstFuelType(genToFuel[row[0]]))
        rowGen = sum([float(val) for val in row[1:]])
        if fuel in genByFuel: genByFuel[fuel] += rowGen
        else: genByFuel[fuel] = rowGen
        totalGen += rowGen
    genByFuelFracTotal = dict()
    for fuel in genByFuel: genByFuelFracTotal[fuel] = genByFuel[fuel]/totalGen
    return genByFuel,genByFuelFracTotal

def plotGenByFuelType(baseGenByFuel,stoGenByFuel,diffGenByFuel):
    fignum = 1
    plt.figure(fignum,figsize=(20,30))
    stogen,basegen,diffgen,fuellabels = list(),list(),list(),list()
    for fuel in stoGenByFuel:
        stogen.append(stoGenByFuel[fuel])
        basegen.append(baseGenByFuel[fuel])
        diffgen.append(diffGenByFuel[fuel])
        fuellabels.append(fuel)
    barWidth = .2
    xLocs = list(range(1,len(fuellabels)+1))
    stogenbars = plt.bar(xLocs,stogen,width = barWidth,color='blue')
    basegenbars = plt.bar([val + barWidth for val in xLocs],basegen,width = barWidth, color='red')
    diffgenbars = plt.bar([val + barWidth*2 for val in xLocs],diffgen,width = barWidth, color='green')
    plt.xticks([val + barWidth*3/2 for val in xLocs], fuellabels)
    plt.xlabel('Fuel Type')
    plt.ylabel('Gen by Fuel Type (GWh)')
    plt.title('Gen by Fuel Type in Storage and Base Runs')
    plt.legend((stogenbars[0],basegenbars[1],diffgenbars[2]),('Storage Run','Base Run','Diff b/wn Runs'))

def compareCo2Emissions(baseGen,stoGen,genToCo2Base,genToCo2Sto):
    baseCo2Ems = calcCo2Ems(baseGen,genToCo2Base) #output in million tons
    stoCo2Ems = calcCo2Ems(stoGen,genToCo2Sto) #output in million tons
    fignum = 2
    plt.figure(fignum,figsize=(20,30))
    vals = [baseCo2Ems,stoCo2Ems]
    plt.bar(range(1,len(vals)+1),vals,width=.5,align='center')
    plt.xticks(range(1,len(vals)+1),['Base Run','Storage Run'])
    plt.xlabel('Run')
    plt.ylabel('Annual CO2 Emissions (million tons)')
    plt.title('Storage - base run CO2 emissions (million tons):' + str(stoCo2Ems - baseCo2Ems))
    print('Base CO2 Ems (tons):',baseCo2Ems,'. Sto CO2 ems:',stoCo2Ems,'. Sto - base CO2 ems:',
            stoCo2Ems - baseCo2Ems)

#Gen in GWh, gentoco2 in ton/GWh
def calcCo2Ems(gen,genToCo2): 
    totalCo2Ems = 0
    for row in gen[1:]:
        genid = row[0]
        rowgen = sum([float(val) for val in row[1:]])
        genCo2Ems = genToCo2[genid]
        totalCo2Ems += rowgen * genCo2Ems / 1E6 
    return totalCo2Ems #million tons

masterFunction()