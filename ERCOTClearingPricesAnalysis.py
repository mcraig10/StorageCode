#Michael Craig
#17 Nov 2016
#Script reads in DAM MCPs for energy and ancillary services in ERCOT
#from 2013-2015, and looks at relationship between them. Reads data
#straight from Excel files

import xlrd,os,csv,openpyxl
from operator import *
from datetime import datetime
from AuxFuncs import *
import matplotlib.pyplot as plt
import statistics
plt.style.use('ggplot')

def setParameters():
    dataDir = 'C:\\Users\\mtcraig\\Desktop\\EPP Research\\Databases\\ERCOTClearingPrices'
    energyFiles = ['rpt.00013060.0000000000000000.DAMLZHBSPP_2013.xlsx',
            'rpt.00013060.0000000000000000.DAMLZHBSPP_2014.xlsx',
            'rpt.00013060.0000000000000000.DAMLZHBSPP_2015.xlsx']
    asFiles = ['rpt.00013091.0000000000000000.20140101080003.DAMASMCPC_2013.csv',
                'rpt.00013091.0000000000000000.20150101080004.DAMASMCPC_2014.csv',
                'rpt.00013091.0000000000000000.20160101080005.DAMASMCPC_2015.csv']
    settlePoint = 'HB_HUBAVG'
    importData = False
    return (dataDir,energyFiles,asFiles,settlePoint,importData)

def masterFunction():
    (dataDir,energyFiles,asFiles,settlePoint,importData) = setParameters()
    if importData == True:
        energyMCPs = importEnergyMCPs(dataDir,energyFiles,settlePoint)
        write2dListToCSV(energyMCPs,os.path.join(dataDir,'energyMCPs.csv'))
        asMCPs = importASMCPs(dataDir,asFiles)
        write2dListToCSV(asMCPs,os.path.join(dataDir,'asMCPs.csv'))
    else:
        energyMCPs = readCSVto2dList(os.path.join(dataDir,'energyMCPs.csv'))
        asMCPs = readCSVto2dList(os.path.join(dataDir,'asMCPs.csv'))
    compareMCPs(energyMCPs,asMCPs)

def importEnergyMCPs(dataDir,energyFiles,settlePoint):
    energyMCPs = [['datetime','energyMCP']]
    # energyMCPsStringDate = [['datetime','energyMCP']]
    for file in energyFiles:
        print('File name:',file)
        wb = openpyxl.load_workbook(os.path.join(dataDir,file))
        for sh in wb:
            print('Sheet name:',sh)
            (dateCol,hourCol,pointCol,mcpCol) = getColNums(sh.rows[0])
            mcpSettlePointRows = [row for row in sh.rows if row[pointCol].value == settlePoint]
            for r in mcpSettlePointRows:
                rDate,rTime = r[dateCol].value,r[hourCol].value
                rHour = str(int(rTime.split(':')[0])-1) #put in 0-23 format for datetime
                rDatetime = datetime.strptime(rDate + ' ' + rHour,'%m/%d/%Y %H')
                energyMCPs.append([rDatetime,float(r[mcpCol].value)])
                # energyMCPsStringDate.append([rDate + ' ' + rHour,float(r[mcpCol].value)])
    return energyMCPs

def getColNums(firstRow):
    for idx in range(len(firstRow)):
        if firstRow[idx].value == 'Delivery Date': dateCol = idx
        elif firstRow[idx].value == 'Hour Ending': hourCol = idx
        elif firstRow[idx].value == 'Settlement Point': pointCol = idx
        elif firstRow[idx].value == 'Settlement Point Price': mcpCol = idx
    return dateCol,hourCol,pointCol,mcpCol

def importASMCPs(dataDir,asFiles):
    asMCPs = [['datetime','regdownMCP','regupMCP','spinMCP','nonspinMCP']]
    # asMCPsStringDate=[['datetime','regdownMCP','regupMCP','spinMCP','nonspinMCP']]
    for file in asFiles:
        print('File name:',file)
        data = readCSVto2dList(os.path.join(dataDir,file))
        (dateCol,hourCol,regdownCol,regupCol,spinCol,nonspinCol) = getASColNums(data[0])
        for r in data[1:]:
            rDate,rTime = r[dateCol],r[hourCol]
            rHour = str(int(rTime.split(':')[0])-1) #put in 0-23 format for datetime
            rDatetime = datetime.strptime(rDate + ' ' + rHour,'%m/%d/%Y %H')
            asMCPs.append([rDatetime,float(r[regdownCol]),float(r[regupCol]),float(r[spinCol]),
                            float(r[nonspinCol])])
            # energyMCPsStringDate.append([rDate + ' ' + rHour,float(r[mcpCol].value)])
    return asMCPs

def getASColNums(firstRow):
    for idx in range(len(firstRow)):
        val = firstRow[idx]
        print(val,len(val))
        if val == 'Delivery Date': dateCol = idx 
        elif val == 'Hour Ending': hourCol = idx
        elif 'REGUP' in val: regupCol = idx
        elif val == 'REGDN': regdownCol = idx
        elif val == 'RRS': spinCol = idx
        elif val == 'NSPIN': nonspinCol = idx
    return dateCol,hourCol,regdownCol,regupCol,spinCol,nonspinCol

def compareMCPs(energyMCPs,asMCPs):
    medianVals,averageVals = dict(),dict()
    figNum, subplotCtr, numSubplots, subplotBase = 1, 1, 4, 220
    plt.figure(figNum,figsize=(20,30))
    for asMCP in asMCPs[0][1:]:
        asMCPDivByEnergyMCP = divideASMCPByEnergyMCP(energyMCPs,asMCPs,asMCP)
        currMedian,currAvg = statistics.median(asMCPDivByEnergyMCP), statistics.mean(asMCPDivByEnergyMCP)
        ax = plt.subplot(subplotBase + subplotCtr)
        subplotCtr += 1
        n, bins, patches = plt.hist(asMCPDivByEnergyMCP, bins=50, range = (0,1))
        # n, bins, patches = plt.hist(asMCPDivByEnergyMCP, bins=50)
        medianLine = plt.axvline(currMedian,color='black',label='median')
        avgLine = plt.axvline(currAvg,color='blue',label='mean')
        plt.xlabel('AS MCP / Energy MCP')
        plt.ylabel('Count')
        plt.title(asMCP)
        plt.legend()
        medianVals[asMCP] = currMedian
        averageVals[asMCP] = currAvg
    print('Median values:',medianVals)
    print('Average values:',averageVals)
    plt.show()

def divideASMCPByEnergyMCP(energyMCPs,asMCPs,asName):
    asCol = asMCPs[0].index(asName)
    energyMCPCol = energyMCPs[0].index('energyMCP')
    currASMCPs = [float(row[asCol]) for row in asMCPs[1:]]
    currEnergyMCPs = [float(row[energyMCPCol]) for row in energyMCPs[1:]]
    return list(map(truediv,currASMCPs,currEnergyMCPs))


masterFunction()


