#Michael Craig, 6 July 2016
#Get wind and solar capacity factors

#INPUTS: generator fleet, states and state abbreviations for analysis,
#whether to get state- or region-specific CFs (e.g., for wind farm in PA,
#whether to select CF for best plant in PA or across all states of analysis),
#and the starting capacity at which to get CFs from CF dataset 
#(setting this value to 0 selects best plants first, and setting it to a higher
#value will exclude best plants until the input starting capacity is met 
#(used for getting CFs for marginal renewables in CE analysis)).

#OUTPUTS: 2d list w/ hourly capacity factors for year, and list of plant IDs 
#and capacities that CF data is for. 

import os, copy, datetime
from AuxFuncs import *

################################################################################
####### GET RENEWABLE CAPACITY FACTORS #########################################
################################################################################
def getRenewableCFs(genFleet,startWindCapacForCFs,startSolarCapacForCFs,states,
        statesAbbrev,matchStateOrRegion,desiredTz,projectName,runLoc,windGenDataYr):
    #Isolate wind & solar units
    plantTypeCol = genFleet[0].index('PlantType')
    windUnits = [genFleet[0]] + [row for row in genFleet if row[plantTypeCol]=='Wind']
    solarUnits = [genFleet[0]] + [row for row in genFleet if row[plantTypeCol]=='Solar PV']
    #Get list of wind / solar sites in region
    if runLoc == 'pc': 
        databaseDir = 'C:\\Users\\mtcraig\\Desktop\\EPP Research\\Databases'
        if projectName == 'storage':
            windDir = os.path.join(databaseDir,'Eastern Wind Dataset Texas')
            solarDir = os.path.join(databaseDir,'NRELSolarPVDataTX')
        elif projectName == 'rips':
            windDir = os.path.join(databaseDir,'Eastern Wind Dataset')
            solarDir = os.path.join(databaseDir,'NRELSolarPVData\\SERC')
    else:
        windDir = os.path.join('Data','Eastern Wind Dataset Texas')
        solarDir = os.path.join('Data','NRELSolarPVDataTX')
    (windCFs,windCfsDtHr,windCfsDtSubhr,ewdIdAndCapac) = getWindCFs(windUnits,windDir,
        startWindCapacForCFs,states,statesAbbrev,matchStateOrRegion,desiredTz,windGenDataYr)
    (solarCFs,solarCfsDtHr,solarCfsDtSubhr,solarFilenameAndCapac) = getSolarCFs(solarUnits,solarDir,
        startSolarCapacForCFs,states,statesAbbrev,matchStateOrRegion,desiredTz)
    return (windCFs,rotate(windCfsDtHr),rotate(windCfsDtSubhr),ewdIdAndCapac,
            solarCFs,rotate(solarCfsDtHr),rotate(solarCfsDtSubhr),solarFilenameAndCapac)

