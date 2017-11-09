#Michael Craig
#October 4, 2016
#Process CE results by: 1) save new builds, 2) add new builds to gen fleet, 
#3) determine which units retire due to economics

import copy, os, random
from AuxFuncs import *
from GAMSAuxFuncs import *
from CreateFleetForCELoop import onlineAndNotRetired
from ModifyGeneratorCapacityWithWaterTData import getCellLatAndLongFromFolderName

########### STORE BUILD DECISIONS FROM CAPACITY EXPANSION ######################
#Inputs: running list of CE builds (2d list), CE model output as GAMS object, 
#curr CE year
#Outputs: new gen builds by technology (list of tuples of (techtype, # builds))
def saveCapacExpBuilds(capacExpBuilds,capacExpModel,currYear):
    newGenerators = extract1dVarResultsFromGAMSModel(capacExpModel,'vN')
    add1dVarResultsTo2dList(newGenerators,capacExpBuilds,'UnitsAdded' + str(currYear))
    return newGenerators

#Adds new column of results to a 2d list, maintaining even 2d list & backfilling
#empty cells if necessary for newly added rows.
#Inputs: results to add, 2d list to add results to in new col, header for new col
def add1dVarResultsTo2dList(varResults,list2d,newColHeader):
    list2d[0].append(newColHeader)
    newCol = list2d[0].index(newColHeader)
    if len(list2d)==1: #first time adding values to 2d list, so just headers
        for (symbol,value) in varResults: list2d.append([symbol,value])
    else:
        for row in list2d[1:]: row.append('') #make even 2d list
        rowLabels = [row[0] for row in list2d]
        for (symbol,value) in varResults:
            if symbol in rowLabels:
                symbolRow = rowLabels.index(symbol)
                list2d[symbolRow][newCol] = value
            else:
                list2d.append([symbol] + ['']*(newCol-1) + [value])
                
########### ADD CAPACITY EXPANSION BUILD DECISIONS TO FLEET ####################
#Inputs: gen fleet (2d list), list of new builds (list of tuples of (techtype,#builds)),
#new tech data (2d list), curr year of CE run, OPTIONAL dict of techtype:cell in which
#tech is added.
#Outputs: new gen fleet w/ new CE builds added
def addNewGensToFleet(genFleet,newGenerators,newTechsCE,currYear,ocAdderMin,ocAdderMax,*args):
    genFleetWithCEResults = copy.deepcopy(genFleet)
    print('CE additions in ' + str(currYear) + ':',newGenerators)
    addGeneratorsToFleet(genFleetWithCEResults,newGenerators,newTechsCE,currYear,
                        ocAdderMin,ocAdderMax,*args)
    return genFleetWithCEResults

