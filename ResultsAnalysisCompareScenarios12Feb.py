#Michael Craig
#Jan 17, 2017

import csv,os,datetime
import numpy as np
import matplotlib.pyplot as plt
from operator import *
from AuxFuncs import *
from GAMSAuxFuncs import *
from CalculateOpCost import calcOpCosts

plt.style.use('ggplot')
rc = {'font.family':'Times New Roman','font.size':35,'text.color':'k',
    'axes.labelcolor':'k','xtick.color':'k','ytick.color':'k','font.weight':'bold'}
# print(plt.rcParams.keys())
plt.rcParams.update(**rc)

# font = {'family' : 'Times New Roman',
#         'size'   : univfontsize,
#         'color'  : 'k'}
# plt.rc('font', **font)

#Plot comparison plots for set of runs w/ & w/out storage
#Fleet mix over time (stacked bar graph by fuel type)
#CO2 emissions in UC runs for each year (bar graph, grouped by year)
#Storage operations (separate plots for energy, reserves, or both scenarios, grouped by years)
#Generation by fuel type in UC runs for each year (stacked bar graph by fuel type,
#separate subplots for each storage scenario)
#Also old code at bottom for comparing CE fleets in multiple folders (use this
#to compare across runs, e.g. CPP vs Deep CO2 target)

############## MASTER FUNCTION #################################################
def masterFunction():
    rootDir = 'C:\\Users\\mtcraig\\Desktop\\EPP Research\\PythonStorageProject'
    resultFolder = 'ResultsSdeepCdeepRet5NewCo2Cap'
    resultDir = os.path.join(rootDir,resultFolder)
    ucFolders = ['NoSto','StoEnergy','StoRes','StoEnergyAndRes']
    # plotFleetMixCE(resultDir)
    plotGenByPlantTypeCE(resultDir)
    # plotCO2EmissionsUC(resultDir,ucFolders)
    # plotCO2EmissionsUCDiffFromNoSto(resultDir,ucFolders)
    # print('Finished co2 plots')
    # plotStorageOperationsUC(resultDir,ucFolders)
    # # plotStorageOperationsHrOfDayUC(resultDir,ucFolders)
    # print('finished sto plots')
    # plotGenByPlantTypeUC(resultDir,ucFolders)
    # plotResByPlantTypeUC(resultDir,ucFolders)
    # plotGenByPlantTypeUCNoSto(resultDir)
    # plotResByPlantTypeUCNoSto(resultDir)
    # plotGenByPlantUCDiffFromNoSto(resultDir,ucFolders)
    # plotResByPlantUCDiffFromNoSto(resultDir,ucFolders)
    # print('finished gen & res plots')
    # calcRECurtailment(resultDir,ucFolders)
    # plotMarginalFuelTypeUC(resultDir,ucFolders)
    plt.show()
################################################################################

############## PLOT FLEET MIX OVER TIME ########################################
def plotFleetMixCE(resultDir):
    #Get universal data
    yearList = getYears(resultDir)
    plantTypes = getPlantTypes(resultDir,yearList)
    #Set up plot
    fig,ctr = plt.figure(1,figsize = (25,35)),1
    colors = [np.random.rand(3,) for val in plantTypes]
    bw = .8
    xlocs = list(range(len(yearList)))
    resultFolder = os.path.join(resultDir,'CE')
    ax = plt.subplot(111)
    ctr += 1
    cumCapacByYear = [0]*len(yearList)
    fleet = readCSVto2dList(os.path.join(resultFolder,'genFleetAfterCE' + str(yearList[-1]) + '.csv'))
    for idx in range(len(plantTypes)):
        pt = plantTypes[idx]
        capacByYear = getCapacOfFtByYear(fleet,pt,yearList)
        ax.bar(xlocs, capacByYear, bottom=cumCapacByYear,label = pt,width = bw,
            align='center',color = colors[idx]) 
        cumCapacByYear = [cumCapacByYear[idx] + capacByYear[idx] for idx in range(len(yearList))]
    plt.xticks([val for val in xlocs],yearList)
    #Add legend
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1],loc='center left', bbox_to_anchor=(1, 0.5))
    plt.ylabel('Capacity (MW)')
    plt.xlabel('Year')
    fig.set_size_inches(5,6)
    fig.savefig(createFigPath(resultDir,'fleetMix'),dpi=100,transparent=True,
                bbox_inches='tight', pad_inches=0.1)
    
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

