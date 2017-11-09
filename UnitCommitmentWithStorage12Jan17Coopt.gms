$TITLE UNIT COMMITMENT WITH STORAGE CONSTRAINTS, 3 OCT 2016, MICHAEL CRAIG

*Turn off output in .lst file
$offlisting
$offsymxref offsymlist

Options
         optcr = 1E-3
         reslim = 600
         limcol = 0
         limrow = 0
         threads = 0
         solprint = silent
*         solvelink = 5
         ;

Sets
         egu                                     "electricity generators"
         windegu(egu)                            "wind electricity generators"
         solaregu(egu)                           "solar electricity generators"
         storageegu(egu)                         "storage units"
         nonstorageegu(egu)                      "non-storage units"
         h                                       "hours"
                 ;

alias(h,hh);

Parameters
*System parameters
         pDemand(h)                              "electricity demand (GWh)"
         pRegupreserves(h)                       "required hourly up regulation reserves (GW)"
         pFlexreserves(h)
         pContreserves(h)
*Unit-specific parameters
         pMinload(egu)                           "minimum load of EGU (GW)"
         pRamprate(egu)                          "ramp rate of EGU, assumed to be the same up & down (GW/hr)"
         pStartupfixedcost(egu)                  "start up cost of EGU (thousands$)"
         pMindowntime(egu)                       "MDT (hours)"
         pCapac(egu)                             "capacity of egu (GW)"
         pHr(egu)                                "heat rate (MMBtu/GWh)"
         pOpcost(egu)                            "plant operating cost (thousands$/GWh)"
         pRegeligible(egu)                       "whether eligible to provide reg reserves (1) or not (0)"
         pFlexeligible(egu)
         pConteligible(egu)
         pCO2emrate(egu)                         "CO2 emissions rate (short ton/MMBtu)"
*Storage parameters
         pStoinenergymarket                        "whether storage can provide energy (1) or not (0)"
         pEfficiency(storageegu)                 "round trip storage efficiency"
         pCapaccharge(storageegu)                "max charging capacity (GW)"
         pMaxstateofcharge(storageegu)           "max stored energy (GWh)"
         pMinstateofcharge(storageegu)           "min stored energy (GWh)"
         pInitialstateofcharge(storageegu)       "initial state of charge (GWh)"
*Max hourly generation for renewables
         pMaxgenwind(h)                          "maximum hourly generation by all wind generators"
         pMaxgensolar(h)                         "maximum hourly generation by all solar generators"
*Carried unit-specific parameters from last optimization
         pOnoroffinitial(egu)                    "whether plant is set to on or off in hour 1 from prior optimization"
         pMdtcarriedhours(egu)                   "MDT carried over from last optimization (hours)"
         pGenabovemininitial(egu)                "gen above min load from last period of prior optimization (GW)"
*Scalars
         pRegoffercost(egu)
         pCO2price                               "carbon price (thouands$/short ton)"
         pCnse                                   "cost of non-served energy (thousands$/GWh)"
         pRampratetoregreservescalar             "converts timeframe that ramp rate is given in to reg reserve provision timeframe"
         pRampratetoflexreservescalar
         pRampratetocontreservescalar
         pMaxregupoffer(egu)
         pMaxflexoffer(egu)
         pMaxcontoffer(egu)
*Diagnostic parameters
         pModelstat
         pSolvestat
                 ;

$if not set gdxincname $abort 'no include file name for data file provided'
$gdxin %gdxincname%
$load egu, windegu, solaregu, storageegu, h, pDemand
$load pMinload, pRamprate, pStartupfixedcost, pMindowntime, pCapac, pOpcost, pHr
$load pCO2emrate, pStoinenergymarket, pEfficiency, pCapaccharge, pMaxstateofcharge
$load pMinstateofcharge, pInitialstateofcharge, pMaxgenwind, pMaxgensolar, pOnoroffinitial
$load pMdtcarriedhours, pGenabovemininitial, pCO2price, pCnse
$load pRegeligible, pFlexeligible, pConteligible, pRegoffercost
$load pRegupreserves, pFlexreserves, pContreserves
$load pRampratetoregreservescalar, pRampratetoflexreservescalar, pRampratetocontreservescalar
$gdxin


