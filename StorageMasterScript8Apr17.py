#Michael Craig, 31 May 2016
#Run capacity expansion and dispatch models w/ climate impacts.

import os, csv, operator, copy, time, random
import numpy as np
import datetime as dt
from gams import *
from AuxFuncs import *
from GAMSAuxFuncs import *
from SetupGeneratorFleet import *
from RemoveHydroFromFleetAndDemand import removeHydroFromFleetAndDemand
from ImportERCOTDemand import importHourlyERCOTDemand
from ImportRegReserveDataERCOT import importRegReserveData
from UpdateFuelPriceFuncs import *
from DemandFuncs import *
from DemandFuncsCE import *
from CO2CapCalculations import getCo2Cap,interpolateCO2Cap
from SetInitCondsUC import *
from ImportNewTechs import getNewTechs
from RetireUnitsCFPriorCE import retireUnitsCFPriorCE
from CreateFleetForCELoop import createFleetForCurrentCELoop, onlineAndNotRetired
from GetRenewableCFs import getRenewableCFs
from GetNewRenewableCFs import getNewWindAndSolarCFs, trimNewRECFsToCEHours
from TrimRegResToCEHours import trimRegResToCEHours
from ProcessCEResults import *
from ScaleRegResForAddedWind import scaleRegResForAddedWind
from CombineWindAndSolarGensToSingleGen import combineWindAndSolarToSinglePlant
from AddStorageToGenFleet import addStorageToGenFleet
from TrimDemandREGenAndResForUC import getDemandAndREGenForUC,getResForUC
from GAMSAddSetToDatabaseFuncs import *
from GAMSAddParamToDatabaseFuncs import *
from ConvertCO2CapToPrice import convertCo2CapToPrice
from SetInitChargeState import setInitChargeFirstUC, setInitChargePerPriorUC
from SetupResultLists import setupHourlyResultsByPlant,setupHourlySystemResults
from SetupHourlyGenByStorageUnit import setupHourlyResultsBySto
from SaveHourlyResults import saveHourlyResultsByPlant,saveHourlySystemResults,saveHourlyStoResults
from WriteUCResults import writeHourlyResultsByPlant, writeHourlyStoResults
from InitializeOnOffExistingGensCE import initializeOnOffExistingGens
from ReservesWWSIS import calcWWSISReserves
from GetIncResForAddedRE import getIncResForAddedRE
from SaveCEOperationalResults import saveCapacExpOperationalData
from LoadCEFleet import loadCEFleet

################################################################################
###### UNIVERSAL PARAMETERS ####################################################
################################################################################
def setKeyParameters():
    #KEY PARAMETERS
    runLoc = 'remote' #'pc' or 'remote'. If remote, assumes all data is in local dir. 
    xsedeRun = False #whether running on XSEDE supercomputer (affects sys_dir in GAMS call)
    #Scenarios:solar & nuclear = low cap costs, ng = low fuel price, coalret = early coal rets, highSto = more sto
    scenario = 'coalret' #cpp, deep, solar, nuclear, ng, coalret, highSto, base, highStoEff 
    co2CapScenario = 'cpp' #cpp, deep, or none (deep = 80% redux from 1990 by 2050)
    runCE,runUC = True,False
    (startYear,endYear,yearStepCE) = (2015,2046,5)
    daysPerSeason = 2
    runFirstUCYear = False #run UC 2015 year
    firstUCYear = 2015
    daysForUC = [val for val in range(1,366)] #start @ 1, go to 1 past end day (e.g., 366 for full year)
    stoScenarios = ['NoSto','StoEnergy','StoRes','StoEnergyAndRes']
    annualDemandGrowth = 0 #fraction per year
    mdtInCE = True
    #GENERAL PARAMETERS
    demandYear = 2015
    testModel = False #use dummy test system; not currently working
    states = ['Texas'] 
    statesAbbrev = ['TX']
    powerSystems =  ['ERC_REST','ERC_WEST','ERC_FRNT','ERC_GWAY'] #GWAY & FRNT are only 1 plant each
    compressFleet = True
    fuelPricesTimeSeries = importFuelPrices(runLoc,scenario)
    ocAdderMin,ocAdderMax = 0,0.05
    if runFirstUCYear == True: resultsDir = 'ResultsC' + co2CapScenario + 'UC' + str(firstUCYear)
    else: resultsDir = ('ResultsS' + scenario + 'C' + co2CapScenario)
    if not os.path.exists(resultsDir): os.makedirs(resultsDir)
    #CO2 CAP PARAMETERS
    co2CapEndYr,co2CapEnd = getCo2Cap(co2CapScenario)
    #RENEWABLE CAPACITY FACTOR PARAMETERS
    tzAnalysis = 'CST'
    projectName = 'storage'
    windGenDataYr = 2005
    #CAPACITY EXPANSION PARAMETERS
    if mdtInCE == True: capacExpFilename = 'CEChronoUCConstraints12Jan17MDT.gms'
    else: capacExpFilename = 'CEChronoUCConstraints12Jan17.gms'
    incITC = True
    retirementCFCutoff = .5 #retire units w/ CF lower than given value
    planningReserveMargin = 0.1375 #fraction of peak demand; ERCOT targeted planning margin
    discountRate = 0.07 #fraction    
    allowCoalWithoutCCS = False
    onlyNSPSUnits = True
    ptEligRetCF = ['Coal Steam']
    maxAddedCapacPerTech = 20000 #MW
    #UNIT COMMITMENT PARAMETERS
    calculateCO2Price = True
    (daysOpt,daysLA) = (1,1)
    #CONVERSION PARAMETERS
    scaleMWtoGW = 1000
    scaleDollarsToThousands = 1000
    scaleLbToShortTon = 2000    
    return (runLoc,testModel,states,statesAbbrev,powerSystems,compressFleet,fuelPricesTimeSeries,
        co2CapEndYr,co2CapEnd,capacExpFilename,startYear,endYear,yearStepCE,retirementCFCutoff,
        daysPerSeason,planningReserveMargin,discountRate,allowCoalWithoutCCS,onlyNSPSUnits,
        calculateCO2Price,scaleMWtoGW,scaleDollarsToThousands,scaleLbToShortTon,
        annualDemandGrowth,stoScenarios,daysForUC,daysOpt,daysLA,tzAnalysis,projectName,
        ocAdderMin,ocAdderMax,maxAddedCapacPerTech,windGenDataYr,resultsDir,runCE,
        runUC,xsedeRun,scenario,runFirstUCYear,demandYear,firstUCYear,ptEligRetCF,incITC)

#Import fuel price future time series
def importFuelPrices(runLoc,scenario):
    if runLoc == 'pc': fuelPriceDir = 'C:\\Users\\mtcraig\\Desktop\\EPP Research\\Databases\\FuelPricesCapacityExpansion'
    else: fuelPriceDir = 'Data'
    if scenario == 'ng': fuelFileName = 'FuelPriceTimeSeries2Aug2016LowNG.csv'
    else: fuelFileName = 'FuelPriceTimeSeries2Aug2016.csv'
    return readCSVto2dList(os.path.join(fuelPriceDir,fuelFileName))

