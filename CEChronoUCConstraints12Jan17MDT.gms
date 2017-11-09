$TITLE CAPACITY EXPANSION WITH CHRONOLOGICAL DEMAND AND UNIT COMMITMENT CONSTRAINTS, 3 OCT 2016, MICHAEL CRAIG

$offlisting
$offsymxref offsymlist

Options
         optcr = 1E-3
         reslim = 500000
         limcol = 0
         limrow = 0
         threads = 0
         solprint = silent
*         solvelink = 5

         ;

Sets
         egu                             existing generators
         windegu(egu)                    existing wind generators
         solaregu(egu)                   existing solar generators
         nonrenewegu(egu)                existing nonrenewable generators
         tech                            candidate plant types for new construction
         thermaltech(tech)               thermal plant types for new construction
         renewtech(tech)                 renewable plant types for new construction
         h                               hours
         peakh(h)                        hour with peak net demand
         springh(h)                      hours representing spring
         summerh(h)                      hours representing summer
         fallh(h)                        hours representing fall
         winterh(h)                      hours representing winter
         demandh(h)                      hours representing max net demand day
         ramph(h)                        hours representing day with max ramp (up or down) in net demand
         ;

alias(springh,springhh);
alias(summerh,summerhh);
alias(fallh,fallhh);
alias(winterh,winterhh);
alias(demandh,demandhh);
alias(ramph,ramphh);

Parameters
*MAX NEW UNITS TO BE BUILT
         pNmax(tech)                     maximum number of new units for each tech that can be built
*SIZE PARAMETERS [GW]
         pCapac(egu)                     hourly capacity of existing generators accounting for curtailments [GW]
         pCapactech(tech)                nameplate capacity of new builds for cost calculations [GW]
*HEAT RATES [MMBtu/GWh]
         pHr(egu)                        heat rate of existing generators [MMBtu per GWh]
         pHrtech(tech)                   heat rate of new builds [MMBtu per GWh]
*COST PARAMETERS
*        Existing generators
         pOpcost(egu)                    total operational cost [thousand$ per GWh] = VOM + FuelCost*HR + EmsCost*EmsRate*HR
*        Potential new builds
         pOpcosttech(tech)               total operational cost [thousand$ per GWh] = VOM + FuelCost*HR + EmsCost*EmsRate*HR
         pFom(tech)                      fixed O&M cost [thousand$ per GW per yr]
         pOcc(tech)                      overnight capital cost [thousand$ per GW]
*UNIT COMMITMENT PARAMETERS
*        Existing generators
         pMinload(egu)                   minimum load of EGU [GW]
         pRamprate(egu)                  up and down ramp rate of EGU [GW per hr]
         pStartupfixedcost(egu)          start up cost of EGU [thousand$]
         pOnoroffinitspr(egu)
         pOnoroffinitsum(egu)
         pOnoroffinitfal(egu)
         pOnoroffinitwin(egu)
         pOnoroffinitdem(egu)
         pOnoroffinitram(egu)
         pMindowntime(egu)
*        Potential new builds
         pMinloadtech(tech)              minimum load of EGU [GW]
         pRampratetech(tech)             up and down ramp rate of EGU assumed to be the same up & down [GW per hr]
         pStartupfixedcosttech(tech)     start up cost of EGU [thousand$]
         pMindowntimetech(tech)
*EMISSIONS RATES [short ton/MMBtu]
         pCO2emrate(egu)                 CO2 emissions rate of existing generators [short ton per MMBtu]
         pCO2emratetech(tech)            CO2 emissions rate of potential new generators [short ton per MMBtu]
*EMISSIONS CAP AND COST
         pCO2emcap                       CO2 annual emissions cap [short tons]
*HOURLY CAPACITY FACTORS FOR NEW RENEWABLES
         pCf(renewtech,h)                hourly capacity factors for potential new renewables
*MAX HOURLY GENERATION FOR EXISTING RENEWABLES
         pMaxgenwind(h)                  max hourly generation for existing wind [GWh]
         pMaxgensolar(h)                 max hourly generation for existing solar [GWh]
*FINANCIAL PARAMETERS
         pR                              discount rate
         pLife(tech)                     lifetime of tech [years]
         pCrf(tech)                      capital recovery factor
*HOURLY ELECTRICITY DEMAND [MWh]
         pDemand(h)                      hourly electricity demand [GWh]
*HOURLY RESERVE REQUIREMENTS [MW]
         pRegupreserveinitial(h)         starting regulation up reserve [GW]
         pAddedregupforaddedwind(h)      additional regulation up reserve [GW] per unit of wind built
         pAddedregupforaddedsolar(h)
         pFlexreserveinitial(h)
         pAddedflexforaddedwind(h)
         pAddedflexforaddedsolar(h)
         pContreserves(h)
*RESERVE PROVISION PARAMETERS
         pRampratetoregreservescalar     converts ramp rate timeframe to reg reserve timeframe
         pRegeligibletech(tech)          candidate plant types eligible to provide reg reserves [0] or not [1]
         pRegeligible(egu)               existing generators eligible to provide reg reserves [0] or not [1]
         pRampratetoflexreservescalar    converts ramp rate timeframe to spin reserve timeframe
         pFlexeligibletech(tech)
         pFlexeligible(egu)
         pRampratetocontreservescalar    converts ramp rate timeframe to spin reserve timeframe
         pConteligibletech(tech)
         pConteligible(egu)
         pMaxflexoffer(egu)
         pMaxcontoffer(egu)
         pMaxregupoffer(egu)
         pMaxflexoffertech(tech)
         pMaxcontoffertech(tech)
         pMaxregupoffertech(tech)
