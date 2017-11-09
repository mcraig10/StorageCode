#Michael Craig
#November 16, 2016

from AuxFuncs import write2dListToCSV
import os

########### WRITE HOURLY RESULTS BY PLANT ######################################
def writeHourlyResultsByPlant(genByPlant,regUpByPlant,regDownByPlant,flexByPlant,contByPlant,
                                turnonByPlant,turnoffByPlant,onOffByPlant,resultsDir,year,modelName,plantOrTech):
    write2dListToCSV(genByPlant,os.path.join(resultsDir,'genBy' + plantOrTech + modelName + str(year) + '.csv'))
    write2dListToCSV(regUpByPlant,os.path.join(resultsDir,'regupBy' + plantOrTech + modelName + str(year) + '.csv'))
    write2dListToCSV(regDownByPlant,os.path.join(resultsDir,'regdownBy' + plantOrTech + modelName + str(year) + '.csv'))
    write2dListToCSV(flexByPlant,os.path.join(resultsDir,'flexBy' + plantOrTech + modelName + str(year) + '.csv'))
    write2dListToCSV(contByPlant,os.path.join(resultsDir,'contBy' + plantOrTech + modelName + str(year) + '.csv'))
    write2dListToCSV(turnonByPlant,os.path.join(resultsDir,'turnonBy' + plantOrTech + modelName + str(year) + '.csv')) 
    write2dListToCSV(turnoffByPlant,os.path.join(resultsDir,'turnoffBy' + plantOrTech + modelName + str(year) + '.csv')) 
    write2dListToCSV(onOffByPlant,os.path.join(resultsDir,'onOffBy' + plantOrTech + modelName + str(year) + '.csv')) 

########### WRITE HOURLY RESULTS BY STORAGE UNITS ##############################
def writeHourlyStoResults(chargeBySto,socBySto,resultsDir,year):
    write2dListToCSV(chargeBySto,os.path.join(resultsDir,'chargeByStoUC' + str(year) + '.csv'))
    write2dListToCSV(socBySto,os.path.join(resultsDir,'socByStoUC' + str(year) + '.csv'))