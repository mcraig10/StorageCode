#Michael Craig, 6 June 2016

#Constructs base generator fleet w/ cooling information, emissions rates, 
#VOM, fuel price, and unit commitment parameters. Then the fleet is compressed.
#DATA SOURCES: fleet - NEEDS; cooling information - EIA860; emissions rates - eGRID;
#VOM & UC parameters - PHORUM.

import csv, os, copy, operator, random
from AuxFuncs import *

################################################################################
#Imports fleet, isolates fleet to given state and power system, removes
#retired units, and adds emissions rates and cooling information.
#IN: states, year, & power system for analysis
#OUT: 2d list of generator fleet
def setupGeneratorFleet(testModel,statesForAnalysis,powerSystemsForAnalysis,retirementYearScreen,
        currYear,fuelPricesTimeSeries,compressFleet,runLoc,ocAdderMin,ocAdderMax,regupCostCoeffs):
    #Import entire current fleet
    if testModel == False: baseGenFleet = importNEEDSFleet(runLoc)
    else: baseGenFleet = importTestFleet(runLoc)
    #Slim down fleet based on region & year of analysis
    stateColName="State Name"
    isolateGensInStates(baseGenFleet,statesForAnalysis,stateColName) 
    isolateGensInPowerSystem(baseGenFleet,powerSystemsForAnalysis)
    # removeRetiredUnits(baseGenFleet,retirementYearScreen)
    #Modify / add fleet parameters
    addEmissionsRates(baseGenFleet,statesForAnalysis,runLoc)
    # addCoolingTechnologyAndSource(baseGenFleet,statesForAnalysis)
    addLatLong(baseGenFleet,statesForAnalysis,runLoc)
    #Compress fleet to get rid of tiny units
    if compressFleet == True: 
        # write2dListToCSV(baseGenFleet,'genFleetPreCompression.csv')
        baseGenFleet = performFleetCompression(baseGenFleet)
    #Add VOM & FOM values
    vomAndFomData = importVomAndFomData(runLoc)
    addVOMandFOM(baseGenFleet,vomAndFomData)
    #Add PHORUM-based UC parameters
    phorumData = importPhorumData(runLoc)
    addUnitCommitmentParameters(baseGenFleet,phorumData)
    #Add fuel prices
    addFuelPrices(baseGenFleet,currYear,fuelPricesTimeSeries)
    #Add random value to rows that will be included in op cost
    addRandomOpCostAdder(baseGenFleet,ocAdderMin,ocAdderMax)
    #Add reg offer costs and reg offer eligibility
    addRegResOfferAndElig(baseGenFleet,regupCostCoeffs)
    return baseGenFleet
################################################################################

################################################################################
#ADD COOLING TECHNOLOGY AND SOURCE TO FLEET
#Imports cooling map and data from EIA 860, then adds them generator fleet
#IN: generator fleet (2d list), states for analysis (1d list) 
def addCoolingTechnologyAndSource(baseGenFleet,statesForAnalysis):
    [assocData,equipData] = get860Data(statesForAnalysis)
    unitsToCoolingIDMap = mapUnitsToCoolingID(assocData,baseGenFleet,equipData)
    addCoolingInfoToFleet(baseGenFleet,equipData,unitsToCoolingIDMap)

#Adds cooling technology and source to fleet
#IN: generator fleet (2d list), cooling equipment data (EIA 860) (2d list), map
#of generator ID to cooling ID (dictionary).
def addCoolingInfoToFleet(baseGenFleet,equipData,unitsToCoolingIDMap):
    coolingHeaders = ['Cooling Tech','Cooling Source']
    baseGenFleet[0].extend(coolingHeaders)
    fleetHeadersMap = mapHeadersToCols(baseGenFleet)
    baseORISCol = fleetHeadersMap['ORIS Plant Code']
    baseUnitCol = fleetHeadersMap['Unit ID']
    for idx in range(1,len(baseGenFleet)):
        genRow = baseGenFleet[idx]
        (orisID,genID) = (genRow[baseORISCol],genRow[baseUnitCol])
        coolingID = unitsToCoolingIDMap[orisID + '+' + genID]
        if coolingID != 'NoMatch':
            [coolingTech,coolingSource] = getCoolingTechAndSource(equipData,orisID,coolingID)
        else:
            [coolingTech,coolingSource] = (coolingID,coolingID)
        baseGenFleet[idx].extend([coolingTech,coolingSource]) 
    
#Gets cooling tech for given ORIS and cooling ID. Works for generators in NEEDS
#that have a corresponding unit in EIA860.
#IN: cooling tech data (2d list), oris ID (str), cooling ID (str)
#OUT: cooling technology and source for input generator
def getCoolingTechAndSource(equipData,orisID,coolingID):
    equipHeadersMap = mapHeadersToCols(equipData)
    equipORISCol = equipHeadersMap['Plant Code']
    equipCoolingIDCol = equipHeadersMap['Cooling ID']
    equipCoolingTechCol = equipHeadersMap['Cooling Type 1']
    equipCoolingSourceCol = equipHeadersMap['Cooling Water Source']
    (equipORISIDs,equipCoolingIDs) = (colTo1dList(equipData,equipORISCol),
                                   colTo1dList(equipData,equipCoolingIDCol)) 
    equipRow = search2Lists(equipORISIDs, equipCoolingIDs, orisID, coolingID)
    coolingTech = equipData[equipRow][equipCoolingTechCol]
    coolingTechMap = getCoolingTechMap()
    coolingTech = coolingTechMap[coolingTech]
    if coolingTech == 'dry cooling': coolingSource = 'None'
    else: coolingSource = equipData[equipRow][equipCoolingSourceCol]
    retireCol = equipHeadersMap['Cooling Status']
    return [coolingTech,coolingSource]

#Maps 2-letter codes to comprehensible cooling techs
#OUT: map of cooling tech abbrev to full name (dictionary)
def getCoolingTechMap():
    coolingTechMap = {'DC': 'dry cooling','OC':'once through with pond',
                        'ON': 'once through no pond','RC':'recirculating with pond or canal',
                        'RF':'recirculating with tower','RI':'recirculating with tower',
                        'RN':'recirculating with tower','HT':'helper tower',
                        'OT':'other','HRC':'hybrid pond or canal with dry cooling',
                        'HRF':'hybrid tower with dry cooling',
                        'HRI':'hybrid tower with dry cooling'}
    return coolingTechMap