#Adds generators to fleet
#Inputs: gen fleet to which new builds are added (2d list), new builds (list of tuples
#of (tech,#builds)), curr year, OPTIONAL dict of techtype:cell in which tech is added.
def addGeneratorsToFleet(genFleetWithCEResults,newGenerators,newTechsCE,currYear,
                ocAdderMin,ocAdderMax,*args):
    (techTypeCol,techCapacCol,techHrCol,techVomCol,techFomCol,techCo2EmsCol,techFuelCol,
        techMinDownCol,techRampCol,techMinLoadCol,techStartCostCol,techRegCostCol,
        techRegOfferCol) = get2dListColNums(newTechsCE,'TechnologyType','Capacity(MW)',
        'HR(Btu/kWh)','VOM(2012$/MWh)','FOM(2012$/MW/yr)','CO2EmissionsRate(lb/MMBtu)',
        'FuelType','MinDownTime(hrs)','RampRate(MW/hr)','MinLoad(MW)','StartCost($2011)',
        'RegOfferCost($/MW)','RegOfferElig')
    (fleetOrisCol,fleetUnitCol,fleetStateCol,fleetYearCol,fleetPlantTypeCol,fleetCapacCol,
        fleetHrCol,fleetVomCol,fleetFomCol,fleetFuelCol,fleetCO2EmsCol,fleetMinDownCol,fleetRampCol,
        fleetMinLoadCol,fleetStartCostCol,fleetOnlineYrCol,fleetIPMRetirementCol,fleetLatCol,
        fleetLongCol,fleetRandAdderCol,fleetRegCostCol,fleetRegOfferCol) = get2dListColNums(genFleetWithCEResults,
        'ORIS Plant Code','Unit ID','State Name','YearAddedCE','PlantType','Capacity (MW)',
        'Heat Rate (Btu/kWh)','VOM($/MWh)','FOM($/MW/yr)','Modeled Fuels','CO2EmRate(lb/MMBtu)',
        'MinDownTime(hrs)','RampRate(MW/hr)','MinLoad(MW)','StartCost($)','On Line Year','Retirement Year',
        'Latitude','Longitude','RandOpCostAdder($/MWh)','RegOfferCost($/MW)','RegOfferElig')
    #Get tech values
    techs = [row[techTypeCol] for row in newTechsCE]
    techCapacs = [row[techCapacCol] for row in newTechsCE]
    techHrs = [row[techHrCol] for row in newTechsCE]
    techVoms = [row[techVomCol] for row in newTechsCE]
    techFoms = [row[techFomCol] for row in newTechsCE]
    techCO2Ems = [row[techCo2EmsCol] for row in newTechsCE]
    techFuels = [row[techFuelCol] for row in newTechsCE]
    techMinDowns = [row[techMinDownCol] for row in newTechsCE]
    techRamps = [row[techRampCol] for row in newTechsCE]
    techMinLoads = [row[techMinLoadCol] for row in newTechsCE]
    techStartCosts = [row[techStartCostCol] for row in newTechsCE]
    techRegCosts = [row[techRegCostCol] for row in newTechsCE]
    techRegOffers = [row[techRegOfferCol] for row in newTechsCE]
    #Get max ORIS ID
    newOrisID = max([int(row[fleetOrisCol]) for row in genFleetWithCEResults[1:]])+1
    (state,unitID) = ('Texas','1')
    #For each candidate tech, check if any added, and if so add to fleet
    for (tech,newBuilds) in newGenerators:
        techRow = techs.index(tech)        
        if newBuilds>0: 
            techCapac = techCapacs[techRow]
            techHr = techHrs[techRow]
            techVom = convertCostToTgtYr('vom',float(techVoms[techRow]))
            techFom = convertCostToTgtYr('fom',float(techFoms[techRow]))
            techCO2Em = techCO2Ems[techRow]
            techFuel = techFuels[techRow]
            techMinDown = techMinDowns[techRow]
            techRamp = techRamps[techRow]
            techMinLoad = techMinLoads[techRow]
            techRegCost = techRegCosts[techRow]
            techRegOffer = techRegOffers[techRow]
            techStartCost = convertCostToTgtYr('startup',float(techStartCosts[techRow]))
            for i in range(int(newBuilds)):
                genFleetWithCEResults.append(['']*len(genFleetWithCEResults[0]))
                genFleetWithCEResults[-1][fleetOrisCol] = newOrisID
                newOrisID += 1
                genFleetWithCEResults[-1][fleetUnitCol] = unitID
                genFleetWithCEResults[-1][fleetStateCol] = state
                genFleetWithCEResults[-1][fleetYearCol] = currYear
                genFleetWithCEResults[-1][fleetOnlineYrCol] = currYear
                genFleetWithCEResults[-1][fleetIPMRetirementCol] = 9999
                genFleetWithCEResults[-1][fleetPlantTypeCol] = tech
                genFleetWithCEResults[-1][fleetCapacCol] = techCapac
                genFleetWithCEResults[-1][fleetHrCol] = techHr
                genFleetWithCEResults[-1][fleetVomCol] = techVom
                genFleetWithCEResults[-1][fleetFomCol] = techFom
                genFleetWithCEResults[-1][fleetFuelCol] = techFuel
                genFleetWithCEResults[-1][fleetCO2EmsCol] = techCO2Em
                genFleetWithCEResults[-1][fleetMinDownCol] = techMinDown
                genFleetWithCEResults[-1][fleetRampCol] = techRamp
                genFleetWithCEResults[-1][fleetMinLoadCol] = techMinLoad
                genFleetWithCEResults[-1][fleetStartCostCol] = techStartCost
                genFleetWithCEResults[-1][fleetRandAdderCol] = random.uniform(ocAdderMin,ocAdderMax)
                genFleetWithCEResults[-1][fleetRegCostCol] = techRegCost
                genFleetWithCEResults[-1][fleetRegOfferCol] = techRegOffer
                if len(args)==1: 
                    techCells = args[0]
                    (cellLat,cellLong) = getCellLatAndLongFromFolderName(techCells[tech])
                    genFleetWithCEResults[-1][fleetLatCol] = cellLat
                    genFleetWithCEResults[-1][fleetLongCol] = cellLong