*DEFINE GENERATORS THAT ARE NOT STORAGE UNITS
nonstorageegu(egu) = not storageegu(egu);

*DEFINE PARAMETERS
pCapaccharge(storageegu) = pCapac(storageegu);
pMaxregupoffer(egu) = pRegeligible(egu)*pRamprate(egu)*pRampratetoregreservescalar;
pMaxflexoffer(egu) = pFlexeligible(egu)*pRamprate(egu)*pRampratetoflexreservescalar;
pMaxcontoffer(egu) = pConteligible(egu)*pRamprate(egu)*pRampratetocontreservescalar;

Variables
         vTotalopcost                            "total cost of power generation (thousands $)"
                 ;

Positive Variables
         vGen(egu,h)                             "power generation at plant egu at end of hour h (GW)"
         vGenabovemin(egu,h)                     "power generation above minimum stable load (GW)"
         vRegup(egu,h)                           "regulation up reserves provided (GW)"
         vFlex(egu,h)
         vCont(egu,h)
         vNse(h)                                 "nonserved energy (GW)"
         vTurnoff(egu,h)                         "indicates whether plant decides to turn off (1) or not (0) in hour h"
         vStateofcharge(storageegu,h)            "energy stored in storage unit at end of hour h (GWh)"
         vCharge(storageegu,h)                   "charged energy by storage unit in hour h (GWh)"
                 ;

Binary Variables
         vTurnon(egu,h)                          "indicates whether plant decides to turn on (1) or not (0) in hour h"
         vOnoroff(egu,h)                         "indicates whether plant is up (1) or down (0) in hour h"
                 ;

Equations
         objfunc                                 "define objective function to be minimized"
         definegenabovemin(egu,h)                "establish relationship between Gen (total gen) and Genabovemin (gen just above min stable load)"
         meetdemand(h)                               "must meet electric demand"
         rampconstraintup(egu,h)                 "ramping up constraint for t>1"
         rampconstraintdown(egu,h)               "ramping down constraint for t>1"
         rampconstraintupinitial(egu,h)          "ramping up constraint at t=1"
         rampconstraintdowninitial(egu,h)        "ramping down constraint at t=1"
         statusofplant(egu,h)                    "balance whether thermal plant is on or off with whether shutting down or starting up"
         determineloadabovemin(egu,h)            "determine what each thermal unit's generation is above its minimum load. Constraints Genabovemin to be between max and min capacity"
         meetflexreserves(h)                     "meet hourly spinning reserve requirements"
         meetcontreserves(h)
         meetregupreserves(h)                      "meet hourly regulation reserve requirements"
         enforcemindowntime(egu,h)               "make sure plant, once it turns off, doesn't turn back on before MDT passes"
         enforcemindowntimecarryover(egu,h)      "enforce MDT from turn off decisions in prior optimization"
         flexreservelimit(egu,h)                 "limit spin reserves provided by generator to multiple of ramp rate"
         contreservelimit(egu,h)
         regupreservelimit(egu,h)                  "limit reg reserves provided by generator to multiple of ramp rate"
         genplusreguplimit(egu,h)                 "limit generation + spin reserves to max capac"
         maxwindgen(h)                           "restrict wind generation to maximum aggregate output"
         maxsolargen(h)                          "restrict solar generation to maxmimum aggregate output"
         genplusuprestosoc(storageegu,h)
         defstateofcharge(storageegu,h)          "define relationship between state of charge, charging and discharging for storage units"
         defstateofchargeinitial(storageegu,h)   "define relationship at t=1 between state of charge, charging and discharging for storage units"
         maxenergystored(storageegu,h)           "limit state of charge to stored energy capacity"
         minenergystored(storageegu,h)           "limit state of charge to stored energy minimum"
         limitcharging(storageegu,h)             "limit charge rate to max charge rate"
         limitflexstoragetoramp
         limitcontstoragetoramp
         limitregupstoragetoramp
         limitstorageresup
                  ;

******************OBJECTIVE FUNCTION******************
*Minimize total operational cost
objfunc .. vTotalopcost =e= sum(h,pCnse*vNse(h))
                 + sum((egu,h), vGen(egu,h)*pOpcost(egu)+pStartupfixedcost(egu)*vTurnon(egu,h)
                         + vRegup(egu,h)*pRegoffercost(egu));
