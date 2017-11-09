#Michael Craig
#August 11, 2016
#Script for modifying generator capacity with water T from RBM.

#1) Gets list of all grid cells from .spat.
#2) Saves T data for each segment in each grid cell into folders for each cell.
#3) Averages T data across all segments for each cell and saves that data in folder for each cell.
#4) Creates dictionaries mapping generators to cells and vice versa.
#5) Using dictionary, pairs generator with water T time series and modifies capacity.

import os, csv, copy
import numpy as np
import datetime as dt
from AuxFuncs import *

################################################################################
####### MASTER FUNCTIONS #######################################################
################################################################################
def processRBMDataIntoIndividualCellFiles(rbmDataDir,tempAndSpatFilename,
            rbmOutputDir,nsegFilename,locPrecision,outputHeaders,numCellsToProcess):
    gridCellLatLongs = getAllGridCellLatLongsInSpatFile(rbmDataDir,tempAndSpatFilename)
    saveAndAverageTDataForAllCells(gridCellLatLongs,rbmDataDir,rbmOutputDir,tempAndSpatFilename,
                                   nsegFilename,locPrecision,outputHeaders,numCellsToProcess)

def determineDailyCurtailmentsForExistingGens(locPrecision,genFleet,rbmOutputDir,curtailmentYear,modelName):
    (genToCellLatLongsDictValues,genToCellLatLongsDict,cellLatLongToGenDict,
                    genToCellLatLongsList) = getGenToCellAndCellToGenDictionaries(genFleet)
    write2dListToCSV(genToCellLatLongsList,'mapGensToCells' + modelName + str(curtailmentYear) + '.csv')
    dailyCurtailmentsAllGensInTgtYr = calculateGeneratorCurtailments(genToCellLatLongsDictValues,genToCellLatLongsDict,
                                            cellLatLongToGenDict,rbmOutputDir,locPrecision,
                                            curtailmentYear,genFleet,modelName)
    return dailyCurtailmentsAllGensInTgtYr #dictionary mapping ORIS+UNITID to 2d vertical list of [datetime,curtailment(mw)]
################################################################################
################################################################################
################################################################################

################################################################################
####### PROCESS RBM DATA INTO INDIVIDUAL CELL FILES ############################
################################################################################
#Get all grid cell lat/longs in spat file
def getAllGridCellLatLongsInSpatFile(rbmDataDir,tempAndSpatFilename):
    spatFile = os.path.join(rbmDataDir,tempAndSpatFilename + '.Spat') 
    f = open(spatFile, 'r')
    lineCtr = 0
    gridCellLatLongs = set()  
    while 1:  
        line = f.readline().rstrip("\n")
        lineCtr += 1  # current line number
        if line=="": break
        lineSplit = line.split()
        (cellLat,cellLong) = (float(lineSplit[4]),float(lineSplit[5]))
        gridCellLatLongs.add((cellLat,cellLong))
    f.close()
    return gridCellLatLongs

#Average temperature data for all segments in each cell, then save all data
def saveAndAverageTDataForAllCells(gridCellLatLongs,rbmDataDir,rbmOutputDir,tempAndSpatFilename,
                                   nsegFilename,locPrecision,outputHeaders,numCellsToProcess):
    print('Num grid cells:',len(gridCellLatLongs))
    (cellCtr,totalCellCtr,tgtCellLatLongs) = (0,0,[])
    for (cellLat,cellLong) in gridCellLatLongs:
        cellCtr += 1
        totalCellCtr += 1
        tgtCellLatLongs.append((cellLat,cellLong))
        if cellCtr == numCellsToProcess or totalCellCtr == len(gridCellLatLongs):           
            saveAndAverageTDataForGridCells(rbmDataDir,rbmOutputDir,tempAndSpatFilename,
                                            nsegFilename,locPrecision,tgtCellLatLongs,outputHeaders)   
            (cellCtr,tgtCellLatLongs) = (0,[])
            print('Cell count:',totalCellCtr)
            
