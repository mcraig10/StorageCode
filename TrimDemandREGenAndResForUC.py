#Michael Craig
#October 4, 2016
#Isolate hourly demand and wind & solar gen for hours input to UC model

#Inputs: curr UC day, num days to optimize for, num days LA, hourly annual demand & wind & solar gen
#Outputs: hourly demand & wind & solar gen for UC hours, UC hours
def getDemandAndREGenForUC(day,daysOpt,daysLA,demandScaled,hourlyWindGen,hourlySolarGen):
    hoursForUC = getUCHours(day,daysOpt,daysLA)    
    if (day + daysOpt + daysLA) <= 366: #necessary data doesn't extend beyond end of year
        demandUC = [demandScaled[hr-1] for hr in hoursForUC] #-1 b/c hours in year start @ 1, not 0 like Python idx
        hourlyWindGenUC = [hourlyWindGen[hr-1] for hr in hoursForUC] #-1 b/c hours in year start @ 1, not 0 like Python idx
        hourlySolarGenUC = [hourlySolarGen[hr-1] for hr in hoursForUC] #-1 b/c hours in year start @ 1, not 0 like Python idx
    else: #necessary data extends beyond end of year, so copy data from last day
        demandUC = getDataPastEndOfYear(day,daysOpt,daysLA,hoursForUC,demandScaled)
        hourlyWindGenUC = getDataPastEndOfYear(day,daysOpt,daysLA,hoursForUC,hourlyWindGen)
        hourlySolarGenUC = getDataPastEndOfYear(day,daysOpt,daysLA,hoursForUC,hourlySolarGen)
    return (demandUC,hourlyWindGenUC,hourlySolarGenUC,hoursForUC)

#Inputs: curr UC day, num days to optimize for, num days LA, hourly annual reg up & down req
#Outputs: hourly reg up & down req for UC hours
def getResForUC(day,daysOpt,daysLA,hourlyRegUp,hourlyRegDown,hourlyFlex,hourlyCont):
    hoursForUC = getUCHours(day,daysOpt,daysLA)    
    if (day + daysOpt + daysLA) <= 366:
        regUpUC = [hourlyRegUp[hr-1] for hr in hoursForUC] #-1 b/c hours in year start @ 1, not 0 like Python idx
        regDownUC = [hourlyRegDown[hr-1] for hr in hoursForUC] #-1 b/c hours in year start @ 1, not 0 like Python idx
        flexUC = [hourlyFlex[hr-1] for hr in hoursForUC]
        contUC = [hourlyCont[hr-1] for hr in hoursForUC]
    else:
        regUpUC = getDataPastEndOfYear(day,daysOpt,daysLA,hoursForUC,hourlyRegUp)
        regDownUC = getDataPastEndOfYear(day,daysOpt,daysLA,hoursForUC,hourlyRegDown)
        flexUC = getDataPastEndOfYear(day,daysOpt,daysLA,hoursForUC,hourlyFlex)
        contUC = getDataPastEndOfYear(day,daysOpt,daysLA,hoursForUC,hourlyCont)
    return (regUpUC,regDownUC,flexUC,contUC)

#Inputs: first day of UC, num days to optimize for, num days LA
#Outputs: 1d list of hours in UC (1-8760 basis)    
def getUCHours(day,daysOpt,daysLA): 
    (firstHour,lastHour) = ((day-1)*24+1,((day-1)+(daysOpt+daysLA))*24)
    hoursForUC = [hr for hr in range(firstHour,int(lastHour)+1)]    
    return hoursForUC

#Extend data for # of days past end of year
def getDataPastEndOfYear(day,daysOpt,daysLA,hoursForUC,dataList):
    daysExtend = (day + daysOpt + daysLA) - 365
    daysWithData = day - 364
    hoursWithData = hoursForUC[:daysWithData*24]
    return [dataList[hr-1] for hr in hoursWithData] * daysExtend