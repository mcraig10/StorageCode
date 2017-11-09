#Michael Craig
#October 4, 2016
#Functions update input fleets' fuel prices for given year

from SetupGeneratorFleet import getFuelPrice

#Updates fleets' fuel prices for given year
#Inputs: gen fleet (2d list), new techs (2d list), current year, future fuel prices (2d list)
def updateFuelPrices(genFleet,newTechsCE,currYear,fuelPricesTimeSeries):
    updateFuelPricesExistingGens(genFleet,currYear,fuelPricesTimeSeries)
    updateFuelPricesNewTechs(newTechsCE,currYear,fuelPricesTimeSeries)

#Update fuel prices for existing generators
def updateFuelPricesExistingGens(genFleet,currYear,fuelPricesTimeSeries):
    fuelPriceCol = genFleet[0].index('FuelPrice($/MMBtu)')
    fuelTypeCol = genFleet[0].index('Modeled Fuels')
    for row in genFleet[1:]:
        fuelPrice = getFuelPrice(row,fuelTypeCol,fuelPricesTimeSeries,currYear)
        row[fuelPriceCol] = fuelPrice
 
#Update fuel prices for new techs
def updateFuelPricesNewTechs(newTechsCE,currYear,fuelPricesTimeSeries):
    fuelPriceCol = newTechsCE[0].index('FuelCost($/MMBtu)')
    fuelTypeCol = newTechsCE[0].index('FuelType')
    for row in newTechsCE[1:]:
        fuelPrice = getFuelPrice(row,fuelTypeCol,fuelPricesTimeSeries,currYear)
        row[fuelPriceCol] = fuelPrice
