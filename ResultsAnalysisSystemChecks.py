#Michael Craig
#Jan 5, 2017

#Checks:
#1) Compare total gen to total demand
#2) Compare total res provision to reserve requirements
#3) Check reserve requirements output by CE model to added wind & solar

from AuxFuncs import *
import csv, os, operator
import matplotlib.pyplot as plt
import numpy as np

plt.style.use('ggplot')

################# SET FOLDERS TO ITERATE OVER ##################################
def setFolders():
    resultFolders = ['ResultsScppCcpp']
    return resultFolders
################################################################################

################# LOAD DATA ####################################################
def loadData(resultsFolder,year,model):
    incSto = False if 'NoSto' in resultsFolder else True
    resultsDir = os.path.join('C:\\Users\\mtcraig\\Desktop\\EPP Research\\PythonStorageProject',resultsFolder)
    sysData = readCSVto2dList(os.path.join(resultsDir,'systemResults' + model + year + '.csv'))
    gen = readCSVto2dList(os.path.join(resultsDir,'genByPlant' + model + year + '.csv'))
    regup = readCSVto2dList(os.path.join(resultsDir,'regupByPlant' + model + year + '.csv'))
    regdown = readCSVto2dList(os.path.join(resultsDir,'regdownByPlant' + model + year + '.csv'))
    flex = readCSVto2dList(os.path.join(resultsDir,'flexByPlant' + model + year + '.csv'))
    cont = readCSVto2dList(os.path.join(resultsDir,'contByPlant' + model + year + '.csv'))
    turnon = readCSVto2dList(os.path.join(resultsDir,'turnonByPlant' + model + year + '.csv'))
    turnoff = readCSVto2dList(os.path.join(resultsDir,'turnoffByPlant' + model + year + '.csv'))
    demand = readCSVto2dList(os.path.join(resultsDir,'demand' + model + year + '.csv'))[0]
    contReq = readCSVto2dList(os.path.join(resultsDir,'reservesCont' + model + year + '.csv'))[0]
    if model=='UC': 
        flexReq = readCSVto2dList(os.path.join(resultsDir,'reservesFlex' + model + year + '.csv'))[0]
        regupReq = readCSVto2dList(os.path.join(resultsDir,'reservesRegUp' + model + year + '.csv'))[0]
        regdownReq = readCSVto2dList(os.path.join(resultsDir,'reservesRegDown' + model + year + '.csv'))[0]
    else: 
        flexReq,regupReq,regdownReq = importResReqsFromCEOutput(sysData)
    if model=='UC': fleet = readCSVto2dList(os.path.join(resultsDir,'genFleet' + model + year + '.csv'))
    else: fleet = readCSVto2dList(os.path.join(resultsDir,'genFleetFor' + model + year + '.csv'))
    if model=='UC' and incSto == True:
        charge = readCSVto2dList(os.path.join(resultsDir,'chargeBySto' + model + year + '.csv'))
        soc = readCSVto2dList(os.path.join(resultsDir,'socBySto' + model + year + '.csv'))
    else: charge,soc = None,None
    return (year,model,incSto,gen,regup,regdown,flex,cont,fleet,
            charge,soc,turnon,turnoff,demand,contReq,flexReq,regupReq,regdownReq,resultsDir)

def importResReqsFromCEOutput(sysData):
    labels = [row[0] for row in sysData]
    return (sysData[labels.index('flex')][1:],sysData[labels.index('regup')][1:],
            sysData[labels.index('regdown')][1:])

