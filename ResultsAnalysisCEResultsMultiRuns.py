#Michael Craig
#Feb 5, 2017

import os
import numpy as np
import matplotlib.pyplot as plt
from AuxFuncs import *
from GAMSAuxFuncs import *
from ResultsAnalysisCompareScenarios12Feb import getYears, getPlantTypes, createFigPath, getSortedPlantTypes

plt.style.use('ggplot')
rc = {'font.family':'Times New Roman','font.size':18,'text.color':'k',
    'axes.labelcolor':'k','xtick.color':'k','ytick.color':'k'}
plt.rcParams.update(**rc)

#Plot fleet mix over CE runs for multiple runs

def masterFunction():
    resultFolders = ['ResultsScppCcppRet5NewCo2Cap','ResultsSdeepCdeepRet5NewCo2Cap90Percent',
                    'ResultsScoalretCcppRet3NewCo2Cap']
    rootDir = 'C:\\Users\\mtcraig\\Desktop\\EPP Research\\PythonStorageProject'
    plotFleetMixCEMultiRuns(resultFolders,rootDir)
    plt.show()

def plotFleetMixCEMultiRuns(resultFolders,rootDir):
    #Get universal data
    # yearList = getYears(os.path.join(rootDir,'ResultsScppCcpp'))    
    yearList = [2015,2025,2035,2045]
    print('Coal steam CCS not in sorted plant types!')
    sortedPlantTypes,sortedPlantTypesLabels,colors = getSortedPlantTypes()
    #Set up plot
    fig,ctr = plt.figure(1,figsize = (25,35)),1
    # colors = [np.random.rand(3,) for val in sortedPlantTypes]
    bw = .8
    xlocs = list(range(len(yearList)))
    for folderName in resultFolders:
        folder = os.path.join(folderName,'CE')
        ax = plt.subplot(1,len(resultFolders),ctr)
        cumCapacByYear = [0]*len(yearList)
        fleet = readCSVto2dList(os.path.join(rootDir,folder,'genFleetAfterCE' + str(yearList[-1]) + '.csv'))
        for idx in range(len(sortedPlantTypes)):
            pt = sortedPlantTypes[idx]
            capacByYear = getCapacOfFtByYear(fleet,pt,yearList,sortedPlantTypes) #convert to GW
            ax.bar(xlocs, capacByYear, bottom=cumCapacByYear,label = sortedPlantTypesLabels[idx],
                width = bw,align='center',color = colors[idx]) 
            cumCapacByYear = [cumCapacByYear[idx] + capacByYear[idx] for idx in range(len(yearList))]
        plt.xticks([val for val in xlocs],yearList)
        plt.ylim([0,120])
        #Add legend
        if ctr == len(resultFolders):
            box = ax.get_position()
            ax.set_position([box.x0, box.y0, box.width, box.height])
            handles, labels = ax.get_legend_handles_labels()
            ax.legend(handles[::-1], labels[::-1],loc='center left', bbox_to_anchor=(1, 0.5))
        if ctr == 1: plt.ylabel('Capacity (GW)')
        plt.xlabel('Year')
        # plt.title(createTitleFromFolderName(folderName))
        if ctr == 1: plt.title('Mid Decarb')
        if ctr == 2: plt.title('Deep Decarb')
        if ctr == 3: plt.title('Mid Decarb, Early Coal Ret.')
        ctr += 1
    # ax = plt.subplot(1,3,ctr)
    # box = ax.get_position()
    # ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    # handles, labels = ax.get_legend_handles_labels()
    # ax.legend(handles[::-1], labels[::-1],loc='center left', bbox_to_anchor=(1, 0.5))
    fig.set_size_inches(8,6)
    fig.savefig(createFigPath(rootDir,'fleetMixAcrossRuns'),dpi=300,
        transparent=True, bbox_inches='tight', pad_inches=0.1)
    
def createTitleFromFolderName(folderName):
    if 'cpp' in folderName: return 'Mid Decarb.'
    else: return 'Deep Decarb.'

#Outputs values in GW
def getCapacOfFtByYear(fleet,pt,yearList,sortedPlantTypes):
    heads = fleet[0]
    ptCol,capacCol = heads.index('PlantType'),heads.index('Capacity (MW)')
    capacByYear = dict()
    for year in yearList: capacByYear[year] = 0
    for row in fleet[1:]:
        if row[ptCol] in sortedPlantTypes: rowPt = row[ptCol]
        else: rowPt = 'Other'
        if rowPt == pt:
            onlineYear,offlineYear = getOnlineYearRange(heads,row) 
            for year in yearList:
                if year >= onlineYear and year < offlineYear: 
                    capacByYear[year] += float(row[capacCol])/1000 #convert to GW
    return [capacByYear[yr] for yr in yearList]

def getOnlineYearRange(heads,row):
    onCol,retCol = heads.index('On Line Year'),heads.index('YearRetiredByCE')
    ageCol = heads.index('YearRetiredByAge')
    ret = int(row[retCol]) if row[retCol] != '' else 2100
    age = int(row[ageCol]) if row[ageCol] != '' else 2100
    offYear = min(ret,age)
    return int(row[onCol]),offYear

masterFunction()