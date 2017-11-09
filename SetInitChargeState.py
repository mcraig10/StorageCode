#Michael Craig
#October 7, 2016
#Set initial state of charge of storage for UC runs, either to arbitrary
#value on very first UC run or based on final state of charge after prior
#UC run.

from GAMSAuxFuncs import *

############### INITIAL CHARGE FOR FIRST UC RUN ################################
#Takes in fleet w/ storage units (1 or more), and returns 1d list of 
#initial charge states (MWh) only for storage units. Position in list corresponds
#to position of storage units in fleet.
def setInitChargeFirstUC(fleetUC):
    initChargeFractionOfMaxCharge = 0.5
    maxChargeCol = fleetUC[0].index('MaxCharge(MWh)')
    stoRows = getStoRows(fleetUC)
    stoChargeInitial = [int(row[maxChargeCol])*initChargeFractionOfMaxCharge 
                        for row in stoRows]
    return stoChargeInitial

#Returns list of fleet rows that are storage units
def getStoRows(fleetUC):
    stoPlantType = 'Storage'
    plantCol = fleetUC[0].index('PlantType')
    stoRows = [row for row in fleetUC if row[plantCol] == stoPlantType]
    return stoRows

############### INITIAL CHARGE PER PRIOR UC RUN ################################
#Inputs: UC output (GAMS obj), fleet, hours included in last UC run (1d list)
#Outputs: 1d list of init charge (MWh) for curr UC run
def setInitChargePerPriorUC(ucModel,fleetUC,hoursForUC,daysLA,scaleMWtoGW):
    lastHourSymbolPriorUCRun = 'h' + str((min(hoursForUC) - 1))
    chargeDict = extract2dVarResultsIntoDict(ucModel,'vStateofcharge') #(storageegu,h)
    chargeInitial = getStoInitCondValues(chargeDict,fleetUC,lastHourSymbolPriorUCRun,scaleMWtoGW)
    return chargeInitial

#Convert dict of output UC values into 1d list
#Inputs: dictionary of UC output (genID:val), gen fleet, last hour symbol of prior UC run
#Outputs: 1d list of init cond values for curr UC run
def getStoInitCondValues(stoInitCondDict,fleetUC,lastHourSymbolPriorUCRun,*args):
    stoInitCondValues = []
    stoRows = getStoRows(fleetUC)
    if len(args)>0: scalar = args[0]
    else: scalar = 1
    for row in stoRows:    
        stoInitCondValues.append(stoInitCondDict[(createGenSymbol(row,fleetUC[0]),lastHourSymbolPriorUCRun)]*scalar)
    return stoInitCondValues

