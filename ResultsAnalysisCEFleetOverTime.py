#Michael Craig
#Jan 9, 2017

from AuxFuncs import *
from GAMSAuxFuncs import createGenSymbol
from CalculateOpCost import *
from UpdateFuelPriceFuncs import *
import matplotlib.pyplot as plt
import os,csv
import numpy as np
from operator import *

plt.style.use('ggplot')

#Run CE model checks for a single run
#Plot fleet mix over time (stacked bar by year w/ PRM superimposed)
#Plot fleet retirements and additions by plant type over time
#Utilization of existing & added techs
#Plot fleet mix over time (stacked bar)

############## PARAMS AND MASTER FUNCTION ######################################
def setFolders():
    resultFolders = ['ResultsSdeepCdeep']
    return resultFolders

def setParams(resultFolder):
    resultDir = os.path.join('C:\\Users\\mtcraig\\Desktop\\EPP Research\\PythonStorageProject',
                                resultFolder)
    yearList = getYears(resultDir)
    fleet = readCSVto2dList(os.path.join(resultDir,'CE','genFleetAfterCE' + str(yearList[-1]) + '.csv'))
    return resultDir,fleet,yearList

def getYears(resultDir):
    allFiles = os.listdir(os.path.join(resultDir,'CE'))
    baseName = 'genFleetAfterCE' #windGenCE or windGenUC
    years = []
    for fileName in allFiles: 
        if baseName in fileName: years.append(int(fileName.split('.')[0][-4:]))
    return years

def importFuelPrices():
    fuelPriceDir = 'C:\\Users\\mtcraig\\Desktop\\EPP Research\\Databases\\FuelPricesCapacityExpansion'
    fuelFileName = 'FuelPriceTimeSeries2Aug2016.csv'
    return readCSVto2dList(os.path.join(fuelPriceDir,fuelFileName))

def masterFunction():
    resultFolders = setFolders()
    for resultFolder in resultFolders:
        resultDir,fleet,yearList = setParams(resultFolder)
        # plotFleetRetirementsAndAdditions(fleet,yearList)
        # plotFleetMixAsStackedBarsOverTime(fleet,[2015] + yearList) #get initial capacity by adding 2015
        # plotFleetMixVsPRMOverTime(fleet,yearList,resultDir) #get initial capacity by adding 2015
        plotGenUtilizationOverTime(yearList,resultDir)
        plt.show()
################################################################################

############## PLOT RETIREMENTS AND ADDITIONS ##################################
def plotFleetRetirementsAndAdditions(fleet,yearList):
    ptCol = fleet[0].index('PlantType')
    plantTypes = set([row[ptCol] for row in fleet[1:]])
    retsCEByYear = getRetiredOrAddedCapacByYearAndPlantType(fleet,'YearRetiredByCE',yearList,plantTypes)
    retsAgeByYear = getRetiredOrAddedCapacByYearAndPlantType(fleet,'YearRetiredByAge',yearList,plantTypes)
    addsByYear = getRetiredOrAddedCapacByYearAndPlantType(fleet,'YearAddedCE',yearList,plantTypes)
    plotRetsAndAdditions(retsCEByYear,retsAgeByYear,addsByYear,yearList)

#Returns dict that maps each year to dict mapping each plant type to retired
#or added capacity.
def getRetiredOrAddedCapacByYearAndPlantType(fleet,col,yearList,plantTypes):
    resultAllYears = dict()
    for year in yearList: resultAllYears[year] = getRetOrAddsInYearByPlantType(fleet,col,year,plantTypes)
    return resultAllYears

#Goes through fleet for given year, and returns dict mapping each plant type
#to retired to added capacity.z
def getRetOrAddsInYearByPlantType(fleet,col,year,plantTypes):
    result = dict()
    ptCol,capacCol = fleet[0].index('PlantType'),fleet[0].index('Capacity (MW)')
    tgtCol = fleet[0].index(col)
    for pt in plantTypes: result[pt] = 0
    for row in fleet[1:]: 
        if row[tgtCol] != '' and int(row[tgtCol]) == year: 
            result[row[ptCol]] += float(row[capacCol])
    return result

def plotRetsAndAdditions(retsCEByYear,retsAgeByYear,addsByYear,yearList):
    plt.figure(1,figsize = (25,35))
    bw = .1
    for idx in range(len(yearList)):
        ax = plt.subplot(len(yearList),1,idx+1)
        xlocs = list(range(len(retsCEByYear[yearList[idx]])))
        retsCE = ax.bar(xlocs,retsCEByYear[yearList[idx]].values(),
                        color = 'blue',label='CE Retirements',width=bw)
        retsAge = ax.bar([val + bw for val in xlocs],retsAgeByYear[yearList[idx]].values(),
                        color = 'red',label ='Age Retirements',width=bw)
        adds = ax.bar([val + bw*2 for val in xlocs],addsByYear[yearList[idx]].values(),
                        color = 'green',label = 'CE Additions',width=bw)
        plt.xticks([val + bw*1.5 for val in xlocs], addsByYear[yearList[idx]].keys())
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        plt.title(yearList[idx])
        if idx+1 == len(yearList):
            plt.xlabel('Plant Type')
            plt.ylabel('Capacity (MW)')
