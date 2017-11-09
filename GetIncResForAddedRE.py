#Michael Craig
#Jan 4, 2017

#Script determines new reserve requirements per unit of RE added by
#capacity expansion model.

from ReservesWWSIS import calcWWSISReserves

#Takes in CFs for hypothetical new wind and solar plants, determines reserve
#requirements for that installed capacity of wind and solar, then normalizes
#reserve requirements to per MW added wind or solar by dividing by hypothetical
#amount of wind and solar added to obtain new CFs.
#Inputs: windIdsAndCapacs (2d list w/ NREL wind IDs used to load gen files),
#solarFilenamesAndCapacs (2d list w/ NREL solar filenames used to load gen files),
#hourly demand, fraction of load included in reg & cont reserves, percentile error
#of wind and solar forecasts included in reg & flex reserves, windCfsDtHr (2d list w/ hourly 
#wind CFs for each wind generator in fleet, col 1 = dt, subsequent cols = gen),
#same formatted 2d lists subhourly wind CFs & solar hourly & subhourly CFs, 
#MW of wind and solar added to fleet in order to get new wind & solar CFs.
#Outputs: 1d lists for entire year of incremental res requirements per MW
#wind or solar added.
def getIncResForAddedRE(newWindCfsDtHr,newWindCfsDtSubhr,newWindIdAndCapac,
    newSolarCfsDtHr,newSolarCfsDtSubhr,newSolarFilenameAndCapac,demandWithGrowth,regLoadFrac,
    contLoadFrac,regErrorPercentile,flexErrorPercentile,addedWindCapac,addedSolarCapac):
    #Calculate new WWSIS reserve requirements for hypothetical added wind and solar
    (contResHourlyInc,regUpHourlyInc,regDownHourlyInc,flexResHourlyInc,allResInc,regUpWindInc,
        regDownWindInc,regUpSolarInc,regDownSolarInc,flexWindInc,flexSolarInc) = calcWWSISReserves(newWindCfsDtHr,
        newWindCfsDtSubhr,newWindIdAndCapac,newSolarCfsDtHr,newSolarCfsDtSubhr,newSolarFilenameAndCapac,
        demandWithGrowth,regLoadFrac,contLoadFrac,regErrorPercentile,flexErrorPercentile)
    regUpWindIncNormd = [val/addedWindCapac for val in regUpWindInc]
    regUpSolarIncNormd = [val/addedSolarCapac for val in regUpSolarInc]
    regDownWindIncNormd = [val/addedWindCapac for val in regDownWindInc]
    regDownSolarIncNormd = [val/addedSolarCapac for val in regDownSolarInc]
    flexWindIncNormd = [val/addedWindCapac for val in flexWindInc]
    flexSolarIncNormd = [val/addedSolarCapac for val in flexSolarInc]
    return (regUpWindIncNormd,regDownWindIncNormd,regUpSolarIncNormd,regDownSolarIncNormd,
            flexWindIncNormd,flexSolarIncNormd)