#Define reserve parameters for UC & CE w/ UC constraints models
def defineReserveParameters():
    #Requirement parameters - based on WWSIS Phase 2
    regLoadFrac = .01 #frac of hourly load in reg up & down
    contLoadFrac = .03 #frac of hourly load in contingency
    regErrorPercentile = 95 #percentile of 10-m wind & 5-m solar forecast errors used in reg reserves
    flexErrorPercentile = 70 #percentile of hourly wind & solar forecast errors used in reg reserves
    #Cost coeff - from Denholm et al. 2013, val of E sto in grid apps
    regUpCostCoeffs = {'Combined Cycle':6,'Combined Cycle CCS':6,'O/G Steam':4,
                        'Coal Steam':10,'Coal Steam CCS':10} #$/MWh
    #Timeframes
    regReserveMinutes = 5 #reg res must be provided w/in 5 mins
    flexReserveMinutes = 10 #spin reserves must be provided w/in 10 minutes
    contingencyReserveMinutes = 30 #contingency res must be provided w/in 30 minutes
    minutesPerHour = 60
    rampRateToRegReserveScalar = regReserveMinutes/minutesPerHour #ramp rate in MW/hr
    rampRateToFlexReserveScalar = flexReserveMinutes/minutesPerHour #ramp rate in MW/hr
    rampRateToContReserveScalar = contingencyReserveMinutes/minutesPerHour
    return (regLoadFrac,contLoadFrac,regErrorPercentile,flexErrorPercentile,
        regUpCostCoeffs,rampRateToRegReserveScalar,rampRateToFlexReserveScalar,
        rampRateToContReserveScalar)
################################################################################
################################################################################
################################################################################

################################################################################
###### MASTER FUNCTION #########################################################
################################################################################
def masterFunction():
    (runLoc,testModel,states,statesAbbrev,powerSystems,compressFleet,fuelPricesTimeSeries,
        co2CapEndYr,co2CapEnd,capacExpFilename,startYear,endYear,yearStepCE,retirementCFCutoff,
        daysPerSeason,planningReserveMargin,discountRate,allowCoalWithoutCCS,onlyNSPSUnits,
        calculateCO2Price,scaleMWtoGW,scaleDollarsToThousands,scaleLbToShortTon,annualDemandGrowth,
        stoScenarios,daysForUC,daysOpt,daysLA,tzAnalysis,projectName,ocAdderMin,ocAdderMax,
        maxAddedCapacPerTech,windGenDataYr,resultsDir,runCE,runUC,xsedeRun,scenario,
        runFirstUCYear,demandYear,firstUCYear,ptEligRetCF,incITC) = setKeyParameters()
    (regLoadFrac,contLoadFrac,regErrorPercentile,flexErrorPercentile,regUpCostCoeffs,
        rrToRegTime,rrToFlexTime,rrToContTime) = defineReserveParameters()
    (genFleet,demandProfile) = getInitialFleetAndDemand(testModel,states,powerSystems,endYear,
                startYear,fuelPricesTimeSeries,compressFleet,runLoc,resultsDir,ocAdderMin,ocAdderMax,
                regUpCostCoeffs,demandYear)
    print('Set up initial data')    
    (capacExpModelsEachYear,capacExpBuilds,capacExpGenByGens,capacExpRetiredUnitsByCE,
            capacExpRetiredUnitsByAge) = ([],[['TechnologyType']],[['ORIS+UnitID']],[],[])
    for currYear in range(startYear,endYear,yearStepCE):
        currCo2Cap = interpolateCO2Cap(currYear,co2CapEndYr,co2CapEnd)
        print('**CAP:',currCo2Cap)
        demandWithGrowth = scaleDemandForGrowthAndEE(demandProfile,annualDemandGrowth,demandYear,currYear)
        if currYear > firstUCYear and runCE == True:
            if currYear == startYear + yearStepCE: 
                print('first CE run!',currYear)
                priorCapacExpModel,priorHoursCE = None,None #first CE run
            (genFleet,genFleetNoRetiredUnits,priorCapacExpModel,priorHoursCE) = runCapacityExpansion(genFleet,
                demandWithGrowth,startYear,currYear,endYear,planningReserveMargin,
                discountRate,fuelPricesTimeSeries,states,statesAbbrev,scaleMWtoGW,scaleDollarsToThousands,
                currCo2Cap,allowCoalWithoutCCS,capacExpFilename,
                onlyNSPSUnits,daysPerSeason,retirementCFCutoff,scaleLbToShortTon,
                tzAnalysis,projectName,runLoc,resultsDir,capacExpModelsEachYear,capacExpBuilds,
                capacExpGenByGens,capacExpRetiredUnitsByCE,capacExpRetiredUnitsByAge,
                ocAdderMin,ocAdderMax,maxAddedCapacPerTech,windGenDataYr,regLoadFrac,
                contLoadFrac,regErrorPercentile,flexErrorPercentile,rrToRegTime,
                rrToFlexTime,rrToContTime,regUpCostCoeffs,xsedeRun,scenario,ptEligRetCF,
                priorCapacExpModel,priorHoursCE,incITC)
        if runUC == True:
            #Either only runs 2015, or runs in all but 2015
            if ((currYear == firstUCYear and runFirstUCYear == True) or 
                (currYear > firstUCYear and runFirstUCYear == False)):
                if currYear == firstUCYear: genFleetNoRetiredUnits = genFleet
                else: genFleetNoRetiredUnits = loadCEFleet(currYear,resultsDir)
                for stoScenario in stoScenarios:
                    (ucResultsByDay,hourlyGenerationByPlants) = runUnitCommitment(genFleetNoRetiredUnits,
                        demandWithGrowth,startYear,currYear,fuelPricesTimeSeries,states,statesAbbrev,
                        scaleMWtoGW,scaleDollarsToThousands,currCo2Cap,calculateCO2Price,scaleLbToShortTon,
                        daysForUC,daysOpt,daysLA,tzAnalysis,projectName,runLoc,resultsDir,
                        stoScenario,ocAdderMin,ocAdderMax,windGenDataYr,regLoadFrac,contLoadFrac,
                        regErrorPercentile,flexErrorPercentile,rrToRegTime,rrToFlexTime,rrToContTime,
                        copy.deepcopy(regUpCostCoeffs),xsedeRun,runCE,scenario)
################################################################################
################################################################################
################################################################################

################################################################################
####### SET UP INITIAL FLEET AND DEMAND ########################################
################################################################################
def getInitialFleetAndDemand(testModel,states,powerSystems,endYear,startYear,
        fuelPricesTimeSeries,compressFleet,runLoc,resultsDir,ocAdderMin,ocAdderMax,
        regUpCostCoeffs,demandYear):
    genFleet = setupGeneratorFleet(testModel,states,powerSystems,endYear,startYear,
            fuelPricesTimeSeries,compressFleet,runLoc,ocAdderMin,ocAdderMax,regUpCostCoeffs)
    demandProfile = importHourlyERCOTDemand(demandYear,runLoc)
    write2dListToCSV([demandProfile],os.path.join(resultsDir,'demandInitial.csv'))
    (genFleetNoHydro,demandMinusHydroGen) = removeHydroFromFleetAndDemand(genFleet,demandProfile,runLoc)
    #Add placeholder columns for additions & retirements by CE
    ceHeaders = ['YearAddedCE','YearRetiredByCE','YearRetiredByAge']
    genFleetNoHydro[0].extend(ceHeaders)
    for row in genFleetNoHydro[1:]: row.extend(['']*len(ceHeaders))
    write2dListToCSV(genFleetNoHydro,os.path.join(resultsDir,'genFleetInitial.csv'))
    return (genFleetNoHydro,demandMinusHydroGen)
