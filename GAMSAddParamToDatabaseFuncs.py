#Michael Craig
#October 4, 2016
#Functions for adding parameters to GAMS database. Used for CE & UC models.

import copy, math
from CalculateOpCost import calcOpCosts,calcOpCostsTech
from GAMSAuxFuncs import *
from AuxFuncs import convertCostToTgtYr

################################################################################
##################### CE & UC PARAMETERS #######################################
################################################################################
##### ADD HOURLY DEMAND PARAMETERS
def addDemandParam(db,demandCE,hourSet,hourSymbols,scaleMWtoGW): 
    demandDict = getParamIndexedByHourDict(demandCE,hourSymbols,1/scaleMWtoGW)
    (demandName,demandDescrip) = ('pDemand','hourly demand (GWh)')
    demandParam = add1dParam(db,demandDict,hourSet,hourSymbols,demandName,demandDescrip)

##### ADD EXISTING GENERATOR PARAMETERS: HR, VOM, fuel cost, CO2 ems rate
def addEguParams(db,genFleet,genSet,genSymbols,scaleMWtoGW,scaleDollarsToThousands,
                scaleLbToShortTon):
    #Heat rate
    scalarHrToMmbtuPerMwh = 1/1000
    hrDict = getEguParamDict(genFleet,'Heat Rate (Btu/kWh)',scalarHrToMmbtuPerMwh*scaleMWtoGW)
    (hrName,hrDescrip) = ('pHr','heat rate (MMBtu/GWh)')
    hrParam = add1dParam(db,hrDict,genSet,genSymbols,hrName,hrDescrip)
    #Emissions rate
    emRateDict = getEguParamDict(genFleet,'CO2EmRate(lb/MMBtu)',1/scaleLbToShortTon)
    (emRateName,emRateDescrip) = ('pCO2emrate','emissions rate (short ton/MMBtu)')
    emRateParam = add1dParam(db,emRateDict,genSet,genSymbols,emRateName,emRateDescrip)

def addEguOpCostParam(db,genFleet,genSet,genSymbols,scaleLbToShortTon,scaleMWtoGW,scaleDollarsToThousands,*co2Price):
    ocDict = getEguOpCostDict(genFleet,scaleLbToShortTon,scaleMWtoGW,scaleDollarsToThousands,co2Price)
    (ocName,ocDescrip) = ('pOpcost','op cost (thousand$/GWh)')
    ocParam = add1dParam(db,ocDict,genSet,genSymbols,ocName,ocDescrip)
   
##### ADD EXISTING RENEWABLE COMBINED MAXIMUM GENERATION VALUES
#Converts 1d list of param vals to hour-indexed dicts, then adds dicts to GAMS db
def addExistingRenewableMaxGenParams(db,hourSet,hourSymbols,hourlySolarGenCE,hourlyWindGenCE,scaleMWtoGW):    
    maxSolarGenDict = getParamIndexedByHourDict(hourlySolarGenCE,hourSymbols,1/scaleMWtoGW)
    maxWindGenDict = getParamIndexedByHourDict(hourlyWindGenCE,hourSymbols,1/scaleMWtoGW)
    (maxSolarGenName,maxSolarGenDescrip) = ('pMaxgensolar','max combined gen by existing solar')
    maxSolarGenParam = add1dParam(db,maxSolarGenDict,hourSet,hourSymbols,maxSolarGenName,maxSolarGenDescrip)
    (maxWindGenName,maxWindGenDescrip) = ('pMaxgenwind','max combined gen by existing wind')
    maxWindGenParam = add1dParam(db,maxWindGenDict,hourSet,hourSymbols,maxWindGenName,maxWindGenDescrip)

#Stores set of values into dictionary keyed by hour
#Inputs: set of param values (1d list), hour symbols (1d list), optional scalar
#Outputs: dictionary of (hour symbol:param val)
def getParamIndexedByHourDict(paramVals,hourSymbols,*scalar):
    paramIndexedByHourDict = dict()
    for idx in range(len(hourSymbols)): paramIndexedByHourDict[hourSymbols[idx]] = paramVals[idx]*scalar[0]
    return paramIndexedByHourDict
################################################################################
################################################################################
################################################################################