def saveAndAverageTDataForGridCells(rbmDataDir,rbmOutputDir,tempAndSpatFilename,
                                    nsegFilename,locPrecision,tgtCellLatLongs,outputHeaders):
    outputDirs = createOutputDirs(rbmOutputDir,tempAndSpatFilename,locPrecision,tgtCellLatLongs)
    (numTotalSegments,numDays) = getNumSegmentsAndDays(rbmDataDir,nsegFilename) 
    (cellInfo,mapSegmentNumToLatLong,mapLatLongToSegmentNum) = getLinesInSpatFileForCell(rbmDataDir,
                                                tempAndSpatFilename,tgtCellLatLongs,numTotalSegments)
    # print('cell info keys:',[key for key in cellInfo])
    # print('segment nums to lat longs:',mapSegmentNumToLatLong)
    # print('lat longs to sgement nums:',mapLatLongToSegmentNum)
    (allSegmentData,waterTAllSegments) = readCellTemperatureData(rbmDataDir,tempAndSpatFilename,
                                                                cellInfo,numTotalSegments,outputHeaders)
    writeCellTemperatureData(allSegmentData,cellInfo,outputDirs,locPrecision,
                             numDays,outputHeaders,mapSegmentNumToLatLong)
    averageAndSaveWaterTOverAllSegmentsInCells(waterTAllSegments,outputDirs,locPrecision,
                                            mapLatLongToSegmentNum,mapSegmentNumToLatLong)

###### CREATE OUTPUT DIRECTORY FOR CELL T DATA #################################
def createOutputDirs(baseOutputDir,tempAndSpatFilename,locPrecision,tgtCellLatLongs):
    outputDirs = dict()
    for (cellLat,cellLong) in tgtCellLatLongs:
        outputDir = os.path.join(baseOutputDir, 
                            '%.*f_%.*f' %(locPrecision, cellLat, locPrecision, cellLong))
        if not os.path.exists(outputDir): os.makedirs(outputDir)
        outputDirs[(cellLat,cellLong)] = outputDir
    return outputDirs

###### EXTRACT TOTAL NUM SEGMENTS AND DAYS IN MODEL RUN ########################
def getNumSegmentsAndDays(dataDir,nsegFilename):
    nseg_nday = np.loadtxt(os.path.join(dataDir,nsegFilename))
    (numTotalSegments,numDays) = (int(nseg_nday[0]),int(nseg_nday[1]))
    return (numTotalSegments,numDays)

###### GET ALL LINES IN SPATIAL FILE THAT CORRESPOND TO CELL ###################
#Gets line numbers in spatial file that match cell. Includes all reaches & segments
#EXCEPT segment 2 in outlet cell (= max segment #) b/c no data for that segment.
def getLinesInSpatFileForCell(dataDir,tempAndSpatFilename,tgtCellLatLongs,numTotalSegments):
    (mapSegmentNumToLatLong,mapLatLongToSegmentNum) = (dict(),dict())
    spatFile = os.path.join(dataDir,tempAndSpatFilename + '.Spat')  # .Temp file
    f = open(spatFile, 'r')
    totalSegmentNum = 0
    cellInfo = dict()  #line num of target grid cell : [reach index, segment index] for that line
    while 1:  #loop over each line in the .Spat file
        line = f.readline().rstrip("\n")
        totalSegmentNum = totalSegmentNum + 1  # current line number
        if line=="": break
        lineSplit = line.split()
        (lat,lon) = (float(lineSplit[4]),float(lineSplit[5]))
        if (lat,lon) in tgtCellLatLongs: #line is for one of target grid cells
            if totalSegmentNum != numTotalSegments: #if not segment 2 in outlet cell (no data)
                (reachIndex,segmentIndex) = (int(lineSplit[0]),int(lineSplit[6]))  #seg = 1 or 2; reach varies
                cellInfo[totalSegmentNum] = [reachIndex,segmentIndex]
                if totalSegmentNum not in mapSegmentNumToLatLong:
                    mapSegmentNumToLatLong[totalSegmentNum] = (lat,lon)
                    if (lat,lon) in mapLatLongToSegmentNum: 
                        mapLatLongToSegmentNum[(lat,lon)].append(totalSegmentNum)
                    else:
                        mapLatLongToSegmentNum[(lat,lon)] = [totalSegmentNum]
    f.close()
    return (cellInfo,mapSegmentNumToLatLong,mapLatLongToSegmentNum)

