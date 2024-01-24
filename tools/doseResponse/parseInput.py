import pandas as pd

sColName = 'Cell Selected - Number of Spots - Mean per Well'


platemap_xlsx = 'preparedHaronyFiles/PLATEMAP.xlsx'
platemapDf = pd.read_excel(platemap_xlsx)

# Final volume in nano liter
final_volume = 30000
platemapDf['finalConc'] = (platemapDf['Conc mM']* 1000000 * platemapDf['volume nL']) / final_volume


print(platemapDf.head(65))

'''
Platemap columns:
'Platt ID', 'Well', 'Compound ID', 'Batch nr', 'Conc mM', 'volume nL'


C1 * V1 = C2 * V2

C2 = (C1*1000 * V1*1000)/ V2

 This is the Excel formula for calculating the final concentration in each well. In the example
 below the final volume in each well is 30 microL
 =((E3/1000)*(F3/0.000000001))/(30/0.001)
'''
