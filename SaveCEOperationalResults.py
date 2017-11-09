#Michael Craig
#Jan 5, 2017

from AuxFuncs import *
from GAMSAuxFuncs import *
from SetupResultLists import setupHourlyGenByPlant,setupHourlySystemResultsWithHourSymbols
import copy, csv

#Saves operational CE results: operations by plants & new techs,
#and MCs on demand and reserve constraints.

def saveCapacExpOperationalData(ceModel,genFleetForCE,newTechsCE,hoursForCE):
    hoursForCESymbols = [createHourSymbol(hr) for hr in hoursForCE]
    (genByPlant,regUpByPlant,regDownByPlant,flexByPlant,contByPlant,turnOnByPlant,
        turnOffByPlant,onOffByPlant,genByTech,regUpByTech,regDownByTech,flexByTech,
        contByTech,turnOnByTech,turnOffByTech,onOffByTech) = saveGeneratorSpecificResults(ceModel,
        genFleetForCE,newTechsCE,hoursForCESymbols)
    sysResults = saveSystemResults(ceModel,hoursForCESymbols)
    co2Ems = extract0dVarResultsFromGAMSModel(ceModel,'vCO2emsannual')
    return (genByPlant,regUpByPlant,regDownByPlant,flexByPlant,contByPlant,turnOnByPlant,
        turnOffByPlant,onOffByPlant,genByTech,regUpByTech,regDownByTech,flexByTech,contByTech,
        turnOnByTech,turnOffByTech,onOffByTech,sysResults,co2Ems)

################### SAVE GENERATOR SPECIFIC RESULTS ############################
#All result arrays need to have same exact format & row/col idxs for gens/hours
def saveGeneratorSpecificResults(ceModel,genFleetForCE,newTechsCE,hoursForCE):
    (genByPlant,regUpByPlant,regDownByPlant,flexByPlant,contByPlant,turnOnByPlant,
        turnOffByPlant,onOffByPlant,genToRow,hourToCol) = setupCEGenResultsLists(genFleetForCE,hoursForCE)
    saveCEResultsByPlantVar(genByPlant,regUpByPlant,regDownByPlant,flexByPlant,contByPlant,
        turnOnByPlant,turnOffByPlant,onOffByPlant,genToRow,hourToCol,ceModel)
    (genByTech,regUpByTech,regDownByTech,flexByTech,contByTech,turnOnByTech,turnOffByTech,onOffByTech,
        genToRowTech,hourToColTech) = setupCETechResultsLists(newTechsCE,hoursForCE)
    saveCEResultsByTechVar(genByTech,regUpByTech,regDownByTech,flexByTech,contByTech,turnOnByTech,
        turnOffByTech,onOffByTech,genToRowTech,hourToColTech,ceModel)
    return (genByPlant,regUpByPlant,regDownByPlant,flexByPlant,contByPlant,turnOnByPlant,turnOffByPlant,
       onOffByPlant,genByTech,regUpByTech,regDownByTech,flexByTech,contByTech,turnOnByTech,turnOffByTech,onOffByTech)

############ SETUP RESULTS LISTS
#Setup empty CE results lists for all by-generator results
def setupCEGenResultsLists(genFleetForCE,hoursForCE):
    (genByPlant,genToRow,hourToCol) = setupHourlyGenByPlant(hoursForCE,genFleetForCE)
    regUpByPlant = copy.deepcopy(genByPlant)
    regDownByPlant = copy.deepcopy(genByPlant)
    flexByPlant = copy.deepcopy(genByPlant)
    contByPlant = copy.deepcopy(genByPlant)
    turnOnByPlant = copy.deepcopy(genByPlant)
    turnOffByPlant = copy.deepcopy(genByPlant)
    onOffByPlant = copy.deepcopy(genByPlant)
    return (genByPlant,regUpByPlant,regDownByPlant,flexByPlant,contByPlant,
            turnOnByPlant,turnOffByPlant,onOffByPlant,genToRow,hourToCol)

#Setup same-formatted results lsits as above for by-tech results
def setupCETechResultsLists(newTechsCE,hoursForCE):
    (genByTech,genToRow,hourToCol) = setupHourlyGenByTech(hoursForCE,newTechsCE)
    regUpByTech = copy.deepcopy(genByTech)
    regDownByTech = copy.deepcopy(genByTech)
    flexByTech = copy.deepcopy(genByTech)
    contByTech = copy.deepcopy(genByTech)
    turnOnByTech = copy.deepcopy(genByTech)
    turnOffByTech = copy.deepcopy(genByTech)
    onOffByTech = copy.deepcopy(genByTech)
    return (genByTech,regUpByTech,regDownByTech,flexByTech,contByTech,turnOnByTech,
            turnOffByTech,onOffByTech,genToRow,hourToCol)

#Setup results lists for techs
def setupHourlyGenByTech(hourSymbolsForUC,newTechsCE):
    (genToRow,hourToCol) = (dict(),dict())
    #Create empty 2d list
    numRows = len(newTechsCE) - 1 + 1 #-1 for header in fleet, +1 for header in new 2d list
    hourlyGenByPlant = []
    for idx in range(numRows): hourlyGenByPlant.append(['']*(1+len(hourSymbolsForUC)))
    #Add hours as first row, starting at col 1 since first col is gen IDs
    genIDLabel = 'genID'
    hourlyGenByPlant[0] = [genIDLabel] + hourSymbolsForUC
    #Create dict mapping hours to col #s
    for idx in range(1,len(hourlyGenByPlant[0])): hourToCol[hourlyGenByPlant[0][idx]] = idx 
    #Add gens as first col, starting at row 1 since first row is hours
    genSymbols = [row[newTechsCE[0].index('TechnologyType')] for row in newTechsCE[1:]]
    for idx in range(1,len(hourlyGenByPlant)): hourlyGenByPlant[idx][0] = genSymbols[idx-1] #-1 b/c row 1 of hourlyGen = hours
    #Create dict mapping gens to row #s
    firstColVals = [row[0] for row in hourlyGenByPlant]
    genToRow = dict()
    for idx in range(1,len(firstColVals)): genToRow[firstColVals[idx]] = idx
    return (hourlyGenByPlant,genToRow,hourToCol)