################################################################################
##################### CAPACITY EXPANSION PARAMETERS ############################
################################################################################
##### ADD NEW TECH PARAMS FOR CE
def addTechParams(db,newTechsCE,techSet,techSymbols,hourSet,hourSymbols,
                    scaleMWtoGW,scaleDollarsToThousands,scaleLbToShortTon):
    #Nameplate capacity (for cost calculations)
    capacDict = getTechParamDict(newTechsCE,techSymbols,'Capacity(MW)',1/scaleMWtoGW)
    (capacName,capacDescrip) = ('pCapactech','capacity (GW) of techs')
    techCapacParam = add1dParam(db,capacDict,techSet,techSymbols,capacName,capacDescrip)
    #Heat rate
    scalarHrToMmbtuPerMwh = 1/1000
    hrDict = getTechParamDict(newTechsCE,techSymbols,'HR(Btu/kWh)',scalarHrToMmbtuPerMwh*scaleMWtoGW)
    (hrName,hrDescrip) = ('pHrtech','heat rate (MMBtu/GWh)')
    techHrParam = add1dParam(db,hrDict,techSet,techSymbols,hrName,hrDescrip)
    #Op cost
    ocDict = getTechOpCostDict(newTechsCE,scaleMWtoGW/scaleDollarsToThousands)
    (ocName,ocDescrip) = ('pOpcosttech','op cost for tech (thousand$/GWh)')
    ocParam = add1dParam(db,ocDict,techSet,techSymbols,ocName,ocDescrip)
    #Fixed O&M
    fixedomDict = getTechParamDict(newTechsCE,techSymbols,'FOM(2012$/MW/yr)',scaleMWtoGW*1/scaleDollarsToThousands)
    for tech in fixedomDict: fixedomDict[tech] = convertCostToTgtYr('fom',fixedomDict[tech])
    (fixedomName,fixedomDescrip) = ('pFom','fixed O&M (thousand$/GW/yr)')
    techFixedomParam = add1dParam(db,fixedomDict,techSet,techSymbols,fixedomName,fixedomDescrip)
    #Overnight capital cost
    occDict = getTechParamDict(newTechsCE,techSymbols,'CAPEX(2012$/MW)',scaleMWtoGW*1/scaleDollarsToThousands)
    for tech in occDict: occDict[tech] = convertCostToTgtYr('occ',occDict[tech])
    (occName,occDescrip) = ('pOcc','overnight capital cost (thousand$/GW)')
    techOccParam = add1dParam(db,occDict,techSet,techSymbols,occName,occDescrip)
    #Emissions rate
    emRateDict = getTechParamDict(newTechsCE,techSymbols,'CO2EmissionsRate(lb/MMBtu)',1/scaleLbToShortTon)
    (emRateName,emRateDescrip) = ('pCO2emratetech','co2 emissions rate (short ton/MMBtu)')
    techEmRateParam = add1dParam(db,emRateDict,techSet,techSymbols,emRateName,emRateDescrip)
    #Lifetime
    lifetimeDict = getTechParamDict(newTechsCE,techSymbols,'Lifetime(years)')
    (lifetimeName,lifetimeDescrip) = ('pLife','years')
    techLifetimeParam = add1dParam(db,lifetimeDict,techSet,techSymbols,lifetimeName,lifetimeDescrip)
    #MDT
    mdtDict = getTechParamDict(newTechsCE,techSymbols,'MinDownTime(hrs)')
    (mdtName,mdtDesc) = ('pMindowntimetech','hrs')
    mdtParam = add1dParam(db,mdtDict,techSet,techSymbols,mdtName,mdtDesc)
    
#Creates dict of (techSymbol:paramVal) for given parameter name
def getTechParamDict(newTechsCE,techSymbols,paramColName,*scalar):
    techCol = newTechsCE[0].index('TechnologyType')
    paramCol = newTechsCE[0].index(paramColName)
    techs = [row[techCol] for row in newTechsCE]
    paramDict = dict()
    for tech in techSymbols:
        rowIdx = techs.index(tech)
        if len(scalar)>0: paramDict[tech] = float(newTechsCE[rowIdx][paramCol])*scalar[0] 
        else: paramDict[tech] = float(newTechsCE[rowIdx][paramCol])
    return paramDict

#Takes in techs and returns dictionary of (tech:opCost)
def getTechOpCostDict(newTechs,scalar):
    opCosts = calcOpCostsTech(newTechs)
    paramDict = dict()
    for idx in range(1,len(newTechs)):
        paramDict[createTechSymbol(newTechs[idx],newTechs[0])] = opCosts[idx-1]*scalar #op costs = 1d list of vals, so offset by 1
    return paramDict

