import os
from AuxFuncs import *

#Checks total fleet generation in base case versus storage charging and
#discharging. Also confirms total charging by storage is right given
#efficiency, final and initial soc, and generation.

baseFolder = 'ResultsFullYearNoStorageCoopt'
stoFolder = 'ResultsFullYearStorageEnergy'

stoEff = .81

#GET GENERATION
genFile = 'genByPlantUC2015.csv'

baseGen = readCSVto2dList(os.path.join(baseFolder,genFile))
stoGen = readCSVto2dList(os.path.join(stoFolder,genFile))

fleetBaseGen = 0
for row in baseGen[1:]:
    fleetBaseGen += sum([float(val) for val in row[1:]])

fleetStoGen = 0
for row in stoGen[1:]:
    fleetStoGen += sum([float(val) for val in row[1:]])

fleetStoGenWithoutSto = 0
for row in stoGen[1:-1]:
    fleetStoGenWithoutSto += sum([float(val) for val in row[1:]])    

stoStoGen = sum([float(val) for val in stoGen[-1][1:]])

#GET CHARGING
chargeFile = 'chargeByStoUC2015.csv'
stoCharge = readCSVto2dList(os.path.join(stoFolder,chargeFile))
stoStoCharge = sum([float(val) for val in stoCharge[-1][1:]])

#GET NSE
nseFile = 'systemResultsUC2015.csv'
nseBase = readCSVto2dList(os.path.join(baseFolder,nseFile))
nseSto = readCSVto2dList(os.path.join(stoFolder,nseFile))
nseRow = [row[0] for row in nseBase].index('nse')
totalNseBase = sum([float(val) for val in nseBase[nseRow][1:]])
totalNseSto = sum([float(val) for val in nseSto[nseRow][1:]])

#GET STATE OF CHARGE
socFile = 'socByStoUC2015.csv'
stoSoc = readCSVto2dList(os.path.join(stoFolder,socFile))
stoSocInitial = float(stoSoc[1][1])
stoSocFinal = float(stoSoc[1][-1])

#RUN CHECKS
print('Sto charge - gen:',stoStoCharge - stoStoGen)
print('Fleet gen, sto run - base run:',(fleetStoGenWithoutSto+totalNseSto) - (fleetBaseGen+totalNseBase))

print('Sto charge:',stoStoCharge,' should equal:',
        (stoSocFinal - stoSocInitial + stoStoGen)/(stoEff))

#CHECK EFFICIENCY LOSSES
#Should be: charge - gen = ((socFinal - socInitial)+gen)/(1-eff)

# print('Fleet gen in base run:',fleetBaseGen)
# print('Fleet gen in storage run:',fleetStoGen)
# print('Fleet gen in storage run w/out storage gen:',fleetStoGenWithoutSto)
# print('Storage gen:',stoStoGen,'and charging:',stoStoCharge)
# print('Storage eff loss from charging:',stoStoCharge*.1)
# print('Fleet gen diff from base to storage run:',fleetStoGenWithoutSto - fleetBaseGen)
# print('Storage gen + eff loss:',stoStoGen + stoStoGen*.1)




#CHECK DEMAND
demandFile = 'demandUC2015.csv'

baseDemand = readCSVto2dList(os.path.join(baseFolder,demandFile))[0]
stoDemand = readCSVto2dList(os.path.join(stoFolder,demandFile))[0]

print('Total base demand:',sum([float(val) for val in baseDemand]))
print('Total sto demand:',sum([float(val) for val in stoDemand]))