##### WIND CFS #####
#All CFs output in EST
def getWindCFs(windUnits,windDir,startWindCapacForCFs,states,statesAbbrev,
                matchStateOrRegion,desiredTz,windGenDataYr):
    #Get total wind capacity by state
    capacCol = windUnits[0].index('Capacity (MW)')
    stateCol = windUnits[0].index('State Name')
    windCapacByState = getCapacsByState(windUnits[1:],capacCol,stateCol)
    #Get wind plants in Eastern Wind Dataset per state until capacity met
    (ewdIdsToStates,ewdIdAndCapac,ewdMetadata) = getBestWindIdsInStates(windDir,windCapacByState,
                                    startWindCapacForCFs,states,statesAbbrev,matchStateOrRegion)
    #Import CFs for each wind plant
    allSiteCfsHourly,allSiteCfsSubhourly,avgFleetCfHr = [],[],[]
    idCol = ewdIdAndCapac[0].index('Id')
    datasetCapacCol = ewdIdAndCapac[0].index('DatasetCapacity')
    for site in ewdIdAndCapac[1:]:
        (siteId,datasetCapac) = (site[idCol],site[datasetCapacCol])
        if 'NoMoreSites' in siteId:
            print('no more sites!')
            if avgFleetCfHr == []: 
                #If doing new RE CFs & existing RE > potential RE capac for CFs,
                #can end up w/ nothing in allSiteCFs. In that case, new RE CFs
                #should jsut be fleet average CF.
                if allSiteCfsHourly == []:  
                    a,tempAllSiteCfsHourly,tempAllSiteCfsSubhourly,tempEwdIdAndCapac = getWindCFs(windUnits,
                                    windDir,0,states,statesAbbrev,matchStateOrRegion,desiredTz,windGenDataYr) 
                    avgFleetCfHr,avgFleetCfSubhr = calcCapacWtdFleetCf(tempEwdIdAndCapac,
                                                            tempAllSiteCfsHourly,tempAllSiteCfsSubhourly)
                else:
                    avgFleetCfHr,avgFleetCfSubhr = calcCapacWtdFleetCf(ewdIdAndCapac,
                                                            allSiteCfsHourly,allSiteCfsSubhourly)
            siteCfsHourly,siteCfsSubhourly = copy.deepcopy(avgFleetCfHr),copy.deepcopy(avgFleetCfSubhr)
        else:
            siteCfsHourly,siteCfsSubhourly = getWindSiteCfs(windDir,siteId,datasetCapac,desiredTz,windGenDataYr)
        addSiteCfsToAggList(siteCfsHourly,siteCfsSubhourly,allSiteCfsHourly,allSiteCfsSubhourly,siteId)
    allSiteCfsHourOfYear = [['HourOfYear'] + [val for val in range(1,8761)]] + copy.deepcopy(allSiteCfsHourly[1:])
    return (allSiteCfsHourOfYear,allSiteCfsHourly,allSiteCfsSubhourly,ewdIdAndCapac)

def addSiteCfsToAggList(siteCfsHourly,siteCfsSubhourly,allSiteCfsHourly,allSiteCfsSubhourly,siteId):
    if allSiteCfsHourly == []:
        allSiteCfsHourly.append(siteCfsHourly[0])
        allSiteCfsHourly.append([siteId] + siteCfsHourly[1][1:]) #replace header w/ site ID
        allSiteCfsSubhourly.append(siteCfsSubhourly[0])
        allSiteCfsSubhourly.append([siteId] + siteCfsSubhourly[1][1:])
    else:
        allSiteCfsHourly.append([siteId] + siteCfsHourly[1][1:]) #replace header w/ site ID
        allSiteCfsSubhourly.append([siteId] + siteCfsSubhourly[1][1:])

def getBestWindIdsInStates(windDir,windCapacByState,startWindCapacForCFs,states,
                            statesAbbrev,matchStateOrRegion):
    ewdMetadataFilename = os.path.join(windDir,'eastern_wind_dataset_site_summary.csv')
    ewdMetadata = readCSVto2dList(ewdMetadataFilename)
    ewdStateCol = ewdMetadata[0].index('State')
    ewdCfCol = ewdMetadata[0].index('NET_CF')
    ewdCapacCol = ewdMetadata[0].index('Capacity (MW)')
    ewdSiteNumberCol = ewdMetadata[0].index('SiteNumber')
    (ewdIdsToState,ewdIdAndCapac) = getWindOrSolarIdsInStatesDecreasingCF(ewdMetadata,
                                          windCapacByState,ewdStateCol,
                                          ewdCfCol,ewdCapacCol,ewdSiteNumberCol,
                                          startWindCapacForCFs,states,statesAbbrev,
                                          matchStateOrRegion)
    return (ewdIdsToState,ewdIdAndCapac,ewdMetadata)

