#Michael Craig
#March 10, 2017
#Determine which coal plants should retire based on CF in PRIOR CE run. (May
#not retire after prior CE run to maintain planning margin.)

from GAMSAuxFuncs import *
from ProcessCEResults import markRetiredUnitsFromCE,sumHourlyGenByGensInCE

def retireUnitsCFPriorCE(genFleet,genFleetPriorCE,retirementCFCutoff,priorCapacExpModel,
                        priorHoursCE,scaleMWtoGW,ptEligRetireCF,currYear):
    unitsRetireCF = markAndSaveRetiredUnitsFromPriorCE(retirementCFCutoff,genFleet,
            genFleetPriorCE,priorCapacExpModel,priorHoursCE,scaleMWtoGW,ptEligRetireCF,currYear)
    print('**retireunits script, units retire CF:',unitsRetireCF)
    return unitsRetireCF

################ RETIRE UNITS BASED ON CF IN PRIOR CE RUN ######################
#Retires coal plants that don't meet CF threshold in PRIOR CE run. These units
#may not retire due to limiting retirements per planning margin.
#INPUTS: Retirement CF cutoff, GAMS CE model output from prior CE run, generator 
#fleet, hours included in CE, scale MW to GW, 1d list of plant types eligible
#to retire based on CFs.
#OUTPUT: 1d list w/ units that retire due to CF
def markAndSaveRetiredUnitsFromPriorCE(retirementCFCutoff,genFleet,genFleetPriorCE,
        priorCapacExpModel,priorHoursCE,scaleMWtoGW,ptEligRetireCF,currYear):
    unitsRetireCF = getUnitsRetireByCF(retirementCFCutoff,genFleet,genFleetPriorCE,
                priorCapacExpModel,priorHoursCE,scaleMWtoGW,ptEligRetireCF)
    markRetiredUnitsFromCE(genFleet,unitsRetireCF,currYear)
    return unitsRetireCF

#Determines which units retire due to CF in prior CE run 
#Inputs: CF cutoff retirement, dictionary (genID:CF) for generators eligible to retire based on CF,
#planning reserve, curr & end year, gen fleet w/ only online gens, plant types that
#can retire due to CF in CE.
#Outputs: 1d list of units to retire for economic reasons
def getUnitsRetireByCF(retirementCFCutoff,genFleet,genFleetPriorCE,
                    priorCapacExpModel,priorHoursCE,scaleMWtoGW,ptEligRetireCF):
    hourlyGenByGens = extract2dVarResultsIntoDict(priorCapacExpModel,'vGen') #(hr,genID):hourly gen [GW]
    ceHoursGenByGens = sumHourlyGenByGensInCE(hourlyGenByGens,scaleMWtoGW)
    gensEligToRetireCFs = getGenCFsInCENotAlreadyRetired(ceHoursGenByGens,genFleet,
                                genFleetPriorCE,ptEligRetireCF,priorHoursCE)
    unitsRetireCF = []
    if len(gensEligToRetireCFs) > 0: 
        minCF = min([gensEligToRetireCFs[gen] for gen in gensEligToRetireCFs])
        if minCF < retirementCFCutoff: #if any plants eligible for retirement
            addAllUnitsWithCFBelowCutoff(gensEligToRetireCFs,retirementCFCutoff,unitsRetireCF)
    return unitsRetireCF

#Determines which gens retire due to CF in prior CE run that didn't already
#retire after last CE run.
#Inputs: total gen by generators for CE hours (dict of genID:total gen), gen fleet 
#only w/ online generators (2d list), list of plant types that can retire based on CF,
#1d list of hours input to CE
#Outputs: dictionary (genID:CF) for generators eligible to retire based on CF
def getGenCFsInCENotAlreadyRetired(ceHoursGenByGens,genFleet,genFleetPriorCE,
                                    plantTypesEligibleForRetirementByCF,hoursForCE):
    gensEligToRetireCFs = dict()
    (capacCol,plantTypeCol) = (genFleet[0].index('Capacity (MW)'),
                                genFleet[0].index('PlantType'))
    econRetCol = genFleet[0].index('YearRetiredByCE')
    genSymbolsFleetFull = [createGenSymbol(row,genFleet[0]) for row in genFleet]
    genSymbolsFleetPriorCE = [createGenSymbol(row,genFleetPriorCE[0]) for row in genFleetPriorCE]
    for gen in ceHoursGenByGens:
        #Need to screen out wind and solar plants in genFleetPriorCE, since these
        #were tacked on @ end of fleet and are not in genFleet. Consequently, if don't
        #have this if statement and don't build new plants, genSymbolsFleetFull.index(gen)
        #call will not find gen listed.
        if (genFleetPriorCE[genSymbolsFleetPriorCE.index(gen)][plantTypeCol] != 'Wind' and 
                genFleetPriorCE[genSymbolsFleetPriorCE.index(gen)][plantTypeCol] != 'Solar PV'):
            genRow = genSymbolsFleetFull.index(gen)
            if genFleet[genRow][plantTypeCol] in plantTypesEligibleForRetirementByCF:
                if genFleet[genRow][econRetCol] == '':
                    genCapac = genFleet[genRow][capacCol]
                    genCF = ceHoursGenByGens[gen]/(float(genCapac)*len(hoursForCE))
                    gensEligToRetireCFs[gen] = genCF
    return gensEligToRetireCFs

#Adds all units elig to retire w/ CF below cutoff to unitsToRetire list
#Inputs: dictionary (genID:CF) for gens elig to retire, retirement CF cutoff,
#empty list to which genIDs for units that should retire are added
def addAllUnitsWithCFBelowCutoff(gensEligToRetireCFs,retirementCFCutoff,unitsRetireCF):
    for gen in gensEligToRetireCFs: 
        genCF = gensEligToRetireCFs[gen]
        if genCF < retirementCFCutoff: unitsRetireCF.append(gen)
################################################################################
