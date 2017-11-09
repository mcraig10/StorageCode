#Michael Craig
#October 6, 2016
#Trim hourly reg res data to CE hours

#Inputs: hourly reg req & hourly inc reg req per GW wind (1d lists), hours included in CE 
#(1d list, 1-8760 basis)
#Outputs: hourly reg res data only for CE hours (1-8760 basis, 1d lists)
def trimRegResToCEHours(hourlyRegUp,hourlyRegDown,hourlyFlex,hourlyCont,hourlyRegUpIncWind,
            hourlyRegUpIncSolar,hourlyRegDownIncWind,hourlyRegDownIncSolar,hourlyFlexIncWind,
            hourlyFlexIncSolar,hoursForCE):
    regUpCE = [hourlyRegUp[hr-1] for hr in hoursForCE] #-1 b/c hours in year start @ 1, not 0 like Python idx
    regUpWindIncCE = [hourlyRegUpIncWind[hr-1] for hr in hoursForCE] 
    regUpSolarIncCE = [hourlyRegUpIncSolar[hr-1] for hr in hoursForCE] 
    regDownCE = [hourlyRegDown[hr-1] for hr in hoursForCE] 
    regDownWindIncCE = [hourlyRegDownIncWind[hr-1] for hr in hoursForCE] 
    regDownSolarIncCE = [hourlyRegDownIncSolar[hr-1] for hr in hoursForCE] 
    flexCE = [hourlyFlex[hr-1] for hr in hoursForCE]
    flexWindIncCE = [hourlyFlexIncWind[hr-1] for hr in hoursForCE]
    flexSolarIncCE = [hourlyFlexIncSolar[hr-1] for hr in hoursForCE]
    contCE = [hourlyCont[hr-1] for hr in hoursForCE]
    return (regUpCE,regDownCE,flexCE,contCE,regUpWindIncCE,regUpSolarIncCE,regDownWindIncCE,
            regDownSolarIncCE,flexWindIncCE,flexSolarIncCE)        