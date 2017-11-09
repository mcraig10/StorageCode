#Michael Craig
#May 9, 2016
#Testing GAMS-Python API

from __future__ import print_function
from gams import *
import os, sys, time
import pandas as pd
import numpy as np
from AuxFuncs import *


####################################
#IMPORT DATA
demandData = readCSVto2dList('Data/demandData.csv')
####################################

###########################################
#CREATE EMPTY WORKSPACE
currDir = os.getcwd()
gamsFileDir = os.path.join(currDir,'gams') #GAMS model is in folder named 'gams'; folder is in directory of this Python script
ws = GamsWorkspace(working_directory=gamsFileDir,system_directory = 'C:\\GAMS\\win64\\24.7')
print('created workspace')
###########################################

###########################################
#SET UP SETS AND PARAMETERS AND ADD TO GAMS WORKSPACE
db = ws.add_database()

# def addTimes(db):
#     #Pass in hourly values
#     newTimes = ["t1","t2","t3"]
#     t = db.add_set("t", 1, "hour")
#     for time in newTimes:
#         t.add_record(time)
#     return (t,newTimes)

def addTimes(db,setName,setDescrip):
    #Pass in hourly values
    newTimes = ["t1","t2","t3"]
    addedSet = db.add_set(setName, 1, setDescrip)
    for time in newTimes:
        addedSet.add_record(time)
    return (addedSet,newTimes)

(t,newTimes) = addTimes(db,'t','hour')
print('length of db:',len(db))
check = db.get_set('t')
print('length of time set:',len(check))
print(check.first_record())

#Add generators & test subsetting generators
# generators = ['g1','g2']
# genSet = db.add_set('g',1,'generators')
# for gen in generators:
#     genSet.add_record(gen)

gensubset = ['g1']
genSubsetSet = db.add_set('gsub',1,'generator subsets')
for gen in gensubset:
    genSubsetSet.add_record(gen)

#Pass in new demand values
newDemand = {"t1":111,"t2":50,"t3":200}
pD = db.add_parameter_dc("pD", [t], "demand at hour t")
for time in newTimes:
    pD.add_record(time).value = newDemand[time]

#Pass in scalar as a parameter (i.e., parameter not indexed to set)
costScalar = 10000
pFCScalar = db.add_parameter('pFCScalar',0,'fuel cost scalar')
pFCScalar.add_record().value = costScalar
###########################################

###########################################
#LOAD GAMS FILE AND ADD TO GAMS WORKSPACE
gamsFile = 'testdispatch.gms'
test = ws.add_job_from_file(gamsFile)
###########################################

###########################################
#RUN OPTIMIZATION
opt = GamsOptions(ws)
opt.defines['gdxincname'] = db.name
test.run(opt,databases=db)

#Alternatively:
# opt = ws.add_options()
# opt.defines["gdxincname"] = db.name
# test.run(opt,databases=db)
###########################################

###########################################
#GET RESULTS FOR VARIABLE
varName = 'vP'
results = []
for rec in test.out_db[varName]:
    results.append((rec.key(0),rec.key(1),rec.level))
    print(varName + "(" + rec.key(0) + "," + rec.key(1) + "): level=" + str(rec.level) + " marginal=" + str(rec.marginal)) #key(x) = value of xth set on which var is defined
print(results)

print(type(test.out_db[varName]),test.out_db[varName])

record = test.out_db[varName].find_record(['g1','t1'])
print('record:',record)

varName = 'vZ'
results = []
for rec in test.out_db[varName]:
    results.append(rec.level)
print(results)

varName = 'totalGen'
results = []
for rec in test.out_db[varName]:
    results.append(rec.level)
    print(rec.level)
print(results)

###########################################
