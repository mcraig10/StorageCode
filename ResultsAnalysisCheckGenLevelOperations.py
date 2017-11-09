#Michael Craig
#November 16, 2016
#Script plots generation + reserves of each unit

#Analyses: 1) compares generation + up reserves to capacity
#2) Compares generation - reg down to min load
#3) Compares generation + up reserve and generation - reg down to ramp capability
#and to reserve timeframe. 
#4) Checks storage ops: gen + res < SOC, res provision < ramp capability in 
#res timeframe, and plots storage ops by time of day and chronologically for period.
#5) Checks MDT for existing and, if CE run, new gens

from AuxFuncs import *
from GAMSAuxFuncs import createGenSymbol,createHourSymbol
import os, copy, operator
import matplotlib.pyplot as plt

plt.style.use('ggplot')

################################################################################
################################################################################
def setFolders():
    resultsFolder = ['ResultsScppCcpp']
    return resultsFolder

def loadData(resultsFolder,year,model):
    incSto = False if 'NoSto' in resultsFolder else True
    resultsDir = os.path.join('C:\\Users\\mtcraig\\Desktop\\EPP Research\\PythonStorageProject',resultsFolder)
    gen = readCSVto2dList(os.path.join(resultsDir,'genByPlant' + model + year + '.csv'))
    regup = readCSVto2dList(os.path.join(resultsDir,'regupByPlant' + model + year + '.csv'))
    regdown = readCSVto2dList(os.path.join(resultsDir,'regdownByPlant' + model + year + '.csv'))
    flex = readCSVto2dList(os.path.join(resultsDir,'flexByPlant' + model + year + '.csv'))
    cont = readCSVto2dList(os.path.join(resultsDir,'contByPlant' + model + year + '.csv'))
    turnon = readCSVto2dList(os.path.join(resultsDir,'turnonByPlant' + model + year + '.csv'))
    turnoff = readCSVto2dList(os.path.join(resultsDir,'turnoffByPlant' + model + year + '.csv'))
    onoff = readCSVto2dList(os.path.join(resultsDir,'onOffByPlant' + model + year + '.csv'))
    if model=='UC': fleet = readCSVto2dList(os.path.join(resultsDir,'genFleet' + model + year + '.csv'))
    else: fleet = readCSVto2dList(os.path.join(resultsDir,'genFleetFor' + model + year + '.csv'))
    if model=='UC' and incSto == True:
        charge = readCSVto2dList(os.path.join(resultsDir,'chargeBySto' + model + year + '.csv'))
        soc = readCSVto2dList(os.path.join(resultsDir,'socBySto' + model + year + '.csv'))
    else: charge,soc = None,None
    return (gen,regup,regdown,flex,cont,fleet,charge,soc,turnon,turnoff,resultsDir,onoff)

def masterFunction():
    resultsFolders = setFolders()
    for resultsFolder in resultsFolders:
        # for model in ['CE','UC']:
        for model in ['UC','CE']:
            if model == 'UC':
                for stoModel in ['NoSto','StoEnergy','StoEnergyAndRes','StoRes']:
                # for stoModel in ['NoSto']:
                    print('***RUNNING CHECKS FOR:',resultsFolder,model,stoModel)
                    runChecks(os.path.join(resultsFolder,model,stoModel),model)
            else:
                print('***RUNNING CHECKS FOR:',resultsFolder,model)
                runChecks(os.path.join(resultsFolder,model),model)
################################################################################
################################################################################

################################################################################
################################################################################
def runChecks(resultsFolder,model):
    for year in getYears(resultsFolder,model):
        print('**CHECKING YEAR ' + str(year))
        (gen,regup,regdown,flex,cont,fleet,charge,soc,turnon,turnoff,
            resultsDir,onoff) = loadData(resultsFolder,year,model)
        (genToCapac,genToMinload,genToPlantType,genToRamp,genToMDT) = getGenDicts(fleet)
        checkGenAndUpRes(gen,regup,flex,cont,genToCapac,resultsDir)
        # checkGenAndDownRes(gen,regdown,genToMinload,resultsDir)
        checkGenAndResVersusRamp(gen,regup,regdown,flex,cont,genToRamp,turnon,turnoff,
                                resultsDir,model)
        checkMDT(onoff,turnon,turnoff,genToMDT,resultsFolder,year,model)
        if 'Storage' in [row[fleet[0].index('PlantType')] for row in fleet]:
            checkStorageOps(gen,regup,regdown,flex,cont,charge,soc,genToCapac,
                            genToPlantType,genToRamp,year,resultsDir)
    
