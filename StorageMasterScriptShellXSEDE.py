#Michael Craig
#Jan 27, 2017
#Shell script for 1) setting working dir to location of Python script and
#2) calling StorageMasterScript with input scenario data

#ORDER OF INPUTS: scenario, co2CapScenario, startYear, stoScenarios
#scenario: cpp, deep, solar, nuclear, ng, coalret, base
#co2CapScenario: cpp, deep, none
#startYear: year in which to start UC runs
#endYear: year in which to end UC runs
#stoScenarios: NoSto, StoEnergy, StoRes, StoEnergyAndRes

import sys,os
from StorageMasterScript16Apr17XSEDE import masterFunction

#Set working directory
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

#Process inputs and call master function
inputData = sys.argv[1:] #exclude 1st item (script name)
scenario = inputData[0]
co2CapScenario = inputData[1]
startYear = int(inputData[2])
endYear = int(inputData[3])
stoScenarios = [inputData[4]]

masterFunction(scenario,co2CapScenario,startYear,endYear,stoScenarios)