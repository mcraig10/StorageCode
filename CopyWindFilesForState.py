#Michael Craig
#Nov 16, 2016

#Copy over NREL eastern wind dataset files to new location
#for given states.

from AuxFuncs import *
import os, copy, shutil

def keyParameters():
    states = {'Texas'}
    currDir = 'C:\\Users\\mtcraig\\Desktop\\EPP Research\\Databases\\Eastern Wind Dataset'
    newDir = 'C:\\Users\\mtcraig\\Desktop\\EPP Research\\Databases\\Eastern Wind Dataset Texas'
    if not os.path.exists(newDir): os.makedirs(newDir)
    masterFile = 'eastern_wind_dataset_site_summary.csv'
    return (states,currDir,newDir,masterFile)

def masterFunction():
    (states,currDir,newDir,masterFile) = keyParameters()
    (siteFilenames,newMasterList) = processMasterFile(currDir,states,masterFile)
    for filename in siteFilenames:
        shutil.copyfile(os.path.join(currDir,filename),os.path.join(newDir,filename))
    write2dListToCSV(newMasterList,os.path.join(newDir,masterFile))

def processMasterFile(currDir,states,masterFile):
    masterData = readCSVto2dList(os.path.join(currDir,masterFile))
    siteCol, stateCol = masterData[0].index('SiteNumber'), masterData[0].index('State')
    masterDataState = [copy.copy(masterData[0])]
    siteFilenames = []
    for row in masterData[1:]:
        if row[stateCol] in states: 
            masterDataState.append(row)
            siteFilenames.append(createSiteFilename(row[siteCol]))
    return (siteFilenames,masterDataState)

#siteNum = str
def createSiteFilename(siteNum):
    numDigitsInSiteFilenames = 5
    numLeadingZerosNeeded = numDigitsInSiteFilenames - len(siteNum) 
    return 'SITE_' + '0' * numLeadingZerosNeeded + siteNum + '.csv'

masterFunction()