################################################################################
################################################################################
################################################################################

################################################################################
####### RUN CAPACITY EXPANSION #################################################
################################################################################
def runCapacityExpansion(genFleet,demandWithGrowth,startYear,currYear,endYear,
        planningReserveMargin,discountRate,fuelPricesTimeSeries,states,statesAbbrev,
        scaleMWtoGW,scaleDollarsToThousands,currCo2Cap,allowCoalWithoutCCS,
        capacExpFilename,onlyNSPSUnits,daysPerSeason,retirementCFCutoff,scaleLbToShortTon,
        tzAnalysis,projectName,runLoc,resultsDirOrig,capacExpModelsEachYear,capacExpBuilds,
        capacExpGenByGens,capacExpRetiredUnitsByCE,capacExpRetiredUnitsByAge,
        ocAdderMin,ocAdderMax,maxAddedCapacPerTech,windGenDataYr,regLoadFrac,contLoadFrac,
        regErrorPercentile,flexErrorPercentile,rrToRegTime,rrToFlexTime,rrToContTime,
        regUpCostCoeffs,xsedeRun,scenario,ptEligRetCF,priorCapacExpModel,priorHoursCE,incITC):
    resultsDir = os.path.join(resultsDirOrig,'CE')
    if not os.path.exists(resultsDir): os.makedirs(resultsDir)
    print('Entering CE loop for year ' + str(currYear))
    write2dListToCSV([[currCo2Cap]],os.path.join(resultsDir,'co2CapCE' + str(currYear) + '.csv'))
    newTechsCE = getNewTechs(allowCoalWithoutCCS,onlyNSPSUnits,regUpCostCoeffs,currYear,
                            runLoc,resultsDir,scenario,incITC)
    updateFuelPrices(genFleet,newTechsCE,currYear,fuelPricesTimeSeries)
    write2dListToCSV(newTechsCE,os.path.join(resultsDir,'newTechsCE' + str(currYear) + '.csv'))
    if priorCapacExpModel != None: #if not in first CE loop
        unitsRetireCFPriorCE = retireUnitsCFPriorCE(genFleet,retirementCFCutoff,priorCapacExpModel,
                priorHoursCE,scaleMWtoGW,ptEligRetCF,currYear)
        print('Num units that retire due to econ from prior CE ' + str(currYear) + ':' + str(len(unitsRetireCFPriorCE)))
        write2dListToCSV([unitsRetireCFPriorCE],os.path.join(resultsDir,'genRetirementsEconCEPrior' + str(currYear) + '.csv'))
    genFleetForCE = createFleetForCurrentCELoop(genFleet,currYear,capacExpRetiredUnitsByAge,
            runLoc,scenario) #removes all retired units
    print('Num units that retire due to age in ' + str(currYear) + ':' + str(len(capacExpRetiredUnitsByAge[-1])-1))
    write2dListToCSV(genFleetForCE,os.path.join(resultsDir,'genFleetForCEPreRECombine' + str(currYear) + '.csv'))
    combineWindAndSolarToSinglePlant(genFleetForCE,runLoc)
    write2dListToCSV(genFleetForCE,os.path.join(resultsDir,'genFleetForCE' + str(currYear) + '.csv'))
    (startWindCapacForCFs,startSolarCapacForCFs) = (0,0)
    (windCFs,windCfsDtHr,windCfsDtSubhr,ewdIdAndCapac,solarCFs,solarCfsDtHr,solarCfsDtSubhr,
        solarFilenameAndCapac) = getRenewableCFs(genFleetForCE,startWindCapacForCFs,startSolarCapacForCFs,
        states,statesAbbrev,'region',tzAnalysis,projectName,runLoc,windGenDataYr)
    write2dListToCSV(windCFs,os.path.join(resultsDir,'windCFsFullYrCE' + str(currYear) + '.csv'))
    write2dListToCSV(windCfsDtHr,os.path.join(resultsDir,'windCFsDtFullYrCE' + str(currYear) + '.csv'))
    write2dListToCSV(windCfsDtSubhr,os.path.join(resultsDir,'windCFsDtSubhrFullYrCE' + str(currYear) + '.csv'))
    write2dListToCSV(ewdIdAndCapac,os.path.join(resultsDir,'windIdAndCapacCE' + str(currYear) + '.csv'))
    write2dListToCSV(solarCFs,os.path.join(resultsDir,'solarCFsFullYrCE' + str(currYear) + '.csv'))
    write2dListToCSV(solarCfsDtHr,os.path.join(resultsDir,'solarCFsDtFullYrCE' + str(currYear) + '.csv'))
    write2dListToCSV(solarCfsDtSubhr,os.path.join(resultsDir,'solarCFsDtSubhrFullYrCE' + str(currYear) + '.csv'))
    write2dListToCSV(solarFilenameAndCapac,os.path.join(resultsDir,'solarIdAndCapacCE' + str(currYear) + '.csv'))
    (netDemand,hourlyWindGen,hourlySolarGen) = getNetDemand(demandWithGrowth,windCFs,
                ewdIdAndCapac,solarCFs,solarFilenameAndCapac,currYear,'CE',resultsDir)
    write2dListToCSV([demandWithGrowth],os.path.join(resultsDir,'demandFullYrCE' + str(currYear) + '.csv'))
    write2dListToCSV([netDemand],os.path.join(resultsDir,'demandNetFullYrCE' + str(currYear) + '.csv'))
    write2dListToCSV([hourlyWindGen],os.path.join(resultsDir,'windGenFullYrCE' + str(currYear) + '.csv'))
    write2dListToCSV([hourlySolarGen],os.path.join(resultsDir,'solarGenFullYrCE' + str(currYear) + '.csv'))
    (demandCE,hourlyWindGenCE,hourlySolarGenCE,hoursForCE,repHrsBySeason,peakNetDemandDayHrs,peakNetRampDayHrs,
        regHrsBySeason,hrsByBlock) = selectWeeksForExpansion(demandWithGrowth,netDemand,hourlyWindGen,
                                                        hourlySolarGen,daysPerSeason,currYear,resultsDir)
    write2dListToCSV([demandCE],os.path.join(resultsDir,'demandCE' + str(currYear) + '.csv'))
    write2dListToCSV([hoursForCE],os.path.join(resultsDir,'hoursCE' + str(currYear) + '.csv'))
    write2dListToCSV([hourlyWindGenCE],os.path.join(resultsDir,'windGenCE' +  str(currYear) + '.csv'))
    write2dListToCSV([hourlySolarGenCE],os.path.join(resultsDir,'solarGenCE' + str(currYear) + '.csv'))
    seasonDemandWeights,weightsList = calculateSeasonalWeights(demandWithGrowth,repHrsBySeason,regHrsBySeason)
    write2dListToCSV(weightsList,os.path.join(resultsDir,'seasonWeightsCE' + str(currYear) + '.csv'))
    peakDemandHour = getPeakDemandHourCE(demandCE,hoursForCE)
    planningReserve = calculatePlanningReserve(demandCE,planningReserveMargin)
    write2dListToCSV([[planningReserve]],os.path.join(resultsDir,'planningReserveCE' + str(currYear) + '.csv'))
    (newWindCFs,newWindCFsSubhr,newSolarCFs,newSolarCFsSubhr,newWindCfsDtHr,newWindCfsDtSubhr,
        newWindIdAndCapac,newSolarCfsDtHr,newSolarCfsDtSubhr,newSolarFilenameAndCapac,
        addedWindCapac,addedSolarCapac) = getNewWindAndSolarCFs(genFleetForCE,netDemand,
        states,statesAbbrev,currYear,'CE',tzAnalysis,projectName,runLoc,resultsDir,windGenDataYr)
    write2dListToCSV([newWindCFs],os.path.join(resultsDir,'windNewCFsFullYrCE' + str(currYear) + '.csv'))
    write2dListToCSV([newWindCFsSubhr],os.path.join(resultsDir,'windNewCFsSubhrFullYrCE' + str(currYear) + '.csv'))
    write2dListToCSV([newSolarCFs],os.path.join(resultsDir,'solarNewCFsFullYrCE' + str(currYear) + '.csv'))
    write2dListToCSV([newSolarCFsSubhr],os.path.join(resultsDir,'solarNewCFsSubhrFullYrCE' + str(currYear) + '.csv'))
    write2dListToCSV([newWindIdAndCapac],os.path.join(resultsDir,'windNewIdAndCapacCE' + str(currYear) + '.csv'))
    write2dListToCSV([newSolarFilenameAndCapac],os.path.join(resultsDir,'solarNewIdAndCapacCE' + str(currYear) + '.csv'))
    (newWindCFsCE,newSolarCFsCE) = trimNewRECFsToCEHours(newWindCFs,newSolarCFs,hoursForCE)
    write2dListToCSV([newWindCFsCE],os.path.join(resultsDir,'windNewCFsCE' + str(currYear) + '.csv'))
    write2dListToCSV([newSolarCFsCE],os.path.join(resultsDir,'solarNewCFsCE' + str(currYear) + '.csv'))
    #Set reserves for existing and incremental reserves for new generators
    (contResHourly,regUpHourly,regDownHourly,flexResHourly,allRes,regUpWind,
        regDownWind,regUpSolar,regDownSolar,flexWind,flexSolar) = calcWWSISReserves(windCfsDtHr,
        windCfsDtSubhr,ewdIdAndCapac,solarCfsDtHr,solarCfsDtSubhr,solarFilenameAndCapac,demandWithGrowth,
        regLoadFrac,contLoadFrac,regErrorPercentile,flexErrorPercentile)
    write2dListToCSV(allRes,os.path.join(resultsDir,'reservesFullYrCE' + str(currYear) + '.csv'))
    write2dListToCSV([contResHourly],os.path.join(resultsDir,'reservesContFullYrCE' + str(currYear) + '.csv'))
    write2dListToCSV([regUpHourly],os.path.join(resultsDir,'reservesRegUpInitFullYrCE' + str(currYear) + '.csv'))
    write2dListToCSV([regDownHourly],os.path.join(resultsDir,'reservesRegDownInitFullYrCE' + str(currYear) + '.csv'))
    write2dListToCSV([flexResHourly],os.path.join(resultsDir,'reservesFlexInitFullYrCE' + str(currYear) + '.csv'))
    (regUpWindInc,regDownWindInc,regUpSolarInc,regDownSolarInc,flexWindInc,
        flexSolarInc) = getIncResForAddedRE(newWindCfsDtHr,newWindCfsDtSubhr,newWindIdAndCapac,
        newSolarCfsDtHr,newSolarCfsDtSubhr,newSolarFilenameAndCapac,demandWithGrowth,regLoadFrac,
        contLoadFrac,regErrorPercentile,flexErrorPercentile,addedWindCapac,addedSolarCapac)
    (regUpCE,regDownCE,flexCE,contCE,regUpWindIncCE,regUpSolarIncCE,regDownWindIncCE,
        regDownSolarIncCE,flexWindIncCE,flexSolarIncCE) = trimRegResToCEHours(regUpHourly,
        regDownHourly,flexResHourly,contResHourly,regUpWindInc,regUpSolarInc,
        regDownWindInc,regDownSolarInc,flexWindInc,flexSolarInc,hoursForCE)
    write2dListToCSV(allRes,os.path.join(resultsDir,'reservesCE' + str(currYear) + '.csv'))
    write2dListToCSV([contCE],os.path.join(resultsDir,'reservesContCE' + str(currYear) + '.csv'))
    write2dListToCSV([regUpCE],os.path.join(resultsDir,'reservesRegUpInitCE' + str(currYear) + '.csv'))
    write2dListToCSV([regDownCE],os.path.join(resultsDir,'reservesRegDownInitCE' + str(currYear) + '.csv'))
    write2dListToCSV([flexCE],os.path.join(resultsDir,'reservesFlexInitCE' + str(currYear) + '.csv'))
    write2dListToCSV([regUpWindIncCE],os.path.join(resultsDir,'reservesRegUpWindIncCE' + str(currYear) + '.csv'))
    write2dListToCSV([regUpSolarIncCE],os.path.join(resultsDir,'reservesRegUpSolarIncCE' + str(currYear) + '.csv'))
    write2dListToCSV([regDownWindIncCE],os.path.join(resultsDir,'reservesRegDownWindIncCE' + str(currYear) + '.csv'))
    write2dListToCSV([regDownSolarIncCE],os.path.join(resultsDir,'reservesRegDownSolarIncCE' + str(currYear) + '.csv'))
    write2dListToCSV([flexWindIncCE],os.path.join(resultsDir,'reservesFlexWindIncCE' + str(currYear) + '.csv'))
    write2dListToCSV([flexSolarIncCE],os.path.join(resultsDir,'reservesFlexSolarIncCE' + str(currYear) + '.csv'))
    onOffInitialEachPeriod = initializeOnOffExistingGens(genFleetForCE,hoursForCE,hourlyWindGenCE,
                                                        hourlySolarGenCE,demandCE,hrsByBlock)
    #Run CE
    print('Set inputs, running CE model...')
    t0 = time.time()
    capacExpModel,ms,ss = callCapacityExpansion(genFleetForCE,hourlyWindGenCE,hourlySolarGenCE,
        demandCE,newTechsCE,planningReserve,discountRate,hoursForCE,newWindCFsCE,
        newSolarCFsCE,scaleMWtoGW,scaleDollarsToThousands,currCo2Cap,capacExpFilename,
        seasonDemandWeights,repHrsBySeason,peakNetDemandDayHrs,peakNetRampDayHrs,peakDemandHour,
        scaleLbToShortTon,runLoc,maxAddedCapacPerTech,onOffInitialEachPeriod,rrToRegTime,
        rrToFlexTime,rrToContTime,regUpCE,regDownCE,regUpWindIncCE,regUpSolarIncCE,regDownWindIncCE,
        regDownSolarIncCE,flexCE,flexWindIncCE,flexSolarIncCE,contCE,xsedeRun)
    write2dListToCSV([['ms','ss'],[ms,ss]],os.path.join(resultsDir,'msAndSsCE' + str(currYear) + '.csv'))
    print('Time (secs) for CE year ' + str(currYear) + ': ' + str(time.time()-t0))
    #Save data
    (genByPlant,regUpByPlant,regDownByPlant,flexByPlant,contByPlant,turnOnByPlant,turnOffByPlant,onOffByPlant,
        genByTech,regUpByTech,regDownByTech,flexByTech,contByTech,turnOnByTech,turnOffByTech,onOffByTech,
        sysResults,co2Ems) = saveCapacExpOperationalData(capacExpModel,genFleetForCE,newTechsCE,hoursForCE)
    writeHourlyResultsByPlant(genByPlant,regUpByPlant,regDownByPlant,flexByPlant,contByPlant,
                                turnOnByPlant,turnOffByPlant,onOffByPlant,resultsDir,currYear,'CE','Plant')
    writeHourlyResultsByPlant(genByTech,regUpByTech,regDownByTech,flexByTech,contByTech,
                                turnOnByTech,turnOffByTech,onOffByTech,resultsDir,currYear,'CE','Tech')
    write2dListToCSV(sysResults,os.path.join(resultsDir,'systemResultsCE' + str(currYear) + '.csv'))
    write2dListToCSV([[co2Ems]],os.path.join(resultsDir,'co2EmsAnnualCE' + str(currYear) + '.csv'))
    capacExpModelsEachYear.append((currYear,capacExpModel))
    newGenerators = saveCapacExpBuilds(capacExpBuilds,capacExpModel,currYear)
    genFleet = addNewGensToFleet(genFleet,newGenerators,newTechsCE,currYear,ocAdderMin,ocAdderMax)
    genFleet = selectAndMarkUnitsRetiredByCE(genFleet,retirementCFCutoff,capacExpModel,currYear,
                    capacExpGenByGens,capacExpRetiredUnitsByCE,scaleMWtoGW,hoursForCE,
                    planningReserve,endYear,capacExpRetiredUnitsByAge,demandCE,hourlyWindGenCE,
                    hourlySolarGenCE,newWindCFsCE,newSolarCFsCE,ptEligRetCF)
    genFleetNoRetiredUnits = createFleetForCurrentCELoop(genFleet,currYear,[],
            runLoc,scenario) #removes all retired units; [] is dummy list b/c not adding ret age units to list
    writeCEInfoToCSVs(capacExpBuilds,capacExpGenByGens,capacExpRetiredUnitsByCE,
            capacExpRetiredUnitsByAge,resultsDir,currYear)
    write2dListToCSV(genFleet,os.path.join(resultsDir,'genFleetAfterCE' + str(currYear) + '.csv'))
    #Write gen fleet for UC to special folder for ease of transfer
    ceUCDir = os.path.join(resultsDirOrig,'CEtoUC')
    if not os.path.exists(ceUCDir): os.makedirs(ceUCDir)
    write2dListToCSV(genFleetNoRetiredUnits,os.path.join(ceUCDir,'genFleetCEtoUC' + str(currYear) + '.csv'))
    return (genFleet,genFleetNoRetiredUnits,capacExpModel,hoursForCE)