def getYears(resultFolder,model):
    allFiles = os.listdir(os.path.join('C:\\Users\\mtcraig\\Desktop\\EPP Research\\PythonStorageProject',resultFolder))
    baseName = 'windGen' + model #windGenCE or windGenUC
    years = []
    for fileName in allFiles: 
        if baseName in fileName:
            years.append(fileName.split('.')[0][-4:])
    return years

def getGenDicts(fleet):
    orisCol,genIdCol = fleet[0].index('ORIS Plant Code'), fleet[0].index('Unit ID')
    capacCol,minloadCol = fleet[0].index('Capacity (MW)'), fleet[0].index('MinLoad(MW)')
    plantTypeCol,rampCol = fleet[0].index('PlantType'),fleet[0].index('RampRate(MW/hr)')
    mdtCol = fleet[0].index('MinDownTime(hrs)')
    genToCapac,genToMinload,genToPlantType,genToRamp,genToMDT = dict(),dict(),dict(),dict(),dict()
    for row in fleet[1:]:
        genToCapac[createGenSymbol(row,fleet[0])] = float(row[capacCol])
        genToMinload[createGenSymbol(row,fleet[0])] = float(row[minloadCol])
        genToPlantType[createGenSymbol(row,fleet[0])] = row[plantTypeCol]
        genToRamp[createGenSymbol(row,fleet[0])] = float(row[rampCol])
        genToMDT[createGenSymbol(row,fleet[0])] = int(float(row[mdtCol]))
    return (genToCapac,genToMinload,genToPlantType,genToRamp,genToMDT)
################################################################################
################################################################################

################################################################################
################################################################################
def checkGenAndUpRes(gen,regup,flex,cont,genToCapac,resultsDir):
    genPlusUpRes = copy.deepcopy(gen) #initial structure
    for rowIdx in range(1,len(genPlusUpRes)):
        for colIdx in range(1,len(genPlusUpRes[rowIdx])):
            genPlusUpRes[rowIdx][colIdx] = (float(gen[rowIdx][colIdx]) + 
                    float(regup[rowIdx][colIdx]) + float(flex[rowIdx][colIdx]) + float(cont[rowIdx][colIdx]))
            if genPlusUpRes[rowIdx][colIdx] > (genToCapac[genPlusUpRes[rowIdx][0]]/1000+1E-6): #1E-3 adds 1 kW to value
                print('Gen + up res exceed capac:',genPlusUpRes[rowIdx][0],' at hour:',genPlusUpRes[0][colIdx])
        genPlusUpRes[rowIdx].append(genToCapac[genPlusUpRes[rowIdx][0]]/1000)
    write2dListToCSV(genPlusUpRes,os.path.join(resultsDir,'genPlusUpResCheck.csv'))
################################################################################
################################################################################

################################################################################
################################################################################
def checkGenAndDownRes(gen,regdown,genToMinload,resultsDir):
    genMinusRegdown = copy.deepcopy(gen)
    for rowIdx in range(1,len(genMinusRegdown)):
        for colIdx in range(1,len(genMinusRegdown[rowIdx])):
            genMinusRegdown[rowIdx][colIdx] = (float(gen[rowIdx][colIdx]) - float(regdown[rowIdx][colIdx]))
            if (genMinusRegdown[rowIdx][colIdx] > 1E-6 and
                 genMinusRegdown[rowIdx][colIdx] < (genToMinload[genMinusRegdown[rowIdx][0]]/1000-1E-6)): #1E-3 adds 1 kW to value
                print('Gen + up res exceed capac:',genMinusRegdown[rowIdx][0],' at hour:',genMinusRegdown[0][colIdx])
        genMinusRegdown[rowIdx].append(genToMinload[genMinusRegdown[rowIdx][0]]/1000)
    write2dListToCSV(genMinusRegdown,os.path.join(resultsDir,'genMinusRegdown.csv'))
