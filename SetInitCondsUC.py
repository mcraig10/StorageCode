#Michael Craig
#October 4, 2016
#Sets values for initial condition parameters for UC run, either for first
#run of entire year using assumed values or based on last values in prior run.

from GAMSAuxFuncs import *

########### SET INITIAL CONDITION PARAMETERS FOR FIRST UC RUN ##################
#For first UC run of year. Assume all plants initially off w/ no carried MDT
#Inputs: gen fleet
#Outputs: 1d list of initial on/off, gen above min (MWh), & carried MDT values
def setInitCondsFirstUC(fleetUC):
    onOffInitial = [0 for i in range(1,len(fleetUC))]
    genAboveMinInitial = [0 for i in range(1,len(fleetUC))] #MW
    mdtCarriedInitial = [0 for i in range(1,len(fleetUC))]
    return (onOffInitial,genAboveMinInitial,mdtCarriedInitial)
            
########### SET INITIAL CONDITION PARAMETERS PER PRIOR UC RUN ##################
#Set values for init cond params based on prior UC run
#Inputs: prior UC run results as GAMS object, gen fleet, hours for curr UC run, 
#num days for optim horiz (i.e., keep those results), num days look ahead (need to skip these).
#Outputs: 1d lists of initial on/off & gen above min (MWh) & carried MDT vals
def setInitCondsPerPriorUC(ucModel,fleetUC,hoursForUC,daysOpt,daysLA,scaleMWtoGW):
    #For genAboveMin & onOff, just need variable value in prior hour
    lastHourSymbolPriorUCRun = 'h' + str((min(hoursForUC) - 1))
    onOffDict = extract2dVarResultsIntoDict(ucModel,'vOnoroff')
    onOffInitial = getInitCondValues(onOffDict,fleetUC,lastHourSymbolPriorUCRun)
    genAboveMinDict = extract2dVarResultsIntoDict(ucModel,'vGenabovemin')
    genAboveMinInitial = getInitCondValues(genAboveMinDict,fleetUC,lastHourSymbolPriorUCRun,scaleMWtoGW) #MW
    #For mdtCarriedInitial, get last turnoff decision, subtract # hours from then
    #to end of last time period, and subtract that from MDT.
    mdtCarriedInitial = getMdtCarriedInitial(onOffInitial,ucModel,fleetUC,hoursForUC,daysOpt,daysLA)
    return (onOffInitial,genAboveMinInitial,mdtCarriedInitial)

#Determines carried MDT hours based on when unit turned off (if at all) in
#prior UC run.
#Inputs: whether initially on/off in curr UC run, prior UC run results, 
#gen fleet, hours included in curr UC run, num days in optimization horizon (i.e., to keep),
#num days included as LA
#Outputs: 1d list of carried MDT hours
def getMdtCarriedInitial(onOffInitial,ucModel,fleetUC,hoursForUC,daysOpt,daysLA):
    mdtCarriedInitial = []
    fleetMDTCol = fleetUC[0].index('MinDownTime(hrs)')
    turnOffDict = extract2dVarResultsIntoDict(ucModel,'vTurnoff')
    lastHourPriorUCRun = min(hoursForUC) - 1
    for rowNum in range(1,len(fleetUC)):
        if onOffInitial[rowNum-1]==1:  #on @ start, so no MDT carried
            mdtCarriedInitial.append(0)
        else:
            genSymbol = createGenSymbol(fleetUC[rowNum],fleetUC[0])
            turnOff = 0
            for hr in range(lastHourPriorUCRun,lastHourPriorUCRun - (24*daysOpt) + 1,-1):
                if turnOffDict[(genSymbol,'h'+str(hr))] == 1 and turnOff == 0:
                    turnOff = 1
                    genMDT = float(fleetUC[rowNum][fleetMDTCol])
                    #Hr that turn off counts toward MDT; therefore +1 to hr. 
                    mdtCarriedInitial.append(max(0,genMDT - (lastHourPriorUCRun - hr + 1)))
            if turnOff == 0: mdtCarriedInitial.append(0) #never turned off in last UC
    return mdtCarriedInitial

#Convert dict of output UC values into 1d list
#Inputs: dictionary of UC output (genID:val), gen fleet, last hour symbol of prior UC run
#Outputs: 1d list of init cond values for curr UC run. For energy values, outputs in MW.
def getInitCondValues(initCondDict,fleetUC,lastHourSymbolPriorUCRun,*args):
    initCondValues = []
    if len(args)>0: scalar = args[0]
    else: scalar = 1
    for row in fleetUC[1:]:    
        initCondValues.append(initCondDict[(createGenSymbol(row,fleetUC[0]),lastHourSymbolPriorUCRun)]*scalar)
    return initCondValues