#Maps NEEDS generator IDs to EIA860 cooling IDs
#IN: cooling association data from EIA860 (2d list), base generator fleet from
#NEEDS (2d list)
#OUT: map of NEEDS generators to EIA860 cooling ID or 'NoMatch' (dictionary)
def mapUnitsToCoolingID(assocData,baseGenFleet,equipData):
    assocHeadersMap = mapHeadersToCols(assocData)
    fleetHeadersMap = mapHeadersToCols(baseGenFleet)
    assocORISCol = assocHeadersMap['Plant Code']
    assocBoilerCol = assocHeadersMap['Boiler ID']
    assocCoolingIDCol = assocHeadersMap['Cooling ID']
    baseORISCol = fleetHeadersMap['ORIS Plant Code']
    baseUnitCol = fleetHeadersMap['Unit ID']
    (assocORISIDs,assocBlrIDs) = (colTo1dList(assocData,assocORISCol),
                                   colTo1dList(assocData,assocBoilerCol)) 
    mapBaseGensToCoolingID = dict()
    for idx in range(1,len(baseGenFleet)):
        (baseORIS,baseUnit) = (baseGenFleet[idx][baseORISCol],
                                baseGenFleet[idx][baseUnitCol])
        assocRow = search2Lists(assocORISIDs, assocBlrIDs, baseORIS, baseUnit)
        if assocRow == False: #no matching oris-gen row
            if baseORIS not in assocORISIDs: #no matching oris row
                assocCoolingID = 'NoMatch'
            else: #matching oris row
                assocRow = assocORISIDs.index(baseORIS)
                assocRowLinkedToRetiredUnit = getRetirementStatusOfAssocRow(assocRow,
                                                                assocData,equipData)
                if assocRowLinkedToRetiredUnit == False:
                    assocCoolingID = assocData[assocRow][assocCoolingIDCol]
                else:
                    foundMatchingRow = False
                    while assocRowLinkedToRetiredUnit == True: 
                        restOfAssocOris = assocORISIDs[assocRow+1:]
                        if baseORIS in restOfAssocOris:
                            assocRow += restOfAssocOris.index(baseORIS)+1
                            assocRowLinkedToRetiredUnit = getRetirementStatusOfAssocRow(assocRow,
                                                                    assocData,equipData)
                            if assocRowLinkedToRetiredUnit == False:
                                foundMatchingRow = True
                        else:
                            assocRowLinkedToRetiredUnit = False
                    if foundMatchingRow: assocCoolingID = assocData[assocRow][assocCoolingIDCol]
                    else: assocCoolingID = 'NoMatch'                    
        else: #found matching oris-gen row
            # assocCoolingID = assocData[assocRow][assocCoolingIDCol]
            assocRowLinkedToRetiredUnit = getRetirementStatusOfAssocRow(assocRow,
                                                                assocData,equipData)
            if assocRowLinkedToRetiredUnit == False: #not retired, so done
                assocCoolingID = assocData[assocRow][assocCoolingIDCol]
            else: #retired, so keep looking
                (restOfAssocOris,restOfAssocBlrs) = (assocORISIDs[assocRow+1:],assocBlrIDs[assocRow+1:])
                assocRow += search2Lists(restOfAssocOris, restOfAssocBlrs, baseORIS, baseUnit) + 1
                if assocRow == False: #no more oris-gen row matches
                    assocCoolingID = 'NoMatch'
                else: #found another oris-gen row match
                    assocRowLinkedToRetiredUnit = getRetirementStatusOfAssocRow(assocRow,
                                                                    assocData,equipData)
                    if assocRowLinkedToRetiredUnit: #found antoher retired cooling type - so quit
                        assocCoolingID = 'NoMatch'
                    else: #found non-retired match
                        assocCoolingID = assocData[assocRow][assocCoolingIDCol]
        mapBaseGensToCoolingID[baseORIS + '+' + baseUnit] = assocCoolingID
    return mapBaseGensToCoolingID

#Check if cooling tech associated with cooling ID for ORIS ID match is retired.
#Returns true if unit is retired.
def getRetirementStatusOfAssocRow(assocRow,assocData,equipData):
    assocHeadersMap = mapHeadersToCols(assocData)
    assocOrisIDCol = assocHeadersMap['Plant Code']
    assocCoolingIDCol = assocHeadersMap['Cooling ID']
    (orisID,coolingID) = (assocData[assocRow][assocOrisIDCol],
                            assocData[assocRow][assocCoolingIDCol])
    equipHeadersMap = mapHeadersToCols(equipData)
    equipORISCol = equipHeadersMap['Plant Code']
    equipCoolingIDCol = equipHeadersMap['Cooling ID']
    equipRetiredCol = equipHeadersMap['Cooling Status']
    (equipORISIDs,equipCoolingIDs) = (colTo1dList(equipData,equipORISCol),
                                   colTo1dList(equipData,equipCoolingIDCol)) 
    equipRow = search2Lists(equipORISIDs, equipCoolingIDs, orisID, coolingID)
    retiredStatus = equipData[equipRow][equipRetiredCol]
    return retiredStatus=='RE'

#Imports EIA860 cooling equipment and association data, and isolates
#equipment data to units in states of analysis
#IN: states for analysis (1d list)
#OUT: EIA860 cooling IDs and technologies (2d lists)
def get860Data(statesForAnalysis):
    [assocData,equipData] = import860data(runLoc)
    #First row is useless data in both lists - remove it
    assocData.pop(0)
    equipData.pop(0)
    stateColName = 'State'
    statesForAnalysisAbbrev = getStateAbbrevs(statesForAnalysis)
    isolateGensInStates(equipData,statesForAnalysisAbbrev,stateColName)
    return [assocData,equipData]

#Imports 860 equipment and association data
#OUT: EIA860 cooling assocation and equipment data (2d lists)
def import860data(runLoc):
    if runLoc == 'pc': dir860 = 'C:\\Users\\mtcraig\\Desktop\\EPP Research\\Databases\\EIA8602014'
    else: dir860 = os.path.join('Data','EIA8602014')
    assocName = '6_1_EnviroAssoc_Y2014_cooling.csv'
    equipName = '6_2_EnviroEquip_Y2014_cooling.csv'
    assocData = readCSVto2dList(os.path.join(dir860,assocName))
    equipData = readCSVto2dList(os.path.join(dir860,equipName))   
    return [assocData,equipData]
################################################################################

################################################################################
#ADD EMISSION RATES FROM EGRID TO GENERATOR FLEET
#Adds eGRID emissions rates to generator fleet
#IN: generator fleet (2d list), states for analysis (1d list)
def addEmissionsRates(baseGenFleet,statesForAnalysis,runLoc):
    (egridBoiler,egridPlant) = importeGridData(statesForAnalysis,runLoc)
    emsHeadersToAdd=["NOxEmRate(lb/MMBtu)","SO2EmRate(lb/MMBtu)",
                  "CO2EmRate(lb/MMBtu)"]
    addHeaders(baseGenFleet,emsHeadersToAdd)    
    addEmissionsRatesValues(baseGenFleet,egridBoiler,egridPlant)
    # write2dListToCSV(baseGenFleet,'genFleetWithoutFilledInEmsRates.csv')
    #fill in missing values w/ avg of similar fuel & plant type
    fillMissingEmissionsRates(baseGenFleet,emsHeadersToAdd) 