******************************************************

******************SYSTEM-WIDE CONSTRAINTS******************
*Spinning reserve requirement: need enough spare capacity in units to meet reserve requirement
meetflexreserves(h)  .. sum(egu,vFlex(egu,h)) =g= pFlexreserves(h);
meetcontreserves(h) .. sum(egu,vCont(egu,h)) =g= pContreserves(h);

*Regulation reserve requirement
meetregupreserves(h) .. sum(egu,vRegup(egu,h)) =g= pRegupreserves(h);

*Supply = demand
meetdemand(h) .. sum(egu,vGen(egu,h)) + vNse(h) - sum(storageegu,vCharge(storageegu,h)) =e= pDemand(h);
***********************************************************

******************GENERATION CONSTRAINTS******************
*Constrain plants to generate below their max capacity
definegenabovemin(egu,h).. vGen(egu,h) =e= vOnoroff(egu,h)*pMinload(egu)+vGenabovemin(egu,h);

*Establish relationship between gen above min load, gen output, and min load
determineloadabovemin(egu,h) .. vGenabovemin(egu,h) =l= (pCapac(egu)-pMinload(egu))*vOnoroff(egu,h);

*Enforce max generation on all wind generators
maxwindgen(h).. pMaxgenwind(h) =g= sum(windegu,vGen(windegu,h));

*Enforce max generation on all solar generators
maxsolargen(h).. pMaxgensolar(h) =g= sum(solaregu,vGen(solaregu,h));
**********************************************************

******************RESERVE PROVISION CONSTRAINTS******************
*Spin and reg reserves limited by ramp rate
regupreservelimit(nonstorageegu,h)$[pMaxregupoffer(nonstorageegu)>0] .. vRegup(nonstorageegu,h) =l= pMaxregupoffer(nonstorageegu)*vOnoroff(nonstorageegu,h);
flexreservelimit(nonstorageegu,h)$[pMaxflexoffer(nonstorageegu)>0] .. vFlex(nonstorageegu,h) =l= pMaxflexoffer(nonstorageegu)*vOnoroff(nonstorageegu,h);
contreservelimit(nonstorageegu,h)$[pMaxcontoffer(nonstorageegu)>0] .. vCont(nonstorageegu,h) =l= pMaxcontoffer(nonstorageegu)*vOnoroff(nonstorageegu,h);
vRegup.fx(nonstorageegu,h)$[pMaxregupoffer(nonstorageegu)=0] = 0;
vFlex.fx(nonstorageegu,h)$[pMaxflexoffer(nonstorageegu)=0] = 0;
vCont.fx(nonstorageegu,h)$[pMaxcontoffer(nonstorageegu)=0] = 0;

*Limit generation + up (reg + spin) reserves to max capacity
genplusreguplimit(egu,h) .. vGen(egu,h) + vFlex(egu,h) + vCont(egu,h) + vRegup(egu,h) =l= pCapac(egu);
*****************************************************************

******************RAMPING CONSTRAINTS******************
*Ensure plants are limited to their ramping speed
rampconstraintup(egu,h)$[ORD(h)>1] .. (vGenabovemin(egu,h) + vFlex(egu,h) + vCont(egu,h) + vRegup(egu,h)) - vGenabovemin(egu,h-1) =l= pRamprate(egu);
rampconstraintdown(egu,h)$[ORD(h)>1] .. (vGenabovemin(egu,h-1) - vGenabovemin(egu,h)) =l= pRamprate(egu);

*Enforce ramp rates in hour 1 of optimization window
rampconstraintupinitial(egu,h)$[ORD(h)=1] .. (vGenabovemin(egu,h) + vFlex(egu,h) + vCont(egu,h) + vRegup(egu,h)) - pGenabovemininitial(egu) =l= pRamprate(egu);
rampconstraintdowninitial(egu,h)$[ORD(h)=1] .. (pGenabovemininitial(egu) - vGenabovemin(egu,h)) =l= pRamprate(egu);
*******************************************************