*PLANNING RESERVE
         pPlanningreserve                planning margin reserve capacity [GW]
*WEIGHT TO SCALE UP VAR COSTS AND EMISSIONS FROM REPRESENTATIVE SEASONAL HOURS TO ENTIRE SEASON
         pWeightspring                   weight for spring hours
         pWeightsummer                   weight for summer hours
         pWeightfall                     weight for fall hours
         pWeightwinter                   weight for winter hours
*DIAGNOSTIC PARAMETERS
         pModelstat
         pSolvestat
         ;

$if not set gdxincname $abort 'no include file name for data file provided'
$gdxin %gdxincname%
$load egu, windegu, solaregu, tech, thermaltech, renewtech, h, peakh, springh, summerh, winterh, fallh, demandh, ramph
$load pNmax, pCapac, pCapactech, pHr, pHrtech, pOpcost, pOpcosttech
$load pFom, pOcc, pMinload, pRamprate, pStartupfixedcost, pMinloadtech, pRampratetech, pStartupfixedcosttech
$load pCO2emrate, pCO2emratetech, pCO2emcap, pCf, pMaxgenwind, pMaxgensolar
$load pOnoroffinitsum, pOnoroffinitfal, pOnoroffinitspr, pOnoroffinitwin, pOnoroffinitdem, pOnoroffinitram
$load pR, pLife, pDemand, pRegupreserveinitial
$load pAddedregupforaddedwind, pAddedregupforaddedsolar
$load pFlexreserveinitial, pAddedflexforaddedwind, pAddedflexforaddedsolar
$load pContreserves, pRampratetoregreservescalar, pRampratetoflexreservescalar, pRampratetocontreservescalar
$load pFlexeligibletech, pFlexeligible, pConteligibletech, pConteligible, pRegeligibletech, pRegeligible
$load pPlanningreserve, pWeightspring, pWeightsummer, pWeightfall, pWeightwinter
$load pMindowntime,pMindowntimetech
$gdxin

*DEFINE NON-RENEWABLE EGUS
nonrenewegu(egu) = not windegu(egu) + solaregu(egu);
*CALCULATE CAPITAL RECOVERY FACTOR
pCrf(tech) = pR / (1 - (1 / ( (1 + pR)**pLife(tech))));
*CALCULATE MAX RESERVE OFFERS
pMaxflexoffer(egu) = pFlexeligible(egu)*pRamprate(egu)*pRampratetoflexreservescalar;
pMaxcontoffer(egu) = pConteligible(egu)*pRamprate(egu)*pRampratetocontreservescalar;
pMaxregupoffer(egu) = pRegeligible(egu)*pRamprate(egu)*pRampratetoregreservescalar;

pMaxflexoffertech(tech) = pFlexeligibletech(tech)*pRampratetech(tech)*pRampratetoflexreservescalar;
pMaxcontoffertech(tech) = pConteligibletech(tech)*pRampratetech(tech)*pRampratetocontreservescalar;
pMaxregupoffertech(tech) = pRegeligibletech(tech)*pRampratetech(tech)*pRampratetoregreservescalar;


Variable
*Total cost variables
         vZ                              obj func [thousand$ per yr]
         vIc                             total investment costs for new plants = fixed O&M + overnight capital costs [thousand$ per yr]
         vVc                             total variable costs for new and existing plants = variable O&M + fuel + emission costs [thousand$ per yr]
*Season operational cost variables
         vVcspring                       variable costs for spring hours
         vVcsummer                       variable costs for summer hours
         vVcfall                         variable costs for fall hours
         vVcwinter                       variable costs for winter hours
         vVcdemand                       variable costs for hours on max demand day
         vVcramp                         variable costs for hours on max ramp day
         ;

Positive variables
*Reserve requirements
         vRegupreserve(h)                amount of reg up reserves [GW]
         vFlexreserve(h)
*Unit commitment variables
*        New units
         vGentech(tech,h)                hourly electricity generation by new plants [GWh]
         vGenabovemintech(tech,h)        hourly electricity generation above min load by new plants [GWh]
         vReguptech(tech,h)              hourly reg up reserves provided by new plants [GWh]
         vFlextech(tech,h)
         vConttech(tech,h)
         vTurnofftech(tech,h)            number of new plants that turn off
*        Existing units
         vGen(egu,h)                     hourly electricity generation by existing plant [GWh]
         vGenabovemin(egu,h)             hourly electricity generation above min load by existing plant [GWh]
         vRegup(egu,h)                   hourly reg up reserves provided by existing plant [GWh]
         vFlex(egu,h)
         vCont(egu,h)
         vTurnoff(egu,h)                 whether existing plant turns off [1] or not [0]
*Season emission variables
         vCO2emsannual                   co2 emissions in entire year from new and existing plants [short ton]
         vCO2emssummer                   co2 emissions in summer from new and existing plants [short ton]
         vCO2emsspring                   co2 emissions in spring from new and existing plants [short ton]
         vCO2emswinter                   co2 emissions in winter from new and existing plants [short ton]
         vCO2emsfall                     co2 emissions in fall from new and existing plants [short ton]
         vCO2emsdemand                   co2 emissions in special hours from new and existing plants [short ton]
         vCO2emsramp
         ;

