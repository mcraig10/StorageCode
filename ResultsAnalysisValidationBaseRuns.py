#Michael Craig
#Nov 18, 2016
#Validate results 

#Analyses: 1) calculates generation by fuel type, then plots it 
#versus historic gen by fuel type.
#2) calculates gen + res by plant type, then plots it (use to check 
#only eligible gens provide res).
#3) plots price histograms for MCs on meet demand & reserve constraints
#4) plots box plot of elec prices (MC on demand) by hour of day, and compares
#to historic data.
#5) plots histogram of hourly res prices / energy prices
#6) plots histogram of energy prices versus historic data w/ median values superimposed.

from AuxFuncs import *
from GAMSAuxFuncs import createGenSymbol,createHourSymbol
from SetupGeneratorFleet import isolateFirstFuelType,mapFleetFuelToPhorumFuels
import matplotlib.pyplot as plt
import os,csv,statistics,copy
from operator import *

plt.style.use('ggplot')

# RESULTSDIR = 'C:\\Users\\mtcraig\\Desktop\\EPP Research\\PythonStorageProject\\ResultsFullYearNoStorageOrCoopt'
RESULTSDIR = 'C:\\Users\\mtcraig\\Desktop\\EPP Research\\PythonStorageProject\\Results'

def setParameters():
    return None

def masterFunction():
    setParameters()
    genToCapac,genToPlantType,genToFuel = getGenDicts()
    calcGenByFuel(genToFuel)
    calcGenAndResByPlantType(genToPlantType)
    sysData = readCSVto2dList(os.path.join(RESULTSDIR,'systemResultsUC2015.csv'))
    getNse(sysData)
    plotPriceHists(sysData)
    plotPriceRatioHists(sysData)
    #Validate against historic data
    plotEnergyPriceUCvsObs(sysData)
    plotPriceDistByHourOfDay(sysData)
    plt.show()

def getGenDicts():
    fleet = readCSVto2dList(os.path.join(RESULTSDIR,'genFleetUC2015.csv'))
    orisCol,genIdCol = fleet[0].index('ORIS Plant Code'), fleet[0].index('Unit ID')
    fuelCol = fleet[0].index('Modeled Fuels')
    capacCol = fleet[0].index('Capacity (MW)')
    plantTypeCol = fleet[0].index('PlantType')
    genToCapac,genToPlantType,genToFuel = dict(),dict(),dict()
    for row in fleet[1:]:
        genToCapac[createGenSymbol(row,fleet[0])] = float(row[capacCol])
        genToPlantType[createGenSymbol(row,fleet[0])] = row[plantTypeCol]
        genToFuel[createGenSymbol(row,fleet[0])] = row[fuelCol]
    return (genToCapac,genToPlantType,genToFuel)

def calcGenByFuel(genToFuel):
    gen = readCSVto2dList(os.path.join(RESULTSDIR,'genByPlantUC2015.csv'))
    genByFuel,totalGen = dict(),0
    for row in gen[1:]:
        if genToFuel[row[0]] == 'Storage': fuel = 'Storage'
        else: fuel = mapFleetFuelToPhorumFuels(isolateFirstFuelType(genToFuel[row[0]]))
        rowGen = sum([float(val) for val in row[1:]])
        if fuel in genByFuel: genByFuel[fuel] += rowGen
        else: genByFuel[fuel] = rowGen
        totalGen += rowGen
    genByFuelFracTotal = dict()
    for fuel in genByFuel: genByFuelFracTotal[fuel] = genByFuel[fuel]/totalGen
    plt.figure(3,figsize=(20,30))
    plotGenByFuelTypeAll(genByFuelFracTotal)
    plotGenByFuelTypeVersusObs(genByFuelFracTotal)

def getNse(sysData):
    sysDataRowLabels = [row[0] for row in sysData]
    nseRow = sysData[sysDataRowLabels.index('nse')]
    print('Total NSE:',sum([float(val) for val in nseRow[1:]]))

def plotGenByFuelTypeAll(genByFuelFracTotal):
    ax = plt.subplot(211)
    plt.bar(range(len(genByFuelFracTotal)),genByFuelFracTotal.values(),color='blue',align='center')
    plt.xticks(range(len(genByFuelFracTotal)), list(genByFuelFracTotal.keys()))
    plt.xlabel('Fuel Type')
    plt.ylabel('Fraction of Total Gen by Fuel Type')
    plt.title('UC Observed Generation by Fuel Type')