##### ADD UC PARAMETERS FOR NEW TECHS
def addTechUCParams(db,newTechsCE,techSet,techSymbols,scaleMWtoGW,scaleDollarsToThousands):
    #Min load
    minLoadDict = getTechParamDict(newTechsCE,techSymbols,'MinLoad(MW)',1/scaleMWtoGW)
    (minLoadName,minLoadDescrip) = ('pMinloadtech','min load (GW)')
    minLoadParam = add1dParam(db,minLoadDict,techSet,techSymbols,minLoadName,minLoadDescrip)
    #Ramp rate
    rampDict = getTechParamDict(newTechsCE,techSymbols,'RampRate(MW/hr)',1/scaleMWtoGW)
    (rampName,rampDescrip) = ('pRampratetech','ramp rate (GW/hr)')
    rampParam = add1dParam(db,rampDict,techSet,techSymbols,rampName,rampDescrip)
    #Start up fixed cost
    newTechsCEForStartCosts = techsWith2012DollarStartCosts(newTechsCE)
    startCostDict = getTechParamDict(newTechsCEForStartCosts,techSymbols,'StartCost($2011)',1/scaleDollarsToThousands)
    (startName,startDescrip) = ('pStartupfixedcosttech','startup fixed cost (thousand$)')
    startCostParam = add1dParam(db,startCostDict,techSet,techSymbols,startName,startDescrip)

#Create new tech 2d list w/ start costs in 2012 dollars
def techsWith2012DollarStartCosts(newTechsCE):
    startCol = newTechsCE[0].index('StartCost($2011)')
    newTechsCEForStartCosts = copy.deepcopy(newTechsCE)
    for row in newTechsCEForStartCosts[1:]: 
        row[startCol] = convertCostToTgtYr('startup',float(row[startCol]))
    return newTechsCEForStartCosts

##### ADD PLANNING RESERVE MARGIN FRACTION PARAMETER
def addPlanningReserveParam(db,planningReserve,scaleMWtoGW): 
    add0dParam(db,'pPlanningreserve','planning reserve',planningReserve*1/scaleMWtoGW)

##### ADD DISCOUNT RATE PARAMETER
def addDiscountRateParam(db,discountRate):
    add0dParam(db,'pR','discount rate',discountRate)

##### ADD FIRM FRACTION FOR EXISTING GENERATORS
#Firm fraction goes towards meeting planning reserve margin
def addExistingPlantFirmFractions(db,genFleet,genSet,genSymbols,firmCapacityCreditsExistingGens):
    firmCreditDict = getFirmCreditExistingGenDict(genFleet,firmCapacityCreditsExistingGens)
    (firmCreditName,firmCreditDescrip) = ('pFirmcapacfractionegu','firm capacity fraction')
    firmCreditExistingGenParam = add1dParam(db,firmCreditDict,genSet,genSymbols,firmCreditName,firmCreditDescrip)

#Returns dict of (genSymbol:capacCredit) based on plant type of each generator    
def getFirmCreditExistingGenDict(genFleet,firmCapacityCreditsExistingGens):
    plantTypeCol = genFleet[0].index('PlantType')
    firmCapacityCreditsExistingGensDict = dict()
    for row in genFleet[1:]:
        capacCredit = firmCapacityCreditsExistingGens[row[plantTypeCol]]
        firmCapacityCreditsExistingGensDict[createGenSymbol(row,genFleet[0])] = capacCredit
    return firmCapacityCreditsExistingGensDict

##### ADD HOURLY CAPACITY FACTORS FOR NEW RENEWABLE TECHS
#For wind and solar CFs, creates dict of (hour,techSymbol):CF, then adds them to GAMS db
def addRenewTechCFParams(db,renewTechSet,renewTechSymbols,hourSet,hourSymbols,newWindCFsCE,newSolarCFsCE):
    renewtechCfDict = dict()
    for renewtech in renewTechSymbols:
        if renewtech == 'Wind': relevantCfs = copy.deepcopy(newWindCFsCE)
        elif renewtech == 'Solar PV': relevantCfs = copy.deepcopy(newSolarCFsCE)
        for idx in range(len(hourSymbols)): renewtechCfDict[(renewtech,hourSymbols[idx])] = relevantCfs[idx]
    (renewtechCFName,renewtechCFDescrip) = ('pCf','capacity factors for new wind and solar')
    renewtechCfParam = add2dParam(db,renewtechCfDict,renewTechSet,hourSet,renewtechCFName,renewtechCFDescrip)
    