########### CALL CAPACITY EXPANSION ############################################
def callCapacityExpansion(genFleet,hourlyWindGenCE,hourlySolarGenCE,demandCE,newTechsCE,
        planningReserve,discountRate,hoursForCE,newWindCFsCE,newSolarCFsCE,scaleMWtoGW,
        scaleDollarsToThousands,currCo2Cap,capacExpFilename,seasonDemandWeights,
        repHrsBySeason,peakNetDemandDayHrs,peakNetRampDayHrs,peakDemandHour,scaleLbToShortTon,runLoc,
        maxAddedCapacPerTech,onOffInitialEachPeriod,rrToRegTime,rrToFlexTime,rrToContTime,
        regUpCE,regDownCE,regUpWindIncCE,regUpSolarIncCE,regDownWindIncCE,regDownSolarIncCE,
        flexCE,flexWindIncCE,flexSolarIncCE,contCE,xsedeRun):
    currDir = os.getcwd()
    if runLoc == 'pc': 
        gamsFileDir = 'C:\\Users\\mtcraig\\Desktop\\EPP Research\\GAMS' 
        gamsSysDir = 'C:\\GAMS\\win64\\24.7'
    else: 
        gamsFileDir = 'GAMSDir'
        gamsSysDir = 'C:\\GAMS\\win64\\24.7'
    if xsedeRun == False: ws = GamsWorkspace(working_directory=gamsFileDir,system_directory=gamsSysDir)
    elif xsedeRun == True: ws = GamsWorkspace(working_directory=gamsFileDir)
    db = ws.add_database()
    #Add sets and parameters to database
    (genSet,genSymbols,hourSet,hourSymbols,techSet,techSymbols,thermalTechSet,thermalTechSymbols,
        renewTechSet,renewTechSymbols) = addSetsToDatabaseCE(db,genFleet,hoursForCE,newTechsCE,
                                            repHrsBySeason,peakNetDemandDayHrs,peakNetRampDayHrs,peakDemandHour)
    addParametersToDatabaseCE(db,hourlyWindGenCE,hourlySolarGenCE,demandCE,
        newTechsCE,genFleet,genSet,genSymbols,hourSet,hourSymbols,techSet,techSymbols,
        thermalTechSet,thermalTechSymbols,renewTechSet,renewTechSymbols,planningReserve,
        discountRate,newWindCFsCE,newSolarCFsCE,scaleMWtoGW,scaleDollarsToThousands,
        currCo2Cap,seasonDemandWeights,scaleLbToShortTon,maxAddedCapacPerTech,
        onOffInitialEachPeriod,rrToRegTime,rrToFlexTime,rrToContTime,regUpCE,regDownCE,
        regUpWindIncCE,regUpSolarIncCE,regDownWindIncCE,regDownSolarIncCE,flexCE,
        flexWindIncCE,flexSolarIncCE,contCE)
    #Load GAMS model
    capacExpFile = capacExpFilename
    capacExpModel = ws.add_job_from_file(capacExpFile)
    #Run GAMS model
    opt = GamsOptions(ws)
    opt.defines['gdxincname'] = db.name
    capacExpModel.run(opt,databases=db)
    ms = capacExpModel.out_db['pModelstat'].find_record().value
    ss = capacExpModel.out_db['pSolvestat'].find_record().value
    if int(ms) != 8 or int(ss) != 1: print('Modelstat & solvestat:',ms,' & ',ss,' (should be 8 and 1)')
    return capacExpModel,ms,ss