############## PLOT GEN BY PLANT TYPE FOR CE RUNS ##############################
def plotGenByPlantTypeCE(resultDir):
    #Universal data
    yearList = getCERunYears(resultDir)
    # plantTypes = getPlantTypes(resultDir,yearList)
    sortedPlantTypes,sortedPlantTypesLabels,colors = getSortedPlantTypes()
    #Set up plot
    fig,bw,ax = plt.figure(7,figsize = (25,35)),.8,plt.subplot(111)
    xlocs = list(range(len(yearList)))
    # colors,xlocs = [np.random.rand(3,) for val in plantTypes],
    currFolder = os.path.join(resultDir,'CE')
    cumGenByYear = [0]*len(yearList)
    for idx in range(len(sortedPlantTypes)):
        pt = sortedPlantTypes[idx]    
        genByYear = getGenOrResOfFtByYear(pt,set(sortedPlantTypes),yearList,currFolder,'CE',
                    'Electricity Generation')
        techGenByYear = getTechGenOfFtByYear(pt,yearList,currFolder)
        totalGenByYear = [genByYear[idx] + techGenByYear[idx] for idx in range(len(genByYear))]
        ax.bar(xlocs, totalGenByYear, bottom=cumGenByYear,label = sortedPlantTypesLabels[idx],width = bw,
            align='center',color = colors[idx]) 
        cumGenByYear = [cumGenByYear[idx] + totalGenByYear[idx] for idx in range(len(yearList))]
    plt.xticks([val for val in xlocs],yearList)
    #Add legend
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1],loc='center left', bbox_to_anchor=(1, 0.5))
    plt.ylabel('Gen. by Plant Type (GWh)')
    plt.title('CE Model, Deep Decarb')
    # plt.title('GenByPlantTypeCE')
    fig.set_size_inches(18,20)
    fig.savefig(createFigPath(resultDir,'genByPlantTypeCEAcrossRuns'),dpi=100,
        transparent=True, bbox_inches='tight', pad_inches=0.1)

def getTechGenOfFtByYear(pt,yearList,currFolder):
    techGenByYear = list()
    for year in yearList:
        gen = readCSVto2dList(os.path.join(currFolder,'genByTechCE' + str(year) + '.csv'))
        genYear = 0
        for row in gen[1:]:
            if row[0] == pt: genYear = sum([float(val) for val in row[1:]])
        techGenByYear.append(genYear)
    return techGenByYear
################################################################################

############## PLOT CO2 EMISSIONS UC ###########################################
def plotCO2EmissionsUC(resultDir,ucFolders):
    yearList = getYears(resultDir)
    fig,ctr = plt.figure(2,figsize = (25,35)),1
    xlocs = list(range(len(yearList)))
    colorCtr,colorInc = .1,(.9-.1)/len(ucFolders)
    bw = .2
    for folder in ucFolders:
        origFolder = os.path.join(resultDir,'UC',folder)
        folderCo2Ems = []
        for year in yearList:
            if year == 2015: currFolder = set2015UCDirRuns(origFolder)
            else: currFolder = origFolder
            # print(year,origFolder,currFolder)
            a,b,c,genToCo2Ems = getGenDict(currFolder,year,'UC')
            gen = readCSVto2dList(os.path.join(currFolder,'genByPlantUC' + str(year) + '.csv'))
            folderCo2Ems.append(calcCo2Ems(gen,genToCo2Ems))
        print('CO2 ems for ' + folder + ':',folderCo2Ems)
        plt.bar([val + bw*(ctr-1) for val in xlocs],folderCo2Ems,width=bw,
                    label=convertFolderNameToTitle(folder),color=str(colorCtr))
        ctr,colorCtr = ctr+1,colorCtr + colorInc
    plt.ylabel('Annual CO$_2$ Emissions (million tons)')
    # plt.title(getTitleFromResultDir(resultDir))
    plt.xticks([val + bw*len(ucFolders)/2 for val in xlocs], [val for val in yearList])
    plt.legend()
    fig.set_size_inches(18,20)
    # fig.savefig(createFigPath(resultDir,'co2EmsAcrossUCRuns'),dpi=300,
    #     transparent=True, bbox_inches='tight', pad_inches=0.1)

#Gen in GWh, gentoco2 in ton/GWh
def calcCo2Ems(gen,genToCo2): 
    totalCo2Ems = 0
    for row in gen[1:]:
        rowgen = sum([float(val) for val in row[1:]])
        totalCo2Ems += rowgen * genToCo2[row[0]] / 1E6 
    return totalCo2Ems #million tons

def getGenDict(resultDir,year,model):
    lbToTon = 2000
    if model=='UC': fleet = readCSVto2dList(os.path.join(resultDir,'genFleetUC' + str(year) + '.csv'))
    elif model=='CE': fleet = readCSVto2dList(os.path.join(resultDir,'genFleetForCE' + str(year) + '.csv'))
    fuelCol = fleet[0].index('Modeled Fuels')
    capacCol = fleet[0].index('Capacity (MW)')
    plantTypeCol = fleet[0].index('PlantType')
    co2Col = fleet[0].index('CO2EmRate(lb/MMBtu)')
    hrCol = fleet[0].index('Heat Rate (Btu/kWh)')
    genToCapac,genToPlantType,genToFuel,genToCo2Ems = dict(),dict(),dict(),dict()
    for row in fleet[1:]:
        genToCapac[createGenSymbol(row,fleet[0])] = float(row[capacCol])
        genToPlantType[createGenSymbol(row,fleet[0])] = row[plantTypeCol]
        genToFuel[createGenSymbol(row,fleet[0])] = row[fuelCol]
        genToCo2Ems[createGenSymbol(row,fleet[0])] = float(row[co2Col])/lbToTon * float(row[hrCol]) #ton/GWh
    return (genToCapac,genToPlantType,genToFuel,genToCo2Ems)