##### ADD FIRM FRACTION FOR NEW TECHS
#Determines firm fraction of new techs based on plant type
def addTechFirmFractions(db,techSet,techSymbols,thermalTechSymbols,renewTechSymbols,newRECapacCredits):
    techFirmFracDict = dict()
    for thermalTech in thermalTechSymbols: techFirmFracDict[thermalTech] = 1
    for renewTech in renewTechSymbols: techFirmFracDict[renewTech] = newRECapacCredits[renewTech]
    (firmCreditName,firmCreditDescrip) = ('pFirmcapacfractiontech','firm capacity fraction for new techs')
    firmCreditTechParam = add1dParam(db,techFirmFracDict,techSet,techSymbols,firmCreditName,firmCreditDescrip)

##### ADD CO2 EMISSIONS CAP
def addCppEmissionsCap(db,co2CppSercCurrYearLimit):
    add0dParam(db,'pCO2emcap','CPP co2 emissions cap [short tons]',co2CppSercCurrYearLimit)

##### ADD WEIGHTS TO SCALE REPRESENTATIVE SEASONAL DEMAND UP
def addSeasonDemandWeights(db,seasonDemandWeights):
    for season in seasonDemandWeights:
        add0dParam(db,'pWeight' + season,'weight on rep. seasonal demand',seasonDemandWeights[season])

##### ADD LIMIT ON MAX NUMBER OF NEW BUILDS PER TECH
def addMaxNumNewBuilds(db,newTechsCE,techSet,techSymbols,maxAddedCapacPerTech):
    techMaxNewBuildsDict = getMaxNumBuilds(newTechsCE,maxAddedCapacPerTech)
    (maxBuildName,maxBuildDescrip) = ('pNmax','max num builds per tech')
    maxBuildParam = add1dParam(db,techMaxNewBuildsDict,techSet,techSymbols,maxBuildName,maxBuildDescrip)

def getMaxNumBuilds(newTechsCE,maxAddedCapacPerTech):
    capacCol = newTechsCE[0].index('Capacity(MW)')
    techCol = newTechsCE[0].index('TechnologyType')
    techMaxNewBuildsDict = dict()
    for row in newTechsCE[1:]:
        techMaxNewBuildsDict[row[techCol]] = math.ceil(maxAddedCapacPerTech/int(row[capacCol]))
    return techMaxNewBuildsDict

##### ADD INITIAL COMMITMENT STATE FOR EXISTING GENS FOR EACH TIME BLOCK
def addInitialOnOffForEachBlock(db,onOffInitialEachPeriod,genSet,genSymbols):
    for block in onOffInitialEachPeriod:
        onOffBlockDict = onOffInitialEachPeriod[block]
        (onOffInitName,onOffInitDes) = ('pOnoroffinit' + block[:3],'on off init in ' + block) #:3 b/c want first 3 letters
        onOffBlockParam = add1dParam(db,onOffBlockDict,genSet,genSymbols,onOffInitName,onOffInitDes)

################################################################################
################################################################################
################################################################################

################################################################################
##################### UNIT COMMITMENT PARAMETERS ###############################
################################################################################
##### GENERATOR UC PARAMETERS
def addEguUCParams(db,fleetUC,genSet,genSymbols,scaleMWtoGW,scaleDollarsToThousands):
    #Min load
    minLoadDict = getEguParamDict(fleetUC,'MinLoad(MW)',1/scaleMWtoGW)
    (minLoadName,minLoadDescrip) = ('pMinload','min load (GW)')
    minLoadParam = add1dParam(db,minLoadDict,genSet,genSymbols,minLoadName,minLoadDescrip)
    #Ramp rate
    rampDict = getEguParamDict(fleetUC,'RampRate(MW/hr)',1/scaleMWtoGW)
    (rampName,rampDescrip) = ('pRamprate','ramp rate (GW/hr)')
    rampParam = add1dParam(db,rampDict,genSet,genSymbols,rampName,rampDescrip)
    #Start up fixed cost
    startCostDict = getEguParamDict(fleetUC,'StartCost($)',1/scaleDollarsToThousands)
    (startName,startDescrip) = ('pStartupfixedcost','startup fixed cost (thousand$)')
    startCostParam = add1dParam(db,startCostDict,genSet,genSymbols,startName,startDescrip)
    #Min down time
    minDownDict = getEguParamDict(fleetUC,'MinDownTime(hrs)',1)
    (minDownName,minDownDescrip) = ('pMindowntime','min down time (hrs)')
    minDownParam = add1dParam(db,minDownDict,genSet,genSymbols,minDownName,minDownDescrip)

