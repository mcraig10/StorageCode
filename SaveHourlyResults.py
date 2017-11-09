#Michael Craig
#October 20, 2016
#Save UC model results for a day into 2d list for all days

# from GAMSAuxFuncs import extract2dVarResultsIntoDictNoLA
from GAMSAuxFuncs import createHourSymbol

############ SAVE HOURLY X PLANT RESULTS #######################################
#Adds results from curr UC run to input 2d lists
def saveHourlyResultsByPlant(genByPlant,regUpByPlant,regDownByPlant,flexByPlant,contByPlant,
            turnonByPlant,turnoffByPlant,onOffByPlant,genToRow,hourToColPlant,ucModel,ucDay,daysOpt):
    saveHourByPlantVar(genByPlant,genToRow,hourToColPlant,ucModel,ucDay,daysOpt,'vGen')
    saveHourByPlantVar(regUpByPlant,genToRow,hourToColPlant,ucModel,ucDay,daysOpt,'vRegup')
    # saveHourByPlantVar(regDownByPlant,genToRow,hourToColPlant,ucModel,ucDay,daysOpt,'vRegdown')
    saveHourByPlantVar(flexByPlant,genToRow,hourToColPlant,ucModel,ucDay,daysOpt,'vFlex')
    saveHourByPlantVar(contByPlant,genToRow,hourToColPlant,ucModel,ucDay,daysOpt,'vCont')
    saveHourByPlantVar(turnonByPlant,genToRow,hourToColPlant,ucModel,ucDay,daysOpt,'vTurnon')
    saveHourByPlantVar(turnoffByPlant,genToRow,hourToColPlant,ucModel,ucDay,daysOpt,'vTurnoff')
    saveHourByPlantVar(onOffByPlant,genToRow,hourToColPlant,ucModel,ucDay,daysOpt,'vOnoroff')

#Add entries to 2d list after extracting results only for optimization horizon.
#Inputs: 2d list w/ gen by plants, uc model (gams obj), first day of uc run,
#num days running in optimizaiton horizon (not inc. LA)
def saveHourByPlantVar(varHourByPlantList,genToRow,hourToColPlant,ucModel,ucDay,daysOpt,varName):
    hoursForOptSet = getHoursInOptimHorizon(ucDay,daysOpt)
    for rec in ucModel.out_db[varName]:
        (gen,hour) = (rec.key(0),rec.key(1)) #Vars are indexed as egu,h
        if hour in hoursForOptSet: 
            (rowIdx,colIdx) = (genToRow[gen],hourToColPlant[hour])
            varHourByPlantList[rowIdx][colIdx] = rec.level

#Inputs: curr UC day, # days in optimization horizon. Outputs: set of hours in curr optimization horizon
def getHoursInOptimHorizon(day,daysOpt):
    (firstHour,lastHour) = ((day-1)*24+1,((day-1)+daysOpt)*24) 
    return set([createHourSymbol(hr) for hr in range(firstHour,lastHour+1)])
################################################################################    

############ SAVE HOURLY SYSTEM RESULTS ########################################
def saveHourlySystemResults(sysResults,resultToRow,hourToColSys,ucModel,ucDay,daysOpt):
    resultLabelToEqnName = {'nse':'vNse','mcGen':'meetdemand','mcRegup':'meetregupreserves',
                            'mcFlex':'meetflexreserves','mcCont':'meetcontreserves'} #'mcRegdown':'meetregdownreserves'
    hoursForOptSet = getHoursInOptimHorizon(ucDay,daysOpt)
    for result in resultLabelToEqnName:
        varName = resultLabelToEqnName[result]
        for rec in ucModel.out_db[varName]:
            hour = rec.key(0)
            if hour in hoursForOptSet: 
                (rowIdx,colIdx) = (resultToRow[result],hourToColSys[hour])
                if 'mc' in result: sysResults[rowIdx][colIdx] = rec.marginal
                else: sysResults[rowIdx][colIdx] = rec.level 
################################################################################

############ SAVE HOURLY STORAGE RESULTS #######################################
def saveHourlyStoResults(chargeBySto,socBySto,genToRowSto,hourToColSto,ucModel,ucDay,daysOpt):
    saveHourByPlantVar(chargeBySto,genToRowSto,hourToColSto,ucModel,ucDay,daysOpt,'vCharge')
    saveHourByPlantVar(socBySto,genToRowSto,hourToColSto,ucModel,ucDay,daysOpt,'vStateofcharge')
################################################################################