Binary variables
*        Existing units
         vOnoroff(egu,h)                 whether existing plant is up [1] or down [0]
         vTurnon(egu,h)                  whether existing plant turns on [1] or not [0]
         ;

Integer variables
*        New units
         vOnorofftech(tech,h)            number of new plants that are on
         vTurnontech(tech,h)             number of new plants that turn on
         vN(tech)                        number of newly constructed plants of each technology type
         ;

Equations
         objfunc                         objective function = sum investment and variable costs
         investmentcost                  calculate investment costs = fixed O&M + annualized capital costs
         varcosttotal                    sum annual variable costs
         varcostspring                   calculate spring variable costs
         varcostsummer                   calculate summer variable costs
         varcostwinter                   calculate winter variable costs
         varcostfall                     calculate fall variable costs
         varcostdemand                  calculate special hour variable costs
         varcostramp
         meetdemand(h)                   meet supply with demand
         meetreservemargin               meet planning reserve requirement with installed capacity
         setflexreserve(h)               determine quantity of required spin reserves
         setregupreserve(h)              determine quantity of required reg up reserves
         meetflexreserve(h)              meet spin reserve requirement
         meetcontreserve(h)
         meetregupreserve(h)             meet reg up reserve requirement
         setgentech(tech,h)              set electricity generation by new plants
         setgenabovemintech(tech,h)      set electricity generation above min load by new plants
         setrenewgentech(renewtech,h)    set electricity generation by new renewable generators
         setgen(egu,h)                   set electricity generation by existing plants
         setgenabovemin(egu,h)           set electricity generation above min load by existing plants
         eguwindgen(h)                   restrict electricity generation by existing wind generation to maximum aggregate output
         egusolargen(h)                  restrict electricity generation by existing solar generation to maximum aggregate output
         limitflexrestech(tech,h)        limit spin reserves by new plants by ramp rate
         limitcontrestech(tech,h)
         limitreguprestech(tech,h)         limit reg reserves by new plants by ramp rate
         limitallresuptech(tech,h)         limit total generation plus reserves of new plants to capacity
         limitflexres(egu,h)             limit spin reserves by existing plants by ramp rate
         limitcontres(egu,h)
         limitregupres(egu,h)              limit reg reserves by existing plants by ramp rate
         limitallresup(egu,h)              limit total generation plus up reserves of existing plants to capacity
         rampuptechspr(tech,springh)     limit ramp up of new plants
         rampuptechfal(tech,fallh)       limit ramp up of new plants
         rampuptechwin(tech,winterh)     limit ramp up of new plants
         rampuptechsum(tech,summerh)     limit ramp up of new plants
         rampuptechdem(tech,demandh)    limit ramp up of new plants
         rampuptechram(tech,ramph)
         rampdowntechspr(tech,springh)   limit ramp down of new plants
         rampdowntechfal(tech,fallh)     limit ramp down of new plants
         rampdowntechwin(tech,winterh)   limit ramp down of new plants
         rampdowntechsum(tech,summerh)   limit ramp down of new plants
         rampdowntechdem(tech,demandh)  limit ramp down of new plants
         rampdowntechram(tech,ramph)
         rampupspr(egu,springh)          limit ramp up of existing plants
         rampupfal(egu,fallh)            limit ramp up of existing plants
         rampupwin(egu,winterh)          limit ramp up of existing plants
         rampupsum(egu,summerh)          limit ramp up of existing plants
         rampupdem(egu,demandh)         limit ramp up of existing plants
         rampupram(egu,ramph)
         rampdownspr(egu,springh)        limit ramp down of existing plants
         rampdownfal(egu,fallh)          limit ramp down of existing plants
         rampdownwin(egu,winterh)        limit ramp down of existing plants
         rampdownsum(egu,summerh)        limit ramp down of existing plants
         rampdowndem(egu,demandh)       limit ramp down of existing plants
         rampdownram(egu,ramph)
         commitmenttechspr(tech,springh)         define unit commitment vars for new plants
         commitmenttechfal(tech,fallh)           define unit commitment vars for new plants
         commitmenttechwin(tech,winterh)         define unit commitment vars for new plants
         commitmenttechsum(tech,summerh)         define unit commitment vars for new plants
         commitmenttechdem(tech,demandh)        define unit commitment vars for new plants
         commitmenttechram(tech,ramph)
         commitmenttechbuilt(tech,h)     limit commitment of new plants to number of new plants built
         commitmentspr(egu,springh)      define unit commitment vars for existing plants
         commitmentfal(egu,fallh)        define unit commitment vars for existing plants
         commitmentwin(egu,winterh)      define unit commitment vars for existing plants
         commitmentsum(egu,summerh)      define unit commitment vars for existing plants
         commitmentdem(egu,demandh)     define unit commitment vars for existing plants
         commitmentram(egu,ramph)
         co2emsannual                    sum annual co2 emissions
         co2emssummer                    calculate summer co2 emissions
         co2emsspring                    calculate spring co2 emissions
         co2emswinter                    calculate winter co2 emissions
         co2emsfall                      calculate fall co2 emissions
         co2emsdemand                   calculate special hour co2 emissions
         co2emsramp
         enforceco2emissionscap          restrict total co2 emissions to cap
         mdttechspr(tech,springh)
         mdttechsum(tech,summerh)
         mdttechwin(tech,winterh)
         mdttechfal(tech,fallh)
         mdttechdem(tech,demandh)
         mdttechram(tech,ramph)
         mdtspr(egu,springh)
         mdtsum(egu,summerh)
         mdtwin(egu,winterh)
         mdtfal(egu,fallh)
         mdtdem(egu,demandh)
         mdtram(egu,ramph)
         ;

