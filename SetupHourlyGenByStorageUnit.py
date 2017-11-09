#Michael Craig
#November 16, 2016

import copy
from SetupResultLists import getHourSymbolsForUC
from GAMSAuxFuncs import createGenSymbol,createHourSymbol

#Setup 2d lists (hours across top, rows of storage units) with charging
#and state of charge by storage units.

def setupHourlyResultsBySto(daysForUC,fleetUC):
    (chargeBySto,genToRowSto,hourToColSto) = setupHourlyResultBySto(daysForUC,fleetUC)
    socBySto = copy.deepcopy(chargeBySto)
    return (chargeBySto,socBySto,genToRowSto,hourToColSto)

#Inputs: days included in UC, fleet UC
#Outputs: empty 2d list of gens x hours, dict mapping gen to row # and hour to col #
def setupHourlyResultBySto(daysForUC,fleetUC):
    stoRows = [fleetUC[0]] + [row for row in fleetUC if row[fleetUC[0].index('PlantType')] == 'Storage']
    #Initialize stuff
    (genToRow,hourToCol,chargeByStoUnits) = (dict(),dict(),[])
    #Create empty 2d list
    numRows = len(stoRows) - 1 + 1 #-1 for header in fleet, +1 for header in new 2d list
    for idx in range(numRows): chargeByStoUnits.append(['']*(1+len(daysForUC)*24))
    #Add hours as first row, starting at col 1 since first col is gen IDs
    hourSymbolsForUC = getHourSymbolsForUC(daysForUC)
    genIDLabel = 'genID'
    chargeByStoUnits[0] = [genIDLabel] + hourSymbolsForUC
    #Create dict mapping hours to col #s
    for idx in range(1,len(chargeByStoUnits[0])): hourToCol[chargeByStoUnits[0][idx]] = idx 
    #Add gens as first col, starting at row 1 since first row is hours
    genSymbols = [createGenSymbol(row,stoRows[0]) for row in stoRows[1:]]
    for idx in range(1,len(chargeByStoUnits)): chargeByStoUnits[idx][0] = genSymbols[idx-1] #-1 b/c row 1 of hourlyGen = hours
    #Create dict mapping gens to row #s
    firstColVals = [row[0] for row in chargeByStoUnits]
    genToRow = dict()
    for idx in range(1,len(firstColVals)): genToRow[firstColVals[idx]] = idx
    return (chargeByStoUnits,genToRow,hourToCol)