#Fills missing generator em rates w/ average for gens w/ same fuel and plant type.
#IN: generator fleet (2d list), emissions headers to add (1d list)
def fillMissingEmissionsRates(baseGenFleet,emsHeadersToAdd):
    #Get headers and columns
    headersToColsMapBase = mapHeadersToCols(baseGenFleet)
    plantTypeCol = headersToColsMapBase['PlantType']
    fuelTypeCol = headersToColsMapBase['Modeled Fuels']
    noxCol = headersToColsMapBase[emsHeadersToAdd[0]]
    so2Col = headersToColsMapBase[emsHeadersToAdd[1]]
    co2Col = headersToColsMapBase[emsHeadersToAdd[2]]
    #Find and fill missing emissions rates values
    for idx in range(1,len(baseGenFleet)):
        if baseGenFleet[idx][noxCol]=='NA':
            (plantType,fuelType) = (baseGenFleet[idx][plantTypeCol],
                                    baseGenFleet[idx][fuelTypeCol])
            [nox,so2,co2] = getEmsRatesOfMatchingFuelAndPlantType(baseGenFleet,plantType,
                                                                  fuelType,emsHeadersToAdd)
            [avgnox,avgso2,avgco2] = [avgListVals(nox),avgListVals(so2),avgListVals(co2)]
            baseGenFleet[idx][noxCol]=avgnox
            baseGenFleet[idx][so2Col]=avgso2
            baseGenFleet[idx][co2Col]=avgco2   

#Gets emissions rates of generators w/ given plant & fuel type
#IN: generator fleet (2d list), plant and fuel type (str), em rate headers (1d list)
#OUT: NOx, SO2 and CO2 emissions rates (1d lists)
def getEmsRatesOfMatchingFuelAndPlantType(baseGenFleet,plantType,fuelType,emsHeadersToAdd):
    #Get headers
    headersToColsMapBase = mapHeadersToCols(baseGenFleet)
    noxCol = headersToColsMapBase[emsHeadersToAdd[0]]
    so2Col = headersToColsMapBase[emsHeadersToAdd[1]]
    co2Col = headersToColsMapBase[emsHeadersToAdd[2]]
    #Get cols w/ matching fuel & plant type
    matchingRowIdxs = getMatchingRowsFuelAndPlantType(baseGenFleet,plantType,fuelType,
                                                      noxCol)
    #If can't find on fuel & plant type, try just fuel type
    if matchingRowIdxs==[]:
        matchingRowIdxs = getMatchingRowsFuelType(baseGenFleet,fuelType,noxCol)
    #If still can't get emissions rate, then ues other plant & fuel type:
    #LFG - NGCT, MSW - biomass, gas & oil O/G Steam - gas O/G Steam, Non-fossil waste - 
    if matchingRowIdxs==[] and fuelType=='Landfill Gas':
        matchingRowIdxs = getMatchingRowsFuelAndPlantType(baseGenFleet,'Combustion Turbine',
                                                          'Natural Gas',noxCol)
    elif matchingRowIdxs==[] and fuelType=='MSW':
        matchingRowIdxs = getMatchingRowsFuelAndPlantType(baseGenFleet,'Biomass',
                                                          'Biomass',noxCol)
    elif matchingRowIdxs==[] and fuelType=='Natural Gas& Distillate Fuel Oil& Residual Fuel Oil':
        matchingRowIdxs = getMatchingRowsFuelAndPlantType(baseGenFleet,'O/G Steam',
                                                          'Natural Gas',noxCol)
    elif matchingRowIdxs==[] and fuelType=='Non-Fossil Waste':
        matchingRowIdxs = getMatchingRowsFuelAndPlantType(baseGenFleet,'Biomass',
                                                          'Biomass',noxCol)
    #Get emissions rates of matching rows
    [nox,so2,co2] = [[],[],[]]
    for rowIdx in matchingRowIdxs:
        row = baseGenFleet[rowIdx]
        nox.append(row[noxCol])
        so2.append(row[so2Col])
        co2.append(row[co2Col])
    return [nox,so2,co2]

#Gets row indexes in generator fleet of generators that match given plant & fuel type,
#filtering out units w/ no emissions rate data.
#IN: generator fleet (2d list), plant and fuel type (str), col w/ nox ems rate (int)
#OUT: row indices of matching plant & fuel type (1d list)
def getMatchingRowsFuelAndPlantType(baseGenFleet,plantType,fuelType,noxCol):
    headersToColsMapBase = mapHeadersToCols(baseGenFleet)
    plantTypeCol = headersToColsMapBase['PlantType']
    fuelTypeCol = headersToColsMapBase['Modeled Fuels']
    matchingRowIdxs = []
    for idx in range(len(baseGenFleet)):
        row = baseGenFleet[idx]
        if row[plantTypeCol]==plantType and row[fuelTypeCol]==fuelType:
            if row[noxCol] != 'NA': #make sure has data!
                matchingRowIdxs.append(idx)
    return matchingRowIdxs

#Gets row indexes in generator fleet of gens w/ same fuel type, filtering
#out units w/ no emissions rate data.
#IN: generator fleet (2d list), fuel type (str), col w/ nox ems rate (int)
#OUT: row indices of matching fuel type (1d list)
def getMatchingRowsFuelType(baseGenFleet,fuelType,noxCol):
    headersToColsMapBase = mapHeadersToCols(baseGenFleet)
    fuelTypeCol = headersToColsMapBase['Modeled Fuels']
    matchingRowIdxs = []
    for idx in range(len(baseGenFleet)):
        row = baseGenFleet[idx]
        if row[fuelTypeCol]==fuelType:
            if row[noxCol] != 'NA': #make sure has data!
                matchingRowIdxs.append(idx)
    return matchingRowIdxs

#Add eGRID emissions rates values to fleet, either using boiler specific 
#data for coal & o/g steam units or plant level average data. Adds
#ems rate in order of nox, so2, and co2, as set by ems headers in addEmissionsRates.
#IN: generator fleet (2d list), eGRID boiler and plant data (2d lists)
def addEmissionsRatesValues(baseFleet,egridBoiler,egridPlant):
    headersToColsMapBase = mapHeadersToCols(baseFleet)
    headersToColsMapEgridBlr = mapHeadersToCols(egridBoiler)
    headersToColsMapEgridPlnt = mapHeadersToCols(egridPlant)
    basePlantTypeCol = headersToColsMapBase['PlantType']
    noEmissionPlantTypes = ['hydro','solar pv','wind','geothermal',
                            'solar thermal','pumped storage','nuclear']
    for idx in range(1,len(baseFleet)):
        plantType = baseFleet[idx][basePlantTypeCol].lower()
        if plantType == 'coal steam':  
            [nox,so2,co2] = getBlrEmRates(baseFleet,idx,egridBoiler)
        elif plantType == 'o/g steam':
            [nox,so2,co2] = getBlrEmRates(baseFleet,idx,egridBoiler)
            if nox == 'NA': #just test on nox, but all would be na
                [nox,so2,co2] = getPlantEmRates(baseFleet,idx,egridPlant)
        elif plantType in noEmissionPlantTypes:
            [nox,so2,co2] = [0,0,0]
        else:
            [nox,so2,co2] = getPlantEmRates(baseFleet,idx,egridPlant)
        #Some plants have no emissions info, so end up w/ zero emission values - 
        #fill in 'NA' if so.
        if [nox,so2,co2] == [0,0,0] and plantType not in noEmissionPlantTypes:
            [nox,so2,co2]=['NA','NA','NA']
        baseFleet[idx].extend([nox,so2,co2])