def getWindOrSolarIdsInStatesDecreasingCF(metadata,capacByState,stateCol,
                                          cfCol,capacCol,siteNumberOrFileCol,
                                          startRECapacForCFs,states,statesAbbrev,
                                          matchStateOrRegion):
    idsToState = dict()
    idAndCapacs = [['Id','DatasetCapacity','FleetCapacity']]
    if matchStateOrRegion == 'region':
        (cfs,capacs,siteNumbers) = getPlantInfoInStateOrRegion(metadata,stateCol,states,
                                                statesAbbrev,startRECapacForCFs,matchStateOrRegion,
                                                cfCol,capacCol,siteNumberOrFileCol)
    for state in capacByState:
        currStateCapac = 0
        if matchStateOrRegion == 'state':
            (cfs,capacs,siteNumbers) = getPlantInfoInStateOrRegion(metadata,stateCol,states,
                                        statesAbbrev,startRECapacForCFs,matchStateOrRegion,
                                        cfCol,capacCol,siteNumberOrFileCol,state)
        idsToState[state]=[]
        while currStateCapac < capacByState[state]:
            if len(cfs)==0:
                fleetCapac = capacByState[state] - currStateCapac
                siteName = 'NoMoreSites' + state
                idsToState[state].append(siteName)
                idAndCapacs.append([siteName,fleetCapac,fleetCapac])
                currStateCapac += fleetCapac
            else:
                maxCfIdx = cfs.index(max(cfs))
                if cfs[maxCfIdx]>1E-3: #some solar sites have 0 CF!
                    datasetCapac = capacs[maxCfIdx]
                    #Trim capacity if unit capacity > spare capacity before reach state capac - capac when start saving CFs
                    fleetCapac = min(datasetCapac,capacByState[state]-currStateCapac)
                    if currStateCapac<startRECapacForCFs and currStateCapac+fleetCapac>=startRECapacForCFs:
                        fleetCapac = startRECapacForCFs - currStateCapac
                    currStateCapac += fleetCapac
                    if currStateCapac>startRECapacForCFs:
                        idsToState[state].append(siteNumbers[maxCfIdx])
                        idAndCapacs.append([siteNumbers[maxCfIdx],datasetCapac,fleetCapac])                    
                cfs.pop(maxCfIdx)
                capacs.pop(maxCfIdx)
                siteNumbers.pop(maxCfIdx)
    return (idsToState,idAndCapacs)

def getPlantInfoInStateOrRegion(metadata,stateCol,states,statesAbbrev,startRECapacForCFs,
                            matchStateOrRegion,cfCol,capacCol,siteNumberOrFileCol,*args):
    if len(args)>0: 
        state = args[0]
        plantsInStateOrRegion = [row for row in metadata[1:] if (row[stateCol]==state or
                row[stateCol]==STATEABBREVS[state])]
    else:
        plantsInStateOrRegion = [row for row in metadata[1:] if (row[stateCol] in states or
                row[stateCol] in statesAbbrev)]
    cfs = [float(row[cfCol]) for row in plantsInStateOrRegion]
    capacs = [float(row[capacCol]) for row in plantsInStateOrRegion]
    siteNumbers = [row[siteNumberOrFileCol] for row in plantsInStateOrRegion]
    return (cfs,capacs,siteNumbers)

def calcCapacWtdFleetCf(idAndCapac,siteCfsHr,siteCfsSubhr):
    fleetCapacCol = idAndCapac[0].index('FleetCapacity')
    idToFleetCapac = getFleetToCapacDict(idAndCapac)
    capacWtdCfsHr = calcCapacWtdFleetCfHrOrSubhr(idToFleetCapac,siteCfsHr)
    capacWtdCfsSubhr = calcCapacWtdFleetCfHrOrSubhr(idToFleetCapac,siteCfsSubhr)
    return capacWtdCfsHr,capacWtdCfsSubhr

def getFleetToCapacDict(idAndCapac):
    idCol = idAndCapac[0].index('Id')
    fleetCapacCol = idAndCapac[0].index('FleetCapacity')
    idToFleetCapac = dict()
    for row in idAndCapac[1:]:
        idToFleetCapac[row[idCol]] = row[fleetCapacCol]
    return idToFleetCapac

def calcCapacWtdFleetCfHrOrSubhr(idToFleetCapac,siteCfs):
    (totalCapac,totalGen) = (0,[])
    for row in siteCfs[1:]:
        (currId,currCfs) = (row[0],row[1:])
        currCapac = idToFleetCapac[currId]
        totalCapac += currCapac
        gens = [val*currCapac for val in currCfs]
        if totalGen == []: totalGen = copy.copy(gens)
        else: totalGen = [totalGen[idx] + gens[idx] for idx in range(len(gens))]
    capacWtdCfs = [copy.deepcopy(siteCfs[0])]
    capacWtdCfs.append(['AnnualAvgCf'] + [val/totalCapac for val in totalGen])
    return capacWtdCfs

