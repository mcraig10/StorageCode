
import os, csv
from AuxFuncs import *
from GAMSAuxFuncs import *

def master():
    rootDir = 'C:\\Users\\mtcraig\\Desktop\\StoResToCompare'
    folders = ['StoEnergy500','StoEnergy2000','NoSto500']
    totalCo2Ems = calcFullRunCo2Diff(rootDir,folders)
    print('total co2 ems (500 stores, 2000 stores, 500 nosto):',totalCo2Ems)
    print('percent diff b/wn stores 500 & 2000 reslim:',(totalCo2Ems[1]-totalCo2Ems[0])/totalCo2Ems[0]*100)
    print('percent diff b/wn stores & nosto 500 reslim:',(totalCo2Ems[2]-totalCo2Ems[0])/totalCo2Ems[0]*100)
    diffDays = getDiffDays(rootDir,['StoEnergy500','StoEnergy2000'])
    print('Diff days:',diffDays)
    diffDaysCo2Diff = calcDiffDaysCo2Diff(rootDir,folders,diffDays)
    print('co2 ems on days w/ diff solve stat for 500 and 2000 reslim:',diffDaysCo2Diff)
    print('percent diff b/wn stores 500 & 2000 reslim:',(diffDaysCo2Diff[1]-diffDaysCo2Diff[0])/diffDaysCo2Diff[0]*100)
    print('percent diff b/wn stores & nosto 500 reslim:',(diffDaysCo2Diff[2]-diffDaysCo2Diff[0])/diffDaysCo2Diff[0]*100)


def getDiffDays(rootDir,folders):
    ms500 = readCSVto2dList(os.path.join(rootDir,folders[0],'msAndSsUC2045.csv'))
    ms2000 = readCSVto2dList(os.path.join(rootDir,folders[1],'msAndSsUC2045.csv'))
    ssCol = ms500[0].index('ss')
    diffDays = list()
    for idx in range(len(ms2000)):
        day = ms2000[idx][0]
        row500Idx = [row[0] for row in ms500].index(day)
        ss500 = ms500[row500Idx][ssCol]
        ss2000 = ms2000[idx][ssCol]
        if ss500 != ss2000:
            diffDays.append(day)
    return diffDays

def calcFullRunCo2Diff(rootDir,folders):
    co2Ems = list()
    for folder in folders:
        a,b,c,genToCo2Ems = getGenDict(rootDir,folder)
        gen = readCSVto2dList(os.path.join(rootDir,folder,'genByPlantUC2045.csv'))
        co2Ems.append(calcCo2Ems(gen,genToCo2Ems))
    return co2Ems

def calcDiffDaysCo2Diff(rootDir,folders,diffDays):
    co2EmsDiffDays = list()
    for folder in folders:
        a,b,c,genToCo2Ems = getGenDict(rootDir,folder)
        gen = readCSVto2dList(os.path.join(rootDir,folder,'genByPlantUC2045.csv'))
        diffDayHourSymbols = getDiffDayHourSymbols(diffDays)
        # print(diffDayHourSymbols)
        slimGen = isolateDiffDaysGen(diffDayHourSymbols,gen)
        if folder == 'StoRes500': write2dListToCSV(slimGen,'test.csv')
        co2EmsDiffDays.append(calcCo2Ems(slimGen,genToCo2Ems))
    return co2EmsDiffDays

def isolateDiffDaysGen(diffDayHourSymbols,gen):
    colsToRemove = list()
    colsToSave = list()
    for col in range(1,len(gen[0])):
        if gen[0][col] not in diffDayHourSymbols:
            colsToRemove.append(col)
        else:
            colsToSave.append(col)
    slimGen = list()
    for idx in range(len(gen)): slimGen.append([gen[idx][0]])
    for col in range(1,len(gen[0])):
        if col not in colsToRemove:
            for idx in range(len(slimGen)): slimGen[idx].append(gen[idx][col])
    return slimGen

def getDiffDayHourSymbols(diffDays):
    diffDayHourSymbols = list()
    for day in diffDays:
        hrs = range((int(day)-1)*24+1,int(day)*24+1)
        hours = ['h' + str(hr) for hr in hrs]
        diffDayHourSymbols.extend(hours)
    return diffDayHourSymbols

def calcCo2Ems(gen,genToCo2): 
    totalCo2Ems = 0
    for row in gen[1:]:
        rowgen = sum([float(val) for val in row[1:]])
        totalCo2Ems += rowgen * genToCo2[row[0]] / 1E6 
    return totalCo2Ems #million tons

def getGenDict(dir,folder):
    lbToTon = 2000
    fleet = readCSVto2dList(os.path.join(dir,folder,'genFleetUC2045.csv'))
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

master()