def loadOtherCEResAndNewBuildData(year,resultsDir):
    flexInit = readCSVto2dList(os.path.join(resultsDir,'reservesFlexInitCE' + str(year) + '.csv'))[0]
    regupInit = readCSVto2dList(os.path.join(resultsDir,'reservesRegUpInitCE' + str(year) + '.csv'))[0]
    regdownInit = readCSVto2dList(os.path.join(resultsDir,'reservesRegDownInitCE' + str(year) + '.csv'))[0]
    flexIncWind = readCSVto2dList(os.path.join(resultsDir,'reservesFlexWindIncCE' + str(year) + '.csv'))[0]
    flexIncSolar = readCSVto2dList(os.path.join(resultsDir,'reservesFlexSolarIncCE' + str(year) + '.csv'))[0]
    regupIncWind = readCSVto2dList(os.path.join(resultsDir,'reservesRegUpWindIncCE' + str(year) + '.csv'))[0]
    regupIncSolar = readCSVto2dList(os.path.join(resultsDir,'reservesRegUpSolarIncCE' + str(year) + '.csv'))[0]
    regdownIncWind = readCSVto2dList(os.path.join(resultsDir,'reservesRegDownWindIncCE' + str(year) + '.csv'))[0]
    regdownIncSolar = readCSVto2dList(os.path.join(resultsDir,'reservesRegDownSolarIncCE' + str(year) + '.csv'))[0]
    newBuilds = readCSVto2dList(os.path.join(resultsDir,'genAdditionsCE' + str(year) + '.csv'))
    newPossBuilds = readCSVto2dList(os.path.join(resultsDir,'newTechsCE' + str(year) + '.csv'))
    genTech = readCSVto2dList(os.path.join(resultsDir,'genByTechCE' + str(year) + '.csv'))
    regupTech = readCSVto2dList(os.path.join(resultsDir,'regupByTechCE' + str(year) + '.csv'))
    regdownTech = readCSVto2dList(os.path.join(resultsDir,'regdownByTechCE' + str(year) + '.csv'))
    flexTech = readCSVto2dList(os.path.join(resultsDir,'flexByTechCE' + str(year) + '.csv'))
    contTech = readCSVto2dList(os.path.join(resultsDir,'contByTechCE' + str(year) + '.csv'))
    return (flexInit,regupInit,regdownInit,flexIncWind,flexIncSolar,regupIncWind,regupIncSolar,
            regdownIncWind,regdownIncSolar,newBuilds,newPossBuilds,genTech,regupTech,regdownTech,
            flexTech,contTech) 
################################################################################

################# MASTER FUNCTION ##############################################
def masterFunction():
    resultFolders = setFolders()
    for resultFolder in resultFolders:
        # for model in ['CE','UC']:
        for model in ['UC']:
            if model=='UC':
                for stoModel in ['NoSto','StoEnergy','StoEnergyAndRes','StoRes']:
                # for stoModel in ['NoSto']:
                    print('***RUNNING CHECKS FOR ',resultFolder,model,stoModel)
                    runChecks(os.path.join(resultFolder,model,stoModel),model)
            else:
                print('***RUNNING CHECKS FOR:',resultFolder,model)
                runChecks(os.path.join(resultFolder,model),model)

def runChecks(resultFolder,model):
    for year in getYears(resultFolder,model):
        print('**Running year ' + str(year))
        (year,model,incSto,gen,regup,regdown,flex,cont,fleet,charge,soc,turnon,turnoff,demand,
            contReq,flexReq,regupReq,regdownReq,resultsDir) = loadData(resultFolder,year,model)
        if model=='CE': 
            (flexInit,regupInit,regdownInit,flexIncWind,flexIncSolar,regupIncWind,regupIncSolar,
                regdownIncWind,regdownIncSolar,newBuilds,newPossBuilds,genTech,regupTech,
                regdownTech,flexTech,contTech) = loadOtherCEResAndNewBuildData(year,resultsDir)
            checkCEResReqOutput(flexReq,regupReq,regdownReq,flexInit,regupInit,regdownInit,
                flexIncWind,flexIncSolar,regupIncWind,regupIncSolar,regdownIncWind,regdownIncSolar,
                newBuilds,year,newPossBuilds)
        if model == 'UC':
            compareTotalGenToDemand(demand,incSto,gen,charge) #need to account for charging
            compareTotalResProvToReq(flexReq,flex,regupReq,regup,regdownReq,regdown,contReq,cont)
        else:
            compareTotalGenToDemandCE(demand,gen,genTech) #need to account for charging
            compareTotalResProvToReqCE(flexReq,flex,regupReq,regup,regdownReq,regdown,contReq,cont,
                                        flexTech,regupTech,regdownTech,contTech)
        # plt.show()