################################################################################

############## PLOT CO2 EMS AS DIFF FROM NO STO SCENARIO #######################
def plotCO2EmissionsUCDiffFromNoSto(resultDir,ucFolders):
    yearList = getYears(resultDir)
    fig,ctr = plt.figure(3,figsize = (12,13)),1
    ax = plt.subplot(1,1,1)
    xlocs = list(range(len(yearList)))
    # colorCtr,colorInc = .1,(.9-.1)/(len(ucFolders)-1) #FOR BLACK/WHITE
    colorCtr,colorInc,colors = 0,1,['lightseagreen','lightcoral','darkslateblue']
    bw = .2
    co2EmsNoSto = getNoStoCo2Ems(resultDir)
    for folder in ucFolders:
        if 'NoSto' not in folder:
            origFolder = os.path.join(resultDir,'UC',folder)
            folderCo2Ems = []
            for idx in range(len(yearList)):
                year = yearList[idx]
                if year == 2015: currFolder = set2015UCDirRuns(origFolder)
                else: currFolder = origFolder
                a,b,c,genToCo2Ems = getGenDict(currFolder,year,'UC')
                gen = readCSVto2dList(os.path.join(currFolder,'genByPlantUC' + str(year) + '.csv'))
                folderCo2Ems.append(calcCo2Ems(gen,genToCo2Ems) - co2EmsNoSto[idx])
            #FOR BLACK/WHITE
            # ax.bar([val + bw*(ctr-1) for val in xlocs],folderCo2Ems,width=bw,
            #             label=convertFolderNameToTitle(folder),color=str(colorCtr))
            #FOR COLOR
            ax.bar([val + bw*(ctr-1) for val in xlocs],folderCo2Ems,width=bw,
                        label=convertFolderNameToTitle(folder),color=colors[colorCtr])
            colorCtr += colorInc
            ctr += 1
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    # ax.set_ylim([-1.0,3.0])
    # ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    ax.legend(frameon=False)
    plt.ylabel('Change in CO$_2$ Emissions \n with Storage (million tons)')
    plt.xlabel('Year')
    # plt.title(getTitleFromResultDir(resultDir))
    plt.xticks([val + bw*len(ucFolders)/2 for val in xlocs], [val for val in yearList])
    # fig.set_size_inches(5,6)
    ax.patch.set_facecolor('white')
    # fig.set_size_inches(14,14)
    fig.savefig(createFigPath(resultDir,'co2EmsDiffFromNoSto'),dpi=600,
        transparent=False, bbox_inches='tight', pad_inches=0.1)

def getNoStoCo2Ems(resultDir):
    co2EmsNoSto = list()
    noStoFolder = os.path.join(resultDir,'UC','NoSto')
    yearList = getYears(resultDir)
    for year in yearList:
        if year == 2015: currFolder = set2015UCDirRuns(noStoFolder)
        else: currFolder = noStoFolder
        a,b,c,genToCo2Ems = getGenDict(currFolder,year,'UC')
        gen = readCSVto2dList(os.path.join(currFolder,'genByPlantUC' + str(year) + '.csv'))
        co2EmsNoSto.append(calcCo2Ems(gen,genToCo2Ems))
    return co2EmsNoSto
################################################################################

############## PLOT STORAGE OPERATIONS #########################################
def plotStorageOperationsUC(resultDir,ucFolders):
    yearList = getYears(resultDir)
    fig,subplotCtr = plt.figure(5,figsize = (25,35)),1
    xlocs = list(range(len(yearList)))
    opsToPlot = ['gen','regup','flex','cont']
    bw = .2
    yMax = getYMax(resultDir,ucFolders,yearList)
    for folder in ucFolders:
        if 'NoSto' not in folder: 
            currFolder = os.path.join(resultDir,'UC',folder)
            ax = plt.subplot(1,4,subplotCtr)
            stogen,storegup,stoflex,stocont = getStoOutputForYears(currFolder,yearList)
            ax.bar([val + bw*0 for val in xlocs],stogen,width=bw,
                        label='Gen.',color='r')
            ax.bar([val + bw*1 for val in xlocs],storegup,width=bw,
                        label='Reg.',color='g')
            ax.bar([val + bw*2 for val in xlocs],stoflex,width=bw,
                        label='Flex.',color='k')
            ax.bar([val + bw*3 for val in xlocs],stocont,width=bw,
                        label='Cont.',color='b')
            plt.title(convertFolderNameToTitle(folder))
            # box = ax.get_position()
            # ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
            # ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
            ax.set_ylim([0,yMax+1])
            if subplotCtr == 1: plt.ylabel('Gen. or Res. Prov. (GWh)')
            if subplotCtr > 1: ax.get_yaxis().set_visible(False)
            plt.xticks([val + bw*len(opsToPlot)/2 for val in xlocs], [val for val in yearList])
            plt.xlabel('Year')
            subplotCtr += 1
    empty = plt.subplot(1,4,4)
    empty.set_frame_on(False)
    empty.get_xaxis().set_visible(False)
    empty.get_yaxis().set_visible(False)
    for (lbl,clr) in [('Gen','r'),('Reg.','g'),('Flex.','k'),('Cont.','b')]: 
        plt.plot(0,0,color=clr,label=lbl)
    empty.legend(loc = 'center left')
    fig.set_size_inches(10,2.3)
    fig.savefig(createFigPath(resultDir,'stoOpsAcrossUCRuns'),dpi=100,
        transparent=True, bbox_inches='tight', pad_inches=0.1)