def addEguRegCostParam(db,fleetUC,genSet,genSymbols,scaleMWtoGW,scaleDollarsToThousands):
    regCostDict = getEguParamDict(fleetUC,'RegOfferCost($/MW)',scaleMWtoGW/scaleDollarsToThousands)
    (regCostName,regCostDesc) = ('pRegoffercost','reg offer cost (thousand$/GW)')
    regCostParam = add1dParam(db,regCostDict,genSet,genSymbols,regCostName,regCostDesc)

##### NON-TIME-VARYING GENERATOR CAPACITIES
def addEguCapacParam(db,genFleet,genSet,genSymbols,scaleMWtoGW):
    capacDict = getEguParamDict(genFleet,'Capacity (MW)',1/scaleMWtoGW)
    (capacName,capacDescrip) = ('pCapac','capacity (GW)')
    capacParam = add1dParam(db,capacDict,genSet,genSymbols,capacName,capacDescrip)

##### STORAGE PARAMETERS
def addStorageParams(db,fleetUC,stoGenSet,stoGenSymbols,stoMarket,scaleMWtoGW):
    stoRows = getStoRows(fleetUC)  
    #Efficiency
    effDict = getStoDict(stoRows,fleetUC[0],'Efficiency')
    effParam = add1dParam(db,effDict,stoGenSet,stoGenSymbols,'pEfficiency','roundtrip eff')
    #Charge capacity
    chargeDict = getStoDict(stoRows,fleetUC[0],'CapacityCharge (MW)',scaleMWtoGW)
    chargeParam = add1dParam(db,chargeDict,stoGenSet,stoGenSymbols,'pCapaccharge','charge capac (GW)')
    #Max state of charge
    maxChargeDict = getStoDict(stoRows,fleetUC[0],'MaxCharge(MWh)',scaleMWtoGW)
    maxChargeParam = add1dParam(db,maxChargeDict,stoGenSet,stoGenSymbols,'pMaxstateofcharge','max charge (GWh)')
    #Min state of charge
    minChargeDict = getStoDict(stoRows,fleetUC[0],'MinCharge(MWh)',scaleMWtoGW)
    minChargeParam = add1dParam(db,minChargeDict,stoGenSet,stoGenSymbols,'pMinstateofcharge','min charge (GWh)')
    #Whether storage can provide energy in energy market
    if stoMarket == 'energy' or stoMarket == 'both': pStoinenergymarket = 1
    elif stoMarket == 'reserve': pStoinenergymarket = 0
    add0dParam(db,'pStoinenergymarket','whether storage can provide energy to energy mkt',
           pStoinenergymarket)

def getStoRows(fleetUC):
    typeCol = fleetUC[0].index('PlantType')
    return [row for row in fleetUC if row[typeCol] == 'Storage']

def getStoDict(stoRows,heads,paramName,*args):
    paramCol = heads.index(paramName)
    paramDict = dict()
    for row in stoRows:
        if len(args) == 1: paramVal = float(row[paramCol])/args[0]
        else: paramVal = float(row[paramCol])
        paramDict[createGenSymbol(row,heads)] = paramVal
    return paramDict

#Storage initial conditions
#Inputs: init charge as 1d list in order of storage units in fleet (MWh)
def addStorageInitCharge(db,initCharge,fleetUC,stoGenSet,stoGenSymbols,scaleMWtoGW):
    stoRows = getStoRows(fleetUC)
    initChargeDict = getStoInitCondDict(initCharge,stoRows,fleetUC[0],scaleMWtoGW)
    initChargeParam = add1dParam(db,initChargeDict,stoGenSet,stoGenSymbols,'pInitialstateofcharge','init charge (GWh)')

def getStoInitCondDict(initCondVals,stoRows,heads,*args):
    if len(args)>0: scalar=args[0]
    else: scalar=1
    paramDict = dict()
    for idx in range(len(stoRows)):
        row = stoRows[idx]
        paramDict[createGenSymbol(row,heads)] = initCondVals[idx]/scalar #MW to GW
    return paramDict

