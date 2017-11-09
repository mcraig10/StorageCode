#Michael Craig
#Dec 2, 2016

#Initialize on/off commitment state of existing units for CE model for first
#hour in each time block (seasons + demand day + ramp day).

from operator import *
from AuxFuncs import *
from GAMSAuxFuncs import *
from CalculateOpCost import calcOpCosts
import copy

#For first hour of each time block, gets gen stack, sorts gens by op cost, then
#meets demand and assigns dispatched gens to "on".
#Inputs: gen fleet, hours + hourly wind & solar gen + demand for CE model (1d list,
#slimmed to CE hours), dict mapping time block to hours in that time block
#Outputs: dict mapping block to dict mapping gen symbol to on/off in first hour of dict.
def initializeOnOffExistingGens(genFleetForCE,hoursCE,hourlyWindGenCE,hourlySolarGenCE,
                                demandCE,hrsByBlock):
    netDemandCE = [demandCE[idx] - hourlyWindGenCE[idx] - hourlySolarGenCE[idx] 
                        for idx in range(len(demandCE))]
    firstHoursIdxs = [0] + [idx for idx in range(1,len(hoursCE)) if (hoursCE[idx]-hoursCE[idx-1]!=1)]
    firstHours = [hoursCE[idx] for idx in firstHoursIdxs]
    firstHoursNetDemand = [netDemandCE[idx] for idx in firstHoursIdxs]
    sortedSymbols,sortedCapacs,reGenSymbols = getGenStack(genFleetForCE)
    blockToOnOff = dict() 
    for idx in range(len(firstHours)):
        currHour,hourNetDemand = firstHours[idx],firstHoursNetDemand[idx]
        genToOnOff = getGenOnOffForHour(sortedSymbols,sortedCapacs,reGenSymbols,hourNetDemand,idx)
        currBlock = mapHourToBlock(currHour,hrsByBlock)
        blockToOnOff[currBlock] = genToOnOff 
    return blockToOnOff

#Get gen stack for fleet, returning sorted gen symbols, capacities, and RE gen symbols.
#Sorted in order of least -> most costly.
def getGenStack(genFleetForCE):
    reFuelTypes = ['Wind','Solar']
    fuelCol = genFleetForCE[0].index('Modeled Fuels')
    genFleetNoRE = [row for row in genFleetForCE if row[fuelCol] not in reFuelTypes]
    reGenSymbols = [createGenSymbol(row,genFleetForCE[0]) for row in genFleetForCE[1:] 
                                                    if row[fuelCol] in reFuelTypes]
    capacCol = genFleetNoRE[0].index('Capacity (MW)')
    genCapacs = [float(row[capacCol]) for row in genFleetNoRE[1:]]
    (genOpCosts,genHrs) = calcOpCosts(genFleetNoRE,1)
    genSymbols = [createGenSymbol(row,genFleetNoRE[0]) for row in genFleetNoRE[1:]]
    genCostSymbolCapac = [[genOpCosts[idx],genSymbols[idx],genCapacs[idx]] for idx in range(len(genOpCosts))]
    sortedGenCostSymbolCapac = sorted(genCostSymbolCapac)
    sortedCapacs = [row[2] for row in sortedGenCostSymbolCapac]
    sortedSymbols = [row[1] for row in sortedGenCostSymbolCapac]
    return sortedSymbols,sortedCapacs,reGenSymbols

#For given net demand value in hour, determine which gens should be on by 
#dispatching them using gen stack.
def getGenOnOffForHour(sortedSymbols,sortedCapacs,reGenSymbols,hourNetDemand,idx):
    onGens,offGens = dispatchGens(sortedSymbols,sortedCapacs,hourNetDemand)
    onGens.extend(reGenSymbols)
    genToOnOff = dict()
    for gen in onGens: genToOnOff[gen] = 1
    for gen in offGens: genToOnOff[gen] = 0
    return genToOnOff
    
#Meet demand w/ gen stack.
def dispatchGens(sortedSymbols,sortedCapacs,hourNetDemand):
    cumCapacs = [sum(sortedCapacs[:idx+1]) for idx in range(len(sortedCapacs))]
    supplyGap = [hourNetDemand - cumCapac  for cumCapac in cumCapacs]
    supplyGapLessThanZero = [le(gap,0) for gap in supplyGap] #le is <=
    if True in supplyGapLessThanZero: #enough gens to meet demand
        idxMeetDemand = supplyGapLessThanZero.index(True)
        onGens = [sortedSymbols[idx] for idx in range(idxMeetDemand+1)]
        offGens = [sortedSymbols[idx] for idx in range(idxMeetDemand+1,len(sortedSymbols))]
    else: #all gens turn on
        onGens = copy.deepcopy(sortedSymbols)
        offGens = []
    return onGens,offGens

def mapHourToBlock(currHour,hrsByBlock):
    for block in hrsByBlock: 
        if currHour in hrsByBlock[block]: return block