def getYMax(resultDir,ucFolders,yearList):
    allVals = list()
    for folder in ucFolders:
        if 'NoSto' not in folder:
            currFolder = os.path.join(resultDir,'UC',folder)
            stogen,storegup,stoflex,stocont = getStoOutputForYears(currFolder,yearList)
            allVals.extend(stogen)
            allVals.extend(storegup)
            allVals.extend(stoflex)
            allVals.extend(stocont)
    return max(allVals)

def getStoOutputForYears(mainFolder,yearList):
    stogen,storegup,stoflex,stocont = list(),list(),list(),list()
    for year in yearList:
        if year == 2015: currFolder = set2015UCDirRuns(mainFolder)
        else: currFolder = mainFolder
        # print(year,mainFolder,currFolder)
        gen,regup,flex,cont = importGenAndRes(currFolder,year)
        a,genToPlantType,c,d = getGenDict(currFolder,year,'UC')
        stogenYr,storegupYr,stoflexYr,stocontYr = getStoOutput(gen,regup,flex,cont,genToPlantType)
        stogen.append(stogenYr)
        storegup.append(storegupYr)
        stoflex.append(stoflexYr)
        stocont.append(stocontYr)
    return stogen,storegup,stoflex,stocont

def importGenAndRes(currFolder,year):
    gen = readCSVto2dList(os.path.join(currFolder,'genByPlantUC' + str(year) + '.csv'))
    regup = readCSVto2dList(os.path.join(currFolder,'regupByPlantUC' + str(year) + '.csv'))
    flex = readCSVto2dList(os.path.join(currFolder,'flexByPlantUC' + str(year) + '.csv'))
    cont = readCSVto2dList(os.path.join(currFolder,'contByPlantUC' + str(year) + '.csv'))
    return gen,regup,flex,cont

def getStoOutput(gen,regup,flex,cont,genToPlantType):
    stoIdx = [idx for idx in range(1,len(gen)) if genToPlantType[gen[idx][0]] == 'Storage'][0]
    stoGenId = gen[stoIdx][0]
    stogen = sum([float(val) for val in gen[stoIdx][1:]])
    storegup = sum([float(val) for val in regup[stoIdx][1:]])
    stoflex = sum([float(val) for val in flex[stoIdx][1:]])
    stocont = sum([float(val) for val in cont[stoIdx][1:]])
    return stogen,storegup,stoflex,stocont
################################################################################

############## PLOT GEN OR RES BY PLANT TYPE ###################################
# plotStorageOperationsHrOfDayUC

def getStoOutputForYearsByHour(mainFolder,yearList):
    stogen,storegup,stoflex,stocont = list(),list(),list(),list()
    for year in yearList:
        genByHour = [0 for val in range(0,24)]
        if year == 2015: currFolder = set2015UCDirRuns(mainFolder)
        else: currFolder = mainFolder
        gen,a,b,c = importGenAndRes(currFolder,year)
        a,genToPlantType,c,d = getGenDict(currFolder,year,'UC')
        stoIdx = [idx for idx in range(1,len(gen)) if genToPlantType[gen[idx][0]] == 'Storage'][0]
        genVals = [float(val) for val in gen[stoIdx][1:]]
        for day in range(0,365):
            dayGen = genVals[day*24:(day+1)*24]
            genByHour = list(map(add,genByHour,dayGen)) #ton/MWh
    return genByHour
################################################################################

############## PLOT GEN OR RES BY PLANT TYPE ###################################
def plotGenByPlantTypeUC(resultDir,ucFolders):
    plotGenOrResByPlantTypeUC(resultDir,ucFolders,'Electricity Generation',4)    

def plotResByPlantTypeUC(resultDir,ucFolders):
    plotGenOrResByPlantTypeUC(resultDir,ucFolders,'Regulation',8)    
    plotGenOrResByPlantTypeUC(resultDir,ucFolders,'Flexibility',9)    
    plotGenOrResByPlantTypeUC(resultDir,ucFolders,'Contingency',10)    