#Look for boiler-level match of given gen in gen fleet to eGRID data, and return emissions 
#rates if find match.
#IN: gen fleet (2d list), idx for row in gen fleet (int), boiler data (2d list)
#OUT: boiler-level nox, so2 & co2 ems rates (1d list)
def getBlrEmRates(baseFleet,idx,egridBoiler):
    #Setup necessary data
    headersToColsMapBase = mapHeadersToCols(baseFleet)
    headersToColsMapEgridBlr = mapHeadersToCols(egridBoiler)
    (baseOrisCol,baseUnitCol) = (headersToColsMapBase["ORIS Plant Code"],
                                 headersToColsMapBase["Unit ID"])
    (egridOrisCol,egridBlrCol) = (headersToColsMapEgridBlr["DOE/EIA ORIS plant or facility code"],
                                  headersToColsMapEgridBlr["Boiler ID"])
    (egridBlrORISIDs,egridBlrIDs) = (colTo1dList(egridBoiler,egridOrisCol),
                                   colTo1dList(egridBoiler,egridBlrCol))    
    #eGrid ORIS IDs are given w/ .0 @ end (e.g., 5834.0). So convert to int and back to str.
    removeTrailingDecimalFromEgridORIS(egridBlrORISIDs)
    #Do mapping
    (baseOrisID,baseUnitID) = (baseFleet[idx][baseOrisCol],baseFleet[idx][baseUnitCol])
    try:
        egridBlrRow = search2Lists(egridBlrORISIDs, egridBlrIDs, baseOrisID, baseUnitID)
        [nox,so2,co2] = calculateEmissionsRatesBlr(egridBoiler,egridBlrRow)
    except:
        # print('No matching boiler for: ORIS' + str(baseOrisID) + ' Blr' + str(baseUnitID))
        [nox,so2,co2] = ['NA','NA','NA']
    return [nox,so2,co2]

#Looks for plant-level match of given unit in gen fleet to eGRID plant data,
#and returns plant-level ems rate of matching plant if found.
#IN: gen fleet (2d list), idx for row in gen fleet (int), plant data (2d list)
#OUT: plant-level nox, so2 & co2 ems rate (1d list)
def getPlantEmRates(baseFleet,idx,egridPlant):
    #Setup necessary data
    headersToColsMapBase = mapHeadersToCols(baseFleet)
    headersToColsMapEgridPlnt = mapHeadersToCols(egridPlant)
    baseOrisCol = headersToColsMapBase["ORIS Plant Code"]
    egridOrisCol = headersToColsMapEgridPlnt["DOE/EIA ORIS plant or facility code"]
    egridORISIDs = colTo1dList(egridPlant,egridOrisCol)   
    #eGrid ORIS IDs are given w/ .0 @ end (e.g., 5834.0). So convert to int and back to str.
    # removeTrailingDecimalFromEgridORIS(egridORISIDs)
    #Do mapping
    baseOrisID = baseFleet[idx][baseOrisCol]
    try:
        egridPlantRow = egridORISIDs.index(baseOrisID)
        [nox,so2,co2] = calculateEmissionsRatesPlnt(egridPlant,egridPlantRow)
    except:
        # print('No matching plant for: ORIS' + str(baseOrisID))
        [nox,so2,co2] = ['NA','NA','NA']
    return [nox,so2,co2]
    
#Gets boiler-level emissions rates.
#IN: eGRID boiler data (2d list), row in boiler data (int)
#OUT: boiler-level emissions rates [lb/mmbtu] (1d list)
def calculateEmissionsRatesBlr(egridBoiler,egridBoilerRow):
    scaleTonsToLbs = 2000
    #Define headers
    htInputHeader = 'Boiler unadjusted annual best heat input (MMBtu)'
    noxHeader = 'Boiler unadjusted annual best NOx emissions (tons)'
    so2Header = 'Boiler unadjusted annual best SO2 emissions (tons)'
    co2Header = 'Boiler unadjusted annual best CO2 emissions (tons)'
    #Calculate values
    headersToColsMap = mapHeadersToCols(egridBoiler)
    (htinputCol,noxCol,so2Col,co2Col) = (headersToColsMap[htInputHeader],
                                        headersToColsMap[noxHeader],
                                        headersToColsMap[so2Header],
                                        headersToColsMap[co2Header])
    blrData = egridBoiler[egridBoilerRow]
    (htInput,noxEms,so2Ems,co2Ems) = (blrData[htinputCol],blrData[noxCol],
                                      blrData[so2Col],blrData[co2Col])
    #Str nums have commas in them - use helper function to turn into numbers 
    (htInput,noxEms,so2Ems,co2Ems) = (toNum(htInput),toNum(noxEms),toNum(so2Ems),
                                      toNum(co2Ems))
    (noxEmsRate,so2EmsRate,co2EmsRate) = (noxEms/htInput*scaleTonsToLbs, 
                                          so2Ems/htInput*scaleTonsToLbs,
                                          co2Ems/htInput*scaleTonsToLbs)
    return [noxEmsRate,so2EmsRate,co2EmsRate]

#Gets plant-level ems rates.
#IN: eGRID plant data (2d list), row in plant data (int)
#OUT: plant-level nox, so2 and co2 ems rates [lb/mmbtu] (1d list)
def calculateEmissionsRatesPlnt(egridPlant,egridPlantRow):
    #Define headers
    noxEmsRateHeader = 'Plant annual NOx input emission rate (lb/MMBtu)'
    so2EmsRateHeader = 'Plant annual SO2 input emission rate (lb/MMBtu)'
    co2EmsRateHeader = 'Plant annual CO2 input emission rate (lb/MMBtu)'
    #Get values
    headersToColsMap = mapHeadersToCols(egridPlant)
    (noxCol,so2Col,co2Col) = (headersToColsMap[noxEmsRateHeader],
                              headersToColsMap[so2EmsRateHeader],
                              headersToColsMap[co2EmsRateHeader])
    plantData = egridPlant[egridPlantRow]
    (noxEmsRate,so2EmsRate,co2EmsRate) = [plantData[noxCol],plantData[so2Col],plantData[co2Col]]
    #Ems rate nums have commas - use helper func to turn into numbers
    (noxEmsRate,so2EmsRate,co2EmsRate) = (toNum(noxEmsRate),
                                          toNum(so2EmsRate),
                                          toNum(co2EmsRate))
    return [noxEmsRate,so2EmsRate,co2EmsRate]