#Returns column numbers of 2d list based on 2d list's  headers for input
#header names.
def get2dListColNums(list2d,*args):
    return [list2d[0].index(colName) for colName in args]

########### FIND AND MARK UNITS RETIRED BY CE ##################################
#Retire units based on generation. Only retire coal units. In last CE run,
#only retire units up to planning margin. 
#Inputs: gen fleet, CF below which coal plants should retire based on generation
#in last CE run, CE output as GAMS obj, curr year, running 2d list of gen in each CE run for each 
#generator, running 2d list of units retired by CE model for economic reasons, 
#scale MW to GW, 1d list of hours input to CE, plannig reserve margin, 
#end year for CE runs, running 2d list of units retired due to age
#Outputs: gen fleet w/ gens that retire for econ reasons per most recent CE run marked 
def selectAndMarkUnitsRetiredByCE(genFleet,genFleetForCE,retirementCFCutoff,capacExpModel,currYear,capacExpGenByGens,
            capacExpRetiredUnitsByCE,scaleMWtoGW,hoursForCE,planningReserve,endYear,
            capacExpRetiredUnitsByAge,demandCE,hourlyWindGenCE,hourlySolarGenCE,newWindCFsCE,
            newSolarCFsCE,plantTypesEligibleForRetirementByCF):
    genFleetUpdated = [genFleet[0]] + [row for row in genFleet[1:] if onlineAndNotRetired(row,genFleet[0],currYear)]
    (retiredUnitsByCE,ceHoursGenByGens) = selectRetiredUnitsByCE(retirementCFCutoff,capacExpModel,
            genFleetUpdated,genFleetForCE,scaleMWtoGW,hoursForCE,planningReserve,currYear,endYear,
            demandCE,hourlyWindGenCE,hourlySolarGenCE,newWindCFsCE,newSolarCFsCE,
            plantTypesEligibleForRetirementByCF)
    print('Num units that retire due to economics in ' + str(currYear) + ':' + str(len(retiredUnitsByCE)))
    saveAnnualGenByGens(ceHoursGenByGens,capacExpGenByGens,currYear)
    capacExpRetiredUnitsByCE.append(['UnitsRetiredByCE' + str(currYear)] + retiredUnitsByCE)
    genFleetWithRetirements = copy.deepcopy(genFleet)
    markRetiredUnitsFromCE(genFleetWithRetirements,retiredUnitsByCE,currYear)
    return genFleetWithRetirements