def plotGenOrResByPlantTypeUC(resultDir,ucFolders,genOrResName,figNum):
    #Universal data
    yearList = getYears(resultDir)    
    #Set up plot
    fig,ctr = plt.figure(figNum,figsize = (25,35)),1
    sortedPlantTypes,sortedPlantTypesLabels,colors = getSortedPlantTypesWithSto()
    xlocs = list(range(len(yearList)))
    bw = .8
    for folder in ucFolders:
        currFolder = os.path.join(resultDir,'UC',folder)
        ax = plt.subplot(1,5,ctr)
        cumGenByYear = [0]*len(yearList)
        for idx in range(len(sortedPlantTypes)):
            pt = sortedPlantTypes[idx]
            genByYear = getGenOrResOfFtByYear(pt,set(sortedPlantTypes),yearList,
                                        currFolder,'UC',genOrResName)
            genByYear = [val/1000 for val in genByYear]
            # print(pt,genByYear)
            ax.bar(xlocs, genByYear, bottom=cumGenByYear,label = pt,width = bw,
                align='center',color = colors[idx]) 
            cumGenByYear = [cumGenByYear[idx] + genByYear[idx] for idx in range(len(yearList))]
            ax.patch.set_facecolor('white')
        plt.xticks([val for val in xlocs],yearList,rotation='vertical')
        #Add legend
        # box = ax.get_position()
        # ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        # handles, labels = ax.get_legend_handles_labels()
        # ax.legend(handles[::-1], labels[::-1],loc='center left', bbox_to_anchor=(1, 0.5))
        if ctr == 1: plt.ylabel(genOrResName + ' (TWh)')
        elif ctr > 1: ax.get_yaxis().set_visible(False)
        plt.xlabel('Year')
        plt.title(convertFolderNameToTitle(folder))
        ctr += 1
    empty = plt.subplot(1,5,5)
    empty.set_frame_on(False)
    empty.get_xaxis().set_visible(False)
    empty.get_yaxis().set_visible(False)
    for idx in range(len(sortedPlantTypesLabels)):
        lbl,clr = sortedPlantTypesLabels[idx],colors[idx]
        plt.plot(0,0,color=clr,label=lbl)
    handles, labels = empty.get_legend_handles_labels()
    leg = empty.legend(handles[::-1], labels[::-1],loc='center left')
    for legobj in leg.legendHandles: legobj.set_linewidth(15.0) #inrease linewidth
    fig.set_size_inches(20,15)
    fig.savefig(createFigPath(resultDir,genOrResName +'ByPTUC'),dpi=400,
        transparent=False, bbox_inches='tight', pad_inches=0.1)

def getGenOrResOfFtByYear(pt,allPts,yearList,mainFolder,model,genOrResName):
    genOrResByYear = list()
    if genOrResName == 'Electricity Generation': csvFile = 'genByPlant'
    elif genOrResName == 'Regulation': csvFile = 'regupByPlant'
    elif genOrResName == 'Flexibility': csvFile = 'flexByPlant'
    elif genOrResName == 'Contingency': csvFile = 'contByPlant'
    if model == 'UC': uc2015Dir = set2015UCDirRuns(mainFolder)
    for year in yearList:
        if year == 2015 and model == 'UC': currFolder = uc2015Dir
        else: currFolder = mainFolder
        # print(year,mainFolder,currFolder)
        genOrRes = readCSVto2dList(os.path.join(currFolder,csvFile + model + str(year) + '.csv'))
        a,genToPlantType,c,d = getGenDict(currFolder,year,model)
        genOrResYear = 0
        for row in genOrRes[1:]:
            currPt = genToPlantType[row[0]]
            if currPt not in allPts: currPt = 'Other'
            if genToPlantType[row[0]] == pt:
                genOrResYear += sum([float(val) for val in row[1:]])
        genOrResByYear.append(genOrResYear)
    return genOrResByYear

def set2015UCDirRuns(mainFolder):
    if 'cpp' in mainFolder: currCap = 'cpp'
    elif 'none' in mainFolder: currCap = 'none'
    elif 'deep' in mainFolder: currCap = 'deep'
    uc2015FolderName = 'ResultsC' + currCap + 'UC2015'
    currStoFolder = os.path.split(mainFolder)[1]
    rootDir = os.path.split(os.path.split(os.path.split(mainFolder)[0])[0])[0]
    uc2015Dir = os.path.join(rootDir,uc2015FolderName,'UC',currStoFolder)
    return uc2015Dir
################################################################################

############## PLOT GEN BY PLANT TYPE ONLY FOR NO STO ##########################
def plotGenByPlantTypeUCNoSto(resultDir):
    plotGenOrResByPlantTypeUCNoSto(resultDir,'Electricity Generation',17)

def plotResByPlantTypeUCNoSto(resultDir):
    plotGenOrResByPlantTypeUCNoSto(resultDir,'Regulation',16)

def plotGenOrResByPlantTypeUCNoSto(resultDir,genOrResName,figNum):
    #Universal data
    yearList = getYears(resultDir)    
    #Set up plot
    fig = plt.figure(figNum,figsize = (25,35))
    sortedPlantTypes,sortedPlantTypesLabels,colors = getSortedPlantTypes()
    xlocs = list(range(len(yearList)))
    bw = .8
    currFolder = os.path.join(resultDir,'UC','NoSto')
    ax = plt.subplot(111)
    cumGenByYear = [0]*len(yearList)
    for idx in range(len(sortedPlantTypes)):
        pt = sortedPlantTypes[idx]
        genByYear = getGenOrResOfFtByYear(pt,set(sortedPlantTypes),yearList,
                                    currFolder,'UC',genOrResName)
        genByYear = [val/1000 for val in genByYear]
        # print(pt,genByYear)
        ax.bar(xlocs, genByYear, bottom=cumGenByYear,label = sortedPlantTypesLabels[idx],
            width = bw,align='center',color = colors[idx]) 
        cumGenByYear = [cumGenByYear[idx] + genByYear[idx] for idx in range(len(yearList))]
    ax.patch.set_facecolor('white')
    plt.xticks([val for val in xlocs],yearList)
    #Add legend
    # box = ax.get_position()
    # ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1],loc='center left', bbox_to_anchor=(1, 0.5),
        frameon=False,borderaxespad=0)
    plt.ylabel(genOrResName + ' (TWh)')
    plt.xlabel('Year')
    fig.set_size_inches(8,10)
    fig.savefig(createFigPath(resultDir,genOrResName +'ByPTUCNoSto'),dpi=400,
        transparent=False, bbox_inches='tight', pad_inches=0.1)