################################################################################

############## PLOT FLEET MIX OVER TIME ########################################
def plotFleetMixAsStackedBarsOverTime(fleet,yearList):
    plt.figure(2,figsize = (25,35))
    ax = plt.subplot(111)
    bw = .5
    ptCol = fleet[0].index('PlantType')
    plantTypes = set([row[ptCol] for row in fleet[1:]])
    cumCapacByYear = [0]*len(yearList)
    colorCtr,colorInc = .1,(.9-.1)/len(plantTypes)
    xlocs = list(range(len(yearList)))
    for pt in plantTypes:
        capacByYear = getCapacOfFtByYear(fleet,pt,yearList) #list of capacities by year (sorted)
        # ax.bar(xlocs, capacByYear, bottom=cumCapacByYear,label = pt,width = bw,
        #         align='center',color=str(colorCtr)) 
        ax.bar(xlocs, capacByYear, bottom=cumCapacByYear,label = pt,width = bw,
                align='center',color = np.random.rand(3,)) 
        cumCapacByYear = [cumCapacByYear[idx] + capacByYear[idx] for idx in range(len(yearList))]
        colorCtr += colorInc
    handles, labels = ax.get_legend_handles_labels()
    plt.xticks([val for val in xlocs],yearList)
    plt.legend(handles[::-1], labels[::-1])
    plt.ylabel('Capacity (MW)')

def getCapacOfFtByYear(fleet,pt,yearList):
    heads = fleet[0]
    ptCol,capacCol = heads.index('PlantType'),heads.index('Capacity (MW)')
    capacByYear = dict()
    for year in yearList: capacByYear[year] = 0
    for row in fleet[1:]:
        if row[ptCol] == pt:
            onlineYear,offlineYear = getOnlineYearRange(heads,row) 
            for year in yearList:
                if year >= onlineYear and year < offlineYear: capacByYear[year] += float(row[capacCol])
    return [capacByYear[yr] for yr in yearList]

def getOnlineYearRange(heads,row):
    onCol,retCol = heads.index('On Line Year'),heads.index('YearRetiredByCE')
    ageCol = heads.index('YearRetiredByAge')
    ret = int(row[retCol]) if row[retCol] != '' else 2100
    age = int(row[ageCol]) if row[ageCol] != '' else 2100
    offYear = min(ret,age)
    return int(row[onCol]),offYear
################################################################################

############## PLOT FLEET MIX OVER TIME VERSUS PRM #############################
def plotFleetMixVsPRMOverTime(fleet,yearList,resultDir):
    yearToPRM = getPRMEachYear(yearList,resultDir)
    plt.figure(3,figsize = (25,35))
    ax = plt.subplot(111)
    bw = .5
    ptCol = fleet[0].index('PlantType')
    plantTypes = set([row[ptCol] for row in fleet[1:]])
    cumCapacByYear = [0]*len(yearList)
    colorCtr,colorInc = .1,(.9-.1)/len(plantTypes)
    xlocs = list(range(len(yearList)))
    for pt in plantTypes:
        if pt != 'Wind' or pt != 'Solar PV' or pt != 'Hydro':
            capacByYear = getCapacOfFtByYear(fleet,pt,yearList) #list of capacities by year (sorted)
            # ax.bar(xlocs, capacByYear, bottom=cumCapacByYear,label = pt,width = bw,
            #         align='center',color=str(colorCtr)) 
            ax.bar(xlocs, capacByYear, bottom=cumCapacByYear,label = pt,width = bw,
                    align='center',color = np.random.rand(3,)) 
            cumCapacByYear = [cumCapacByYear[idx] + capacByYear[idx] for idx in range(len(yearList))]
            colorCtr += colorInc
    for idx in range(len(yearList)):
        currYear = yearList[idx]
        ax.plot([idx-bw/2,idx+bw/2],[yearToPRM[currYear],yearToPRM[currYear]],'k--',lw=5)
    handles, labels = ax.get_legend_handles_labels()
    plt.xticks([val for val in xlocs],yearList)
    plt.legend(handles[::-1], labels[::-1])
    plt.ylabel('Non-RE Capacity (MW)')
    plt.title('Non-RE Capacity versus Planning Reserve (dashed line)')

def getPRMEachYear(yearList,resultDir):
    yearToPRM = dict()
    for year in yearList:
        yearToPRM[year] = float(readCSVto2dList(os.path.join(resultDir,'planningReserveCE' + str(year) + '.csv'))[0][0])
    return yearToPRM
################################################################################    