#Inputs: dir w/ wind data, site ID to get gen data for, wind site capac,
#desired timezone, year for wind gen data
#Outputs: 2 2d lists, both have first row = datetime. 1 2d list = hourly 
#CFs, 2nd 2d list = subhourly CFs. Also row labels
def getWindSiteCfs(windDir,siteId,siteCapac,desiredTz,windGenDataYr):
    numDigitsInFilename = 5
    genFilename = 'SITE_' + ('0' * (numDigitsInFilename - len(siteId))) + siteId + '.csv'
    genData = readCSVto2dList(os.path.join(windDir,genFilename))
    genData[0:2] = [] #delete first 2 rows - useless metadata
    datetimeAndGen = convertTimeToDatetimeInTgtTz(genData,'wind',siteId,desiredTz,'UTC')
    datetimeAndGenInYr = [datetimeAndGen[0]] + [row for row in datetimeAndGen[1:] 
                                                if row[0].year == windGenDataYr]
    datetimeAndGenInYrHourly = convertGenToHourly(datetimeAndGenInYr)
    subhourlyCfs = convertToCfs(datetimeAndGenInYr,siteCapac)
    hourlyCfs = convertToCfs(datetimeAndGenInYrHourly,siteCapac)
    return hourlyCfs,subhourlyCfs

#Converts datetimes to CST
#Inputs: gen data (2d list w/ datetime in col 1 and gen data in col 2), 
#whether processing wind or solar gen data, and site ID or filename
#Outputs: 2d list w/ gen data (datetime in col 1, gen data in col 2)
def convertTimeToDatetimeInTgtTz(genData,windOrSolar,siteOrFilename,tgtTz,siteTz):
    datetimeAndGen = [['datetimeCST','power(MW)' + siteOrFilename]]
    tzOffsetDict = {'UTCtoCST':-6,'CSTtoCST':0,'ESTtoCST':-1,'CSTtoEST':1,'UTCtoEST':-5}
    timezoneOffset = tzOffsetDict[siteTz+'to'+tgtTz]
    if windOrSolar == 'wind':
        dateCol = genData[0].index('DATE')
        timeCol = genData[0].index('TIME(UTC)')
        genCol = genData[0].index('NETPOWER(MW)')
    elif windOrSolar == 'solar':
        dateAndTimeCol = genData[0].index('LocalTime')
        genCol = genData[0].index('Power(MW)')
    for row in genData[1:]:
        if windOrSolar == 'wind': 
            year,month,day = divideWindDate(row[dateCol])
            hour,minute = divideWindTime(row[timeCol])
        else: 
            year,month,day,hour,minute = divideSolarDatetime(row[dateAndTimeCol])
        rowDatetime = datetime.datetime(year,month,day,hour,minute)
        rowDatetimeCST = rowDatetime + datetime.timedelta(hours=timezoneOffset)
        datetimeAndGen.append([rowDatetimeCST,float(row[genCol])])
    return datetimeAndGen

#Return year, month, day from date in wind gen data
def divideWindDate(windDate):
    return int(windDate[0:4]),int(windDate[4:6]),int(windDate[6:])

#Return hour,minute from time in wind gen data
def divideWindTime(windTime):
    if len(windTime) < 3: return 0,int(windTime)
    else: return int(windTime[:-2]),int(windTime[-2:])

#Return year,month,day,hour,minute from datetime in solar gen data
def divideSolarDatetime(solarDatetime):
    baseYear = 2000 #solar year is given as '06', so add 2000
    solarDate,solarTime = solarDatetime.split(' ')
    solarDateSplit = solarDate.split('/')
    solarTimeSplit = solarTime.split(':')
    return (baseYear+int(solarDateSplit[2]),int(solarDateSplit[0]),int(solarDateSplit[1]),
            int(solarTimeSplit[0]),int(solarTimeSplit[1]))