################################################################################

############## PLOT GEN BY PLANT TYPE AS DIFF FROM NO STO ######################
def plotGenByPlantUCDiffFromNoSto(resultDir,ucFolders):
    plotGenOrResByPlantUCDiffFromNoSto(resultDir,ucFolders,'Generation',6)

def plotResByPlantUCDiffFromNoSto(resultDir,ucFolders):
    plotGenOrResByPlantUCDiffFromNoSto(resultDir,ucFolders,'Regulation',11)
    # plotGenOrResByPlantUCDiffFromNoSto(resultDir,ucFolders,'Flexibility',12)
    # plotGenOrResByPlantUCDiffFromNoSto(resultDir,ucFolders,'Contingency',13)

def plotGenOrResByPlantUCDiffFromNoSto(resultDir,ucFolders,genOrResName,figNum):
    #Universal data
    yearList = getYears(resultDir)
    sortedPlantTypes,colors = getSortedPlantTypes()
    #Set up plot
    fig,ctr = plt.figure(figNum,figsize = (25,35)),1
    xlocs = list(range(len(yearList)))
    bw = .08
    genOrResDiffByFolder,yMax,yMin = getDiffsAllYearsByFolder(resultDir,ucFolders,sortedPlantTypes,
                                                yearList,genOrResName) 
    folderCtr = -1
    for idx in range(len(ucFolders)):
        if 'NoSto' not in ucFolders[idx]:
            folder,folderCtr = ucFolders[idx],folderCtr + 1 #need ctr b/c NoSto not indexed
            ax = plt.subplot(1,4,ctr)
            print(folderCtr)
            genOrResDiffCurrFolder = genOrResDiffByFolder[folderCtr]
            for idx in range(len(sortedPlantTypes)):
                genDiffByYear = genOrResDiffCurrFolder[idx]
                ax.bar([val + bw*idx for val in xlocs], genDiffByYear,width=bw,
                            label = sortedPlantTypes[idx],color = colors[idx]) 
            plt.xticks([val + bw*len(sortedPlantTypes)/2 for val in xlocs], [val for val in yearList])
            ax.set_ylim([yMin,yMax])
            #Add legend
            # box = ax.get_position()
            # ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
            # handles, labels = ax.get_legend_handles_labels()
            # ax.legend(handles[::-1], labels[::-1],loc='center left', bbox_to_anchor=(1, 0.5))
            if ctr == 1: plt.ylabel('Diff. in ' + genOrResName + ' from No Sto. (GWh)')
            if ctr > 1: ax.get_yaxis().set_visible(False)
            plt.title(convertFolderNameToTitle(folder))
            plt.xlabel('Year')
            ctr += 1
    empty = plt.subplot(1,4,4)
    empty.set_frame_on(False)
    empty.get_xaxis().set_visible(False)
    empty.get_yaxis().set_visible(False)
    for idx in range(len(sortedPlantTypes)):
        lbl,clr = sortedPlantTypes[idx],colors[idx]
        plt.plot(0,0,color=clr,label=lbl)
    empty.legend(loc = 'center left')
    fig.set_size_inches(12,3)
    fig.savefig(createFigPath(resultDir,genOrResName + 'ByPTDiffFromNoSto'),dpi=100,
        transparent=True, bbox_inches='tight', pad_inches=0.1)

def getDiffsAllYearsByFolder(resultDir,ucFolders,sortedPlantTypes,yearList,
                            genOrResName):
    genOrResDiffByFolder = list()
    noStoFolder = os.path.join(resultDir,'UC','NoSto')
    yMax,yMin = 0,0
    for folder in ucFolders:
        diffAllPts = list()
        if 'NoSto' not in folder:
            currFolder = os.path.join(resultDir,'UC',folder)
            for idx in range(len(sortedPlantTypes)):
                pt = sortedPlantTypes[idx]
                genDiffPt = getGenOrResDiffOfFtByYear(pt,set(sortedPlantTypes),
                                yearList,currFolder,noStoFolder,genOrResName)
                diffAllPts.append(genDiffPt)
                if max(genDiffPt)>yMax: yMax = max(genDiffPt)
                if min(genDiffPt)<yMin: yMin = min(genDiffPt)
            genOrResDiffByFolder.append(diffAllPts)
    return genOrResDiffByFolder,yMax,yMin

