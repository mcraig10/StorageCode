#Michael Craig
#October 4, 2016
#Functions for adding sets to GAMS database. Used for CE & UC models.

from GAMSAuxFuncs import *

########### ADD GENERATOR SETS #################################################
#Add gen sets & subsets
def addGeneratorSets(db,genFleet):
    genSymbols = isolateGenSymbols(genFleet,'')
    (genSetName,genSetDescription,genSetDimension) = ('egu','existing generators',1)
    genSet = addSet(db,genSymbols,genSetName,genSetDescription,genSetDimension) 
    windGenSymbols = isolateGenSymbols(genFleet,'Wind')
    (windGenSetName,windGenSetDescription,windGenSetDimension) = ('windegu','existing wind generators',1)
    windGenSet = addSet(db,windGenSymbols,windGenSetName,windGenSetDescription,windGenSetDimension) 
    solarGenSymbols = isolateGenSymbols(genFleet,'Solar PV')
    (solarGenSetName,solarGenSetDescription,solarGenSetDimension) = ('solaregu','existing solar generators',1)
    solarGenSet = addSet(db,solarGenSymbols,solarGenSetName,solarGenSetDescription,solarGenSetDimension) 
    return (genSet,genSymbols,windGenSet,windGenSymbols,solarGenSet,solarGenSymbols)

def addStoGenSets(db,genFleet):
    stoGenSymbols = isolateGenSymbols(genFleet,'Storage')
    (stoSetName,stoSetDesc,stoSetDim) = ('storageegu','existing storage generators',1)
    stoGenSet = addSet(db,stoGenSymbols,stoSetName,stoSetDesc,stoSetDim) 
    return (stoGenSet,stoGenSymbols)

#Gen symbols: g1, g2, etc., where # = row in gen fleet
def isolateGenSymbols(genFleet,genPlantType):
    if genPlantType == '': #all generators
        genSymbols = [createGenSymbol(row,genFleet[0]) for row in genFleet[1:]]
    else:
        plantTypeCol = genFleet[0].index('PlantType')
        genSymbols = [createGenSymbol(row,genFleet[0]) for row in genFleet[1:]
                        if row[plantTypeCol]==genPlantType]    
    return genSymbols

########### ADD HOUR SETS ######################################################
#Add all hours
def addHourSet(db,hours):
    hourSymbols = [createHourSymbol(hour) for hour in hours]
    (hourSetName,hourSetDescrip,hourSetDim) = ('h','hour',1)
    hourSet = addSet(db,hourSymbols,hourSetName,hourSetDescrip,hourSetDim)
    return (hourSet,hourSymbols)

#Define season subsets of hours
#Inputs: GAMS db, dict of (season:rep hrs)
def addHourSeasonSubsets(db,repHrsBySeason):
    for season in repHrsBySeason:
        seasonHours = repHrsBySeason[season]
        seasonHourSymbols = [createHourSymbol(hour) for hour in seasonHours]
        hourSubsetName = createHourSubsetName(season)
        addSeasonHourSubset(db,hourSubsetName,season,seasonHourSymbols)

def createHourSubsetName(subsetPrefix):
    return subsetPrefix + 'h'

def addSeasonHourSubset(db,hourSubsetName,season,seasonHourSymbols):
    (seasonSetName,seasonSetDescrip,seasonSetDim) = (hourSubsetName,'hours in ' + season,1)
    hourSeasonSet = addSet(db,seasonHourSymbols,seasonSetName,seasonSetDescrip,seasonSetDim)

#Define special subsets of hours
#Inputs: GAMS db, 1d list of special hours
def addPeakNetDemandDayHoursSubset(db,peakNetDemandDayHrs):
    hourSymbols = [createHourSymbol(hour) for hour in peakNetDemandDayHrs]
    hourSubsetName = createHourSubsetName('demand')
    (specialSetName,specialSetDescrip,specialSetDim) = (hourSubsetName,'hours in max demand day',1)
    hourSpecialSet = addSet(db,hourSymbols,specialSetName,specialSetDescrip,specialSetDim)

#Define special subsets of hours
#Inputs: GAMS db, 1d list of special hours
def addPeakNetRampDayHoursSubset(db,peakNetRampDayHrs):
    hourSymbols = [createHourSymbol(hour) for hour in peakNetRampDayHrs]
    hourSubsetName = createHourSubsetName('ramp')
    (specialSetName,specialSetDescrip,specialSetDim) = (hourSubsetName,'hours in max ramp day',1)
    hourSpecialSet = addSet(db,hourSymbols,specialSetName,specialSetDescrip,specialSetDim)

#Define peak demand hour subset
def addPeakHourSubset(db,peakDemandHour):
    peakHrSymbol = [createHourSymbol(peakDemandHour)]
    hourSubsetName = createHourSubsetName('peak')
    (specialSetName,specialSetDescrip,specialSetDim) = (hourSubsetName,'peak hour',1)
    hourSpecialSet = addSet(db,peakHrSymbol,specialSetName,specialSetDescrip,specialSetDim)

########### ADD NEW TECH SETS ##################################################
#Inputs: GAMS db, new techs (2d list)
def addNewTechsSets(db,newTechsCE):
    (techSymbols,thermalTechSymbols,renewTechSymbols) = isolateTechSymbols(newTechsCE)
    #Add all techs
    (techSetName,techSetDescrip,techSetDim) = ('tech','techs for expansion',1)
    techSet = addSet(db,techSymbols,techSetName,techSetDescrip,techSetDim)
    #Add thermal tech subset
    (thermalTechSetName,thermalTechSetDescrip,thermalTechSetDim) = ('thermaltech',
                                        'thermal techs for expansion',1)
    thermalTechSet = addSet(db,thermalTechSymbols,thermalTechSetName,
                            thermalTechSetDescrip,thermalTechSetDim)
    #Add renew tech subset
    (renewTechSetName,renewTechSetDescrip,renewTechSetDim) = ('renewtech',
                                        'renewable techs for expansion',1)
    renewTechSet = addSet(db,renewTechSymbols,renewTechSetName,
                          renewTechSetDescrip,renewTechSetDim)
    return (techSet,techSymbols,thermalTechSet,thermalTechSymbols,renewTechSet,renewTechSymbols)

#Takes in new techs (2d list), and returns tech types all together or separated
#as thermal versus renewable
def isolateTechSymbols(newTechsCE):
    techTypeCol = newTechsCE[0].index('ThermalOrRenewable')
    techSymbols = [createTechSymbol(row,newTechsCE[0]) for row in newTechsCE[1:]]
    techThermalSymbols = [createTechSymbol(row,newTechsCE[0]) for row in newTechsCE[1:] 
                                                        if row[techTypeCol]=='thermal']
    techRenewSymbols = [createTechSymbol(row,newTechsCE[0]) for row in newTechsCE[1:] 
                                                        if row[techTypeCol]=='renewable']
    return (techSymbols,techThermalSymbols,techRenewSymbols)

########### GENERIC FUNCTION TO ADD SET TO DATABASE ############################
#Adds set to GAMS db
def addSet(db,setSymbols,setName,setDescription,setDim):
    addedSet = db.add_set(setName, setDim, setDescription)
    for symbol in setSymbols:
        addedSet.add_record(symbol)
    return addedSet