###### READ CELL TEMPERATURE DATA ##############################################
#Temperature data: hour 1, all cells + segments + reaches, then hour 2, all cells + segments + reaches, etc.
def readCellTemperatureData(dataDir,tempAndSpatFilename,cellInfo,numTotalSegments,outputHeaders):
    tempFile = os.path.join(dataDir,tempAndSpatFilename + '.Temp')  # .Temp file
    allSegmentData = {} #total segment number (=line #in .spat file): np array of year, month, day, flow(cfs), streamTemp(degC).
    for totalSegmentNum in cellInfo: allSegmentData[totalSegmentNum] = [] #initialize b/c adding to lists in dict later
    waterTAllSegments = {} #store just water T for each segment
    for totalSegmentNum in cellInfo: waterTAllSegments[totalSegmentNum] = dict()
    f = open(tempFile, 'r')
    lineCtr = 0
    while 1:  # loop over each line in the .Temp file
        tempLineRaw = f.readline().rstrip("\n")
        lineCtr = lineCtr + 1
        if tempLineRaw=="": break
        totalSegmentNum = lineCtr%numTotalSegments  # corresponding line number in the .Spat file
        if totalSegmentNum in cellInfo:
            (tLineData,year,month,day,waterT) = processRawTemperatureLineData(tempLineRaw,outputHeaders)
            #Save entire line of segment data
            allSegmentData[totalSegmentNum].append(tLineData)    
            #Save just water T data of segment into nested dictionary - total segment number: date : waterT
            waterTAllSegments[totalSegmentNum][createDateLabel(year,month,day)] = waterT
    f.close()
    for i in allSegmentData: allSegmentData[i] = np.asarray(allSegmentData[i])
    return (allSegmentData,waterTAllSegments)

def processRawTemperatureLineData(tempLineRaw,outputHeaders):
    (tDataDict,year,month,day,waterT) = readRawTemperatureLineData(tempLineRaw)
    tLineData = processTempDataDictIntoRow(tDataDict,outputHeaders)
    return (tLineData,year,month,day,waterT)

def readRawTemperatureLineData(tempLineRaw):
    lineSplit = tempLineRaw.split()
    decimal_year = lineSplit[0]
    year = int(decimal_year.split('.')[0])
    day_of_year = int(lineSplit[1])
    if day_of_year > 360 and float('0.'+decimal_year.split('.')[1]) <= 0.005:  # correct bad decimal year integer part
        year = year - 1
    date = dt.datetime(year, 1, 1) + dt.timedelta(days=day_of_year-1)  # convert day of year to date
    flow = float(lineSplit[8])
    streamT = float(lineSplit[5])
    headwaterT = float(lineSplit[6])
    airT = float(lineSplit[7])
    tDataDict = {'year':year,'month':date.month,'day':date.day,'flow':flow,'streamT':streamT,
                'headwaterT':headwaterT,'airT':airT}
    return (tDataDict,year,date.month,date.day,streamT)

def processTempDataDictIntoRow(tempDataDict,outputHeaders):
    tLineData = ['']*len(outputHeaders)
    (yearCol,monthCol,dayCol,flowCol,streamTCol,headTCol,airTCol) = getDataColNums(outputHeaders)
    tLineData[yearCol] = tempDataDict['year']
    tLineData[monthCol] = tempDataDict['month']
    tLineData[dayCol] = tempDataDict['day']
    tLineData[flowCol] = tempDataDict['flow']
    tLineData[streamTCol] = tempDataDict['streamT']
    tLineData[headTCol] = tempDataDict['headwaterT']
    tLineData[airTCol] = tempDataDict['airT']
    return tLineData

def getDataColNums(cols):
    (yearCol,monthCol,dayCol,flowCol,streamTCol,headTCol,airTCol) = (cols.index('Year'),
                cols.index('Month'),cols.index('Day'),cols.index('Streamflow(cfs)'),
                cols.index('StreamT(degC)'),cols.index('HeadwaterT(degC)'),cols.index('AirT(degC)'))
    return (yearCol,monthCol,dayCol,flowCol,streamTCol,headTCol,airTCol)

def createDateLabel(year,month,day):
    return '%s-%s-%s' %(year,month,day)