################################### ADD SETS
def addSetsToDatabaseCE(db,genFleet,hoursForCE,newTechsCE,repHrsBySeason,peakNetDemandDayHrs,
                        peakNetRampDayHrs,peakDemandHour):
    (genSet,genSymbols,windGenSet,windGenSymbols,solarGenSet,solarGenSymbols) = addGeneratorSets(db,genFleet)
    (hourSet,hourSymbols) = addHourSet(db,hoursForCE)
    addHourSeasonSubsets(db,repHrsBySeason)
    addPeakNetDemandDayHoursSubset(db,peakNetDemandDayHrs)
    addPeakNetRampDayHoursSubset(db,peakNetRampDayHrs)
    addPeakHourSubset(db,peakDemandHour)
    (techSet,techSymbols,thermalTechSet,thermalTechSymbols,
            renewTechSet,renewTechSymbols) = addNewTechsSets(db,newTechsCE)
    return (genSet,genSymbols,hourSet,hourSymbols,techSet,techSymbols,thermalTechSet,
            thermalTechSymbols,renewTechSet,renewTechSymbols)

################################### ADD PARAMETERS
def addParametersToDatabaseCE(db,hourlyWindGenCE,hourlySolarGenCE,demandCE,newTechsCE,genFleet,
        genSet,genSymbols,hourSet,hourSymbols,techSet,techSymbols,thermalTechSet,
        thermalTechSymbols,renewTechSet,renewTechSymbols,planningReserve,discountRate,
        newWindCFsCE,newSolarCFsCE,scaleMWtoGW,scaleDollarsToThousands,currCo2Cap,
        seasonDemandWeights,scaleLbToShortTon,maxAddedCapacPerTech,onOffInitialEachPeriod,
        rrToRegTime,rrToFlexTime,rrToContTime,regUpCE,regDownCE,regUpWindIncCE,regUpSolarIncCE,
        regDownWindIncCE,regDownSolarIncCE,flexCE,flexWindIncCE,flexSolarIncCE,contCE):
    #Add normal CE parameters
    addDemandParam(db,demandCE,hourSet,hourSymbols,scaleMWtoGW) 
    addTechParams(db,newTechsCE,techSet,techSymbols,hourSet,hourSymbols,
                    scaleMWtoGW,scaleDollarsToThousands,scaleLbToShortTon)
    addTechUCParams(db,newTechsCE,techSet,techSymbols,scaleMWtoGW,scaleDollarsToThousands)
    addEguParams(db,genFleet,genSet,genSymbols,scaleMWtoGW,scaleDollarsToThousands,scaleLbToShortTon)
    addEguOpCostParam(db,genFleet,genSet,genSymbols,scaleLbToShortTon,scaleMWtoGW,scaleDollarsToThousands)
    addEguCapacParam(db,genFleet,genSet,genSymbols,scaleMWtoGW)
    addPlanningReserveParam(db,planningReserve,scaleMWtoGW) 
    addDiscountRateParam(db,discountRate) 
    addExistingRenewableMaxGenParams(db,hourSet,hourSymbols,hourlySolarGenCE,hourlyWindGenCE,scaleMWtoGW)
    addRenewTechCFParams(db,renewTechSet,renewTechSymbols,hourSet,hourSymbols,newWindCFsCE,newSolarCFsCE)
    addCppEmissionsCap(db,currCo2Cap)
    addSeasonDemandWeights(db,seasonDemandWeights)
    addMaxNumNewBuilds(db,newTechsCE,techSet,techSymbols,maxAddedCapacPerTech)
    #Add UC constraint parameters
    addEguUCParams(db,genFleet,genSet,genSymbols,scaleMWtoGW,scaleDollarsToThousands)
    addRegReserveParameters(db,regUpCE,regDownCE,rrToRegTime,hourSet,
                            hourSymbols,scaleMWtoGW,'CE') #last param is model name
    addRegIncParams(db,regUpWindIncCE,regUpSolarIncCE,regDownWindIncCE,regDownSolarIncCE,hourSet,hourSymbols)
    addFlexIncParams(db,flexWindIncCE,flexSolarIncCE,hourSet,hourSymbols)
    addFlexReserveParameters(db,flexCE,rrToFlexTime,hourSet,hourSymbols,scaleMWtoGW,'CE')
    addContReserveParameters(db,contCE,rrToContTime,hourSet,hourSymbols,scaleMWtoGW)
    addEguEligibleToProvideRes(db,genFleet,genSet,genSymbols)
    addTechEligibleToProvideRes(db,newTechsCE,techSet,techSymbols)
    addInitialOnOffForEachBlock(db,onOffInitialEachPeriod,genSet,genSymbols)