#Determines which units retire for economic reasons after CE run.
#Inputs: see prior function. genFleetUpdated = gen fleet w/ only online units.
#Outputs: 1d list of gens that retire for economic reasons, dictionary of 
#genID:total gen over CE hours in CE run.
def selectRetiredUnitsByCE(retirementCFCutoff,capacExpModel,genFleetUpdated,genFleetForCE,
        scaleMWtoGW,hoursForCE,planningReserve,currYear,endYear,demandCE,hourlyWindGenCE,
        hourlySolarGenCE,newWindCFsCE,newSolarCFsCE,plantTypesEligibleForRetirementByCF):
    hourlyGenByGens = extract2dVarResultsIntoDict(capacExpModel,'vGen') #(hr,genID):hourly gen [GW]
    ceHoursGenByGens = sumHourlyGenByGensInCE(hourlyGenByGens,scaleMWtoGW)
    gensEligToRetireCFs = getGenCFsInCE(ceHoursGenByGens,genFleetUpdated,genFleetForCE,
                                        plantTypesEligibleForRetirementByCF,hoursForCE)
    unitsToRetire = retireUnitsByCF(retirementCFCutoff,gensEligToRetireCFs,planningReserve,
                                    currYear,endYear,genFleetUpdated,demandCE,hourlyWindGenCE,
                                    hourlySolarGenCE,newWindCFsCE,newSolarCFsCE)
    return (unitsToRetire,ceHoursGenByGens)

#Sum generation by each generator in CE run (so only for hours in CE model)
#Inputs: dictionary of (hr,genID):hourly gen [GWh], scale MW to GW
#Outputs: dictionary of genID:total annual gen
def sumHourlyGenByGensInCE(hourlyGenByGens,scaleMWtoGW):
    ceHoursGenByGens = dict()
    for (genSymbol,hourSymbol) in hourlyGenByGens:
        if genSymbol not in ceHoursGenByGens:
            ceHoursGenByGens[genSymbol] = float(hourlyGenByGens[(genSymbol,hourSymbol)]) * scaleMWtoGW
        else:
            ceHoursGenByGens[genSymbol] += float(hourlyGenByGens[(genSymbol,hourSymbol)]) * scaleMWtoGW
    return ceHoursGenByGens

#Inputs: total gen by generators for CE hours (dict of genID:total gen), gen fleet 
#only w/ online generators (2d list), list of plant types that can retire based on CF,
#1d list of hours input to CE
#Outputs: dictionary (genID:CF) for generators eligible to retire based on CF
def getGenCFsInCE(ceHoursGenByGens,genFleetUpdated,genFleetForCE,
                plantTypesEligibleForRetirementByCF,hoursForCE):
    gensEligToRetireCFs = dict()
    (capacCol,plantTypeCol) = (genFleetUpdated[0].index('Capacity (MW)'),
                                genFleetUpdated[0].index('PlantType'))
    genSymbolsForFleet = [createGenSymbol(row,genFleetUpdated[0]) for row in genFleetUpdated]
    genSymbolsForCEFleet = [createGenSymbol(row,genFleetForCE[0]) for row in genFleetForCE]
    for gen in ceHoursGenByGens:
        #Need to screen out wind and solar plants in genFleetForCE, since these
        #are tacked on @ end and are not in genFleetUpdated. Consequently, if don't
        #have this if statement and don't build new plants, genSymbolsForFleet.index(gen)
        #call will not find gen listed.
        if (genFleetForCE[genSymbolsForCEFleet.index(gen)][plantTypeCol] != 'Wind' and 
                    genFleetForCE[genSymbolsForCEFleet.index(gen)][plantTypeCol] != 'Solar PV'):
            if genFleetUpdated[genSymbolsForFleet.index(gen)][plantTypeCol] in plantTypesEligibleForRetirementByCF:
                genCapac = genFleetUpdated[genSymbolsForFleet.index(gen)][capacCol]
                genCF = ceHoursGenByGens[gen]/(float(genCapac)*len(hoursForCE))
                gensEligToRetireCFs[gen] = genCF
    return gensEligToRetireCFs