################################################################################

################# GET YEARS OF RESULTS #########################################
def getYears(resultFolder,model):
    allFiles = os.listdir(os.path.join('C:\\Users\\mtcraig\\Desktop\\EPP Research\\PythonStorageProject',resultFolder))
    baseName = 'windGen' + model #windGenCE or windGenUC
    years = []
    for fileName in allFiles: 
        if baseName in fileName:
            years.append(fileName.split('.')[0][-4:])
    return years
################################################################################

################# CHECK RESERVE REQUIREMENTS DETERMINED BY CE ##################
#Compares total res req output by CE to manually calculated res req based on
#added RE capacity & incremental res reqs for each unit of RE added.
#Inputs: 1d list w/ res req output by CE model, initial res req input to CE model
#(1d list), incremental res reqs for each added RE unit (1d lists), number
# new builds by fuel type (2d list), year for check, and info on new possible builds
#(use to get total added RE capacity).
#Outputs: prints whether have output res reqs don't equal calc'd res reqs. 
def checkCEResReqOutput(flexReq,regupReq,regdownReq,flexInit,regupInit,regdownInit,
        flexIncWind,flexIncSolar,regupIncWind,regupIncSolar,regdownIncWind,regdownIncSolar,
        newBuilds,year,newPossBuilds):
    newWind,newSolar = getNewWindAndSolarCapac(newBuilds,year,newPossBuilds)
    checkResReq(flexReq,flexInit,flexIncWind,flexIncSolar,newWind,newSolar,'flex')
    checkResReq(regupReq,regupInit,regupIncWind,regupIncSolar,newWind,newSolar,'regup')
    # checkResReq(regdownReq,regdownInit,regdownIncWind,regdownIncSolar,newWind,newSolar,'regdown')

#Calculate added wind and solar capacity based on # new builds, year, and capac for
#new techs.
def getNewWindAndSolarCapac(newBuilds,year,newPossBuilds):
    yearCol = newBuilds[0].index('UnitsAdded' + str(year))
    techCol = newBuilds[0].index('TechnologyType')
    techPossCol,capacPossCol = newPossBuilds[0].index('TechnologyType'),newPossBuilds[0].index('Capacity(MW)')
    techPossRowLabels = [row[techPossCol] for row in newPossBuilds]
    techToNewCapac = dict()
    for row in newBuilds[1:]: 
        tech = row[techCol]
        techCapac = float(newPossBuilds[techPossRowLabels.index(tech)][capacPossCol])
        numTechs = float(row[yearCol])
        techToNewCapac[tech] = numTechs*techCapac
    return techToNewCapac['Wind'],techToNewCapac['Solar PV']

#Checks res req calculated for given res type.
def checkResReq(req,init,incWind,incSolar,newWind,newSolar,name):
    calcdReq = [float(init[idx]) + float(incWind[idx])*newWind 
                + float(incSolar[idx])*newSolar for idx in range(len(init))]
    print('Checking CE req output for ' + name)
    reqScaled = [float(val)*1000 for val in req]
    compareTwoLists(reqScaled,calcdReq,'ceReq','calcdReq')
################################################################################

################# COMPARE HOURLY TOTAL GEN TO DEMAND ###########################
#Inputs: 1d list w/ hourly demand, whether to include storage or not, hourly gen
#by each gen (2d list, row 1 = dts, col 1 = gen labels), 1d list w/ charging
#by storage (add to demand for total elec demand).
#OUtputs: prints if toatl gen =/= demand
def compareTotalGenToDemand(demand,incSto,gen,charge):
    hourIdxs = getHourIdxsFromGenOrRes(gen)
    #For UC model, import demand & res reqs for full yr; for CE, same length
    demand = [float(demand[hourIdxs[idx]]) for idx in range(len(hourIdxs))]
    if incSto == True:
        chargeVals = charge[1][1:] #remove headers
        demand = [float(demand[idx]) + float(chargeVals[idx])*1000 for idx in range(len(demand))]
        # for idx in range(len(hourIdxs)): demand[hourIdxs[idx]] += float(chargeVals[idx])*1000
    hourlyGen = sumHourlyValues(gen)
    compareTwoLists(hourlyGen,demand,'totalGen','demand')
    plot2Lists(hourlyGen,demand,1,'Gen v Demand')