################################################################################
################################################################################

################################################################################
################################################################################
def checkGenAndResVersusRamp(gen,regup,regdown,flex,cont,genToRamp,turnon,turnoff,resultsDir,model):
    changeGen = [copy.copy(gen[0])]
    for row in gen[1:]:
        changeGen.extend([[row[0]] + [0] + [float(row[idx]) - float(row[idx-1]) for idx in range(2,len(row))]])
    changeGenPlusRes = copy.deepcopy(changeGen)
    changeGenMinusRegDown = copy.deepcopy(changeGen)
    for ridx in range(1,len(changeGen)):
        genRamp = genToRamp[changeGen[ridx][0]]
        for cidx in range(1,len(changeGen[ridx])):
            changeGenPlusRes[ridx][cidx] = (changeGen[ridx][cidx] + float(regup[ridx][cidx]) 
                                                + float(flex[ridx][cidx]) + float(cont[ridx][cidx]))
            if model == 'CE': #screen out first hours of seasons
                if cidx > 1 and int(turnon[0][cidx][1:]) - int(turnon[0][cidx-1][1:]) == 1: 
                    if changeGenPlusRes[ridx][cidx] > genRamp/1000 + 1E-6 and float(turnon[ridx][cidx]) != 1:
                        print('Gen change plus up res exceed ramp at unit',changeGen[ridx][0],' at idx:',cidx)
            else:
                if changeGenPlusRes[ridx][cidx] > genRamp/1000 + 1E-6 and float(turnon[ridx][cidx]) != 1:
                    print('Gen change plus up res exceed ramp at unit',changeGen[ridx][0],' at idx:',cidx)
            # changeGenMinusRegDown[ridx][cidx] = changeGen[ridx][cidx] - float(regdown[ridx][cidx]) 
            # if changeGen[ridx][cidx] < 0 and round(float(turnoff[ridx][cidx])) != 1: #round b/c get some vals very close to 1
            #     if changeGenMinusRegDown[ridx][cidx] < -genRamp/1000 - 1E-5:
            #         print('Gen change minus reg down exceed ramp at unit',changeGen[ridx][0],' at idx:',cidx)
    write2dListToCSV(changeGenPlusRes,os.path.join(resultsDir,'changeGenPlusRes.csv'))
    # write2dListToCSV(changeGenMinusRegDown,os.path.join(resultsDir,'changeGenMinusRegdown.csv'))
################################################################################
################################################################################

################################################################################
################################################################################
def checkMDT(onoff,turnon,turnoff,genToMDT,resultsFolder,year,model):
    if model=='CE':
        print('checking tech mdt')
        checkTechMDT(resultsFolder,year,model)
    print('checking gen mdt')
    checkGenMDT(onoff,turnon,turnoff,genToMDT)

def checkGenMDT(onoff,turnon,turnoff,genToMDT):
    onoffRowLabels = [row[0] for row in onoff]
    hourSets,hourSetIdxs = getHourSets(onoff)
    for gen in genToMDT:
        if genToMDT[gen]>0:
            onoffVals = [int(float(val)) for val in onoff[onoffRowLabels.index(gen)][1:]]
            for [startIdx,endIdx] in hourSetIdxs:
                onoffValsInHourSet = onoffVals[startIdx:endIdx]
                minDownObserved = calcMinDown(onoffValsInHourSet)
                if minDownObserved < genToMDT[gen]: 
                    print('**Gen violates MDT! Gen:',gen,' w/ MDT & obs MDT of ',genToMDT[gen],' and ',minDownObserved)
           