##### RESERVE PARAMETERS
#Add reg reserve parameters
def addRegReserveParameters(db,regUp,regDown,rrToRegTime,hourSet,hourSymbols,scaleMWtoGW,modelName):
    rampToRegParam = db.add_parameter('pRampratetoregreservescalar',0,'convert ramp rate to reg timeframe')
    rampToRegParam.add_record().value = rrToRegTime
    #Add hourly reg reserves; in CE model, increases w/ built wind, hence diff
    #name than UC model.
    regUpDict = getParamIndexedByHourDict(regUp,hourSymbols,1/scaleMWtoGW)
    if modelName == 'UC': regParamName = 'pRegupreserves'
    elif modelName == 'CE': regParamName = 'pRegupreserveinitial'
    (regUpName,regUpDescr) = (regParamName,'hourly reg up reserves (GWh)')
    regParam = add1dParam(db,regUpDict,hourSet,hourSymbols,regUpName,regUpDescr)
    regDownDict = getParamIndexedByHourDict(regDown,hourSymbols,1/scaleMWtoGW)
    if modelName == 'UC': regParamName = 'pRegdownreserves'
    elif modelName == 'CE': regParamName = 'pRegdownreserveinitial'
    (regDownName,regDownDescr) = (regParamName,'hourly reg down reserves (GWh)')
    regParam = add1dParam(db,regDownDict,hourSet,hourSymbols,regDownName,regDownDescr)

#Add params for increased reg up & down per unit of wind & solar added. No scaling
#b/c original val is MWreserve/MWwind = GWreserve/GWwind.
def addRegIncParams(db,regUpWindIncCE,regUpSolarIncCE,regDownWindIncCE,regDownSolarIncCE,hourSet,hourSymbols):
    regUpWindIncDict = getParamIndexedByHourDict(regUpWindIncCE,hourSymbols,1)
    add1dParam(db,regUpWindIncDict,hourSet,hourSymbols,'pAddedregupforaddedwind','reg up inc for added wind')    
    regUpSolarIncDict = getParamIndexedByHourDict(regUpSolarIncCE,hourSymbols,1)
    add1dParam(db,regUpSolarIncDict,hourSet,hourSymbols,'pAddedregupforaddedsolar','reg up inc for added solar')    
    regDownWindIncDict = getParamIndexedByHourDict(regDownWindIncCE,hourSymbols,1)
    add1dParam(db,regDownWindIncDict,hourSet,hourSymbols,'pAddedregdownforaddedwind','reg down inc for added wind')    
    regDownSolarIncDict = getParamIndexedByHourDict(regDownSolarIncCE,hourSymbols,1)
    add1dParam(db,regDownSolarIncDict,hourSet,hourSymbols,'pAddedregdownforaddedsolar','reg down inc for added solar')    

#Add params for increased flex per unit of wind & solar added
def addFlexIncParams(db,flexWindIncCE,flexSolarIncCE,hourSet,hourSymbols):
    flexWindDict = getParamIndexedByHourDict(flexWindIncCE,hourSymbols,1)
    add1dParam(db,flexWindDict,hourSet,hourSymbols,'pAddedflexforaddedwind','flex inc for added wind')
    flexSolarDict = getParamIndexedByHourDict(flexSolarIncCE,hourSymbols,1)
    add1dParam(db,flexSolarDict,hourSet,hourSymbols,'pAddedflexforaddedsolar','flex inc for added solar')

def addFlexReserveParameters(db,flexRes,rrToFlexTime,hourSet,hourSymbols,scaleMWtoGW,modelName):
    rampToFlexParam = db.add_parameter('pRampratetoflexreservescalar',0,'convert ramp rate to flex timeframe')
    rampToFlexParam.add_record().value = rrToFlexTime
    flexDict = getParamIndexedByHourDict(flexRes,hourSymbols,1/scaleMWtoGW)
    if modelName == 'UC': regParamName = 'pFlexreserves'
    elif modelName == 'CE': regParamName = 'pFlexreserveinitial'
    (flexName,flexDesc) = (regParamName,'hourly flex reserves (GWh)')
    flexParam = add1dParam(db,flexDict,hourSet,hourSymbols,flexName,flexDesc)
    