******************OBJECTIVE FUNCTION******************
*Objective: minimize fixed + variable costs
objfunc..                vZ =e= vIc + vVc;
******************************************************

******************CALCULATE COSTS******************
*Fixed costs = annual fixed O&M + fixed annualized capital costs
investmentcost..         vIc =e= sum(tech,vN(tech)*pFom(tech)*pCapactech(tech)+vN(tech)*pOcc(tech)*pCapactech(tech)*pCrf(tech));

*Variable costs = electricity generation costs by new and existing plants
varcosttotal..           vVc =e= vVcspring + vVcsummer + vVcwinter + vVcfall + vVcdemand + vVcramp;

varcostspring..          vVcspring =e= pWeightspring*(sum((tech,springh),vGentech(tech,springh)*pOpcosttech(tech)+pStartupfixedcosttech(tech)*vTurnontech(tech,springh))
                                                 + sum((egu,springh),vGen(egu,springh)*pOpcost(egu) + pStartupfixedcost(egu)*vTurnon(egu,springh)));

varcostsummer..          vVcsummer =e= pWeightsummer*(sum((tech,summerh),vGentech(tech,summerh)*pOpcosttech(tech)+pStartupfixedcosttech(tech)*vTurnontech(tech,summerh))
                                                 + sum((egu,summerh),vGen(egu,summerh)*pOpcost(egu) + pStartupfixedcost(egu)*vTurnon(egu,summerh)));

varcostwinter..          vVcwinter =e= pWeightwinter*(sum((tech,winterh),vGentech(tech,winterh)*pOpcosttech(tech)+pStartupfixedcosttech(tech)*vTurnontech(tech,winterh))
                                                 + sum((egu,winterh),vGen(egu,winterh)*pOpcost(egu) + pStartupfixedcost(egu)*vTurnon(egu,winterh)));

varcostfall..            vVcfall =e= pWeightfall*(sum((tech,fallh),vGentech(tech,fallh)*pOpcosttech(tech)+pStartupfixedcosttech(tech)*vTurnontech(tech,fallh))
                                                 + sum((egu,fallh),vGen(egu,fallh)*pOpcost(egu) + pStartupfixedcost(egu)*vTurnon(egu,fallh)));

varcostdemand..         vVcdemand =e= sum((tech,demandh),vGentech(tech,demandh)*pOpcosttech(tech)+pStartupfixedcosttech(tech)*vTurnontech(tech,demandh))
                                                 + sum((egu,demandh),vGen(egu,demandh)*pOpcost(egu) + pStartupfixedcost(egu)*vTurnon(egu,demandh));

varcostramp..            vVcramp =e= sum((tech,ramph),vGentech(tech,ramph)*pOpcosttech(tech)+pStartupfixedcosttech(tech)*vTurnontech(tech,ramph))
                                                 + sum((egu,ramph),vGen(egu,ramph)*pOpcost(egu) + pStartupfixedcost(egu)*vTurnon(egu,ramph));

***************************************************

******************SYSTEM-WIDE GENERATION AND RESERVE CONSTRAINTS*******************
*Demand = generation by new and existing plants
meetdemand(h)..          sum(tech,vGentech(tech,h))+sum(egu,vGen(egu,h)) =e= pDemand(h);

*Meet planning reserve margin
meetreservemargin..      sum(thermaltech,pCapactech(thermaltech)*vN(thermaltech))
                           + sum((renewtech,peakh),pCapactech(renewtech)*vN(renewtech)*pCf(renewtech,peakh))
                           + sum(nonrenewegu,pCapac(nonrenewegu)) + sum(peakh,pMaxgenwind(peakh) + pMaxgensolar(peakh)) =g= pPlanningreserve;

*Define spinning and reg reserve requirement based on new builds
setflexreserve(h)..      vN('Wind')*pCapactech('Wind')*pAddedflexforaddedwind(h) +
                                 vN('Solar PV')*pCapactech('Solar PV')*pAddedflexforaddedsolar(h) +
                                 pFlexreserveinitial(h) =e= vFlexreserve(h);

setregupreserve(h)..     vN('Wind')*pCapactech('Wind')*pAddedregupforaddedwind(h) +
                                 vN('Solar PV')*pCapactech('Solar PV')*pAddedregupforaddedsolar(h) +
                                 pRegupreserveinitial(h) =e= vRegupreserve(h);

*Meet spinning and regulation reserve requirements
meetflexreserve(h)..     sum(tech,vFlextech(tech,h)) + sum(egu,vFlex(egu,h)) =g= vFlexreserve(h);
meetcontreserve(h)..     sum(tech,vConttech(tech,h)) + sum(egu,vCont(egu,h)) =g= pContreserves(h);
meetregupreserve(h)..    sum(tech,vReguptech(tech,h)) + sum(egu,vRegup(egu,h)) =g= vRegupreserve(h);
***********************************************************************************

******************BUILD DECISIONS******************
*Limit total number builds to input value
vN.up(tech) = pNmax(tech);
vOnorofftech.up(tech,h) = pNmax(tech);
vTurnontech.up(tech,h) = pNmax(tech);
vTurnofftech.up(tech,h) = pNmax(tech);
***************************************************