#Input: 1d list of 1/0 ints 
def calcMinDown(onoffVals):
    lastIdxWasZero,minDown = True,9999 #True at first so that in first hour, if off, not counting MDT in effect
    for idx in range(len(onoffVals)):
        if onoffVals[idx] == 0 and lastIdxWasZero == False:
            if 1 in onoffVals[idx:]: 
                distToOne = onoffVals[idx:].index(1) 
                if distToOne<minDown: minDown = distToOne 
                lastIdxWasZero = True
        elif onoffVals[idx] == 1:
            lastIdxWasZero = False
    return minDown

def checkTechMDT(resultsFolder,year,model):
    turnonTech,turnoffTech,onoffTech,techs,built = loadTechData(resultsFolder,year,model)
    techToMDT = getTechToMDT(techs)
    hourSets,hourSetIdxs = getHourSets(onoffTech)
    onoffLabels = [row[0] for row in onoffTech]
    for tech in techToMDT:
        if techToMDT[tech]>0:
            techBuilt = getNumAdded(tech,built,year)
            onoffVals = [int(float(val)) for val in onoffTech[onoffLabels.index(tech)][1:]]
            for [startIdx,endIdx] in hourSetIdxs:
                onoffValsInHourSet = onoffVals[startIdx:endIdx]
                onoffValsDisagg = disaggregateOnOffVals(onoffValsInHourSet,techBuilt)
                for onoffVals1Gen in onoffValsDisagg:
                    minDownObserved = calcMinDown(onoffVals1Gen)
                    if minDownObserved < techToMDT[tech]:
                        print('**Tech violates MDT! Tech:',tech,' w/ MDT and obs MDT of ',
                                    techToMDT[tech],' and ',minDownObserved)

def getHourSets(onoffTech):
    hours = [int(float(val[1:])) for val in onoffTech[0][1:]]
    hourSets,setIdxs = [],[]
    lastIdxSet = 0
    for idx in range(1,len(hours)):
        if hours[idx] != hours[idx-1]+1:
            hourSets.append(hours[lastIdxSet:idx])
            setIdxs.append([lastIdxSet,idx])
            lastIdxSet = idx
        elif idx == len(hours)-1:
            hourSets.append(hours[lastIdxSet:idx+1])
            setIdxs.append([lastIdxSet,idx+1])
    return hourSets,setIdxs

def getTechToMDT(techs):
    techToMDT = dict()
    mdtCol = techs[0].index('MinDownTime(hrs)')
    techCol = techs[0].index('TechnologyType')
    for row in techs[1:]:
        techToMDT[row[techCol]] = int(float(row[mdtCol]))
    return techToMDT

def getNumAdded(tech,built,year):
    yearCol = built[0].index('UnitsAdded' + str(year))
    techRow = [row[0] for row in built].index(tech)
    return int(float(built[techRow][yearCol]))

def disaggregateOnOffVals(onoffVals,techBuilt):
    onoffValsDisagg = list()
    for idx in range(techBuilt): onoffValsDisagg.append([0 for val in range(len(onoffVals))])
    for idx in range(len(onoffVals)):
        numOn = onoffVals[idx]
        for rowIdx in range(numOn): onoffValsDisagg[rowIdx][idx] = 1
    return onoffValsDisagg

def loadTechData(resultsFolder,year,model):
    resultsDir = os.path.join('C:\\Users\\mtcraig\\Desktop\\EPP Research\\PythonStorageProject',resultsFolder)
    turnonTech = readCSVto2dList(os.path.join(resultsDir,'turnonByTech' + model + year + '.csv'))
    turnoffTech = readCSVto2dList(os.path.join(resultsDir,'turnoffByTech' + model + year + '.csv'))
    onoffTech = readCSVto2dList(os.path.join(resultsDir,'onOffByTech' + model + year + '.csv'))
    techs = readCSVto2dList(os.path.join(resultsDir,'newTechs' + model + year + '.csv'))
    built = readCSVto2dList(os.path.join(resultsDir,'genAdditions' + model + year + '.csv'))
    return turnonTech,turnoffTech,onoffTech,techs,built