def addContReserveParameters(db,contRes,rrToContTime,hourSet,hourSymbols,scaleMWtoGW):
    rampToContParam = db.add_parameter('pRampratetocontreservescalar',0,'convert ramp rate to cont timeframe')
    rampToContParam.add_record().value = rrToContTime
    contDict = getParamIndexedByHourDict(contRes,hourSymbols,1/scaleMWtoGW)
    (contName,contDesc) = ('pContreserves','hourly cont reserves (GWh)')
    contParam = add1dParam(db,contDict,hourSet,hourSymbols,contName,contDesc)
    
##### INITIAL CONDITIONS
#Always pass in energy values in MWh
def addEguInitialConditions(db,genSet,genSymbols,fleetUC,onOffInitial,genAboveMinInitial,
                            mdtCarriedInitial,scaleMWtoGW):
    onOffInitialDict = getInitialCondsDict(fleetUC,onOffInitial,1)
    (onOffInitialName,onOffInitialDescrip) = ('pOnoroffinitial','whether initially on (1) or off (0) based on last UC')
    onOffInitialParam = add1dParam(db,onOffInitialDict,genSet,genSymbols,onOffInitialName,onOffInitialDescrip)
    mdtCarryDict = getInitialCondsDict(fleetUC,mdtCarriedInitial,1)
    (mdtCarryName,mdtCarryDescrip) = ('pMdtcarriedhours','remaining min down time hrs from last UC (hrs))')
    mdtCarryParam = add1dParam(db,mdtCarryDict,genSet,genSymbols,mdtCarryName,mdtCarryDescrip)
    genAboveMinDict = getInitialCondsDict(fleetUC,genAboveMinInitial,scaleMWtoGW) #don't scale - comes out as GW
    (genAboveMinName,genAboveMinDescrip) = ('pGenabovemininitial','initial gen above min load based on last UC (GW)')
    genAboveMinParam = add1dParam(db,genAboveMinDict,genSet,genSymbols,genAboveMinName,genAboveMinDescrip)

def getInitialCondsDict(fleetUC,initialCondValues,scalar):
    initCondsDict = dict()
    for rowNum in range(1,len(fleetUC)):
        initCondsDict[createGenSymbol(fleetUC[rowNum],fleetUC[0])] = initialCondValues[rowNum-1] / scalar
    return initCondsDict

##### WHICH GENERATORS ARE ELIGIBLE TO PROVIDE RESERVES
#Add parameter for which existing generators can provide flex, cont, or reg reserves
def addEguEligibleToProvideRes(db,fleetUC,genSet,genSymbols,*stoMarket):
    fleetOrTechsFlag = 'fleet'
    eligibleFlexDict = getEligibleSpinDict(fleetUC,fleetOrTechsFlag,stoMarket)
    (eligFlexName,eligFlexDesc) = ('pFlexeligible','egu eligible to provide flex (1) or not (0)')
    eligFlexParam = add1dParam(db,eligibleFlexDict,genSet,genSymbols,eligFlexName,eligFlexDesc)
    eligContDict = getEligibleSpinDict(fleetUC,fleetOrTechsFlag,stoMarket)
    (eligContName,eligContDesc) = ('pConteligible','egu eligible to provide cont (1) or not (0)')
    eligContParam = add1dParam(db,eligContDict,genSet,genSymbols,eligContName,eligContDesc)
    eligibleRegDict = getEguParamDict(fleetUC,'RegOfferElig',1)
    (eligRegName,eligRegDescrip) = ('pRegeligible','egu eligible to provide reg res (1) or not (0)')
    eligibleRegParam = add1dParam(db,eligibleRegDict,genSet,genSymbols,eligRegName,eligRegDescrip)

#Add parameter for which new techs can provide spin or reg reserves
def addTechEligibleToProvideRes(db,newTechsCE,techSet,techSymbols):
    fleetOrTechsFlag = 'techs'
    eligibleFlexDict = getEligibleSpinDict(newTechsCE,fleetOrTechsFlag)
    (eligFlexName,eligFlexDesc) = ('pFlexeligibletech','tech eligible to provide flex (1) or not (0)')
    eligFlexParam = add1dParam(db,eligibleFlexDict,techSet,techSymbols,eligFlexName,eligFlexDesc)
    eligContDict = getEligibleSpinDict(newTechsCE,fleetOrTechsFlag)
    (eligContName,eligContDesc) = ('pConteligibletech','tech eligible to provide cont (1) or not (0)')
    eligContParam = add1dParam(db,eligContDict,techSet,techSymbols,eligContName,eligContDesc)
    regOfferEligDict = getTechParamDict(newTechsCE,techSymbols,'RegOfferElig')
    (regName,regDesc) = ('pRegeligibletech','reg up offer eligible')
    regOfferParam = add1dParam(db,regOfferEligDict,techSet,techSymbols,regName,regDesc)

