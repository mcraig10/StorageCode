#Michael Craig
#October 20, 2016
#Save UC model results for a day into 2d list for all days

# from GAMSAuxFuncs import extract2dVarResultsIntoDictNoLA
from GAMSAuxFuncs import createHourSymbol

#Add entries to 2d list after extracting results only for optimization horizon.
#Inputs: 2d list w/ gen by plants, uc model (gams obj), first day of uc run,
#num days running in optimizaiton horizon (not inc. LA)
def saveHourlyGenByPlant(hourlyGenByPlant,genToRow,hourToCol,ucModel,ucDay,daysOpt):
    hoursForOptSet = getHoursInOptimHorizon(ucDay,daysOpt)
    # hourlyGenForDay = extract2dVarResultsIntoDictNoLA(modelResults,varName,hoursForOpt) #dict of (gen,hour):val
    for rec in ucModel.out_db['vGen']:
        (gen,hour) = (rec.key(0),rec.key(1)) #Vars are indexed as egu,h
        if hour in hoursForOptSet: 
            (rowIdx,colIdx) = (genToRow[gen],hourToCol[hour])
            hourlyGenByPlant[rowIdx][colIdx] = rec.level

#Inputs: curr UC day, # days in optimization horizon. Outputs: set of hours in curr optimization horizon
def getHoursInOptimHorizon(day,daysOpt):
    (firstHour,lastHour) = ((day-1)*24+1,((day-1)+daysOpt)*24) 
    return set([createHourSymbol(hr) for hr in range(firstHour,lastHour+1)])
    