################################################################################
################################################################################

################################################################################
################################################################################
def checkStorageOps(gen,regup,regdown,flex,cont,charge,soc,genToCapac,genToPlantType,genToRamp,year,resultsDir):
    (stogen,storegup,storegdown,stoflex,stocont,stocharge,stosoc,stoGenId) = getStoOps(gen,regup,
                                    regdown,flex,cont,charge,soc,genToPlantType,resultsDir)
    plotHourlyStoOpsOverTime(stogen,storegup,storegdown,stoflex,stocont,stocharge,stosoc,year,resultsDir)
    checkGenPlusUpRes(stogen,storegup,storegdown,stoflex,stocont,stocharge,stosoc)
    checkResVersusRamp(storegup,storegdown,stoflex,stocont,genToRamp[stoGenId])
    plotStoOpsByHourOfDay(stogen,storegup,storegdown,stoflex,stocont,stocharge,year,resultsDir)
    print('max gen:',max(stogen))
    print('max regup:',max(storegup))
    # print('max regdown:',max(storegdown))
    print('max flex:',max(stoflex))
    print('max cont:',max(stocont))
    print('max charge:',max(stocharge))
    # plt.show()

def getStoOps(gen,regup,regdown,flex,cont,charge,soc,genToPlantType,resultsDir):
    stoIdx = [idx for idx in range(1,len(gen)) if genToPlantType[gen[idx][0]] == 'Storage'][0]
    stoGenId = gen[stoIdx][0]
    stogen = [float(val)*1000 for val in gen[stoIdx][1:]]
    storegup = [float(val)*1000 for val in regup[stoIdx][1:]]
    print('***NOT HANDLING STO REG DOWN')
    storegdown = None
    # storegdown = [float(val)*1000 for val in regdown[stoIdx][1:]]
    stoflex = [float(val)*1000 for val in flex[stoIdx][1:]]
    stocont = [float(val)*1000 for val in cont[stoIdx][1:]]
    stoIdx = [idx for idx in range(1,len(charge)) if genToPlantType[charge[idx][0]] == 'Storage'][0]
    stocharge = [float(val)*1000 for val in charge[stoIdx][1:]]
    stosoc = [float(val)*1000 for val in soc[stoIdx][1:]]
    stoOps = [['gen'] + stogen,['regup'] + storegup,#['regdown'] + storegdown,
                ['flex'] + stoflex,['cont'] + stocont,['charge'] + stocharge,['soc']+stosoc]
    stoOpsVert = []
    for colIdx in range(len(stoOps[0])):
        stoOpsVert.append([row[colIdx] for row in stoOps])
    write2dListToCSV(stoOpsVert,os.path.join(resultsDir,'storageOperations.csv'))
    return stogen,storegup,storegdown,stoflex,stocont,stocharge,stosoc,stoGenId

def plotHourlyStoOpsOverTime(stogen,storegup,storegdown,stoflex,stocont,stocharge,
                            stosoc,year,resultsDir):
    (figNum,subplotCtr) = (1,1)
    fig = plt.figure(figNum,figsize=(20,30))
    ax = plt.subplot(111)
    startHour,endHour = 0,len(stogen)
    genLine = ax.plot(stogen[startHour:endHour],label='Gen')
    regupLine = ax.plot(storegup[startHour:endHour],label='Regup')
    # regdownLine = ax.plot(storegdown[startHour:endHour],label='Regdown')
    flexLine = ax.plot(stoflex[startHour:endHour],label='Flex')
    contLine = ax.plot(stocont[startHour:endHour],label='Cont')
    chargeLine = ax.plot(stocharge[startHour:endHour],label='Charge')
    socLine = ax.plot(stosoc[startHour:endHour],label='SOC')
    plt.legend()
    plt.ylabel('MWh')
    plt.xlabel('Hour')
    figDir = os.path.join(resultsDir,'Figs')
    if not os.path.exists(figDir): os.makedirs(figDir)
    fig.set_size_inches(7,8)
    fig.savefig(os.path.join(figDir,'stoOpsOverTime' + year + '.png'),dpi=300,
        transparent=True, bbox_inches='tight', pad_inches=0.1)
    fig.clf()