#Converts subhourly to hourly gen by counting # of power output entires for each 
#hour and generator, then averaging them together.
#Inputs: subhourly (10 or 5 min) power output (2d list, col 1 = datetime CST, 
#col 2 = gen)
#Outputs: average hourly gen *2d list, col 1 = datetime CST,
#col 2 = average hourly gen for each gen).
def convertGenToHourly(genSubhourly):
    datetimeCol = genSubhourly[0].index('datetimeCST')
    hourlyGen = [copy.deepcopy(genSubhourly[0])]
    countGen = [copy.deepcopy(genSubhourly[0])]
    hourlyGenAverage = [copy.deepcopy(genSubhourly[0])]
    dtHourToRowDict = dict()
    lastRowDtToHour = datetime.datetime(1980,1,1,1,1) #random datetime
    for row in genSubhourly[1:]:
        rowDt = row[datetimeCol]
        rowDtToHour = datetime.datetime(rowDt.year,rowDt.month,rowDt.day,rowDt.hour,0)
        if rowDtToHour == lastRowDtToHour:
            hourlyGen[-1][1] += row[1]
            countGen[-1][1] += 1
        else:
            hourlyGen.append([rowDtToHour] + [row[1]])
            countGen.append([rowDtToHour] + [1])
        lastRowDtToHour = rowDtToHour
    for idx in range(1,len(hourlyGen)):
        hourlyGenAverage.append([hourlyGen[idx][datetimeCol],hourlyGen[idx][1]/countGen[idx][1]])
    return hourlyGenAverage

#Inputs: 2d list (datetime 1st col, gen 2nd col, w/ headers), capacity of curr wind gen
#Outputs: 2d list (datetime first row, gen 2nd row, w/ labels)
def convertToCfs(datetimeAndGen,siteCapac):
    dateCol,genCol = 0,1
    dateInfoHoriz = [row[dateCol] for row in datetimeAndGen]
    cfsHoriz = [datetimeAndGen[0][genCol]] + [float(row[genCol])/siteCapac for row in datetimeAndGen[1:]]
    return [dateInfoHoriz,cfsHoriz]

##### SOLAR CFS #####
#All CFs output in CST
def getSolarCFs(solarUnits,solarDir,startSolarCapacForCFs,states,statesAbbrev,matchStateOrRegion,
                desiredTz):
    #Get total wind capacity by state
    capacCol = solarUnits[0].index('Capacity (MW)')
    stateCol = solarUnits[0].index('State Name')
    solarCapacByState = getCapacsByState(solarUnits[1:],capacCol,stateCol)
    #Get solar plants in NREL dataset per state until capacity met
    (solarIdsToStates,solarFilenameAndCapac,solarFilenameAndCapacAndTz,solarMetadata) = getBestSolarIdsInStates(
                                                                    solarDir,solarCapacByState,startSolarCapacForCFs,
                                                                    states,statesAbbrev,matchStateOrRegion)
    #Import CFs for each wind plant
    idCol = solarFilenameAndCapacAndTz[0].index('Id')
    datasetCapacCol = solarFilenameAndCapacAndTz[0].index('DatasetCapacity')
    tzCol = solarFilenameAndCapacAndTz[0].index('Timezone')
    allSiteCfsHourly,allSiteCfsSubhourly,avgFleetCfHr = [],[],[]
    for site in solarFilenameAndCapacAndTz[1:]:
        (siteFilename,datasetSiteCapac,siteTz) = (site[idCol],site[datasetCapacCol],site[tzCol])
        for state in solarIdsToStates:
            if siteFilename in solarIdsToStates[state]: siteState = STATEABBREVS[state]
        if 'NoMoreSites' in siteFilename:
            if avgFleetCfHr == []: 
                #If doing new RE CFs & existing RE > potential RE capac for CFs,
                #can end up w/ nothing in allSiteCFs. In that case, new RE CFs
                #should jsut be fleet average CF.
                if allSiteCfsHourly == []:  
                    a,tempAllSiteCfsHr,tempAllSiteCfsSubhr,tempFileAndCapac = getSolarCFs(solarUnits,solarDir,
                                            0,states,statesAbbrev,matchStateOrRegion,desiredTz) 
                    avgFleetCfHr,avgFleetCfSubhr = calcCapacWtdFleetCf(tempFileAndCapac,
                                                            tempAllSiteCfsHr,tempAllSiteCfsSubhr)
                else:
                    avgFleetCfHr,avgFleetCfSubhr = calcCapacWtdFleetCf(solarFilenameAndCapac,
                                                            allSiteCfsHourly,allSiteCfsSubhourly)
            siteCfsHourly,siteCfsSubhourly = copy.deepcopy(avgFleetCfHr),copy.deepcopy(avgFleetCfSubhr)
        else:
            siteCfsHourly,siteCfsSubhourly = getSolarSiteCfs(solarDir,siteFilename,datasetSiteCapac,siteTz,desiredTz)
        addSiteCfsToAggList(siteCfsHourly,siteCfsSubhourly,allSiteCfsHourly,allSiteCfsSubhourly,siteFilename)
    allSiteCfsHourOfYear = [['HourOfYear'] + [val for val in range(1,8761)]] + copy.deepcopy(allSiteCfsHourly[1:])
    return (allSiteCfsHourOfYear,allSiteCfsHourly,allSiteCfsSubhourly,solarFilenameAndCapac)