################################################################################

################################################################################
#ADD LAT/LONG FROM EGRID TO FLEET
def addLatLong(baseGenFleet,statesForAnalysis,runLoc):
    (egridBoiler,egridPlant) = importeGridData(statesForAnalysis,runLoc)
    latLongHeadersToAdd=["Latitude","Longitude"]
    addHeaders(baseGenFleet,latLongHeadersToAdd)    
    addLatLongValues(baseGenFleet,egridPlant)

#Add lat/long values to base fleet using eGRID plant data
def addLatLongValues(baseFleet,egridPlant):
    headersToColsMapBase = mapHeadersToCols(baseFleet)
    headersToColsMapEgrid = mapHeadersToCols(egridPlant)
    baseOrisCol = headersToColsMapBase['ORIS Plant Code']
    egridOrisCol = headersToColsMapEgrid['DOE/EIA ORIS plant or facility code']
    (egridLatCol,egridLongCol) = (headersToColsMapEgrid['Plant latitude'],
                                    headersToColsMapEgrid['Plant longitude'])
    egridORISIDs = colTo1dList(egridPlant,egridOrisCol)   
    for idx in range(1,len(baseFleet)):
        genRow = baseFleet[idx]
        genORIS = genRow[baseOrisCol]
        if genORIS in egridORISIDs:
            egridRow = egridORISIDs.index(genORIS)
            (genLat,genLong) = (egridPlant[egridRow][egridLatCol],
                                egridPlant[egridRow][egridLongCol])
        else:
            (genLat,genLong) = ('NA','NA')
        baseFleet[idx].extend([genLat,genLong])
################################################################################

################################################################################
#COMPRESS FLEET BY COMBINING SMALL UNITS
def performFleetCompression(genFleet):
    fuelAndPlantTypeToCompress = [('Landfill Gas','Landfill Gas'),
            ('Distillate Fuel Oil','Combustion Turbine'),('MSW','Municipal Solid Waste'),
            ('Natural Gas','Combustion Turbine'),('Biomass','Biomass'),
            ('Natural Gas& Distillate Fuel Oil','O/G Steam'),('Natural Gas','O/G Steam'),
            ('Natural Gas','Combined Cycle')]
    for (fuel,plant) in fuelAndPlantTypeToCompress:
        compressFuelAndPlantType(genFleet,fuel,plant)
    return genFleet

def compressFuelAndPlantType(genFleet,fuel,plant):
    maxSizeToCombine = 75
    head = genFleet[0]
    (plantCol,fuelCol,capacCol) = (head.index('PlantType'),head.index('Modeled Fuels'),
                                    head.index('Capacity (MW)'))
    # (coolTechCol,coolSourceCol) = (head.index('Cooling Tech'),head.index('Cooling Source'))
    idxsToRemoveAndCombine = []
    startFleetLength = len(genFleet)
    for idx in range(1,startFleetLength):
        rowFuel = isolateFirstFuelType(genFleet[idx][fuelCol])
        if (rowFuel == fuel and genFleet[idx][plantCol] == plant
                and float(genFleet[idx][capacCol]) < maxSizeToCombine):
                # (genFleet[idx][coolTechCol] == 'NoMatch' or genFleet[idx][coolSourceCol] == 'NoMatch')):
            idxsToRemoveAndCombine.append(idx)
    combineGenerators(genFleet,idxsToRemoveAndCombine,fuel,plant,startFleetLength)
    for idx in reversed(idxsToRemoveAndCombine): genFleet.pop(idx)