def plotStoOpsByHourOfDay(stogen,storegup,storegdown,stoflex,stocont,stocharge,year,resultsDir):
    allStoOps = {'stogen':stogen,'storegup':storegup,#'storegdown':storegdown,
                    'stoflex':stoflex,'stocont':stocont,'stocharge':stocharge}
    figNum,subplotCtr = 2,1
    fig = plt.figure(figNum,figsize=(20,30))
    for stoOp in allStoOps:
        stoOpsByHourOfDay = calcStoOpsByHourOfDay(allStoOps[stoOp])
        ax = plt.subplot(230 + subplotCtr)
        subplotCtr += 1
        currBar = ax.bar(range(1,len(stoOpsByHourOfDay)+1),stoOpsByHourOfDay,align='center')
        plt.title(stoOp)
        plt.xlabel('Hour of Day')
        plt.ylabel('MWh') 
        plt.xlim([0,25])
        plt.xticks(range(1,len(stoOpsByHourOfDay)+1), list(range(1,len(stoOpsByHourOfDay)+1)))
    figDir = os.path.join(resultsDir,'Figs')
    if not os.path.exists(figDir): os.makedirs(figDir)
    fig.set_size_inches(15,20)
    fig.savefig(os.path.join(figDir,'stoOpsHourOfDay' + year + '.png'),dpi=300,
                transparent=True, bbox_inches='tight', pad_inches=0.1)
    fig.clf()
    
def calcStoOpsByHourOfDay(vals):
    hoursInDay = 24
    valsHoursInDay = [0]*hoursInDay
    for idx in range(len(vals)):
        valsHoursInDay[idx%hoursInDay] += vals[idx]
    return valsHoursInDay

def checkGenPlusUpRes(stogen,storegup,storegdown,stoflex,stocont,stocharge,stosoc):
    genPlusUpRes = list(map(operator.add,stogen,storegup))
    genPlusUpRes = list(map(operator.add,genPlusUpRes,stoflex))
    genPlusUpRes = list(map(operator.add,genPlusUpRes,stocont))
    for idx in range(len(genPlusUpRes)):
        if genPlusUpRes[idx] > stosoc[idx] + 1E-3: 
            print('Gen plus res exceed soc at idx:',idx)
#Ramp = MW/hr
def checkResVersusRamp(storegup,storegdown,stoflex,stocont,ramp):
    regTime,flexTime,contTime = 5,10,30 #mins
    rampToReg,rampToFlex,rampToCont = regTime/60,flexTime/60,contTime/60
    for idx in range(len(storegup)):
        if storegup[idx] > ramp*rampToReg:
            print('Regup exceeds ramp at idx:',idx)
        # if storegdown[idx] > ramp*rampToReg:
        #     print('Regdown exceeds ramp at idx:',idx)
        if stoflex[idx] > ramp*rampToFlex:
            print('Flex exceeds ramp at idx:',idx)
        if stocont[idx] > ramp*rampToCont:
            print('Cont exceeds ramp at idx:',idx)
################################################################################
################################################################################

def testCalcMDT():
    print('testing calcMDT')
    test = [1,1,0,0,0,1,0,0,1,0,0,0,0]
    assert(calcMinDown(test) == 2)
    test = [1,1,0,0,0,1,0,0,0,1,0,0,0,0]
    assert(calcMinDown(test) == 3)

def testDisagg():
    print('disagg')
    assert(disaggregateOnOffVals([3,4,5,0,1],6) == [[1,1,1,0,1],[1,1,1,0,0],[1,1,1,0,0],[0,1,1,0,0],[0,0,1,0,0],[0,0,0,0,0]])

def testGetHourSets():
    print('testing gethoursets')
    assert(getHourSets([['g','h1','h2','h3','h8','h10','h11']]) == [[1,2,3],[8],[10,11]])
    print('passed')

masterFunction()