################################################################################
################################################################################
################################################################################

################################################################################
####### RUN UNIT COMMITMENT ####################################################
################################################################################
def runUnitCommitment(genFleet,demandScaled,startYear,ucYear,fuelPricesTimeSeries,
        states,statesAbbrev,scaleMWtoGW,scaleDollarsToThousands,currCo2Cap,calculateCO2Price,
        scaleLbToShortTon,daysForUC,daysOpt,daysLA,tzAnalysis,projectName,runLoc,
        resultsDir,stoScenario,ocAdderMin,ocAdderMax,windGenDataYr,regLoadFrac,contLoadFrac,
        regErrorPercentile,flexErrorPercentile,rrToRegTime,rrToFlexTime,rrToContTime,
        regUpCostCoeffsUC,xsedeRun,runCE,scenario):
    resultsDir = os.path.join(resultsDir,'UC',stoScenario)
    if not os.path.exists(resultsDir): os.makedirs(resultsDir)
    print('Entering UC loop for year ' + str(ucYear) + ' and scenario ' + stoScenario)
    fleetUC = copy.deepcopy(genFleet)
    (startWindCapacForCFs,startSolarCapacForCFs) = (0,0)
    (windCFs,windCfsDtHr,windCfsDtSubhr,windIdAndCapac,solarCFs,solarCfsDtHr,solarCfsDtSubhr,
            solarFilenameAndCapac) = getRenewableCFs(fleetUC,startWindCapacForCFs,startSolarCapacForCFs,
            states,statesAbbrev,'region',tzAnalysis,projectName,runLoc,windGenDataYr)
    write2dListToCSV([demandScaled],os.path.join(resultsDir,'demandUC' + str(ucYear) + '.csv'))
    write2dListToCSV(windCFs,os.path.join(resultsDir,'windCFsUC' + str(ucYear) + '.csv'))
    write2dListToCSV(windCfsDtHr,os.path.join(resultsDir,'windCFsDtUC' + str(ucYear) + '.csv'))
    write2dListToCSV(windCfsDtSubhr,os.path.join(resultsDir,'windCFsDtSubhrUC' + str(ucYear) + '.csv'))
    write2dListToCSV(windIdAndCapac,os.path.join(resultsDir,'windIdAndCapacUC' + str(ucYear) + '.csv'))
    write2dListToCSV(solarCFs,os.path.join(resultsDir,'solarCFsUC' + str(ucYear) + '.csv'))
    write2dListToCSV(solarCfsDtHr,os.path.join(resultsDir,'solarCFsDtUC' + str(ucYear) + '.csv'))
    write2dListToCSV(solarCfsDtSubhr,os.path.join(resultsDir,'solarCFsDtSubhrUC' + str(ucYear) + '.csv'))
    write2dListToCSV(solarFilenameAndCapac,os.path.join(resultsDir,'solarIdAndCapacUC' + str(ucYear) + '.csv'))
    (contResHourly,regUpHourly,regDownHourly,flexResHourly,allRes,regUpWind,
        regDownWind,regUpSolar,regDownSolar,flexWind,flexSolar) = calcWWSISReserves(windCfsDtHr,
        windCfsDtSubhr,windIdAndCapac,solarCfsDtHr,solarCfsDtSubhr,solarFilenameAndCapac,demandScaled,
        regLoadFrac,contLoadFrac,regErrorPercentile,flexErrorPercentile)
    write2dListToCSV(allRes,os.path.join(resultsDir,'reservesUC' + str(ucYear) + '.csv'))
    write2dListToCSV([contResHourly],os.path.join(resultsDir,'reservesContUC' + str(ucYear) + '.csv'))
    write2dListToCSV([regUpHourly],os.path.join(resultsDir,'reservesRegUpUC' + str(ucYear) + '.csv'))
    write2dListToCSV([regDownHourly],os.path.join(resultsDir,'reservesRegDownUC' + str(ucYear) + '.csv'))
    write2dListToCSV([flexResHourly],os.path.join(resultsDir,'reservesFlexUC' + str(ucYear) + '.csv'))
    (netDemand,hourlyWindGen,hourlySolarGen) = getNetDemand(demandScaled,windCFs,
        windIdAndCapac,solarCFs,solarFilenameAndCapac,ucYear,'UC',resultsDir)
    write2dListToCSV([[val] for val in hourlyWindGen],os.path.join(resultsDir,'windGenUC' + str(ucYear) + '.csv'))
    write2dListToCSV([[val] for val in hourlySolarGen],os.path.join(resultsDir,'solarGenUC' + str(ucYear) + '.csv'))
    updateFuelPricesExistingGens(fleetUC,ucYear,fuelPricesTimeSeries)
    combineWindAndSolarToSinglePlant(fleetUC,runLoc)
    if calculateCO2Price==True:
        co2Price = convertCo2CapToPrice(fleetUC,hourlyWindGen,hourlySolarGen,demandScaled,currCo2Cap,
                                        scaleMWtoGW,scaleDollarsToThousands,scaleLbToShortTon,runLoc)
    else:
        co2Price = 0
    print('CO2 price:',co2Price,'$/ton')
    write2dListToCSV([[co2Price]],os.path.join(resultsDir,'co2PriceUC' + str(ucYear) + '.csv'))
    #Set storage parameters and UC filename depending on storage scenario (keep after CO2 price calc)
    if stoScenario != 'NoSto': 
        ucFilename = 'UnitCommitmentWithStorage12Jan17Coopt.gms'
        storageParams,stoUnitsToAdd = importStorageParams(runLoc,scenario),1
        if stoScenario == 'StoEnergy': stoMarket,stoType = 'energy','PumpedHydro'
        elif stoScenario == 'StoRes': stoMarket,stoType = 'reserve','LiIon'
        elif stoScenario == 'StoEnergyAndRes': stoMarket,stoType = 'both','LiIon'
        if stoMarket != 'energy': regUpCostCoeffsUC['PumpedHydro'],regUpCostCoeffsUC['LiIon'] = 2,2 #only use LiIon
        addRegCostAndOfferEligToStoParams(regUpCostCoeffsUC,storageParams)
        fleetUC = addStorageToGenFleet(fleetUC,storageParams,stoType,stoUnitsToAdd,ocAdderMin,
                                    ocAdderMax,regUpCostCoeffsUC)
    else:
        ucFilename,stoMarket = 'UnitCommitment12Jan17Coopt.gms','energy' #doesn't matter what stoMarket is
    write2dListToCSV(fleetUC,os.path.join(resultsDir,'genFleetUC' + str(ucYear) + '.csv'))
    #Run unit commitment for each day in year
    ucResultsByDay = [] #list of UC GAMS models
    (genByPlant,regUpByPlant,flexByPlant,contByPlant,turnonByPlant,turnoffByPlant,regDownByPlant,
            onOffByPlant,genToRow,hourToColPlant) = setupHourlyResultsByPlant(daysForUC,fleetUC)
    if stoScenario != 'NoSto': 
        (chargeBySto,socBySto,genToRowSto,hourToColSto) = setupHourlyResultsBySto(daysForUC,fleetUC)
    (sysResults,resultToRow,hourToColSys) = setupHourlySystemResults(daysForUC)
    msAndSs = [['day','ms','ss']] #store modelstat & solvestat from GAMS
    for dayIdx in range(0,len(daysForUC),daysOpt):
        day = daysForUC[dayIdx] 
        (demandUC,hourlyWindGenUC,hourlySolarGenUC,hoursForUC) = getDemandAndREGenForUC(day,
                                                                daysOpt,daysLA,demandScaled,
                                                                hourlyWindGen,hourlySolarGen)
        (regUpUC,regDownUC,flexUC,contUC) = getResForUC(day,daysOpt,daysLA,regUpHourly,regDownHourly,
                                                        flexResHourly,contResHourly)
        if daysForUC[0]==day: #first day, therefore no initial conditions defined. MW energy values
            (onOffInitial,genAboveMinInitial,mdtCarriedInitial) = setInitCondsFirstUC(fleetUC)
            if stoScenario != 'NoSto': stoChargeInitial = setInitChargeFirstUC(fleetUC)
        else: #other days. MW energy values
            (onOffInitial,genAboveMinInitial,mdtCarriedInitial) = setInitCondsPerPriorUC(ucModel,fleetUC,
                                                                        hoursForUC,daysOpt,daysLA,scaleMWtoGW)
            if stoScenario != 'NoSto': 
                stoChargeInitial = setInitChargePerPriorUC(ucModel,fleetUC,hoursForUC,daysLA,scaleMWtoGW)
        if stoScenario == 'NoSto': stoChargeInitial = None
        t0 = time.time()
        ucModel,ms,ss = callUnitCommitment(ucFilename,fleetUC,hourlyWindGenUC,hourlySolarGenUC,
                demandUC,hoursForUC,onOffInitial,genAboveMinInitial,mdtCarriedInitial,
                scaleMWtoGW,scaleDollarsToThousands,co2Price,scaleLbToShortTon,regUpUC,
                regDownUC,stoChargeInitial,runLoc,stoMarket,stoScenario,
                rrToRegTime,rrToFlexTime,rrToContTime,flexUC,contUC,xsedeRun)
        print('Time (secs) for UC day ' + str(day) + ': ' + str(time.time()-t0))
        ucResultsByDay.append((day,ucModel)) #just saves GAMS model
        saveHourlyResultsByPlant(genByPlant,regUpByPlant,regDownByPlant,flexByPlant,contByPlant,
                    turnonByPlant,turnoffByPlant,onOffByPlant,genToRow,hourToColPlant,ucModel,day,daysOpt)
        if stoScenario != 'NoSto': 
            saveHourlyStoResults(chargeBySto,socBySto,genToRowSto,hourToColSto,ucModel,day,daysOpt)
        saveHourlySystemResults(sysResults,resultToRow,hourToColSys,ucModel,day,daysOpt)
        msAndSs.append([day,ms,ss])
    writeHourlyResultsByPlant(genByPlant,regUpByPlant,regDownByPlant,flexByPlant,contByPlant,
                                turnonByPlant,turnoffByPlant,onOffByPlant,resultsDir,ucYear,'UC','Plant')
    if stoScenario != 'NoSto': writeHourlyStoResults(chargeBySto,socBySto,resultsDir,ucYear)
    write2dListToCSV(sysResults,os.path.join(resultsDir,'systemResultsUC' + str(ucYear) + '.csv'))
    write2dListToCSV(msAndSs,os.path.join(resultsDir,'msAndSsUC' + str(ucYear) + '.csv'))
    return (ucResultsByDay,genByPlant)