###### WRITE CELL TEMPERATURE DATA ##############################################
def writeCellTemperatureData(allSegmentData,cellInfo,outputDirs,locPrecision,numDays,
                             outputHeaders,mapSegmentNumToLatLong):
    for totalSegmentNum in cellInfo:
        (cellLat,cellLong) = mapSegmentNumToLatLong[totalSegmentNum]
        outputDir = outputDirs[(cellLat,cellLong)]
        baseFilename = createBaseFilenameToReadOrWrite(locPrecision, cellLat, cellLong)
        fullFilename = baseFilename + '_reach%d_seg%d' %(cellInfo[totalSegmentNum][0], cellInfo[totalSegmentNum][1])
        fullFilePath = os.path.join(outputDir,fullFilename)
        f = open(fullFilePath, 'w')
        f.write(createHeaderStr(outputHeaders))
        dataCurr = allSegmentData[totalSegmentNum]
        for i in range(numDays):
            f.write('%d %d %d %.1f %.2f %.2f %.2f\n' %(dataCurr[i,0], dataCurr[i,1], dataCurr[i,2], 
                                                    dataCurr[i,3], dataCurr[i,4], dataCurr[i,5], dataCurr[i,6]))
        f.close()

def createBaseFilenameToReadOrWrite(locPrecision, inputLat, inputLong):
    return '%.*f_%.*f' %(locPrecision, inputLat, locPrecision, inputLong)

def createHeaderStr(outputHeaders):
    headStr = ''
    for idx in range(len(outputHeaders)):
        headStr += outputHeaders[idx]
        if outputHeaders[idx]!=outputHeaders[-1]: headStr += ' ' #not last header
    return headStr + '\n'

###### AVERAGE AND SAVE CELL TEMPERATURE DATA ##################################
def averageAndSaveWaterTOverAllSegmentsInCells(waterTAllSegments,outputDirs,locPrecision,
                                                mapLatLongToSegmentNum,mapSegmentNumToLatLong):
    for (cellLat,cellLon) in mapLatLongToSegmentNum:
        currCellSegmentNums = mapLatLongToSegmentNum[(cellLat,cellLon)]
        waterTAllSegmentsInCell = isolateWaterTDataForCell(waterTAllSegments,currCellSegmentNums)
        waterTAvgInCell = averageWaterTOverAllSegmentsInCell(waterTAllSegmentsInCell )
        sortedAvgWaterT2dList = convertAvgWaterTTo2dList(waterTAvgInCell)
        verticalSortedAvgWaterT2dList = flip2dList(sortedAvgWaterT2dList)
        outputDir = outputDirs[(cellLat,cellLon)]
        saveAverageWaterT(verticalSortedAvgWaterT2dList,outputDir, locPrecision, cellLat, cellLon)

def isolateWaterTDataForCell(waterTAllSegments,currCellSegmentNums):
    waterTAllSegmentsInCell = dict()
    for segmentNum in currCellSegmentNums:
        waterTAllSegmentsInCell[segmentNum] = waterTAllSegments[segmentNum]
    return waterTAllSegmentsInCell

def averageWaterTOverAllSegmentsInCell(waterTAllSegments):
    waterTSums = dict()
    for segment in waterTAllSegments:
        waterTSegment = waterTAllSegments[segment]
        for date in waterTSegment:
            waterTSums[date] = waterTSums.get(date,0) + waterTSegment[date]
    waterTAvgInCell = dict()
    numSegments = len(waterTAllSegments)
    for date in waterTSums: waterTAvgInCell[date] = waterTSums[date]/numSegments
    return waterTAvgInCell

def convertAvgWaterTTo2dList(waterTAvgInCell):
    sortedAvgWaterT2dList = []
    sortedDatesList = createDatesList(waterTAvgInCell)
    sortedAvgWaterT2dList.append(['Datetime'] + sortedDatesList)
    waterTAvgList = ['AverageWaterT(degC)'] + convertWaterTDictToSortedList(sortedDatesList,waterTAvgInCell)
    sortedAvgWaterT2dList.append(waterTAvgList)
    return sortedAvgWaterT2dList

#Outputs sorted list of datetimes
def createDatesList(waterTAvgInCell):
    datesList = []
    for listDate in waterTAvgInCell:
        (year,month,day) = getElementsOfDate(listDate)
        dateAsDatetime = dt.date(year,month,day)
        datesList.append(dateAsDatetime)
    return sorted(datesList)