def getGenOrResDiffOfFtByYear(pt,allPts,yearList,currFolder,noStoFolder,genOrResName):
    genByYear = getGenOrResOfFtByYear(pt,allPts,yearList,currFolder,'UC',genOrResName)
    genByYearNoSto = getGenOrResOfFtByYear(pt,allPts,yearList,noStoFolder,'UC',genOrResName)
    return [genByYear[idx] - genByYearNoSto[idx] for idx in range(len(genByYear))]
################################################################################

# ############## PLOT MARGINAL FUEL TYPES ########################################
# def plotMarginalFuelTypeUC(resultDir,ucFolders):
#     #Universal data
#     yearList = getYears(resultDir)
#     #Set up plot
#     fig,ctr = plt.figure(12,figsize = (25,35)),1
#     xlocs = list(range(len(yearList)))
#     bw = .08
#     for folder in ucFolders:
#         origFolder = os.path.join(resultDir,'UC',folder)
#         ax = plt.subplot(4,1,ctr)
#         ctr += 1
#         for year in [2045]:
#         # for year in yearList:
#             if year == 2015: currFolder = set2015UCDirRuns(origFolder)
#             else: currFolder = origFolder
#             marginalPTs = getMarginalPTHourly(currFolder,year)
#             print(marginalPTs)
#             marginalFuelCountDict = countMargFuel(marginalFuels)
#             ax.bar(range(len(marginalFuelCountDict)),marginalFuelCountDict.values(),
#                     align='center')
#             ax.bar(range(len(marginalFuelCountDict)),marginalFuelCountDict.keys())
        

#         cumGenByYear = [0]*len(yearList)
#         for idx in range(len(plantTypes)):
#             pt = plantTypes[idx]

#             # genByYear = getGenOrResOfFtByYear(pt,yearList,currFolder,'UC',genOrResName)
#             print(pt,genByYear)
#             ax.bar(xlocs, genByYear, bottom=cumGenByYear,label = pt,width = bw,
#                 align='center',color = colors[idx]) 
#             cumGenByYear = [cumGenByYear[idx] + genByYear[idx] for idx in range(len(yearList))]
#         plt.xticks([val for val in xlocs],yearList)
#         #Add legend
#         box = ax.get_position()
#         ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
#         handles, labels = ax.get_legend_handles_labels()
#         ax.legend(handles[::-1], labels[::-1],loc='center left', bbox_to_anchor=(1, 0.5))
#         plt.ylabel(genOrResName + '(GWh)')
#         plt.title(convertFolderNameToTitle(folder))
#     fig.set_size_inches(18,20)
#     fig.savefig(createFigPath(resultDir,'marginalFuelType'),dpi=200,
#         transparent=True, bbox_inches='tight', pad_inches=0.1)    

# def getMarginalPTHourly(currFolder,year):
#     #Get MCs
#     sysResults = readCSVto2dList(os.path.join(currFolder,'systemResultsUC' + str(year) + '.csv'))
#     mcRow = [row[0] for row in sysResults].index('mcGen')
#     mcs = [float(val) for val in sysResults[mcRow][1:]]
#     #Get co2 price
#     co2Price = readCSVto2dList(os.path.join(currFolder,'co2PriceUC' + str(year) + '.csv'))
#     co2Price = float(co2Price[0][0])
#     #Get op costs
#     fleet = readCSVto2dList(os.path.join(currFolder,'genFleetUC' + str(year) + '.csv'))
#     opcosts,a = calcOpCosts(fleet,2000,co2Price) #1d list of op costs
#     #Get generation
#     gen = readCSVto2dList(os.path.join(currFolder,'genByPlantUC' + str(year) + '.csv'))
#     genGens = [row[0] for row in gen[1:]]
#     #Stack gens in increasing op cost order
#     genIds = [createGenSymbol(row,fleet[0]) for row in fleet[1:]]
#     genOcAndId = [[opcosts[idx],genIds[idx]] for idx in range(len(opcosts))] #oc,id
#     genOcAndIdSorted = sorted(genOcAndId)
#     for hr in range(len(mcs)):
#         mc = mcs[hr]
#         genInHr = [float(row[hr+1]) for row in gen[1:]] #hr+1 b/c gen has labels in col 0
#         ocLessThanMC = [le(row[0],mc+1E-5) for row in genOcAndIdSorted] #le is val1<=val2
#         # highestOC = (len(ocLessThanMC)-1) - list(reversed(ocLessThanMC)).index(1)
#         gensOcLeMc = [genOcAndIdSorted[idx][1] for idx in range(len(genOcAndIdSorted))
#                          if ocLessThanMC[idx]==1]
#         genByGensOcLeMc = [genInHr[genGens.index(genId)] for genId in gensOcLeMc]
#         print('sum le:',sum(genByGensOcLeMc))
#         print('max and min le:',max(genByGensOcLeMc),min(genByGensOcLeMc))
#         gensOcGeMc = [genOcAndIdSorted[idx][1] for idx in range(len(genOcAndIdSorted))
#                          if ocLessThanMC[idx]==0]
#         genByGensOcGeMc = [genInHr[genGens.index(genId)] for genId in gensOcGeMc]
#         print('sum ge:',sum(genByGensOcGeMc))
#         print('max and min ge:',max(genByGensOcGeMc),min(genByGensOcGeMc))
#     print(gensOcLeMc)
#     print(genByGensOcLeMc)
#     print(gensOcGeMc)
#     print(genByGensOcGeMc)