########### IMPORT STORAGE PARAMETERS ##########################################
def importStorageParams(runLoc,scenario):
    if runLoc == 'pc': stoDir = 'C:\\Users\\mtcraig\\Desktop\\EPP Research\\StorageParameters'
    else: stoDir = 'Data'
    if scenario == 'highSto': stoFile = 'StorageParams18Jan17HighSto.csv'
    elif scenario == 'highStoEff': stoFile = 'StorageParams18Jan17HighStoEff.csv'
    else: stoFile = 'StorageParams18Jan17.csv'
    return readCSVto2dList(os.path.join(stoDir,stoFile)) 

########### ADD REG COST AND OFFER TO STO PARAMETERS ###########################
def addRegCostAndOfferEligToStoParams(regUpCostCoeffsUC,storageParams):
    storageParams[0].extend(['RegOfferCost($/MW)','RegOfferElig'])
    stoTypeCol = storageParams[0].index('StorageType')
    for row in storageParams[1:]: 
        if row[stoTypeCol] in regUpCostCoeffsUC: regOfferCost,regOfferElig = regUpCostCoeffsUC[row[stoTypeCol]],1
        else: regOfferCost,regOfferElig = 0,0
        row.extend([regOfferCost,regOfferElig])

########### SHRINK FLEET AND DEMAND FOR TESTING UC #############################
def shrinkFleetAndDemandForTesting(fleetUC,demandScaled):
    fleetSizeReduction = 20
    capacCol = fleetUC[0].index('Capacity (MW)')
    origFleetCapac = sum([float(row[capacCol]) for row in fleetUC[1:]])
    fleetUC = [fleetUC[0]] + [row for row in fleetUC[len(fleetUC)//fleetSizeReduction:]]
    newCapac = sum([float(row[capacCol]) for row in fleetUC[1:]])
    scaleDemand = newCapac/origFleetCapac
    demandScaled = [float(val)*scaleDemand for val in demandScaled]
    return (demandScaled,fleetUC)
 
########### RUN UNIT COMMITMENT MODEL ##########################################
def callUnitCommitment(ucFilename, fleetUC,hourlyWindGenUC,hourlySolarGenUC,demandUC,hoursForUC,
       onOffInitial,genAboveMinInitial,mdtCarriedInitial,scaleMWtoGW,scaleDollarsToThousands,
       co2Price,scaleLbToShortTon,regUpUC,regDownUC,stoChargeInitial,runLoc,stoMarket,stoScenario,
       rrToRegTime,rrToFlexTime,rrToContTime,flexUC,contUC,xsedeRun):
    currDir = os.getcwd()
    if runLoc == 'pc':
        gamsFileDir = 'C:\\Users\\mtcraig\\Desktop\\EPP Research\\GAMS' 
        gamsSysDir = 'C:\\GAMS\\win64\\24.7'
    else:
        gamsFileDir = 'GAMSDir'
        gamsSysDir = 'C:\\GAMS\\win64\\24.7'
    if xsedeRun == False: wsUC = GamsWorkspace(working_directory=gamsFileDir,system_directory=gamsSysDir)
    elif xsedeRun == True: wsUC = GamsWorkspace(working_directory=gamsFileDir)
    dbUC = wsUC.add_database()
    #Add sets and parameters to database
    cnse = 10000
    (genSet,genSymbols,hourSet,hourSymbols,stoGenSet,
        stoGenSymbols) = addSetsToDatabaseUC(dbUC,fleetUC,hoursForUC,stoScenario)
    addParametersToDatabaseUC(dbUC,hourlyWindGenUC,hourlySolarGenUC,demandUC,fleetUC,
        genSet,genSymbols,hourSet,hourSymbols,cnse,rrToFlexTime,onOffInitial,genAboveMinInitial,
        mdtCarriedInitial,scaleMWtoGW,scaleDollarsToThousands,co2Price,hoursForUC,
        scaleLbToShortTon,rrToRegTime,regUpUC,regDownUC,stoGenSet,stoGenSymbols,
        stoChargeInitial,stoMarket,stoScenario,rrToContTime,flexUC,contUC)
    #Load and run GAMS model
    ucModel = wsUC.add_job_from_file(ucFilename)
    optUC = GamsOptions(wsUC)
    optUC.defines['gdxincname'] = dbUC.name
    ucModel.run(optUC,databases=dbUC)
    ms,ss = ucModel.out_db['pModelstat'].find_record().value,ucModel.out_db['pSolvestat'].find_record().value
    if int(ms) != 8 or int(ss) != 1: print('Modelstat & solvestat:',ms,' & ',ss,' (should be 8 and 1)')
    return ucModel,ms,ss

################################### ADD SETS
def addSetsToDatabaseUC(db,fleetUC,hoursForUC,stoScenario):
    (genSet,genSymbols,windGenSet,windGenSymbols,solarGenSet,
            solarGenSymbols) = addGeneratorSets(db,fleetUC)
    if stoScenario != 'NoSto': (stoGenSet,stoGenSymbols) = addStoGenSets(db,fleetUC)
    else: (stoGenSet,stoGenSymbols) = (None,None)
    (hourSet,hourSymbols) = addHourSet(db,hoursForUC)
    return (genSet,genSymbols,hourSet,hourSymbols,stoGenSet,stoGenSymbols)

################################### ADD PARAMETERS
def addParametersToDatabaseUC(db,hourlyWindGenUC,hourlySolarGenUC,demandUC,fleetUC,
        genSet,genSymbols,hourSet,hourSymbols,cnse,rrToFlexTime,onOffInitial,genAboveMinInitial,
        mdtCarriedInitial,scaleMWtoGW,scaleDollarsToThousands,co2Price,hoursForUC,scaleLbToShortTon,
        rrToRegTime,regUpUC,regDownUC,stoGenSet,stoGenSymbols,stoChargeInitial,stoMarket,
        stoScenario,rrToContTime,flexUC,contUC):
    addDemandParam(db,demandUC,hourSet,hourSymbols,scaleMWtoGW) 
    addEguParams(db,fleetUC,genSet,genSymbols,scaleMWtoGW,scaleDollarsToThousands,scaleLbToShortTon) 
    addEguOpCostParam(db,fleetUC,genSet,genSymbols,scaleLbToShortTon,scaleMWtoGW,scaleDollarsToThousands,co2Price)
    addEguCapacParam(db,fleetUC,genSet,genSymbols,scaleMWtoGW)
    addEguUCParams(db,fleetUC,genSet,genSymbols,scaleMWtoGW,scaleDollarsToThousands)
    addEguInitialConditions(db,genSet,genSymbols,fleetUC,onOffInitial,genAboveMinInitial,
        mdtCarriedInitial,scaleMWtoGW)
    if stoScenario != 'NoSto':
        addStorageParams(db,fleetUC,stoGenSet,stoGenSymbols,stoMarket,scaleMWtoGW)
        addStorageInitCharge(db,stoChargeInitial,fleetUC,stoGenSet,stoGenSymbols,scaleMWtoGW)
    addEguEligibleToProvideRes(db,fleetUC,genSet,genSymbols,stoMarket)
    addExistingRenewableMaxGenParams(db,hourSet,hourSymbols,hourlySolarGenUC,
        hourlyWindGenUC,scaleMWtoGW)
    addRegReserveParameters(db,regUpUC,regDownUC,rrToRegTime,hourSet,hourSymbols,scaleMWtoGW,'UC') 
    addEguRegCostParam(db,fleetUC,genSet,genSymbols,scaleMWtoGW,scaleDollarsToThousands)
    addFlexReserveParameters(db,flexUC,rrToFlexTime,hourSet,hourSymbols,scaleMWtoGW,'UC')
    addContReserveParameters(db,contUC,rrToContTime,hourSet,hourSymbols,scaleMWtoGW)
    addCostNonservedEnergy(db,cnse,scaleMWtoGW,scaleDollarsToThousands)
    addCo2Price(db,co2Price,scaleDollarsToThousands)
################################################################################
################################################################################
################################################################################

masterFunction()