#Returns dict of whether units can provide spin reserves or not based on the plant type
def getEligibleSpinDict(fleetOrTechsData,fleetOrTechsFlag,*stoMarket):
    (windPlantType,solarPlantType) = getWindAndSolarPlantTypes()
    plantTypesNotProvideRes = {windPlantType,solarPlantType}
    if len(stoMarket) > 0 and len(stoMarket[0]) > 0 and stoMarket[0][0] == 'energy': plantTypesNotProvideRes.add('Storage') 
    if fleetOrTechsFlag=='fleet': plantTypeCol = fleetOrTechsData[0].index('PlantType')
    elif fleetOrTechsFlag=='techs': plantTypeCol = fleetOrTechsData[0].index('TechnologyType')
    eligibleSpinDict = dict()
    for rowNum in range(1,len(fleetOrTechsData)):
        plantType = fleetOrTechsData[rowNum][plantTypeCol]
        if plantType in plantTypesNotProvideRes: provideSpin = 0
        else: provideSpin = 1
        if fleetOrTechsFlag=='fleet': symbol = createGenSymbol(fleetOrTechsData[rowNum],fleetOrTechsData[0])
        elif fleetOrTechsFlag=='techs': symbol = plantType
        eligibleSpinDict[symbol] = provideSpin
    return eligibleSpinDict

def getWindAndSolarPlantTypes():
    return ('Wind','Solar PV')

##### COST OF NON-SERVED ENERGY
def addCostNonservedEnergy(db,cnse,scaleMWtoGW,scaleDollarsToThousands):
    add0dParam(db,'pCnse','cost of non-served energy (thousand$/GWh)',
               cnse*scaleMWtoGW*1/scaleDollarsToThousands)

##### CO2 PRICE
def addCo2Price(db,co2Price,scaleDollarsToThousands):
    add0dParam(db,'pCO2price','co2 emissions price (thousand$/short ton)',
               co2Price*1/scaleDollarsToThousands)
################################################################################
################################################################################
################################################################################

################################################################################
############ GENERIC FUNCTIONS TO ADD PARAMS TO GAMS DB ########################
################################################################################
def add0dParam(db,paramName,paramDescrip,paramValue):
    addedParam = db.add_parameter(paramName,0,paramDescrip)
    addedParam.add_record().value = paramValue

def add1dParam(db,paramDict,idxSet,setSymbols,paramName,paramDescrip):
    addedParam = db.add_parameter_dc(paramName,[idxSet],paramDescrip)
    for idx in setSymbols:
        addedParam.add_record(idx).value = paramDict[idx]
    return addedParam

def add2dParam(db,param2dDict,idxSet1,idxSet2,paramName,paramDescrip):
    addedParam = db.add_parameter_dc(paramName,[idxSet1,idxSet2],paramDescrip)
    for k,v in iter(param2dDict.items()):
        addedParam.add_record(k).value = v
    return addedParam    

#Takes in gen fleet and param col name, and returns a dictionary of (genSymbol:paramVal) 
#for each row.
def getEguParamDict(genFleet,paramColName,*scalar):
    paramCol = genFleet[0].index(paramColName)
    paramDict = dict()
    for row in genFleet[1:]:
        paramDict[createGenSymbol(row,genFleet[0])] = float(row[paramCol])*scalar[0]
    return paramDict

#Takes in gen fleet and returns dictionary of (genSymbol:opCost)
def getEguOpCostDict(genFleet,scaleLbToShortTon,scaleMWtoGW,scaleDollarsToThousands,*co2Price):
    if len(co2Price[0])>0: (opCosts,hrs) = calcOpCosts(genFleet,scaleLbToShortTon,co2Price[0][0]) #thousand $/GWh
    else: (opCosts,hrs) = calcOpCosts(genFleet,scaleLbToShortTon) #thousand $/GWh
    paramDict = dict()
    for idx in range(1,len(genFleet)):
        genSymb = createGenSymbol(genFleet[idx],genFleet[0])
        paramDict[genSymb] = opCosts[idx-1]*scaleMWtoGW/scaleDollarsToThousands #op costs = 1d list of vals, so offset by 1
    return paramDict
################################################################################
################################################################################
################################################################################