******************GENERATION CONSTRAINTS******************
*NEW UNITS
*Limit gen and genabovemin, which account for # units on in each tech set
setgentech(tech,h)..  vGentech(tech,h) =e= vOnorofftech(tech,h)*pMinloadtech(tech)+vGenabovemintech(tech,h);

setgenabovemintech(tech,h) .. vGenabovemintech(tech,h) =l= (pCapactech(tech)-pMinloadtech(tech))*vOnorofftech(tech,h);

*Renewable generation limited by CF, capacity, and number on
setrenewgentech(renewtech,h)..          vGentech(renewtech,h) =l= vOnorofftech(renewtech,h)*pCapactech(renewtech)*pCf(renewtech,h);

*EXISTING UNITS
*Limit gen and genabovemin
setgen(egu,h)..  vGen(egu,h) =e= vOnoroff(egu,h)*pMinload(egu)+vGenabovemin(egu,h);

setgenabovemin(egu,h) .. vGenabovemin(egu,h) =l= (pCapac(egu)-pMinload(egu))*vOnoroff(egu,h);

*Enforce max generation by all existing wind plants
eguwindgen(h)..  pMaxgenwind(h) =g= sum(windegu,vGen(windegu,h));

*Enforce max generation by all existing solar plants
egusolargen(h).. pMaxgensolar(h) =g= sum(solaregu,vGen(solaregu,h));
*********************************************************

******************RESERVE CONSTRAINTS******************
*NEW UNITS
*Limit spinning and regulation reserves each to ramp capability and time of reserve
limitflexrestech(tech,h)$[pMaxflexoffertech(tech)>0].. vFlextech(tech,h) =l= pMaxflexoffertech(tech)*vOnorofftech(tech,h);
limitcontrestech(tech,h)$[pMaxcontoffertech(tech)>0].. vConttech(tech,h) =l= pMaxcontoffertech(tech)*vOnorofftech(tech,h);
limitreguprestech(tech,h)$[pMaxregupoffertech(tech)>0].. vReguptech(tech,h) =l= pMaxregupoffertech(tech)*vOnorofftech(tech,h);
vFlextech.fx(tech,h)$[pMaxflexoffertech(tech)=0] = 0;
vConttech.fx(tech,h)$[pMaxcontoffertech(tech)=0] = 0;
vReguptech.fx(tech,h)$[pMaxregupoffertech(tech)=0] = 0;

*Limit spinning and regulation up reserves together to spare capacity
limitallresuptech(tech,h).. vGentech(tech,h) + vFlextech(tech,h) + vConttech(tech,h) + vReguptech(tech,h) =l= pCapactech(tech) * vOnorofftech(tech,h);

*EXISTING UNITS
*Limit spining and regulation reserves each to ramp capability and time of reserve
limitflexres(egu,h)$[pMaxflexoffer(egu)>0] .. vFlex(egu,h) =l= pMaxflexoffer(egu)*vOnoroff(egu,h);
limitcontres(egu,h)$[pMaxcontoffer(egu)>0] .. vCont(egu,h) =l= pMaxcontoffer(egu)*vOnoroff(egu,h);
limitregupres(egu,h)$[pMaxregupoffer(egu)>0] .. vRegup(egu,h) =l= pMaxregupoffer(egu)*vOnoroff(egu,h);
vFlex.fx(egu,h)$[pMaxflexoffer(egu)=0] = 0;
vCont.fx(egu,h)$[pMaxcontoffer(egu)=0] = 0;
vRegup.fx(egu,h)$[pMaxregupoffer(egu)=0] = 0;

*Limit spinning and regulation up reserves together to spare capacity
limitallresup(egu,h) .. vGen(egu,h) + vFlex(egu,h) + vCont(egu,h) + vRegup(egu,h) =l= pCapac(egu);
*******************************************************

******************RAMP CONSTRAINTS******************
*NEW UNITS
*Ensure plants are limited to their ramping speed
rampuptechspr(tech,springh)$[ORD(springh)>1] .. vGenabovemintech(tech,springh)+vReguptech(tech,springh)+vFlextech(tech,springh)+vConttech(tech,springh)
                                                -vGenabovemintech(tech,springh-1) =l= pRampratetech(tech)*vOnorofftech(tech,springh)
                                                                                      + vTurnontech(tech,springh)*pCapactech(tech);
rampdowntechspr(tech,springh)$[ORD(springh)>1] .. (vGenabovemintech(tech,springh-1)-vGenabovemintech(tech,springh))
                                                                  =l= pRampratetech(tech)*vOnorofftech(tech,springh) + vTurnofftech(tech,springh)*pCapactech(tech);

rampuptechsum(tech,summerh)$[ORD(summerh)>1] .. vGenabovemintech(tech,summerh)+vReguptech(tech,summerh)+vFlextech(tech,summerh)+vConttech(tech,summerh)
                                                 -vGenabovemintech(tech,summerh-1) =l= pRampratetech(tech)*vOnorofftech(tech,summerh)
                                                                                       + vTurnontech(tech,summerh)*pCapactech(tech);
rampdowntechsum(tech,summerh)$[ORD(summerh)>1] .. (vGenabovemintech(tech,summerh-1)-vGenabovemintech(tech,summerh))
                                                                  =l= pRampratetech(tech)*vOnorofftech(tech,summerh) + vTurnofftech(tech,summerh)*pCapactech(tech);