def getElementsOfDate(listDate):
    year = int(listDate[:4])
    restOfDate = listDate[5:]
    monthEndIdx = restOfDate.index('-')
    month = int(restOfDate[:monthEndIdx])
    day = int(restOfDate[monthEndIdx+1:])
    return (year,month,day)

def convertWaterTDictToSortedList(sortedDatesList,waterTDict):
    waterTDates = ['']*len(sortedDatesList)
    for listDate in waterTDict:
        (year,month,day) = getElementsOfDate(listDate)
        dateAsDatetime = dt.date(year,month,day)
        waterTDates[sortedDatesList.index(dateAsDatetime)] = waterTDict[listDate]
    return waterTDates

def flip2dList(list2d):
    flippedList = []
    for colIdx in range(len(list2d[0])):
        newList = []
        for rowIdx in range(len(list2d)):
            newList.append(list2d[rowIdx][colIdx])
        flippedList.append(newList)
    return flippedList

def saveAverageWaterT(waterTAvgs2dList,outputDir,locPrecision,inputLat,inputLong):
    filenameToSave = createAverageTFilename(locPrecision,inputLat,inputLong)
    write2dListToCSV(waterTAvgs2dList,os.path.join(outputDir,filenameToSave))

def createAverageTFilename(locPrecision,inputLat,inputLong):
    baseFilename = createBaseFilenameToReadOrWrite(locPrecision,inputLat,inputLong)
    return baseFilename + 'Average.csv'
################################################################################
################################################################################
################################################################################

################################################################################
####### MAP GENERATORS TO AND FROM RBM GRID CELLS  #############################
################################################################################
def getGenToCellAndCellToGenDictionaries(genFleet):
    (fleetLatCol,fleetLongCol) = (genFleet[0].index('Latitude'),genFleet[0].index('Longitude'))
    genToCellLatLongsDictValues = [['ORIS+UnitID','GenLat,GenLong','CellLat,CellLong']]
    genToCellLatLongsList = copy.deepcopy(genToCellLatLongsDictValues)
    genToCellLatLongsDict = dict()
    cellLatLongToGenDict = dict()
    for row in genFleet[1:]:
        genID = createGenSymbol(row,genFleet[0])
        (genLat,genLong) = (row[fleetLatCol],row[fleetLongCol])
        cellLoc = 'NA'
        if genLat != 'NA' and genLat != '': 
            cellLoc = find125GridMaurerLatLong(float(genLat),float(genLong))
            if cellLoc in cellLatLongToGenDict:
                cellLatLongToGenDict[cellLoc].append(genID)
            else:
                cellLatLongToGenDict[cellLoc] = [genID]
        genToCellLatLongsDict[genID] = [genID,(genLat,genLong),cellLoc]
        genToCellLatLongsList.append([genID,(genLat,genLong),cellLoc])
    return (genToCellLatLongsDictValues,genToCellLatLongsDict,cellLatLongToGenDict,
            genToCellLatLongsList)   

def createGenSymbol(row,headers):
    (orisCol,unitCol) = (headers.index('ORIS Plant Code'),headers.index('Unit ID'))
    return str(row[orisCol]) + '+' + row[unitCol]        

def separateGenSymbol(genSymbol):
    separatorIdx = genSymbol.index('+')
    return (genSymbol[:separatorIdx],genSymbol[separatorIdx+1:])

#Get (lat,lon) of 1/8 grid cell that a (lat, lon) point falls in
def find125GridMaurerLatLong(lat, lon):
   lat_grid = np.around(8.0*lat-0.5)/8.0 + 0.0625
   lon_grid = np.around(8.0*lon-0.5)/8.0 + 0.0625
   return (lat_grid, lon_grid)
################################################################################
################################################################################
################################################################################