def getCapacsByState(fleetNoHeader,capacCol,stateCol):
    capacByState = dict()
    for row in fleetNoHeader:
        (state,capac) = (row[stateCol],row[capacCol])
        if state in capacByState: capacByState[state] += float(capac)
        else: capacByState[state] = float(capac)
    return capacByState

def getBestSolarIdsInStates(solarDir,solarCapacByState,startSolarCapacForCFs,states,
                            statesAbbrev,matchStateOrRegion):
    solarMetadataFilename = os.path.join(solarDir,'SolarCapacityFactorsNRELTX.csv')
    solarMetadata = readCSVto2dList(solarMetadataFilename)
    solarStateCol = solarMetadata[0].index('State')
    solarCfCol = solarMetadata[0].index('CF')
    solarCapacCol = solarMetadata[0].index('PlantSize')
    solarFilenameCol = solarMetadata[0].index('File')
    (solarIdsToState,solarIdAndCapac) = getWindOrSolarIdsInStatesDecreasingCF(solarMetadata,
                                          solarCapacByState,solarStateCol,
                                          solarCfCol,solarCapacCol,solarFilenameCol,
                                          startSolarCapacForCFs,states,statesAbbrev,matchStateOrRegion)
    idCol = solarIdAndCapac[0].index('Id')
    solarIdAndCapacAndTz = [solarIdAndCapac[0] + ['Timezone']] 
    for idAndCapac in solarIdAndCapac[1:]:
        for state in solarIdsToState: 
            if idAndCapac[idCol] in solarIdsToState[state]: 
                solarIdAndCapacAndTz.append(idAndCapac + [timezoneOfSolarSite(state,idAndCapac[idCol])])
    return (solarIdsToState,solarIdAndCapac,solarIdAndCapacAndTz,solarMetadata)

def timezoneOfSolarSite(state,solarFilename):
    if STATETIMEZONES[state] == 'CST' or STATETIMEZONES[state] == 'EST':
        return STATETIMEZONES[state]
    else: #in KY or TN, which is half & half CST & EST
        kyLine = [(36.601261, -84.861318),(38.048865, -86.251172)]
        tnLine = [(36.601261, -85.076648),(34.997791, -85.605184)]
        if state == 'Tennessee': line = tnLine
        elif state == 'Kentucky': line = kyLine
        (siteLat,siteLong) = getCoordsFromFilename(solarFilename)
        if siteEastOfLine(line,float(siteLat),float(siteLong)): return 'EST'
        else: return 'CST'

def getCoordsFromFilename(solarFilename):
    latStart = solarFilename.index('_')+1
    latEnd = solarFilename[latStart:].index('_')
    lat = solarFilename[latStart:(latStart+latEnd)]
    longStart = solarFilename.index('-')
    longEnd = solarFilename[longStart:].index('_')
    longitude = solarFilename[longStart:(longStart+longEnd)]
    return (lat,longitude)

