#Michael Craig
#October 20, 2016
#Setup empty 2d list w/ all gens in rows & hours in col,
#and return that list + 2 dicts mapping genID to row & hour to col

from GAMSAuxFuncs import createGenSymbol,createHourSymbol
import copy

############ SETUP GEN X HOUR RESULT LISTS #####################################
#Outputs empty 2d lists that will store gen-by-hour results
#Inputs: days included in UC, fleet UC
#Outputs: empty 2d lists of gens x hours, dict mapping gen to row # and hour to col #
def setupHourlyResultsByPlant(daysForUC,fleetUC):
    hourSymbolsForUC = getHourSymbolsForUC(daysForUC)
    (genByPlant,genToRow,hourToCol) = setupHourlyGenByPlant(hourSymbolsForUC,fleetUC)
    regUpByPlant = copy.deepcopy(genByPlant)
    regDownByPlant = copy.deepcopy(genByPlant)
    flexByPlant = copy.deepcopy(genByPlant)
    contByPlant = copy.deepcopy(genByPlant)
    turnonByPlant = copy.deepcopy(genByPlant)
    turnoffByPlant = copy.deepcopy(genByPlant)
    onOffByPlant = copy.deepcopy(genByPlant)
    return (genByPlant,regUpByPlant,flexByPlant,contByPlant,turnonByPlant,
        turnoffByPlant,regDownByPlant,onOffByPlant,genToRow,hourToCol) #

#Inputs: days included in UC, fleet UC
#Outputs: empty 2d list of gens x hours, dict mapping gen to row # and hour to col #
def setupHourlyGenByPlant(hourSymbolsForUC,fleetUC):
    (genToRow,hourToCol) = (dict(),dict())
    #Create empty 2d list
    numRows = len(fleetUC) - 1 + 1 #-1 for header in fleet, +1 for header in new 2d list
    hourlyGenByPlant = []
    for idx in range(numRows): hourlyGenByPlant.append(['']*(1+len(hourSymbolsForUC)))
    #Add hours as first row, starting at col 1 since first col is gen IDs
    genIDLabel = 'genID'
    hourlyGenByPlant[0] = [genIDLabel] + hourSymbolsForUC
    #Create dict mapping hours to col #s
    for idx in range(1,len(hourlyGenByPlant[0])): hourToCol[hourlyGenByPlant[0][idx]] = idx 
    #Add gens as first col, starting at row 1 since first row is hours
    genSymbols = [createGenSymbol(row,fleetUC[0]) for row in fleetUC[1:]]
    for idx in range(1,len(hourlyGenByPlant)): hourlyGenByPlant[idx][0] = genSymbols[idx-1] #-1 b/c row 1 of hourlyGen = hours
    #Create dict mapping gens to row #s
    firstColVals = [row[0] for row in hourlyGenByPlant]
    genToRow = dict()
    for idx in range(1,len(firstColVals)): genToRow[firstColVals[idx]] = idx
    return (hourlyGenByPlant,genToRow,hourToCol)

#Input: list of days for UC. Output: list of hours for UC (1-8760 basis)
def getHourSymbolsForUC(daysForUC):
    hourSymbols = []
    for day in daysForUC: 
        (firstHour,lastHour) = ((day-1)*24+1,day*24) 
        hourSymbols += [createHourSymbol(hr) for hr in range(firstHour,lastHour+1)]
    return hourSymbols
################################################################################

############ SETUP HOURLY RESULT LISTS #########################################
#Inputs: days included iN UC (1d list)
#Outputs: 2d list - 1st row = hours, other rows = diff sys results; dict mapping
#hour symbol to col #; dict mapping result name to row #
def setupHourlySystemResults(daysForUC):
    hourSymbolsForUC = getHourSymbolsForUC(daysForUC)
    resultLabels = ['mcGen','mcRegup','mcFlex','mcCont','nse'] #'mcRegdown',
    return setupHourlySystemResultsWithHourSymbols(hourSymbolsForUC,resultLabels)

def setupHourlySystemResultsWithHourSymbols(hourSymbols,resultLabels):
    hourToColSys, resultToRow, sysResults, numRows = dict(), dict(), [], len(resultLabels) + 1
    #Initialize empty 2d list
    for idx in range(numRows): sysResults.append(['']*(1+len(hourSymbols)))
    #Add hour labels across top
    sysResults[0] = ['Hour'] + hourSymbols
    for idx in range(1,len(sysResults[0])): hourToColSys[sysResults[0][idx]] = idx 
    #Add row labels
    for idx in range(1,len(sysResults)):
        currLabel = resultLabels[idx-1] 
        sysResults[idx][0] = currLabel #-1 b/c row 1 of hourlyGen = hours
        resultToRow[currLabel] = idx
    return (sysResults,resultToRow,hourToColSys)
################################################################################