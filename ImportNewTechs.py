#Michael Craig
#October 4, 2016
#Function imports data for new technologies eligible for construction in capacity expansion model

import os
from AuxFuncs import *

#Import new tech data by loading forecasts of tech data + 2d list w/ missing data,
#and fill in that 2d list w/ forecast data for current year.
#Inputs: flags indicating which techs to import or not import
#Outputs: 2d list w/ headers
def getNewTechs(allowCoalWithoutCCS,onlyNSPSUnits,regUpCostCoeffs,currYear,runLoc,
                resultsDir,scenario,incITC):
    #Set directory data is in
    if runLoc == 'pc': newPlantDataDir = 'C:\\Users\\mtcraig\\Desktop\\EPP Research\\NewPlantData\\ATB'
    else: newPlantDataDir = 'Data\\NewPlantData'
    #Set which new tech file, based on whether in special scenario
    if scenario == 'solar': 
        techFrmwrkFile,techDataFile = 'NewTechFrameworkLowSolarCost.csv','newTechDataATBLowSolarCost.csv'
    elif scenario == 'nuclear':
        techFrmwrkFile,techDataFile = 'NewTechFramework.csv','newTechDataATBLowNukeCost.csv'
    else: 
        techFrmwrkFile,techDataFile = 'NewTechFramework.csv','newTechDataATB.csv'
    newTechsCEFilename = os.path.join(newPlantDataDir,techFrmwrkFile)
    newTechsCE = readCSVto2dList(newTechsCEFilename)
    if allowCoalWithoutCCS == False: newTechsCE = removeCoalWithoutCCSFromNewTechs(newTechsCE)
    if onlyNSPSUnits == True: newTechsCE = removeUnitsNotCompliantWithNSPS(newTechsCE)
    addRegUpOfferCostAndElig(newTechsCE,regUpCostCoeffs)
    inputValuesForCurrentYear(newTechsCE,newPlantDataDir,currYear,techDataFile)
    if incITC == True: modRECapCostForITC(newTechsCE,currYear)
    return newTechsCE

#Remove coal w/out CCS from new tech data
#Input: new techs (2d list w/ headers)
#Outputs: new techs w/out coal w/out CCS (2d list)
def removeCoalWithoutCCSFromNewTechs(newTechsCE):
    techTypeCol = newTechsCE[0].index('TechnologyType')
    newTechsCENoCoalWithoutCCS = [row for row in newTechsCE if row[techTypeCol] != 'Coal Steam']
    return newTechsCENoCoalWithoutCCS

#Remove new techs not compliant w/ NSPS
#Input: new techs (2d list w/ headers)
#Outputs: new techs w/out units not compliant w/ NSPS (2d list w/ headers)
def removeUnitsNotCompliantWithNSPS(newTechsCE):
    nspsCompliantCol = newTechsCE[0].index('NSPSCompliant')
    newTechsNSPSCompliant = [newTechsCE[0]] + [row for row in newTechsCE[1:] if row[nspsCompliantCol] == 'Yes']
    return newTechsNSPSCompliant

#Add reg offer cost and eligiblity to new techs
def addRegUpOfferCostAndElig(newTechsCE,regUpCostCoeffs):
    newTechsCE[0].extend(['RegOfferCost($/MW)','RegOfferElig'])
    plantTypeCol = newTechsCE[0].index('TechnologyType')
    for row in newTechsCE[1:]:
        if row[plantTypeCol] in regUpCostCoeffs: 
            regCost,regOffer = regUpCostCoeffs[row[plantTypeCol]],1
        else: 
            regCost,regOffer = 0,0
        row.extend([regCost,regOffer])

def inputValuesForCurrentYear(newTechsCE,newPlantDataDir,currYear,techDataFile):
    newPlantData = readCSVto2dList(os.path.join(newPlantDataDir,techDataFile))
    (forecastTechCol,forecastParamCol) = (newPlantData[0].index('TechnologyType'),
                                            newPlantData[0].index('Parameter'))
    newTechsTechCol = newTechsCE[0].index('TechnologyType')
    if str(currYear) in newPlantData[0]: yearCol = newPlantData[0].index(str(currYear))
    else: yearCol = len(newPlantData[0])-1
    # paramsToFill = ['HR(Btu/kWh)','CAPEX(2012$/MW)','FOM(2012$/MW/yr)','VOM(2012$/MWh)']
    for row in newPlantData[1:]:
        (currTech,currParam,currVal) = (row[forecastTechCol],row[forecastParamCol],row[yearCol])
        newTechsTechs = [row[newTechsTechCol] for row in newTechsCE]
        if currTech in newTechsTechs:
            newTechsCERow = newTechsTechs.index(currTech)
            newTechsCECol = newTechsCE[0].index(currParam)
            newTechsCE[newTechsCERow][newTechsCECol] = float(currVal)

#Account for ITC in RE cap costs
#http://programs.dsireusa.org/system/program/detail/658
def modRECapCostForITC(newTechsCE,currYear):
    windItc,windItcYear = .21,2020 #wind ITC expires at 2020; .21 is average of 2016-2019 ITCs
    solarItcInit,solarItcIndef, solarItcYear = .3,.1,2020 #solar ITC doesn't expire, but goes from .3 to .1
    if currYear <= windItcYear: modRECost(newTechsCE,windItc,'Wind')
    if currYear <= solarItcYear: modRECost(newTechsCE,solarItcInit,'Solar PV')
    else: modRECost(newTechsCE,solarItcIndef,'Solar PV')
    
def modRECost(newTechsCE,itc,plantType):
    ptCol = newTechsCE[0].index('TechnologyType')
    capexCol = newTechsCE[0].index('CAPEX(2012$/MW)')
    ptRow = [row[0] for row in newTechsCE].index(plantType)
    newTechsCE[ptRow][capexCol] *= (1-itc)

################### OLD FUNCTION ####################################
#Import new tech data
#Inputs: flags indicating which techs to import or not import
#Outputs: 2d list w/ headers
# def getNewTechs(allowCoalWithoutCCS,onlyNSPSUnits):
#     newPlantDataDir = 'C:\\Users\\mtcraig\\Desktop\\EPP Research\\NewPlantData'
#     newPlantFilename = os.path.join(newPlantDataDir,'CandidateTechsCapacExp.csv')
#     newTechsCE = readCSVto2dList(newPlantFilename)
#     if allowCoalWithoutCCS == False: newTechsCE = removeCoalWithoutCCSFromNewTechs(newTechsCE)
#     if onlyNSPSUnits == True: newTechsCE = removeUnitsNotCompliantWithNSPS(newTechsCE)
#     return newTechsCE