################################################################################
####### CURTAIL GENERATOR CAPACITY WITH WATER TEMPERATURES #####################
################################################################################
def calculateGeneratorCurtailments(genToCellLatLongsDictValues,genToCellLatLongsDict,
                                    cellLatLongToGenDict,rbmOutputDir,locPrecision,
                                    curtailmentYear,genFleet,modelName):
    dailyCurtailmentsAllGensInTgtYr = dict()
    dailyCurtailmentsList = []
    plantTypesForCurtailment = definePlantTypesForCurtailment()
    for (cellLat,cellLong) in cellLatLongToGenDict:
        #Load cell's avg water T data (2d list of Y-M-D, water T (vertical)); returns None if no cell data
        cellTemperature = loadCellAvgWaterT(cellLat,cellLong,rbmOutputDir,locPrecision) 
        gensInCell = cellLatLongToGenDict[(cellLat,cellLong)] #list of ORIS-UNITID in cell
        (datesInCurtailYear,tInCurtailYear) = getDatesAndTempsInCurtailmentYear(cellTemperature,
                                                                                curtailmentYear)
        for gen in gensInCell:
            (plantType,hr,fuelAndCoalType,coolType,fgdType) = getKeyCurtailParams(gen,genFleet)
            plantCurtailReg = loadRegressionForPlant(plantType,hr,fuelAndCoalType,coolType,
                                                    fgdType,plantTypesForCurtailment)
            (dailyCurtailmentsGen,dailyCurtailmentVals) = calcCurtailmentForGen(datesInCurtailYear,
                                                         tInCurtailYear,plantCurtailReg)
            dailyCurtailmentsAllGensInTgtYr[gen] = dailyCurtailmentsGen
            dailyCurtailmentsList.append([gen] + dailyCurtailmentVals)
    write2dListToCSV(dailyCurtailmentsList,'curtailmentsDailyAllGens' + modelName + str(curtailmentYear) + '.csv')
    return dailyCurtailmentsAllGensInTgtYr

###### DEFINE PLANT TYPES THAT CAN BE THERMALLY CURTAILED ######################
def definePlantTypesForCurtailment():
    return {'Coal Steam','Combined Cycle','Coal Steam CCS','Combined Cycle CCS'}

###### LOAD WATER T AND METEOROLOGICAL VARIABLES ###############################
def loadCellAvgWaterT(cellLat,cellLong,rbmOutputDir,locPrecision):
    cellFoldername = createBaseFilenameToReadOrWrite(locPrecision,cellLat,cellLong)
    cellFolder = os.path.join(rbmOutputDir,cellFoldername)
    allCellFolders = os.listdir(rbmOutputDir)
    if cellFoldername in allCellFolders:
        averageTFilename = createAverageTFilename(locPrecision,cellLat,cellLong)
        cellTemperature = readCSVto2dList(os.path.join(cellFolder,averageTFilename))
    else:
        cellTemperature = loadDummyWaterTData(rbmOutputDir,allCellFolders,locPrecision)
    return cellTemperature 

#If no water T data for cell, then load fake dataset and replace all water Ts
#with 2 so no curtailment
def loadDummyWaterTData(rbmOutputDir,allCellFolders,locPrecision):
    fakeWaterT = 2
    dummyFolder = allCellFolders[0]
    (cellLat,cellLong) = getCellLatAndLongFromFolderName(dummyFolder)
    averageTFilename = createAverageTFilename(locPrecision,cellLat,cellLong)
    dummyCellT = readCSVto2dList(os.path.join(rbmOutputDir,dummyFolder,averageTFilename))
    (dateCol,waterTCol) = (dummyCellT[0].index('Datetime'),dummyCellT[0].index('AverageWaterT(degC)'))
    for row in dummyCellT[1:]: row[waterTCol] = fakeWaterT
    return dummyCellT

def getCellLatAndLongFromFolderName(dummyFolder):
    dividerIdx = dummyFolder.index('_')
    return (float(dummyFolder[:dividerIdx]),float(dummyFolder[dividerIdx+1:]))

###### ISOLATE DATA FOR YEAR OF ANALYSIS #######################################
def getDatesAndTempsInCurtailmentYear(cellTemperature,curtailmentYear):
    (dateCol,waterTCol) = (cellTemperature[0].index('Datetime'),cellTemperature[0].index('AverageWaterT(degC)'))
    rowsInCurtailmentYear = [row for row in cellTemperature[1:] 
                            if int(getElementsOfDate(row[dateCol])[0])==curtailmentYear] #skip header row
    datesInCurtailmentYear = [row[dateCol] for row in rowsInCurtailmentYear]
    temperaturesInCurtailmentYear = [float(row[waterTCol]) for row in rowsInCurtailmentYear]
    return (datesInCurtailmentYear,temperaturesInCurtailmentYear)