def plotGenByFuelTypeVersusObs(genByFuelFracTotal):
    ax = plt.subplot(212)
    barWidth = .3
    ercotGenByFuelFracTotalObs2015 = {'Coal':.281,'NaturalGas':.483,'Nuclear':.113,
                                    'Wind':.117}
    obsGen,ucGen,genLabels = [],[],[]
    for fuel in ercotGenByFuelFracTotalObs2015:
        obsGen.append(ercotGenByFuelFracTotalObs2015[fuel])
        ucGen.append(genByFuelFracTotal[fuel])
        genLabels.append(fuel)
    xLocs = list(range(len(genLabels)))
    ucBars = plt.bar(xLocs,ucGen,width = barWidth,color='blue')
    obsBars = plt.bar([val + barWidth for val in xLocs],obsGen,width = barWidth, color='red')
    plt.xticks([val + barWidth for val in xLocs], genLabels)
    plt.xlabel('Fuel Type')
    plt.ylabel('Fraction of Total Gen by Fuel Type')
    plt.title('Observed vs UC Generation by Fuel Type')
    plt.legend((ucBars[0],obsBars[1]),('UC','Observed'))

def calcGenAndResByPlantType(genToPlantType):
    gen = readCSVto2dList(os.path.join(RESULTSDIR,'genByPlantUC2015.csv'))
    regup = readCSVto2dList(os.path.join(RESULTSDIR,'regupByPlantUC2015.csv'))
    regdown = readCSVto2dList(os.path.join(RESULTSDIR,'regdownByPlantUC2015.csv'))
    flex = readCSVto2dList(os.path.join(RESULTSDIR,'flexByPlantUC2015.csv'))
    cont = readCSVto2dList(os.path.join(RESULTSDIR,'contByPlantUC2015.csv'))
    plt.figure(5,figsize=(20,30))
    subplotCtr = 1
    labels = ['gen','regup','regdown','flex','cont']
    data = [gen,regup,regdown,flex,cont]
    for idx in range(len(data)):
        currlabel,currdata = labels[idx],data[idx]
        dataFracTotal = calcGenOrResByPlantType(genToPlantType,currdata)
        pltGenOrResByPlantType(dataFracTotal,currlabel,subplotCtr)
        subplotCtr += 1

def calcGenOrResByPlantType(genToPlantType,genOrRes):
    genOrResByType,totalGen = dict(),0
    for row in genOrRes[1:]:
        plantType = genToPlantType[row[0]]
        rowGen = sum([float(val) for val in row[1:]])
        if plantType in genOrResByType: genOrResByType[plantType] += rowGen
        else: genOrResByType[plantType] = rowGen
        totalGen += rowGen
    genOrResByTypeFracTotal = dict()
    for plantType in genOrResByType: genOrResByTypeFracTotal[plantType] = genOrResByType[plantType]/totalGen
    return (genOrResByTypeFracTotal)

def pltGenOrResByPlantType(genOrResByTypeFracTotal,plotLabel,subplotCtr):
    ax = plt.subplot(510 + subplotCtr)
    barWidth = .8
    plt.bar(range(len(genOrResByTypeFracTotal)),genOrResByTypeFracTotal.values(),
                    width=barWidth,color='blue',align='center')
    plt.xticks(range(len(genOrResByTypeFracTotal)), list(genOrResByTypeFracTotal.keys()))
    ax.set_xlim(0-barWidth,len(genOrResByTypeFracTotal))
    if subplotCtr == 4: plt.xlabel('Plant Type')
    plt.ylabel(plotLabel)
    if subplotCtr == 1: plt.title('UC Coopt, No Storage, 2015, Gen or Res as Fraction of Total')

def plotPriceHists(sysData):
    sysDataRowLabels = [row[0] for row in sysData]
    sysPriceLabels = ['mcGen','mcRegup','mcRegdown','mcFlex','mcCont']
    figNum, subplotCtr, subplotBase = 1, 1, 320
    plt.figure(figNum,figsize=(20,30))
    for priceLabel in sysPriceLabels:
        labelRowIdx = sysDataRowLabels.index(priceLabel)
        row = sysData[labelRowIdx]
        prices = [float(val) for val in row[1:]]
        currMedian,currAvg = statistics.median(prices), statistics.mean(prices)
        ax = plt.subplot(subplotBase + subplotCtr)
        subplotCtr += 1
        # n, bins, patches = plt.hist(asMCPDivByEnergyMCP, bins=50, range = (0,1))
        n, bins, patches = plt.hist(prices, bins=50, range=(0,50))
        medianLine = plt.axvline(currMedian,color='black',label='median',linewidth=2)
        avgLine = plt.axvline(currAvg,color='blue',label='mean',linewidth=2)
        plt.xlabel('Marginal Cost ($/MWh)')
        plt.ylabel('Count')
        plt.title(priceLabel)
        plt.legend()

