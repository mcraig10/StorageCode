#Michael Craig
#Jan 24, 2017

#Plot gen and reserves by plant type sequentially for given
#scenario and time period.

from AuxFuncs import *
from GAMSAuxFuncs import *
import os,csv,operator,copy
import numpy as np
import matplotlib.pyplot as plt

plt.style.use('ggplot')

######## SET PARAMS AND LOAD DATA ##############################################
def setParameters():
    resultFolder = 'Resultsdeep2015to2056in10Stp23Jan'
    model = 'UC'
    days = list(range(300,321))
    years = [2015,2045]
    stoScenario = 'NoSto'
    baseDir = 'C:\\Users\\mtcraig\\Desktop\\EPP Research\\PythonStorageProject'
    resultDir = os.path.join(baseDir,resultFolder,model,stoScenario)
    return resultDir,days,years

def loadData(resultDir,year):
    gen = readCSVto2dList(os.path.join(resultDir,'genByPlantUC' + str(year) + '.csv'))
    regup = readCSVto2dList(os.path.join(resultDir,'regupByPlantUC' + str(year) + '.csv'))
    flex = readCSVto2dList(os.path.join(resultDir,'flexByPlantUC' + str(year) + '.csv'))
    cont = readCSVto2dList(os.path.join(resultDir,'contByPlantUC' + str(year) + '.csv'))
    fleet = readCSVto2dList(os.path.join(resultDir,'genFleetUC' + str(year) + '.csv'))
    return gen,regup,flex,cont,fleet
################################################################################

######## MASTER FUNCTION #######################################################
def masterFunction():
    resultDir,days,years = setParameters()
    for year in years:
        gen,regup,flex,cont,fleet = loadData(resultDir,year)
        genToPt = getGenToPt(fleet)
        plotGenOrRes(gen,days,fleet,genToPt,1,'Gen')
        plotGenOrRes(regup,days,fleet,genToPt,2,'Regup Res')
        plotGenOrRes(flex,days,fleet,genToPt,3,'Flex Res')
        plotGenOrRes(cont,days,fleet,genToPt,4,'Cont Res')
        plt.show()
################################################################################

######## GET DICT MAPPING GEN ID TO PLANT TYPE #################################
def getGenToPt(fleet):
    plantTypeCol = fleet[0].index('PlantType')
    genToPt = dict()
    for row in fleet[1:]:
        genToPt[createGenSymbol(row,fleet[0])] = row[plantTypeCol]
    return genToPt
################################################################################

######## PLOT GEN OR RES BY PT SEQUENTIALLY ####################################
def plotGenOrRes(data,days,fleet,genToPt,figNum,dataName):
    fig = plt.figure(figNum,figsize = (25,35))
    ax = plt.subplot(111)
    plantTypes = getPlantTypes(fleet)
    xlocs = np.arange(len(data[0][1:]))
    dataByPts,labels = list(),list()
    for pt in plantTypes:
        dataByPt = sumGenOrResByPt(data,genToPt,pt)
        dataByPts.append(dataByPt)
        labels.append(pt)
    ax.stackplot(xlocs,np.row_stack(dataByPts),labels=labels)
    plt.xticks([val*24 for val in range(len(days))], days)
    plt.title(dataName)
    addLegend(ax)
    plt.ylabel('Gen or Res By Plant Type (GWh)')

def sumGenOrResByPt(data,genToPt,pt):
    dataByPt = []
    for row in data[1:]:
        if genToPt[row[0]] == pt:
            rowVals = [float(val) for val in row[1:]]
            if dataByPt == []: dataByPt = copy.copy(rowVals)
            else: dataByPt = list(map(operator.add,dataByPt,rowVals))
    return dataByPt

def getPlantTypes(fleet):
    ptCol = fleet[0].index('PlantType')
    plantTypes = set([row[ptCol] for row in fleet[1:]])
    pts = list(plantTypes)
    ptsSorted = ['Nuclear','Coal Steam','Combined Cycle']
    ptsSorted = ptsSorted + [pt for pt in pts if pt not in ptsSorted]
    return ptsSorted

def addLegend(ax):
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1],loc='center left', bbox_to_anchor=(1, 0.5))
################################################################################

masterFunction()