# #This tries to map based on op cost; doesn't work.
# # def getMarginalPTHourly(currFolder,year):
# #     #Get MCs
# #     sysResults = readCSVto2dList(os.path.join(currFolder,'systemResultsUC' + str(year) + '.csv'))
# #     mcRow = [row[0] for row in sysResults].index('mcGen')
# #     mcs = [float(val) for val in sysResults[mcRow][1:]]
# #     #Get co2 price
# #     co2Price = readCSVto2dList(os.path.join(currFolder,'co2PriceUC' + str(year) + '.csv'))
# #     co2Price = float(co2Price[0][0])
# #     print(co2Price)
# #     #Get op costs
# #     fleet = readCSVto2dList(os.path.join(currFolder,'genFleetUC' + str(year) + '.csv'))
# #     opcosts,a = calcOpCosts(fleet,2000,co2Price) #1d list of op costs
    
# #     # write2dListToCSV([mcs],'mctest.csv')
# #     # write2dListToCSV([opcosts],'octest.csv')

# #     #Match MC to op cost
# #     mcToOC = list()
# #     for mc in mcs:
# #         mcMatchCtr = 0
# #         for oc in opcosts:
# #             # if mc == oc: mcMatchCtr += 1
# #             if almostEquals(mc,oc): mcMatchCtr += 1
# #         mcToOC.append(mcMatchCtr)
# #     # write2dListToCSV([mcToOC],'mctooc.csv')
# #     print('**',mcToOC,max(mcToOC),min(mcToOC))

# def almostEquals(val1,val2):
#     return abs(val1-val2)<1E-5

# ################################################################################

############## AUX FUNCTIONS ###################################################
def getTitleFromResultDir(resultDir):
    resultFolder = os.path.basename(os.path.normpath(resultDir))
    if 'cpp' in resultFolder: currCap = 'CPP'
    elif 'deep' in resultFolder: currCap = 'Deep Decarb'
    return currCap + ' CO2 Reduction Scenario'

def createFigPath(resultDir,baseName):
    if 'cpp' in resultDir: baseName += 'CPP'
    elif 'deep' in resultDir: baseName += 'Deep'
    figDir = os.path.join(resultDir,'Figs')
    if not os.path.exists(figDir): os.makedirs(figDir)
    now = datetime.datetime.now()
    return os.path.join(figDir,baseName + str(now.month) + 'D' + str(now.day) + '.png')

#Initialize with 2015 b/c base 2015 runs are in diff folder
def getYears(resultDir):
    allFiles = os.listdir(os.path.join(resultDir,'UC','NoSto'))
    baseName = 'genByPlantUC' #arbitrary UC input file
    years = [2015]
    for fileName in allFiles: 
        if baseName in fileName: years.append(int(fileName.split('.')[0][-4:]))
    return years

def getCERunYears(resultDir):
    allFiles = os.listdir(os.path.join(resultDir,'CE'))
    baseName = 'genByPlantCE' #arbitrary UC input file
    years = []
    for fileName in allFiles: 
        if baseName in fileName: years.append(int(fileName.split('.')[0][-4:]))
    return years

def getPlantTypes(resultDir,years):
    #Gets all plant types b/c genFleetAfterCE has all plants added & retired
    fleet = readCSVto2dList(os.path.join(resultDir,'CE','genFleetAfterCE' + str(years[-1]) + '.csv'))
    ptCol = fleet[0].index('PlantType')
    plantTypes = set([row[ptCol] for row in fleet[1:]])
    return list(plantTypes)

def convertFolderNameToTitle(folder):
    if folder == 'NoSto': title = 'No Storage'
    else:
        if folder == 'StoEnergy': title = 'Energy\nOnly'
        elif folder == 'StoRes': title = 'Reserves\nOnly'
        elif folder == 'StoEnergyAndRes': title = 'Energy and\nReserves'
    return title

def getSortedPlantTypes():
    sortedPlantTypes = ['Nuclear','Coal Steam','Combined Cycle',
                        'Combined Cycle CCS','Wind','Solar PV','Other']
    sortedPlantTypesLabels = ['Nuclear','Coal Steam','Combined\nCycle',
                        'Combined\nCycle CCS','Wind','Solar PV','Other']
    colors = ['g','k','.4','.8','b','y','c']
    colors = ['lightseagreen','lightcoral','darkslateblue','plum','sage','gold','rosybrown']
    return sortedPlantTypes,sortedPlantTypesLabels,colors

def getSortedPlantTypesWithSto():
    sortedPlantTypes,sortedPlantTypesLabels,colors = getSortedPlantTypes()
    sortedPlantTypes.append('Storage')
    sortedPlantTypesLabels.append('Storage')
    colors.append('darkgray')
    return sortedPlantTypes,sortedPlantTypesLabels,colors
################################################################################

masterFunction()