******************ON/OFF CONSTRAINTS******************
*Constrains status of plant per whether it's on/off, turning on, or shutting down
statusofplant(egu,h) .. vOnoroff(egu,h) =e= pOnoroffinitial(egu)$[ORD(h)=1]+vOnoroff(egu,h-1)$[ORD(h)>1]+vTurnon(egu,h)-vTurnoff(egu,h);

*Limit plant to not start up until it reaches its min down time
enforcemindowntime(egu,h)$[ORD(h)>pMdtcarriedhours(egu)] .. 1-vOnoroff(egu,h) =g= sum(hh$[ORD(hh)<=ORD(h) and ORD(hh)>(ORD(h)-pMindowntime(egu))],vTurnoff(egu,hh));
*enforcemindowntime(egu,h) .. 1-vOnoroff(egu,h) =g= sum(hh$[ORD(hh)<=ORD(h) and ORD(hh)>(ORD(h)-pMindowntime(egu))],vTurnoff(egu,hh));

*Enforce MDT hours carried over from last optimization
enforcemindowntimecarryover(egu,h)$[ORD(h)<=pMdtcarriedhours(egu)] .. vOnoroff(egu,h) =l= 0;
******************************************************

******************STORAGE CONSTRAINTS******************
*LIMIT PARTICIPATION OF STORAGE IN ENERGY MARKET
vGen.up(storageegu,h) = pStoinenergymarket * pCapac(storageegu);

*LIMIT GENERATION PLUS UP RESERVES TO STATE OF CHARGE
genplusuprestosoc(storageegu,h) .. vGen(storageegu,h) + vRegup(storageegu,h) + vFlex(storageegu,h) + vCont(storageegu,h) =l= vStateofcharge(storageegu,h);

*CHARGE STATE CONSTRAINTS
*Link state of charge, charging, and discharging in hours > 1
defstateofcharge(storageegu,h)$[ORD(h)>1] .. vStateofcharge(storageegu,h) =e= vStateofcharge(storageegu,h-1) - vGen(storageegu,h)
                                                                                 + pEfficiency(storageegu) * vCharge(storageegu,h);

*Link state of charge, charging, and discharging in hour 1
defstateofchargeinitial(storageegu,h)$[ORD(h)=1] .. vStateofcharge(storageegu,h) =e= pInitialstateofcharge(storageegu) - vGen(storageegu,h)
                                                                                         + pEfficiency(storageegu) * vCharge(storageegu,h);

*Limit state of charge to maximum and minimum storage capacity
maxenergystored(storageegu,h) .. vStateofcharge(storageegu,h) =g= pMinstateofcharge(storageegu);
minenergystored(storageegu,h) .. vStateofcharge(storageegu,h) =l= pMaxstateofcharge(storageegu);

*RATE OF CHARGE CONSTRAINT
*Limit rate of charging, and constrain charging to when storage unit is off (i.e., not discharging)
limitcharging(storageegu,h) .. vCharge(storageegu,h) =l= pCapaccharge(storageegu) * (1 - vOnoroff(storageegu,h));

*RESERVE CONSTRAINTS
*Limit reg up and down and spin to ramp capabilities. Assume ramp rate is same for charging and generation
limitregupstoragetoramp(storageegu,h) .. vRegup(storageegu,h) =l= pRegeligible(storageegu)*pRamprate(storageegu)*pRampratetoregreservescalar;
limitflexstoragetoramp(storageegu,h) .. vFlex(storageegu,h) =l= pFlexeligible(storageegu)*pRamprate(storageegu)*pRampratetoflexreservescalar;
limitcontstoragetoramp(storageegu,h) .. vCont(storageegu,h) =l= pConteligible(storageegu)*pRamprate(storageegu)*pRampratetocontreservescalar;

*Limit reg up to spare capacity while discharging & to charge amount while charging
limitstorageresup(storageegu,h) .. vRegup(storageegu,h) + vFlex(storageegu,h) + vCont(storageegu,h) =l= (vOnoroff(storageegu,h)*pCapac(storageegu)
                                                                                                         - vGen(storageegu,h)) + vCharge(storageegu,h);
*******************************************************

model unitcommitment /all/;
solve unitcommitment using mip minimizing vTotalopcost;

pModelstat = unitcommitment.Modelstat;
pSolvestat = unitcommitment.solvestat;