#For multi boxplots in 1 fig, each row = 1 boxplot
def plotPriceDistByHourOfDay(sysData):
    #Plot UC values
    plt.figure(6,figsize=(20,30))
    plt.subplot(121)
    mcGenRow = [row[0] for row in sysData].index('mcGen')
    mcGen = [float(val) for val in sysData[mcGenRow][1:]]
    mcGenHourOfDay = getValsByHourOfDay(mcGen)
    plt.boxplot(mcGenHourOfDay)
    plt.ylabel('Marignal Gen Cost ($/MWh)')
    plt.xlabel('Hour of Day')
    plt.xlim([0,25])
    plt.ylim([0,100])
    plt.xticks(range(1,25), list(range(1,25)))
    plt.title('UC Output')
    #Plot observed values
    plt.subplot(122)
    dataDir = 'C:\\Users\\mtcraig\\Desktop\\EPP Research\\Databases\\ERCOTClearingPrices'
    energyMCPs = readCSVto2dList(os.path.join(dataDir,'energyMCPs.csv'))
    energyMCPCol = energyMCPs[0].index('energyMCP')
    dateCol = energyMCPs[0].index('datetime')
    sysDataRowLabels = [row[0] for row in sysData]
    mcps2015 = [float(row[energyMCPCol]) for row in energyMCPs[1:] if '2015' in row[dateCol]]
    mcps2015HourOfDay = getValsByHourOfDay(mcps2015)
    plt.boxplot(mcps2015HourOfDay)
    plt.ylabel('MCP ($/MWh)')
    plt.xlabel('Hour of Day')
    plt.xlim([0,25])
    plt.ylim([0,100])
    plt.xticks(range(1,25), list(range(1,25)))
    plt.title('Actual 2015 MCPs')

#Returns 2d list, each row = vals for separate hour of day
def getValsByHourOfDay(vals):
    hoursInDay = 24
    valsHourInDay = make2dList(24,0)
    for idx in range(len(vals)):
        valsHourInDay[idx%hoursInDay].append(vals[idx])
    return valsHourInDay

def make2dList(rows, cols):
    a=[]
    for row in range(rows): a += [[0]*cols]
    return a

def plotPriceRatioHists(sysData):
    sysDataRowLabels = [row[0] for row in sysData]
    resPriceLabels = ['mcRegup','mcRegdown','mcFlex','mcCont']
    energyPrices = [float(val) for val in sysData[sysDataRowLabels.index('mcGen')][1:]]
    figNum, subplotCtr, numSubplots, subplotBase = 2, 1, 4, 220
    plt.figure(figNum,figsize=(20,30))
    for priceLabel in resPriceLabels:
        labelRowIdx = sysDataRowLabels.index(priceLabel)
        row = sysData[labelRowIdx]
        resPrices = [float(val) for val in row[1:]]
        resPriceRatio = list(map(truediv,resPrices,energyPrices))
        resPriceRatio = [val for val in resPriceRatio if val != float('inf')]
        currMedian,currAvg = statistics.median(resPriceRatio), statistics.mean(resPriceRatio)
        ax = plt.subplot(subplotBase + subplotCtr)
        subplotCtr += 1
        # n, bins, patches = plt.hist(asMCPDivByEnergyMCP, bins=50, range = (0,1))
        n, bins, patches = plt.hist(resPriceRatio, bins=50, range=(0,1))
        medianLine = plt.axvline(currMedian,color='black',label='median',linewidth=2)
        avgLine = plt.axvline(currAvg,color='blue',label='mean',linewidth=2)
        plt.xlabel('AS Marginal Cost / Energy Marginal Cost')
        plt.ylabel('Count')
        plt.title(priceLabel)
        plt.legend()

def plotEnergyPriceUCvsObs(sysData):
    dataDir = 'C:\\Users\\mtcraig\\Desktop\\EPP Research\\Databases\\ERCOTClearingPrices'
    energyMCPs = readCSVto2dList(os.path.join(dataDir,'energyMCPs.csv'))
    energyMCPCol = energyMCPs[0].index('energyMCP')
    sysDataRowLabels = [row[0] for row in sysData]
    currEnergyMCPs = [float(row[energyMCPCol]) for row in energyMCPs[1:]]
    ucEnergyPrices = [float(val) for val in sysData[sysDataRowLabels.index('mcGen')][1:]]
    plt.figure(4,figsize = (20,30))
    ax = plt.subplot(211)
    plt.hist(ucEnergyPrices, bins=50, range = (0,100),color='blue')
    medianLine = plt.axvline(statistics.median(ucEnergyPrices),color='black',label='median',linewidth=2)
    plt.xlabel('UC Energy MC ($/MWh)')
    plt.ylabel('Count')
    ax = plt.subplot(212)
    plt.hist(currEnergyMCPs, bins=50, range = (0,100),color='red')
    medianLine = plt.axvline(statistics.median(currEnergyMCPs),color='black',label='median',linewidth=2)
    plt.xlabel('Observed Energy MC ($/MWh)')
    plt.ylabel('Count')

masterFunction()

    


# def plotGenByFuel(genByFuel):
#     figNum = 1
#     plt.figure(figNum,figsize=(20,30))
#     ax = plt.subplot(111)
    
#     plt.ylabel('Gen (GWh)')
#     plt.title('Gen By Fuel Type')
#     plt.legend()
    