# #New techs not in genFleetForCE, so add rows for them to genFleet
# def addNewTechsToResultsLists(genByPlant,genToRow,newTechsCE):
#     plantTypeCol = newTechsCE[0].index('TechnologyType')
#     for row in newTechsCE[1:]:
#         newRowIdx = len(genByPlant)
#         genByPlant.append([row[plantTypeCol]] + ['']*(len(genByPlant[0])-1))
#         genToRow[row[plantTypeCol]] = newRowIdx 

############ SAVE GENERATOR RESULTS
#Save gen-level CE results
def saveCEResultsByPlantVar(genByPlant,regUpByPlant,regDownByPlant,flexByPlant,contByPlant,
            turnOnByPlant,turnOffByPlant,onOffByPlant,genToRow,hourToCol,ceModel):
    saveHourByPlantVarCE(genByPlant,genToRow,hourToCol,ceModel,'vGen')
    saveHourByPlantVarCE(regUpByPlant,genToRow,hourToCol,ceModel,'vRegup')
    # saveHourByPlantVarCE(regDownByPlant,genToRow,hourToCol,ceModel,'vRegdown')
    saveHourByPlantVarCE(flexByPlant,genToRow,hourToCol,ceModel,'vFlex')
    saveHourByPlantVarCE(contByPlant,genToRow,hourToCol,ceModel,'vCont')
    saveHourByPlantVarCE(turnOnByPlant,genToRow,hourToCol,ceModel,'vTurnon')
    saveHourByPlantVarCE(turnOffByPlant,genToRow,hourToCol,ceModel,'vTurnoff')
    saveHourByPlantVarCE(onOffByPlant,genToRow,hourToCol,ceModel,'vOnoroff')
    
def saveCEResultsByTechVar(genByTech,regUpByTech,regDownByTech,flexByTech,contByTech,
            turnOnByTech,turnOffByTech,onOffByTech,genToRow,hourToCol,ceModel):
    saveHourByPlantVarCE(genByTech,genToRow,hourToCol,ceModel,'vGentech')
    saveHourByPlantVarCE(regUpByTech,genToRow,hourToCol,ceModel,'vReguptech')
    # saveHourByPlantVarCE(regDownByTech,genToRow,hourToCol,ceModel,'vRegdowntech')
    saveHourByPlantVarCE(flexByTech,genToRow,hourToCol,ceModel,'vFlextech')
    saveHourByPlantVarCE(contByTech,genToRow,hourToCol,ceModel,'vConttech')
    saveHourByPlantVarCE(turnOnByTech,genToRow,hourToCol,ceModel,'vTurnontech')
    saveHourByPlantVarCE(turnOffByTech,genToRow,hourToCol,ceModel,'vTurnofftech')
    saveHourByPlantVarCE(onOffByTech,genToRow,hourToCol,ceModel,'vOnorofftech')

#Extract results from CE GAMS model and add to proper list
def saveHourByPlantVarCE(varHourByPlantList,genToRow,hourToCol,ceModel,varName):
    for rec in ceModel.out_db[varName]:
        (rowIdx,colIdx) = (genToRow[rec.key(0)],hourToCol[rec.key(1)]) #vars indexed as egu,h or tech,h
        varHourByPlantList[rowIdx][colIdx] = rec.level
################################################################################

################### SAVE SYSTEM RESULTS ########################################
def saveSystemResults(ceModel,hoursForCE):
    resultLabels = ['mcGen','mcRegup','mcRegdown','mcFlex','mcCont','flex',
                    'regup','regdown']
    sysResults,resultToRow,hourToCol = setupHourlySystemResultsWithHourSymbols(hoursForCE,resultLabels)
    saveCEResultsBySysVar(sysResults,resultToRow,hourToCol,ceModel)
    return sysResults

########### SAVE SYSTEM RESULTS
#Note that setupHourlySystemResultsWitHourSymbols also produces a row w/ nse,
#but nse is not in CE, so don't save those values here. That's also why
#need to do "for result in resultLabel..." rather than in resultToRow.
def saveCEResultsBySysVar(sysResults,resultToRow,hourToColSys,ceModel):
    resultLabelToEqnName = {'mcGen':'meetdemand','mcRegup':'meetregupreserve',
        'mcFlex':'meetflexreserve','mcCont':'meetcontreserve','flex':'vFlexreserve',
        'regup':'vRegupreserve'}#,'regdown':'vRegdownreserve','mcRegdown':'meetregdownreserve'}
    for result in resultLabelToEqnName:
        varName = resultLabelToEqnName[result]
        for rec in ceModel.out_db[varName]:
            (rowIdx,colIdx) = (resultToRow[result],hourToColSys[rec.key(0)])
            if 'mc' in result: sysResults[rowIdx][colIdx] = rec.marginal
            else: sysResults[rowIdx][colIdx] = rec.level 
################################################################################