###### GET KEY PARAMETERS FOR CURTAILMENT ######################################
#Parameters that affect curtailment: coal steam vs NGCC, bit vs. subbit vs. lignite,
#HR, once through vs. recirc vs. dry cooling, wet FGD vs. lime spray dryer
def getKeyCurtailParams(gen,genFleet):
    genRow = getGenRowInFleet(gen,genFleet)
    heads = genFleet[0]
    (plantTypeCol,hrCol,coalTypeCol,coolTypeCol,so2ControlCol) = (heads.index('PlantType'),
                    heads.index('Heat Rate (Btu/kWh)'),heads.index('Modeled Fuels'),
                    heads.index('Cooling Tech'),heads.index('Wet/DryScrubber'))
    (plantType,hr) = (genRow[plantTypeCol],genRow[hrCol])
    fuelAndCoalType = isolateFirstFuelType(genRow[coalTypeCol])
    coolType = getCoolType(genRow[coolTypeCol])
    fgdType = getSO2Control(genRow[so2ControlCol])
    return (plantType,hr,fuelAndCoalType,coolType,fgdType)

def getGenRowInFleet(gen,genFleet):
    (orisID,unitID) = separateGenSymbol(gen)
    (orisCol,unitIdCol) =  (genFleet[0].index('ORIS Plant Code'),genFleet[0].index('Unit ID')) 
    # print('gen fleet:',gen,genFleet)
    return [row for row in genFleet if str(row[orisCol]) == orisID and row[unitIdCol] == unitID][0] #return 1d list

def isolateFirstFuelType(fuel):
    multiFuelDivider = '&' #some plants have multiple modeled fuels divided by &
    if multiFuelDivider in fuel: fuel = fuel[:fuel.index(multiFuelDivider)]
    return fuel

def getCoolType(coolingType):
    possibleCoolingTypes = ['once through','dry cooling','recirculating']
    finalCoolType = 'NA'
    for possibleCoolingType in possibleCoolingTypes:
        if possibleCoolingType in coolingType: finalCoolType = possibleCoolingType
    return finalCoolType
    
def getSO2Control(so2Control):
    possibleFGDTypes = ['wet','dry']
    fgdType = 'NA'
    for possibleFGDType in possibleFGDTypes:
        if possibleFGDType in so2Control.lower(): fgdType = possibleFGDType
    return fgdType

###### LOAD CURTAILMENT REGRESSION FOR PLANT ###################################
#If plant not eligible for curtailment (e.g., wind), assume no curtailment.
def loadRegressionForPlant(plantType,hr,fuelAndCoalType,coolType,fgdType,plantTypesForCurtailment):
    if plantType in plantTypesForCurtailment:
        plantReg = loadPlantReg(plantType,hr,fuelAndCoalType,coolType,fgdType)
    else:
        plantReg = 0
    return plantReg

def loadPlantReg(plantType,hr,fuelAndCoalType,coolType,fgdType):
    return 1

###### CALCULATE DAILY CURTAILMENTS FOR 1 GENERATOR ############################
def calcCurtailmentForGen(datesInCurtailYear,tInCurtailYear,plantCurtailReg):
    dailyCurtailmentVals = [calcCurtailment(waterT,plantCurtailReg) for waterT in tInCurtailYear]
    dailyCurtailmentsGen = [['Datetime','Curtailment(MW)']] 
    dailyCurtailmentsGen += [[datesInCurtailYear[idx],dailyCurtailmentVals[idx]] for idx in range(len(dailyCurtailmentVals))]
    return (dailyCurtailmentsGen,dailyCurtailmentVals)

def calcCurtailment(waterT,plantCurtailReg):    
    return waterT*plantCurtailReg

################################################################################
################################################################################
################################################################################

################################################################################
####### TEST FUNCTIONS #########################################################
################################################################################
def testFlip2dList():
    print('testing flip2d list')
    assert(flip2dList([[3,4,9],[1,2,3]]) == [[3,1],[4,2],[9,3]])
    assert(flip2dList([[3,4,9]]) == [[3],[4],[9]])
    print('passed')

def testFunctions():
    testFlip2dList()

# testFunctions()
################################################################################
################################################################################
################################################################################