#Combine generators based on when they came online
def combineGenerators(genFleet,idxsToRemoveAndCombine,fuel,plant,startFleetLength):
    onlineYearCol = genFleet[0].index('On Line Year')
    onlineYears = [int(genFleet[idx][onlineYearCol]) for idx in idxsToRemoveAndCombine]
    (firstYr,lastYr,stepYr) = (1975,2026,10)
    yearIntervals = [yr for yr in range(firstYr,lastYr,stepYr)]
    for endingYear in yearIntervals:
        if endingYear == firstYr: beginningYear = 0
        else: beginningYear = endingYear - stepYr
        idxsInInterval = [idx for idx in idxsToRemoveAndCombine if (int(genFleet[idx][onlineYearCol]) <= endingYear and 
                                                                    int(genFleet[idx][onlineYearCol]) > beginningYear)]
        if len(idxsInInterval)>0:
            combineGeneratorsInDecade(genFleet,idxsInInterval,endingYear-stepYr//2,fuel,plant,startFleetLength)

def combineGeneratorsInDecade(genFleet,idxsInInterval,medianYearInInterval,fuel,plant,startFleetLength):
    maxCombinedSize = 300
    (runningCombinedSize,idxsToCombine) = (0,[])
    capacCol = genFleet[0].index('Capacity (MW)')
    for idx in idxsInInterval:
        if (runningCombinedSize + float(genFleet[idx][capacCol]) > maxCombinedSize):
            addCombinedIdxsToFleet(genFleet,idxsToCombine,runningCombinedSize,fuel,plant,medianYearInInterval)
            runningCombinedSize = float(genFleet[idx][capacCol])
            idxsToCombine = [idx]
        else:
            runningCombinedSize += float(genFleet[idx][capacCol])
            idxsToCombine.append(idx)
    if len(idxsToCombine)>0: #combine remaining units
        addCombinedIdxsToFleet(genFleet,idxsToCombine,runningCombinedSize,fuel,plant,medianYearInInterval)

def addCombinedIdxsToFleet(genFleet,idxsToCombine,combinedCapac,fuel,plant,medianYearInInterval):
    headers = genFleet[0]
    newRow = ['']*len(headers)
    rowsToCombine = [genFleet[idx] for idx in idxsToCombine]
    capacCol = headers.index('Capacity (MW)')
    capacWts = [float(row[capacCol])/combinedCapac for row in rowsToCombine]
    parametersToCombine = ['NOxEmRate(lb/MMBtu)','SO2EmRate(lb/MMBtu)',
                           'CO2EmRate(lb/MMBtu)','Heat Rate (Btu/kWh)']
    for param in parametersToCombine:
        colNum = headers.index(param)
        paramVals = [float(row[colNum]) for row in rowsToCombine]
        newRow[colNum] = sum(list(map(operator.mul,capacWts,paramVals)))
    newRow[capacCol] = combinedCapac
    addStateOrisFuelOnlineYearAndPlantType(genFleet,newRow,fuel,plant,medianYearInInterval)
    genFleet.append(newRow)

def addStateOrisFuelOnlineYearAndPlantType(genFleet,newRow,fuel,plant,*onlineYear):
    (stateCol,orisCol) = (genFleet[0].index('State Name'),genFleet[0].index('ORIS Plant Code'))
    (unitCol,fuelCol) = (genFleet[0].index('Unit ID'),genFleet[0].index('Modeled Fuels'))
    (onlineYearCol,ipmRetireCol) = (genFleet[0].index('On Line Year'),genFleet[0].index('Retirement Year'))
    plantCol = genFleet[0].index('PlantType')
    maxOris = max([int(row[orisCol]) for row in genFleet[1:]])
    (newRow[orisCol],newRow[stateCol],newRow[unitCol]) = (maxOris+1,'Texas','1')
    (newRow[fuelCol],newRow[plantCol]) = (fuel,plant)
    newRow[ipmRetireCol] = 9999
    if len(onlineYear)>0: newRow[onlineYearCol] = onlineYear[0]
################################################################################

################################################################################
#ADD VARIABLE AND FIXED O&M COSTS
#Based on plant type
def addVOMandFOM(baseGenFleet,vomAndFomData):
    vomAndFomHeader = ['VOM($/MWh)','FOM($/MW/yr)']
    addHeaders(baseGenFleet,vomAndFomHeader)
    addVomAndFomValues(baseGenFleet,vomAndFomData)

def addVomAndFomValues(baseGenFleet,vomAndFomData):
    plantTypeColFleet = baseGenFleet[0].index('PlantType')
    (vomColFleet,fomColFleet) = (baseGenFleet[0].index('VOM($/MWh)'),baseGenFleet[0].index('FOM($/MW/yr)'))
    plantTypeColData = vomAndFomData[0].index('PlantType')
    plantTypesData = [row[plantTypeColData] for row in vomAndFomData]
    (vomColData,fomColData) = (vomAndFomData[0].index('VOM(2012$/MWh)'),vomAndFomData[0].index('FOM(2012$/MW/yr)'))
    for row in baseGenFleet[1:]:
        dataRow = plantTypesData.index(row[plantTypeColFleet])
        vomValue = convertCostToTgtYr('vom',float(vomAndFomData[dataRow][vomColData]))
        fomValue = convertCostToTgtYr('fom',float(vomAndFomData[dataRow][fomColData]))
        if vomColFleet >= len(row): row.extend([vomValue,fomValue]) #haven't added VOM or FOM values yet
        else: (row[vomColFleet],row[fomColFleet]) = (vomValue,fomValue) #filling in values in row that already has blank space for VOM & FOM

def importVomAndFomData(runLoc):
    if runLoc == 'pc': dirName = 'C:\\Users\\mtcraig\\Desktop\\EPP Research\\NewPlantData'
    else: dirName = os.path.join('Data','NewPlantData')
    fileName = 'VOMandFOMValuesExistingPlants4Aug2016.csv'
    fullFileName = os.path.join(dirName,fileName)
    return readCSVto2dList(fullFileName)
################################################################################

################################################################################
#ADD UNIT COMMITMENT PARAMETERS
#Based on fuel and plant type; data from PHORUM
def addUnitCommitmentParameters(baseGenFleet,phorumData):
    ucHeaders = ['MinDownTime(hrs)','RampRate(MW/hr)','MinLoad(MW)','StartCost($)']
    addHeaders(baseGenFleet,ucHeaders)
    addUCValues(baseGenFleet,ucHeaders,phorumData)

def addUCValues(baseGenFleet,ucHeaders,phorumData):
    capacCol = baseGenFleet[0].index('Capacity (MW)')
    fuelCol = baseGenFleet[0].index('Modeled Fuels')
    plantTypeCol = baseGenFleet[0].index('PlantType')
    for ucHeader in ucHeaders:
        currCol = baseGenFleet[0].index(ucHeader)
        ucHeaderToPhorumParamName = mapHeadersToPhorumParamNames()
        phorumParamName = ucHeaderToPhorumParamName[ucHeader]
        for row in baseGenFleet[1:]:
            (fuel,plantType,size) = (row[fuelCol],row[plantTypeCol],float(row[capacCol]))
            fuel = isolateFirstFuelType(fuel)
            phorumValue = getMatchingPhorumValue(phorumData,fuel,plantType,size,phorumParamName)
            if ucHeader == 'MinDownTime(hrs)': valToAdd = phorumValue
            else: 
                valToAdd = phorumValue*size
                if ucHeader == 'StartCost($)': valToAdd = convertCostToTgtYr('startup',valToAdd)
            if currCol >= len(row): row.append(valToAdd) #for when first adding values
            else: row[currCol] = valToAdd #for filling in values after have already added

def isolateFirstFuelType(fuel):
    multiFuelDivider = '&' #some plants have multiple modeled fuels divided by &
    if multiFuelDivider in fuel: fuel = fuel[:fuel.index(multiFuelDivider)]
    return fuel

def getMatchingPhorumValue(phorumData,fuel,plantType,size,paramName):
    if plantType == 'Fuel Cell': plantType = 'Combustion Turbine'
    fuel = mapFleetFuelToPhorumFuels(fuel)
    phorumPropertyNameCol = phorumData[0].index('PropertyName')
    phorumFuelCol = phorumData[0].index('Fuel')
    phorumPlantTypeCol = phorumData[0].index('PlantType')
    phorumLowerSizeCol = phorumData[0].index('LowerPlantSizeLimit')
    phorumUpperSizeCol = phorumData[0].index('UpperPlantSizeLimit')
    phorumValueCol = phorumData[0].index('PropertyValue')
    phorumProperties = [row[phorumPropertyNameCol] for row in phorumData[1:]]
    phorumFuels = [row[phorumFuelCol] for row in phorumData[1:]]
    phorumPlantTypes = [row[phorumPlantTypeCol] for row in phorumData[1:]]
    phorumLowerSizes = [int(row[phorumLowerSizeCol]) for row in phorumData[1:]]
    phorumUpperSizes = [int(row[phorumUpperSizeCol]) for row in phorumData[1:]]
    phorumValues = [float(row[phorumValueCol]) for row in phorumData[1:]]
    for idx in range(len(phorumProperties)):
        if (phorumProperties[idx] == paramName and phorumFuels[idx] == fuel and 
            (phorumPlantTypes[idx] == plantType or phorumPlantTypes[idx] == 'All') and 
            (phorumLowerSizes[idx] <= size and phorumUpperSizes[idx] > size)):
            return float(phorumValues[idx])

def mapFleetFuelToPhorumFuels(fleetFuel):
    fleetFuelToPhorumFuelMap = {'Bituminous':'Coal','Petroleum Coke':'Pet. Coke',
            'Subbituminous':'Coal','Lignite':'Coal','Natural Gas':'NaturalGas',
            'Distillate Fuel Oil':'Oil','Hydro':'Hydro','Landfill Gas':'LF Gas',
            'Biomass':'Biomass','Solar':'Solar','Non-Fossil Waste':'Non-Fossil',
            'MSW':'MSW','Pumped Storage':'Hydro','Residual Fuel Oil':'Oil',
            'Wind':'Wind','Nuclear Fuel':'Nuclear','Coal':'Coal'}
    return fleetFuelToPhorumFuelMap[fleetFuel]

def mapHeadersToPhorumParamNames():
    return {'MinDownTime(hrs)':'Min Down Time','RampRate(MW/hr)':'Ramp Rate',
            'MinLoad(MW)':'Min Stable Level','StartCost($)':'Start Cost'}
################################################################################

################################################################################
#ADD FUEL PRICES
def addFuelPrices(baseGenFleet,currYear,fuelPriceTimeSeries):
    fuelPriceHeader = ['FuelPrice($/MMBtu)']
    addHeaders(baseGenFleet,fuelPriceHeader)
    addFuelPriceValues(baseGenFleet,fuelPriceTimeSeries,currYear)

def addFuelPriceValues(baseGenFleet,fuelPriceTimeSeries,currYear):
    fuelCol = baseGenFleet[0].index('Modeled Fuels')
    for row in baseGenFleet[1:]: row.append(getFuelPrice(row,fuelCol,fuelPriceTimeSeries,currYear))
        
def getFuelPrice(fleetRow,fleetFuelCol,fuelPriceTimeSeries,currYear):
    fuel = fleetRow[fleetFuelCol]
    fuel = isolateFirstFuelType(fuel)
    fuelPriceDollarUnadjusted = getFuelPriceForFuelType(fuel,fuelPriceTimeSeries,currYear)
    return convertCostToTgtYr('fuel',fuelPriceDollarUnadjusted)

def getFuelPriceForFuelType(fuel,fuelPriceTimeSeries,currYear):
    fuel = mapFleetFuelToPhorumFuels(fuel) 
    fuelPriceFuelCol = fuelPriceTimeSeries[0].index('FuelPrices($/MMBtu)')
    fuelPriceFuels = [row[fuelPriceFuelCol] for row in fuelPriceTimeSeries]
    fuelPriceYears = [int(yr) for yr in fuelPriceTimeSeries[0][1:]]
    fuelPriceRow = fuelPriceFuels.index(fuel)
    fuelPricePrices = [float(price) for price in fuelPriceTimeSeries[fuelPriceRow][1:]]
    if currYear in fuelPriceYears: yearCol = fuelPriceYears.index(currYear)
    elif currYear > max(fuelPriceYears): yearCol = fuelPriceYears.index(max(fuelPriceYears))
    return fuelPricePrices[yearCol]
################################################################################

################################################################################
#IMPORT DATA
#Import base generator fleet from NEEDS
#OUT: gen fleet (2d list)
def importNEEDSFleet(runLoc):
    if runLoc == 'pc': dirName = 'C:\\Users\\mtcraig\\Desktop\\EPP Research\\Databases\\NEEDS'  
    else: dirName = 'Data' 
    fileName = 'needs_v515_nocommas.csv'
    fullFileName = os.path.join(dirName,fileName)
    return readCSVto2dList(fullFileName)

def importTestFleet(runLoc):
    if runLoc == 'pc': dirName = 'C:\\Users\\mtcraig\\Desktop\\EPP Research\\Databases\\CETestFleet'
    else: dirName = ''
    fileName = 'testFleetTiny.csv'
    fullFileName = os.path.join(dirName,fileName)
    return readCSVto2dList(fullFileName)    

#Import eGRID boiler and plant level data, then isolate plants and boilers in state
#IN: states for analysis (1d list)
#OUT: eGRID boiler and plant data (2d lists)
def importeGridData(statesForAnalysis,runLoc):
    if runLoc == 'pc': dirName = 'C:\\Users\\mtcraig\\Desktop\\EPP Research\\Databases\\eGRID2015'
    else: dirName = os.path.join('Data','eGRID2015')
    egridBoiler = importeGridBoilerData(dirName)
    egridPlant = importeGridPlantData(dirName)
    egridStateColName = 'Plant state abbreviation'
    statesForAnalysisAbbrev = getStateAbbrevs(statesForAnalysis)
    isolateGensInStates(egridBoiler,statesForAnalysisAbbrev,egridStateColName)
    isolateGensInStates(egridPlant,statesForAnalysisAbbrev,egridStateColName)
    return (egridBoiler,egridPlant)

#Import eGRID boiler data and remove extra headers
#IN: directory w/ egrid data (str)
#OUT: boiler data (2d list)
def importeGridBoilerData(dirName):
    fileName = 'egrid2012_data_boiler.csv'
    fullFileName = os.path.join(dirName,fileName)
    boilerData = readCSVto2dList(fullFileName)
    boilerDataSlim = elimExtraneousHeaderInfo(boilerData,'eGRID2012 file boiler sequence number')
    return boilerDataSlim

#Import eGRID plant data and remove extra headers
#IN: directory w/ egrid data (str)
#OUT: plant data (2d list)
def importeGridPlantData(dirName):
    fileName = 'egrid2012_data_plant.csv'
    fullFileName = os.path.join(dirName,fileName)
    plantData = readCSVto2dList(fullFileName)
    plantDataSlim = elimExtraneousHeaderInfo(plantData,'eGRID2012 file plant sequence number')
    return plantDataSlim

#Eliminates first several rows in egrid CSV that has no useful info
#IN: eGRID fleet (2d list), value in col 0 in first row w/ valid data that want
#to save (str)
#OUT: eGRID fleet (2d list)
def elimExtraneousHeaderInfo(egridFleet,valueInFirstValidRow):
    for idx in range(len(egridFleet)):
        if egridFleet[idx][0]==valueInFirstValidRow:
            egridFleetSlim = copy.deepcopy(egridFleet[idx:])
    return egridFleetSlim

#Removes retired units from fleet based on input year
#IN: gen fleet (2d list), year below which retired units should be removed
#from fleet (int)
def removeRetiredUnits(baseGenFleet,retirementYearScreen):
    colName = "Retirement Year"
    colNum = baseGenFleet[0].index(colName)
    rowsToRemove= []
    for rowIdx in range(1,len(baseGenFleet)):
        retireYear = baseGenFleet[rowIdx][colNum]
        if int(retireYear)<retirementYearScreen: rowsToRemove.append(rowIdx)
    if rowsToRemove != []: removeRows(baseGenFleet,rowsToRemove)

#Isolates fleet to generators in states of interest
#IN: gen fleet (2d list), states for analyiss (1d list), col name w/ state data
#(str)
#OUT: gen fleet (2d list)
def isolateGensInStates(baseGenFleet,statesForAnalysis,colName):
    rowsToRemove = identifyRowsToRemove(baseGenFleet,statesForAnalysis,
                                        colName)
    removeRows(baseGenFleet,rowsToRemove)
    return baseGenFleet

#Isolates fleet to generators in power system of interest
#IN: gen fleet (2d list), power sys for analyiss (1d list)
#OUT: gen fleet (2d list)
def isolateGensInPowerSystem(baseGenFleet,powerSystemsForAnalysis):
    colName = "Region Name"
    rowsToRemove = identifyRowsToRemove(baseGenFleet,powerSystemsForAnalysis,
                                        colName)
    removeRows(baseGenFleet,rowsToRemove)
    return baseGenFleet

#Import PHORUM data (VOM + UC parameters)
def importPhorumData(runLoc):
    if runLoc == 'pc': dirName = 'C:\\Users\\mtcraig\\Desktop\\EPP Research\\Databases\\PHORUM'
    else: dirName = 'Data'
    fileName = 'PHORUMUCParameters10Jun2016CapacExpPaper.csv'
    return readCSVto2dList(os.path.join(dirName,fileName))

################################################################################

################################################################################
#ADD RANDOM OP COST ADDER TO FLEET IN NEW COLUMN
#Add to all fuel types. Use value of 0.05 - makes up ~0.03% on average of fleet. 
#Max addition to op cost of gen in fleet is 0.19%.  
def addRandomOpCostAdder(baseGenFleet,ocAdderMin,ocAdderMax):
    randValHeader = 'RandOpCostAdder($/MWh)'
    addHeaders(baseGenFleet,[randValHeader])
    randValCol = baseGenFleet[0].index(randValHeader)
    random.seed()
    for row in baseGenFleet[1:]: row.append(random.uniform(ocAdderMin,ocAdderMax))
################################################################################

################################################################################
#ADD REG OFFER COST AND ELIGIBILITY
#Based on params in Denholm 2013, Val of energy sto for grid apps
def addRegResOfferAndElig(baseGenFleet,regupCostCoeffs):
    baseGenFleet[0].extend(['RegOfferCost($/MW)','RegOfferElig'])
    plantTypeCol = baseGenFleet[0].index('PlantType')
    for row in baseGenFleet[1:]:
        currPlantType = row[plantTypeCol]
        if currPlantType in regupCostCoeffs: regupCost,regElig = regupCostCoeffs[currPlantType],1
        else: regupCost,regElig = 0,0
        row.extend([regupCost,regElig])

################################################################################
#GENERAL UTILITY FUNCTIONS
#Get abbreviations (which eGRID uses but NEEDS does not)
#IN: states for analysis (1d list)
#OUT: map of states names to state abbreviations (dict)
def getStateAbbrevs(statesForAnalysis): 
    stateAbbreviations = {'Virginia':'VA','North Carolina':'NC','South Carolina':'SC',
                         'Georgia':'GA','Mississippi':'MS','Alabama':'AL','Louisiana':'LA',
                         'Missouri':'MO','Arkansas':'AR','Illinois':'IL',
                         'Kentucky':'KY','Tennessee':'TN','Texas':'TX'}
    statesForAnalysisAbbrev = []
    for state in statesForAnalysis:
        statesForAnalysisAbbrev.append(stateAbbreviations[state])
    return statesForAnalysisAbbrev

#Returns a list of rows to remove for values in a given column that don't 
#equal any value in valuesToKeep.
#IN: any 2d list, values in specified column to keep (1d list), col name (str)
#OUT: row indices to remove (1d list)
def identifyRowsToRemove(list2d,valuesToKeep,colName):
    headersToColsMap = mapHeadersToCols(list2d)
    colNumber = headersToColsMap[colName]
    rowsToRemove=[]
    for row in range(1,len(list2d)):
        if list2d[row][colNumber] not in valuesToKeep:
            rowsToRemove.append(row)
    return rowsToRemove

#IN: data (2d list), row idx to remove (1d list)
def removeRows(baseGenFleet,rowsToRemove):
    for row in reversed(rowsToRemove):
        baseGenFleet.pop(row)

#Returns a dictionary mapping headers to column numbers
#IN: fleet (2d list)
#OUT: map of header name to header # (dict)
def mapHeadersToCols(fleet):
    headers = fleet[0]
    headersToColsMap = dict()
    for colNum in range(len(headers)):
        header = headers[colNum]
        headersToColsMap[header] = colNum
    return headersToColsMap

#IN: data (2d list), headers to add to first row of data (1d list)
def addHeaders(fleet,listOfHeaders):
    for header in listOfHeaders:
        fleet[0].append(header)

#Returns average of values in input 1d list
def avgListVals(listOfVals):
    (total,count) = (0,0)
    for val in listOfVals:
        total += float(val)
        count += 1
    return total/count

#Removes '.0' from end of ORIS IDs in eGRID
def removeTrailingDecimalFromEgridORIS(egridORISIDs):
    for idx in range(1,len(egridORISIDs)):
        egridORISIDs[idx] = egridORISIDs[idx][:-2]

#Converts a string w/ commas in it to a float
def toNum(s):
    numSegments = s.split(',')
    result = ""
    for segment in numSegments:
        result += segment
    return float(result)

#Return row idx (or False) where list1=data1 and list2=data2
def search2Lists(list1,list2,data1,data2):
    if (data1 not in list1) or (data2 not in list2):
            return False
    for idx in range(len(list1)):
        if list1[idx] == data1 and list2[idx] == data2:
            return idx
    return False
    
#Convert specified column in 2d list to a 1-d list
def colTo1dList(data,colNum):
    listWithColData = []
    for dataRow in data:
        listWithColData.append(dataRow[colNum])
    return listWithColData
################################################################################

################################################################################
#TEST FUNCTIONS
#Several utility functions used here are tested in other scripts. Other 
#functions were tested manually using output test fleets.
def testAvgListVals():
    print('testing avgListVals')
    assert(avgListVals([5,3])==4.0)
    assert(avgListVals(['5','3'])==4.0)
    assert(avgListVals([1,1])==1.0)
    assert(avgListVals([10,8,6])==8.0)
    print('passed')

def testToNum():
    print('testing toNum')
    assert(toNum('50,000')==float(50000))
    assert(toNum('4,000')==float(4000))
    print('passed')

def testSearch2Lists():
    print('testing search2Lists')
    assert(search2Lists([5,3,2],[1,4,4],3,4)==1)
    assert(search2Lists([5,3,2],[1,4,4],3,1)==False)
    assert(search2Lists([5,3,2],[1,4,4],8,8)==False)
    assert(search2Lists([5,3,2],[1,4,4],5,1)==0)
    print('passed')

def testColto1dList():
    print('testing colTo1dList')
    assert(colTo1dList([[3,2],[5,4]],0)==[3,5])
    assert(colTo1dList([[3,2],[5,4]],1)==[2,4])
    print('pasesd')

def testAll():
    testAvgListVals()
    testToNum()
    testSearch2Lists()
    testColto1dList()

# testAll()
################################################################################

# setupGeneratorFleet()