#Long = x coord, lat = y coord
def siteEastOfLine(line,siteLat,siteLong):
    (deltaLat,deltaLong) = (line[0][0]-line[1][0],line[0][1]-line[1][1])
    lineSlope = deltaLat/deltaLong
    intercept = line[1][0] - lineSlope * line[1][1] #b = y - mx
    longOnLineForSiteLat = (siteLat-intercept)/lineSlope #x = (y-b)/m
    return siteLong > longOnLineForSiteLat #long decreases (more negative) west across US

def getSolarSiteCfs(solarDir,siteFilename,siteCapac,siteTz,desiredTz):
    genData = readCSVto2dList(os.path.join(solarDir,'TX',siteFilename))
    datetimeAndGen = convertTimeToDatetimeInTgtTz(genData,'solar',siteFilename,desiredTz,siteTz)
    datetimeAndGenInYrHourly = convertGenToHourly(datetimeAndGen)
    subhourlyCfs = convertToCfs(datetimeAndGen,siteCapac)
    hourlyCfs = convertToCfs(datetimeAndGenInYrHourly,siteCapac)
    return hourlyCfs,subhourlyCfs
################################################################################
################################################################################
################################################################################


################################################################################
####### MISC. DATA #############################################################
################################################################################
STATETIMEZONES = {'North Carolina':'EST','South Carolina':'EST','Virginia':'EST',
                  'Georgia':'EST','Mississippi':'CST','Alabama':'CST','Louisiana':'CST',
                  'Missouri':'CST','Arkansas':'CST','Illinois':'CST','Kentucky':'CSTorEST',
                  'Tennessee':'CSTorEST','Texas':'CST'}

STATEABBREVS = {'North Carolina':'NC','South Carolina':'SC','Virginia':'VA',
                  'Georgia':'GA','Mississippi':'MS','Alabama':'AL','Louisiana':'LA',
                  'Missouri':'MO','Arkansas':'AR','Illinois':'IL','Kentucky':'KY',
                  'Tennessee':'TN','Texas':'TX'}
################################################################################
################################################################################
################################################################################

################################################################################
####### TEST FUNCTIONS #########################################################
################################################################################
def testTimezoneAssignment():
    print('Testing timezone assignment')
    assert(timezoneOfSolarSite('Arkansas','hello.csv')=='CST')
    assert(timezoneOfSolarSite('South Carolina','hello.csv')=='EST')
    assert(getCoordsFromFilename('Actual_29.15_-90.15_2006_UPV_140MW_5_Min.csv')==('29.15','-90.15'))
    kyLine = [(36.601261, -84.861318),(38.048865, -86.251172)]
    tnLine = [(36.601261, -85.076648),(34.997791, -85.605184)]
    assert(siteEastOfLine(kyLine,35,-500)==False)
    assert(siteEastOfLine(kyLine,30,-1)==True)
    assert(siteEastOfLine(kyLine,36.55,-88.15)==False)
    assert(siteEastOfLine(kyLine,37.493,-82.679)==True)
    assert(siteEastOfLine(kyLine,37.525,-84.557)==True)
    assert(siteEastOfLine(tnLine,35,-500)==False)
    assert(siteEastOfLine(tnLine,30,-1)==True)
    assert(siteEastOfLine(tnLine,35.066,-85.009)==True)
    assert(siteEastOfLine(tnLine,36.541,-86.101)==False)
    assert(timezoneOfSolarSite('Kentucky','Actual_38.05_-84.55_2006_DPV_34MW_5_Min.csv')=='EST')
    assert(timezoneOfSolarSite('Kentucky','Actual_38.85_-84.75_2006_DPV_31MW_5_Min.csv')=='EST')
    assert(timezoneOfSolarSite('Kentucky','Actual_36.55_-88.15_2006_UPV_29MW_5_Min.csv')=='CST')
    assert(timezoneOfSolarSite('Tennessee','Actual_36.65_-87.35_2006_DPV_35MW_5_Min.csv')=='CST')
    assert(timezoneOfSolarSite('Tennessee','Actual_34.95_-85.25_2006_DPV_38MW_5_Min.csv')=='EST')
    print('Passed')

################################################################################
################################################################################
################################################################################