rampuptechwin(tech,winterh)$[ORD(winterh)>1] .. vGenabovemintech(tech,winterh)+vReguptech(tech,winterh)+vFlextech(tech,winterh)+vConttech(tech,winterh)
                                                 -vGenabovemintech(tech,winterh-1) =l= pRampratetech(tech)*vOnorofftech(tech,winterh)
                                                                                       + vTurnontech(tech,winterh)*pCapactech(tech);
rampdowntechwin(tech,winterh)$[ORD(winterh)>1] .. (vGenabovemintech(tech,winterh-1)-vGenabovemintech(tech,winterh))
                                                                  =l= pRampratetech(tech)*vOnorofftech(tech,winterh) + vTurnofftech(tech,winterh)*pCapactech(tech);

rampuptechfal(tech,fallh)$[ORD(fallh)>1] .. vGenabovemintech(tech,fallh)+vReguptech(tech,fallh)+vFlextech(tech,fallh)+vConttech(tech,fallh)
                                                 -vGenabovemintech(tech,fallh-1) =l= pRampratetech(tech)*vOnorofftech(tech,fallh)
                                                                                     + vTurnontech(tech,fallh)*pCapactech(tech);
rampdowntechfal(tech,fallh)$[ORD(fallh)>1] .. (vGenabovemintech(tech,fallh-1)-vGenabovemintech(tech,fallh))
                                                                  =l= pRampratetech(tech)*vOnorofftech(tech,fallh) + vTurnofftech(tech,fallh)*pCapactech(tech);

rampuptechdem(tech,demandh)$[ORD(demandh)>1] .. vGenabovemintech(tech,demandh)+vReguptech(tech,demandh)+vFlextech(tech,demandh)+vConttech(tech,demandh)
                                                 -vGenabovemintech(tech,demandh-1) =l= pRampratetech(tech)*vOnorofftech(tech,demandh)
                                                                                       + vTurnontech(tech,demandh)*pCapactech(tech);
rampdowntechdem(tech,demandh)$[ORD(demandh)>1] .. (vGenabovemintech(tech,demandh-1)-vGenabovemintech(tech,demandh))
                                                                  =l= pRampratetech(tech)*vOnorofftech(tech,demandh) + vTurnofftech(tech,demandh)*pCapactech(tech);

rampuptechram(tech,ramph)$[ORD(ramph)>1] .. vGenabovemintech(tech,ramph)+vReguptech(tech,ramph)+vFlextech(tech,ramph)+vConttech(tech,ramph)
                                                 -vGenabovemintech(tech,ramph-1) =l= pRampratetech(tech)*vOnorofftech(tech,ramph)
                                                                                     + vTurnontech(tech,ramph)*pCapactech(tech);
rampdowntechram(tech,ramph)$[ORD(ramph)>1] .. (vGenabovemintech(tech,ramph-1)-vGenabovemintech(tech,ramph))
                                                                  =l= pRampratetech(tech)*vOnorofftech(tech,ramph) + vTurnofftech(tech,ramph)*pCapactech(tech);

*EXISTING UNITS
*Ensure plants are limited to their ramping speed
rampupspr(egu,springh)$[ORD(springh)>1] .. vGenabovemin(egu,springh)+vRegup(egu,springh)+vFlex(egu,springh)+vCont(egu,springh)-vGenabovemin(egu,springh-1) =l= pRamprate(egu);
rampdownspr(egu,springh)$[ORD(springh)>1] .. (vGenabovemin(egu,springh-1)-vGenabovemin(egu,springh)) =l= pRamprate(egu);

rampupsum(egu,summerh)$[ORD(summerh)>1] .. vGenabovemin(egu,summerh)+vRegup(egu,summerh)+vFlex(egu,summerh)+vCont(egu,summerh)-vGenabovemin(egu,summerh-1) =l= pRamprate(egu);
rampdownsum(egu,summerh)$[ORD(summerh)>1] .. (vGenabovemin(egu,summerh-1)-vGenabovemin(egu,summerh)) =l= pRamprate(egu);

rampupwin(egu,winterh)$[ORD(winterh)>1] .. vGenabovemin(egu,winterh)+vRegup(egu,winterh)+vFlex(egu,winterh)+vCont(egu,winterh)-vGenabovemin(egu,winterh-1) =l= pRamprate(egu);
rampdownwin(egu,winterh)$[ORD(winterh)>1] .. (vGenabovemin(egu,winterh-1)-vGenabovemin(egu,winterh)) =l= pRamprate(egu);

rampupfal(egu,fallh)$[ORD(fallh)>1] .. vGenabovemin(egu,fallh)+vRegup(egu,fallh)+vFlex(egu,fallh)+vCont(egu,fallh)-vGenabovemin(egu,fallh-1) =l= pRamprate(egu);
rampdownfal(egu,fallh)$[ORD(fallh)>1] .. (vGenabovemin(egu,fallh-1)-vGenabovemin(egu,fallh)) =l= pRamprate(egu);

rampupdem(egu,demandh)$[ORD(demandh)>1] .. vGenabovemin(egu,demandh)+vRegup(egu,demandh)+vFlex(egu,demandh)+vCont(egu,demandh)-vGenabovemin(egu,demandh-1) =l= pRamprate(egu);
rampdowndem(egu,demandh)$[ORD(demandh)>1] .. (vGenabovemin(egu,demandh-1)-vGenabovemin(egu,demandh)) =l= pRamprate(egu);