#Determines which units retire due to CF.
#Inputs: CF cutoff retirement, dictionary (genID:CF) for generators eligible to retire based on CF,
#planning reserve, curr & end year, gen fleet w/ only online gens
#Outputs: 1d list of units to retire for economic reasons
def retireUnitsByCF(retirementCFCutoff,gensEligToRetireCFs,planningReserve,currYear,endYear,
                    genFleetUpdated,demandCE,hourlyWindGenCE,hourlySolarGenCE,newWindCFsCE,newSolarCFsCE):
    unitsToRetire = []
    if len(gensEligToRetireCFs) > 0: 
        minCF = min([gensEligToRetireCFs[gen] for gen in gensEligToRetireCFs])
        if minCF < retirementCFCutoff: #if any plants eligible for retirement
            # if currYear < endYear: #not in final CE loop, so retire all units w/ CF < cutoff
            #     addAllUnitsWithCFBelowCutoff(gensEligToRetireCFs,retirementCFCutoff,unitsToRetire)
            # else: #if last CE loop, retire units below CF cutoff in order of inc CF until hit planning reserve
            addUnitsWithCFBelowCutoffUntilPlanningMargin(gensEligToRetireCFs,retirementCFCutoff,
                            unitsToRetire,genFleetUpdated,planningReserve,demandCE,
                            hourlyWindGenCE,hourlySolarGenCE,newWindCFsCE,newSolarCFsCE,currYear)
    return unitsToRetire

#Inputs: gen fleet w/ only online units, demand and existing + new RE gen info, curr year. 
#Outputs: fleet capacity @ hour of peak demand / planning reserve, accounting
#for hourly variability in RE generation.
def sumFleetCapac(genFleetUpdated,demandCE,hourlyWindGenCE,hourlySolarGenCE,
                    newWindCFsCE,newSolarCFsCE,currYear):
    capacCol,plantTypeCol = genFleetUpdated[0].index('Capacity (MW)'),genFleetUpdated[0].index('PlantType')
    peakDemandHour = demandCE.index(max(demandCE))
    existWindGenAtPeak,existSolarGenAtPeak = hourlyWindGenCE[peakDemandHour],hourlySolarGenCE[peakDemandHour]
    newWindCFAtPeak,newSolarCFAtPeak = newWindCFsCE[peakDemandHour],newSolarCFsCE[peakDemandHour]
    newWindRows = getNewRERows('Wind',genFleetUpdated,currYear)
    newSolarRows = getNewRERows('Solar PV',genFleetUpdated,currYear)
    newWindCapac = sum([float(row[capacCol]) for row in newWindRows])
    newSolarCapac = sum([float(row[capacCol]) for row in newSolarRows])
    otherRows = [row for row in genFleetUpdated[1:] if (row[plantTypeCol] not in ('Wind','Solar PV'))]
    nonRECapacs = sum([float(row[capacCol]) for row in otherRows])
    return (nonRECapacs + existWindGenAtPeak + existSolarGenAtPeak + 
            newWindCFAtPeak * newWindCapac + newSolarCFAtPeak * newSolarCapac)

#Return new RE rows for given plant type    
def getNewRERows(plantType,fleet,currYear):
    plantTypeCol = fleet[0].index('PlantType')
    yearAddedCECol = fleet[0].index('YearAddedCE')
    return [row for row in fleet if (row[plantTypeCol] == plantType and row[yearAddedCECol] == currYear)]

#Adds all units elig to retire w/ CF below cutoff to unitsToRetire list
#Inputs: dictionary (genID:CF) for gens elig to retire, retirement CF cutoff,
#empty list to which genIDs for units that should retire are added
def addAllUnitsWithCFBelowCutoff(gensEligToRetireCFs,retirementCFCutoff,unitsToRetire):
    for gen in gensEligToRetireCFs: 
        genCF = gensEligToRetireCFs[gen]
        if genCF < retirementCFCutoff: unitsToRetire.append(gen)