#Similar function as above for CE, except adds in tech gen
def compareTotalGenToDemandCE(demand,gen,genTech):
    hourlyGen = sumHourlyValues(gen)
    hourlyGenTech = sumHourlyValues(genTech)
    totalGen = list(map(operator.add,hourlyGen,hourlyGenTech))
    compareTwoLists(totalGen,demand,'totalGen','demand')
    plot3ListsWith2Fills(hourlyGen,totalGen,demand,1,'genGen','techGen','Gen v Demand')
################################################################################

################# COMPARE RESERVE PROVISION TO RESERVE REQ #####################
#Inputs: 2d lists w/ hourly reserves provided by each gen (col 1 = gen IDs, row1 = 
#datetimes), and 1d lists w/ reserve requirements.
#Outputs: prints whether violations occur
def compareTotalResProvToReq(flexReq,flex,regupReq,regup,regdownReq,regdown,contReq,cont):
    hourIdxs = getHourIdxsFromGenOrRes(flex)
    flexReq = [float(flexReq[hourIdxs[idx]]) for idx in range(len(hourIdxs))]
    regupReq = [float(regupReq[hourIdxs[idx]]) for idx in range(len(hourIdxs))]
    # regdownReq = [float(regdownReq[hourIdxs[idx]]) for idx in range(len(hourIdxs))]
    contReq = [float(contReq[hourIdxs[idx]]) for idx in range(len(hourIdxs))]
    flexHourly = compareResAndReq(flexReq,flex,'flex')
    regupHourly = compareResAndReq(regupReq,regup,'regup')
    # regdownHourly = compareResAndReq(regdownReq,regdown,'regdown')
    contHourly = compareResAndReq(contReq,cont,'cont')
    plot2Lists(flexHourly,flexReq,2,'Flex Prov vs Req')
    plot2Lists(regupHourly,regupReq,3,'Regup Prov vs Req')
    # plot2Lists(regdownHourly,regdownReq,4,'Regdown Prov vs Req')
    plot2Lists(contHourly,contReq,5,'Cont Prov vs Req')

#Similar function as above, except combines reserves provided by existing & new gens
def compareTotalResProvToReqCE(flexReq,flex,regupReq,regup,regdownReq,regdown,contReq,cont,
                            flexTech,regupTech,regdownTech,contTech):
    hourIdxs = getHourIdxsFromGenOrRes(flex)
    flexReq = [float(flexReq[idx])*1000 for idx in range(len(flexReq))]
    regupReq = [float(regupReq[idx])*1000 for idx in range(len(regupReq))]
    # regdownReq = [float(regdownReq[idx])*1000 for idx in range(len(regdownReq))]
    flexHourly,flexTechHourly,flexTotalHourly = compareResAndReqCE(flexReq,flex,flexTech,'flex')
    regupHourly,regupTechHourly,regupTotalHourly = compareResAndReqCE(regupReq,regup,regupTech,'regup')
    # regdownHourly,regdownTechHourly,regdownTotalHourly = compareResAndReqCE(regdownReq,regdown,regdownTech,'regdown')
    contHourly,contTechHourly,contTotalHourly = compareResAndReqCE(contReq,cont,contTech,'cont')
    plot3ListsWith2Fills(flexHourly,flexTotalHourly,flexReq,2,'genFlex','techFlex','Flex Req v Prov')
    plot3ListsWith2Fills(regupHourly,regupTotalHourly,regupReq,3,'genRegup','techRegup','Regup Req v Prov')
    # plot3ListsWith2Fills(regdownHourly,regdownTotalHourly,regdownReq,4,'genRegdown','techRegdown','Regdown Req v Prov')
    plot3ListsWith2Fills(contHourly,contTotalHourly,contReq,5,'genCont','techCont','Cont Req v Prov')