rampupram(egu,ramph)$[ORD(ramph)>1] .. vGenabovemin(egu,ramph)+vRegup(egu,ramph)+vFlex(egu,ramph)+vCont(egu,ramph)-vGenabovemin(egu,ramph-1) =l= pRamprate(egu);
rampdownram(egu,ramph)$[ORD(ramph)>1] .. (vGenabovemin(egu,ramph-1)-vGenabovemin(egu,ramph)) =l= pRamprate(egu);
****************************************************

******************UNIT COMMITMENT CONSTRAINTS******************
*NEW UNITS
*Constrains status of plant per whether it's on/off, turning on, or shutting down
commitmenttechspr(tech,springh)$[ORD(springh)>1] .. vOnorofftech(tech,springh) =e= vOnorofftech(tech,springh-1)+vTurnontech(tech,springh)-vTurnofftech(tech,springh);
commitmenttechsum(tech,summerh)$[ORD(summerh)>1] .. vOnorofftech(tech,summerh) =e= vOnorofftech(tech,summerh-1)+vTurnontech(tech,summerh)-vTurnofftech(tech,summerh);
commitmenttechwin(tech,winterh)$[ORD(winterh)>1] .. vOnorofftech(tech,winterh) =e= vOnorofftech(tech,winterh-1)+vTurnontech(tech,winterh)-vTurnofftech(tech,winterh);
commitmenttechfal(tech,fallh)$[ORD(fallh)>1] ..   vOnorofftech(tech,fallh) =e= vOnorofftech(tech,fallh-1)+vTurnontech(tech,fallh)-vTurnofftech(tech,fallh);
commitmenttechdem(tech,demandh)$[ORD(demandh)>1] .. vOnorofftech(tech,demandh) =e= vOnorofftech(tech,demandh-1)+vTurnontech(tech,demandh)-vTurnofftech(tech,demandh);
commitmenttechram(tech,ramph)$[ORD(ramph)>1] ..  vOnorofftech(tech,ramph) =e= vOnorofftech(tech,ramph-1)+vTurnontech(tech,ramph)-vTurnofftech(tech,ramph);

*Limit number new units on to number built
commitmenttechbuilt(tech,h) .. vOnorofftech(tech,h) =l= vN(tech);

*EXISTING UNITS
*Constrains status of plant per whether it's on/off, turning on, or shutting down
commitmentspr(egu,springh) .. vOnoroff(egu,springh) =e= pOnoroffinitspr(egu)$[ORD(springh)=1] + vOnoroff(egu,springh-1)$[ORD(springh)>1] + vTurnon(egu,springh) - vTurnoff(egu,springh);
commitmentsum(egu,summerh) .. vOnoroff(egu,summerh) =e= pOnoroffinitsum(egu)$[ORD(summerh)=1] + vOnoroff(egu,summerh-1)$[ORD(summerh)>1] +vTurnon(egu,summerh)-vTurnoff(egu,summerh);
commitmentwin(egu,winterh) .. vOnoroff(egu,winterh) =e= pOnoroffinitwin(egu)$[ORD(winterh)=1] + vOnoroff(egu,winterh-1)$[ORD(winterh)>1] +vTurnon(egu,winterh)-vTurnoff(egu,winterh);
commitmentfal(egu,fallh) ..   vOnoroff(egu,fallh) =e= pOnoroffinitfal(egu)$[ORD(fallh)=1] + vOnoroff(egu,fallh-1)$[ORD(fallh)>1] +vTurnon(egu,fallh)-vTurnoff(egu,fallh);
commitmentdem(egu,demandh) .. vOnoroff(egu,demandh) =e= pOnoroffinitdem(egu)$[ORD(demandh)=1] + vOnoroff(egu,demandh-1)$[ORD(demandh)>1] +vTurnon(egu,demandh)-vTurnoff(egu,demandh);
commitmentram(egu,ramph) ..   vOnoroff(egu,ramph) =e= pOnoroffinitram(egu)$[ORD(ramph)=1] + vOnoroff(egu,ramph-1)$[ORD(ramph)>1] +vTurnon(egu,ramph)-vTurnoff(egu,ramph);
***************************************************************

******************MIN DOWN TIME CONSTRAINTS******************
*NEW UNITS
mdttechspr(tech,springh)$[ORD(springh)>pMindowntimetech(tech)] .. vN(tech)-vOnorofftech(tech,springh) =g= sum(springhh$[ORD(springhh)<=ORD(springh)
                                                                                         and ORD(springhh)>(ORD(springh)-pMindowntimetech(tech))],vTurnofftech(tech,springhh));
mdttechsum(tech,summerh)$[ORD(summerh)>pMindowntimetech(tech)] .. vN(tech)-vOnorofftech(tech,summerh) =g= sum(summerhh$[ORD(summerhh)<=ORD(summerh)
                                                                                         and ORD(summerhh)>(ORD(summerh)-pMindowntimetech(tech))],vTurnofftech(tech,summerhh));
mdttechwin(tech,winterh)$[ORD(winterh)>pMindowntimetech(tech)] .. vN(tech)-vOnorofftech(tech,winterh) =g= sum(winterhh$[ORD(winterhh)<=ORD(winterh)
                                                                                         and ORD(winterhh)>(ORD(winterh)-pMindowntimetech(tech))],vTurnofftech(tech,winterhh));
mdttechfal(tech,fallh)$[ORD(fallh)>pMindowntimetech(tech)] .. vN(tech)-vOnorofftech(tech,fallh) =g= sum(fallhh$[ORD(fallhh)<=ORD(fallh)
                                                                                         and ORD(fallhh)>(ORD(fallh)-pMindowntimetech(tech))],vTurnofftech(tech,fallhh));