#In order of increasing CF, adds gens w/ CF below cutoff to to-retire list
#until fleet capacity hits planning reserve margin.
#Inputs: dict (genID:CF) for gens elig to retire, retirement CF cutoff, empty
#list for units that will be retired, gen fleet, planning reseve (MW)
def addUnitsWithCFBelowCutoffUntilPlanningMargin(gensEligToRetireCFs,retirementCFCutoff,
                    unitsToRetire,genFleetUpdated,planningReserve,demandCE,hourlyWindGenCE,
                    hourlySolarGenCE,newWindCFsCE,newSolarCFsCE,currYear):
    (gensWithCFBelowCutoff,genCFsWithCFBelowCutoff) = ([],[])
    #Get list of genIDs that are eligible to retire based on CF
    for gen in gensEligToRetireCFs:
        genCF = gensEligToRetireCFs[gen]
        if genCF < retirementCFCutoff: 
            gensWithCFBelowCutoff.append(gen)
            genCFsWithCFBelowCutoff.append(genCF)
    print('Gens with CF below cutoff:',gensWithCFBelowCutoff)
    print('Gen CFs with CF below cutoff:',genCFsWithCFBelowCutoff)
    #Retire units until hit planning margin
    totalFleetCapac = sumFleetCapac(genFleetUpdated,demandCE,hourlyWindGenCE,
                                hourlySolarGenCE,newWindCFsCE,newSolarCFsCE,currYear)
    retiredCapac = 0
    capacCol = genFleetUpdated[0].index('Capacity (MW)')
    genSymbolsForFleet = [createGenSymbol(row,genFleetUpdated[0]) for row in genFleetUpdated]
    while totalFleetCapac - retiredCapac > planningReserve and len(gensWithCFBelowCutoff)>0:
        minCFIdx = genCFsWithCFBelowCutoff.index(min(genCFsWithCFBelowCutoff))
        genId = gensWithCFBelowCutoff[minCFIdx]
        unitsToRetire.append(genId) 
        gensWithCFBelowCutoff.pop(minCFIdx)
        genCFsWithCFBelowCutoff.pop(minCFIdx)
        retiredCapac += float(genFleetUpdated[genSymbolsForFleet.index(genId)][capacCol])

#Convert dict of genID:total gen into list of tuples, then add those values
#to 2d list.
#Inputs: dict of genID:total gen in last CE run, running 2d list of 
#generation by each generator for each CE run, curr year
def saveAnnualGenByGens(ceHoursGenByGens,capacExpGenByGens,currYear):
    annualGenByGenTupleList = [(key,ceHoursGenByGens[key]) for key in ceHoursGenByGens]
    add1dVarResultsTo2dList(annualGenByGenTupleList,capacExpGenByGens,'AnnualGen(MW)' + str(currYear))

#Marks which generators retire due to econ reasons per most recent CE run.
#Inputs: gen fleet w/ only online units, list of units retired for econ reasons,
#curr year
def markRetiredUnitsFromCE(genFleetWithRetirements,retiredUnitsByCE,currYear):
    retiredCol = genFleetWithRetirements[0].index('YearRetiredByCE')
    orisCol = genFleetWithRetirements[0].index('ORIS Plant Code')
    unitIdCol = genFleetWithRetirements[0].index('Unit ID')
    genSymbols = [createGenSymbol(row,genFleetWithRetirements[0]) for row in genFleetWithRetirements]
    for retiredUnit in retiredUnitsByCE:
        fleetRow = genSymbols.index(retiredUnit)
        genFleetWithRetirements[fleetRow][retiredCol] = currYear

########### SAVE CAPACITY EXPANSION RESULTS ####################################
#Write some results into CSV files
def writeCEInfoToCSVs(capacExpBuilds,capacExpGenByGens,capacExpRetiredUnitsByCE,
                    capacExpRetiredUnitsByAge,resultsDir,currYear):
    write2dListToCSV(capacExpBuilds,os.path.join(resultsDir,'genAdditionsCE' + str(currYear) + '.csv'))
    write2dListToCSV(capacExpGenByGens,os.path.join(resultsDir,'genByGensCE' + str(currYear) + '.csv'))
    write2dListToCSV(capacExpRetiredUnitsByCE,os.path.join(resultsDir,'genRetirementsEconCE' + str(currYear) + '.csv'))
    write2dListToCSV(capacExpRetiredUnitsByAge,os.path.join(resultsDir,'genRetirementsAgeCE' + str(currYear) + '.csv'))