############## PLOT GEN UTILIZATION OVER TIME ##################################
def plotGenUtilizationOverTime(yearList,resultDir):
    resultDir = os.path.join(resultDir,'CE')
    plt.figure(4,figsize=(25,35))
    ctr = 1
    for year in yearList:
        fleet = readCSVto2dList(os.path.join(resultDir,'genFleetForCE' + str(year) + '.csv'))
        capacCol = fleet[0].index('Capacity (MW)')
        fleetGenRows = [createGenSymbol(row,fleet[0]) for row in fleet[1:]]
        ax = plt.subplot(3,2,ctr)
        ctr += 1
        #Update fuel prices to current year
        newTechs = readCSVto2dList(os.path.join(resultDir,'newTechsCE' + str(year) + '.csv'))
        fuelPricesTimeSeries = importFuelPrices()
        updateFuelPrices(fleet,newTechs,year,fuelPricesTimeSeries)
        #Get exist gens util & op cost
        fleetOpcosts,hrs = calcOpCosts(fleet,2000,0)
        genGen = readCSVto2dList(os.path.join(resultDir,'genByPlantCE' + str(year) + '.csv'))
        genRegup = readCSVto2dList(os.path.join(resultDir,'regupByPlantCE' + str(year) + '.csv'))
        genFlex = readCSVto2dList(os.path.join(resultDir,'flexByPlantCE' + str(year) + '.csv'))
        genCont = readCSVto2dList(os.path.join(resultDir,'contByPlantCE' + str(year) + '.csv'))
        yearUtils,yearOpcosts = [],[]
        for row in genGen[1:]:
            unit,gen = row[0],sum([float(val) for val in row[1:]])*1000
            regup = sum([float(val) for val in genRegup[[row[0] for row in genRegup].index(unit)][1:]])*1000
            flex = sum([float(val) for val in genFlex[[row[0] for row in genFlex].index(unit)][1:]])*1000
            cont = sum([float(val) for val in genCont[[row[0] for row in genCont].index(unit)][1:]])*1000
            fleetRowIdx = fleetGenRows.index(unit)
            capac = float(fleet[fleetRowIdx+1][capacCol])
            opcost = fleetOpcosts[fleetRowIdx]
            util = (gen+regup+flex+cont)/(capac*len(row[1:]))
            if util>2: print(unit,capac)
            yearUtils.append(util)
            yearOpcosts.append(opcost)
        ax.scatter(yearOpcosts,yearUtils,color='red',label='ExistingGens')
        #Get op cost and utilization for new techs
        addedTechs = readCSVto2dList(os.path.join(resultDir,'genAdditionsCE' + str(year) + '.csv'))
        addedCol = addedTechs[0].index('UnitsAdded' + str(year))
        fpCol,hrCol = newTechs[0].index('FuelCost($/MMBtu)'),newTechs[0].index('HR(Btu/kWh)')
        vomCol,techCapacCol = newTechs[0].index('VOM(2012$/MWh)'),newTechs[0].index('Capacity(MW)')
        techCol = newTechs[0].index('TechnologyType')
        techGen = readCSVto2dList(os.path.join(resultDir,'genByTechCE' + str(year) + '.csv'))
        techRegup = readCSVto2dList(os.path.join(resultDir,'regupByTechCE' + str(year) + '.csv'))
        techFlex = readCSVto2dList(os.path.join(resultDir,'flexByTechCE' + str(year) + '.csv'))
        techCont = readCSVto2dList(os.path.join(resultDir,'contByTechCE' + str(year) + '.csv'))
        techOpcosts,hrs = calcBaseOpCost(fpCol,hrCol,vomCol,newTechs)
        yearUtils,yearOpcosts = [],[]
        for row in techGen[1:]:
            tech,gen = row[0],sum([float(val) for val in row[1:]])*1000
            opcost = techOpcosts[[row[techCol] for row in newTechs].index(tech)-1]
            regup = sum([float(val) for val in techRegup[[row[0] for row in techRegup].index(tech)][1:]])*1000
            flex = sum([float(val) for val in techFlex[[row[0] for row in techFlex].index(tech)][1:]])*1000
            cont = sum([float(val) for val in techCont[[row[0] for row in techCont].index(tech)][1:]])*1000
            techRowIdx = [row[0] for row in newTechs].index(tech)
            capac = float(newTechs[techRowIdx][techCapacCol])
            numAdded = float(addedTechs[[row[0] for row in addedTechs].index(tech)][addedCol])
            if numAdded>0: util = (gen+regup+flex+cont)/(capac*numAdded*len(row[1:]))
            else: util = 0
            yearUtils.append(util)
            yearOpcosts.append(opcost)
        ax.scatter(yearOpcosts,yearUtils,color='blue',label='NewTechs')
        plt.xlim(xmin=-3)
        plt.ylim(ymin=-.02)
        plt.legend()
        plt.title('Util versus Op Cost in ' + str(year))
        plt.xlabel('Op Cost ($/MWh)')
        plt.ylabel('Utilization by Gen & Res Prov')


################################################################################    
masterFunction()