#Compares res provision & requirement for given reserve
def compareResAndReq(req,prov,resName):
    print('Comparing provision and req for ' + resName)
    hourlyProv = sumHourlyValues(prov)
    compareTwoLists(hourlyProv,req,'totalProvision','req')
    return hourlyProv

#Compares res provision & requirement for given reserve
def compareResAndReqCE(req,prov,provTech,resName):
    print('Comparing provision and req for ' + resName)
    hourlyProv = sumHourlyValues(prov)
    hourlyTechProv = sumHourlyValues(provTech)
    totalProv = list(map(operator.add,hourlyProv,hourlyTechProv))
    compareTwoLists(totalProv,req,'totalProvision','req')
    return hourlyProv,hourlyTechProv,totalProv
################################################################################

################# AUX FUNCS ####################################################
#Inputs: 2d list of gen or res (row 1 = dts)
#Outputs: 1d list of hours in optimization
def getHourIdxsFromGenOrRes(gen):
    #gen[0][1:] b/c dts are in row 1, exc. gen header. val[1:] b/c hour string is 'h...'
    hours = [int(val[1:])-1 for val in gen[0][1:]] 
    return hours

#Inputs: 2d list of gen or res provisionv aleus (col 1 = gen labels, row 1 = datetimes).
#Output: 1d list of hourly summed values.
def sumHourlyValues(genOrRes):
    hourlyVals = list()
    for col in range(1,len(genOrRes[0])):
        hourlyVals.append(sum([float(row[col])*1000 for row in genOrRes[1:]]))
    return hourlyVals
    
#Compares each entry in 2 lists by idx position, accounting for msall dif.
#Inputs: 2 1d lists w/ values, and names of each list
def compareTwoLists(list1,list2,name1,name2):
    for idx in range(len(list1)):
        if name2 == 'demand':
            if (float(list1[idx]) < (float(list2[idx])-1E-3) 
                or float(list1[idx]) > (float(list2[idx])+1E-3)):
                    print('Lists ' + name1 + ' and ' + name2 + ' do not match at idx ' + str(idx) + 
                            ' with values ' + str(float(list1[idx])) + ' and ' + str(float(list2[idx])))
        else:   
            if float(list1[idx]) < (float(list2[idx])-1E-3):
                    print('List ' + name1 + ' is smaller than ' + name2 + ' at idx ' + str(idx) + 
                            ' with values ' + str(float(list1[idx])) + ' and ' + str(float(list2[idx])))

#Plots 2 1d lists w/ just values. Fill list = filled area under curve. Line list
#is just a line.
def plot2Lists(fillList,lineList,figNum,plotTitle):
    plt.figure(figNum,figsize=(20,30))
    ax = plt.subplot(111)
    ax.plot(lineList,'k',lw=3)
    # ax.plot(fillList,'r',lw=3)
    ax.fill_between(np.array(range(len(fillList))),np.array(fillList))
    plt.title(plotTitle)

#Plots 3 1d lists, 2 for stacked fill
def plot3ListsWith2Fills(fillList1,fillList2,lineList,figNum,fill1Name,fill2Name,plotTitle):
    plt.figure(figNum,figsize=(20,30))
    ax = plt.subplot(111)
    ax.plot(lineList,'k',lw=3)
    # ax.plot(fillList,'r',lw=3)
    fill1 = ax.fill_between(np.array(range(len(fillList1))),np.array([0]*len(fillList1)),
                            np.array(fillList1),label=fill1Name,color='blue')
    fill2 = ax.fill_between(np.array(range(len(fillList2))),np.array(fillList1),
                            np.array(fillList2),color='red',label=fill2Name)
    plt.title(plotTitle)
    plt.legend()
################################################################################

masterFunction()