mdttechdem(tech,demandh)$[ORD(demandh)>pMindowntimetech(tech)] .. vN(tech)-vOnorofftech(tech,demandh) =g= sum(demandhh$[ORD(demandhh)<=ORD(demandh)
                                                                                         and ORD(demandhh)>(ORD(demandh)-pMindowntimetech(tech))],vTurnofftech(tech,demandhh));
mdttechram(tech,ramph)$[ORD(ramph)>pMindowntimetech(tech)] .. vN(tech)-vOnorofftech(tech,ramph) =g= sum(ramphh$[ORD(ramphh)<=ORD(ramph)
                                                                                         and ORD(ramphh)>(ORD(ramph)-pMindowntimetech(tech))],vTurnofftech(tech,ramphh));

*EXISTING UNITS
mdtspr(egu,springh)$[ORD(springh)>pMindowntime(egu)] .. 1-vOnoroff(egu,springh) =g= sum(springhh$[ORD(springhh)<=ORD(springh)
                                                                                         and ORD(springhh)>(ORD(springh)-pMindowntime(egu))],vTurnoff(egu,springhh));
mdtsum(egu,summerh)$[ORD(summerh)>pMindowntime(egu)] .. 1-vOnoroff(egu,summerh) =g= sum(summerhh$[ORD(summerhh)<=ORD(summerh)
                                                                                         and ORD(summerhh)>(ORD(summerh)-pMindowntime(egu))],vTurnoff(egu,summerhh));
mdtwin(egu,winterh)$[ORD(winterh)>pMindowntime(egu)] .. 1-vOnoroff(egu,winterh) =g= sum(winterhh$[ORD(winterhh)<=ORD(winterh)
                                                                                         and ORD(winterhh)>(ORD(winterh)-pMindowntime(egu))],vTurnoff(egu,winterhh));
mdtfal(egu,fallh)$[ORD(fallh)>pMindowntime(egu)] .. 1-vOnoroff(egu,fallh) =g= sum(fallhh$[ORD(fallhh)<=ORD(fallh)
                                                                                         and ORD(fallhh)>(ORD(fallh)-pMindowntime(egu))],vTurnoff(egu,fallhh));
mdtdem(egu,demandh)$[ORD(demandh)>pMindowntime(egu)] .. 1-vOnoroff(egu,demandh) =g= sum(demandhh$[ORD(demandhh)<=ORD(demandh)
                                                                                         and ORD(demandhh)>(ORD(demandh)-pMindowntime(egu))],vTurnoff(egu,demandhh));
mdtram(egu,ramph)$[ORD(ramph)>pMindowntime(egu)] .. 1-vOnoroff(egu,ramph) =g= sum(ramphh$[ORD(ramphh)<=ORD(ramph)
                                                                                         and ORD(ramphh)>(ORD(ramph)-pMindowntime(egu))],vTurnoff(egu,ramphh));
*************************************************************

******************CO2 EMISSIONS CONSTRAINT******************
*Co2 emissions = electricity generation * co2 emissions rate
co2emsannual..   vCO2emsannual =e= vCO2emsspring + vCO2emssummer + vCO2emswinter + vCO2emsfall + vCO2emsdemand + vCO2emsramp;

co2emsspring..   vCO2emsspring =e= pWeightspring*(sum((egu,springh),vGen(egu,springh)*pHr(egu)*pCO2emrate(egu))
                                                 + sum((tech,springh),vGentech(tech,springh)*pHrtech(tech)*pCO2emratetech(tech)));

co2emssummer..   vCO2emssummer =e= pWeightsummer*(sum((egu,summerh),vGen(egu,summerh)*pHr(egu)*pCO2emrate(egu))
                                                 + sum((tech,summerh),vGentech(tech,summerh)*pHrtech(tech)*pCO2emratetech(tech)));

co2emswinter..   vCO2emswinter =e= pWeightwinter*(sum((egu,winterh),vGen(egu,winterh)*pHr(egu)*pCO2emrate(egu))
                                                 + sum((tech,winterh),vGentech(tech,winterh)*pHrtech(tech)*pCO2emratetech(tech)));

co2emsfall..     vCO2emsfall =e= pWeightfall*(sum((egu,fallh),vGen(egu,fallh)*pHr(egu)*pCO2emrate(egu))
                                                 + sum((tech,fallh),vGentech(tech,fallh)*pHrtech(tech)*pCO2emratetech(tech)));

co2emsdemand..  vCO2emsdemand =e= sum((egu,demandh),vGen(egu,demandh)*pHr(egu)*pCO2emrate(egu))
                                                 + sum((tech,demandh),vGentech(tech,demandh)*pHrtech(tech)*pCO2emratetech(tech));

co2emsramp..    vCO2emsramp =e= sum((egu,ramph),vGen(egu,ramph)*pHr(egu)*pCO2emrate(egu))
                                                 + sum((tech,ramph),vGentech(tech,ramph)*pHrtech(tech)*pCO2emratetech(tech));

*Meet emissions cap
enforceco2emissionscap.. vCO2emsannual =l= pCO2emcap;
************************************************************

Model expansion includes all equations /all/;
solve expansion using mip minimizing vZ;

pModelstat = expansion.Modelstat;
pSolvestat = expansion.solvestat;
