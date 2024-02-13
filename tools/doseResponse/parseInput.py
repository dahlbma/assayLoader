import pandas as pd
#import numpy as np


'''
Platemap columns:
'Platt ID', 'Well', 'Compound ID', 'Batch nr', 'Conc mM', 'volume nL'


C1 * V1 = C2 * V2

C2 = (C1*1000 * V1*1000)/ V2

 This is the Excel formula for calculating the final concentration in each well. In the example
 below the final volume in each well is 30 microL
 =((E3/1000)*(F3/0.000000001))/(30/0.001)


'''



sDataColName = 'Cell Selected - Number of Spots - Mean per Well'

platemap_xlsx = 'preparedHaronyFiles/PLATEMAP.xlsx'
platemapDf = pd.read_excel(platemap_xlsx)

rawDataFiles_xlsx = 'preparedHaronyFiles/prepared_plate_to_file.xlsx'
rawDataFilesDf = pd.read_excel(rawDataFiles_xlsx)

# Final volume in nano liter (nL)
final_volume = 30000
platemapDf['finalConc_nL'] = (platemapDf['Conc mM']* 1000000 * platemapDf['volume nL']) / final_volume

combinedDataDf = pd.DataFrame()
for index, row in rawDataFilesDf.iterrows():
    plate = row['plate']
    file_path = 'preparedHaronyFiles/' + row['file']

    rawDataDf = pd.read_csv(file_path)
    plates = [plate] * len(rawDataDf)
    rawDataDf.insert(0, 'plate', plates)
    if len(combinedDataDf) == 0:
        combinedDataDf = rawDataDf
    else:
        combinedDataDf = pd.concat([combinedDataDf, rawDataDf], ignore_index=True)

platemapDf['rawData'] = ''

for index, row in platemapDf.iterrows():
    plate_id = row['Platt ID']
    well = row['Well']

    matching_row = combinedDataDf[(combinedDataDf['plate'] == plate_id) & (combinedDataDf['Well'] == well)]
    if not matching_row.empty:
        # Update 'rawData' in platemapDf
        platemapDf.at[index, 'rawData'] = matching_row[sDataColName].values[0]


# Remove columns 'Conc mM' and 'volume nL'
columns_to_remove = ['Conc mM', 'volume nL']
platemapDf = platemapDf.drop(columns=columns_to_remove)


excel_file_path = 'prepare_platemap.xlsx'
platemapDf.to_excel(excel_file_path, index=False)



# Group by 'Batch' and calculate mean and yVariance
#grouped_df = platemapDf.groupby(['Batch nr', 'Compound ID', 'finalConc_nL'])['rawData'].agg(['mean', 'var']).reset_index()
grouped_df = platemapDf.groupby(['Batch nr', 'Compound ID', 'finalConc_nL'])['rawData'].agg(['mean', 'std']).reset_index()
resultDf = grouped_df.rename(columns={'mean': 'yMean', 'std': 'yStd'})

### Do proper calculation here instead!!!
### This is just some dummy scaling 8 (max inhibition value) to be close to 100.
### Need proper calculation here
resultDf['yStd'] = resultDf['yStd'] * 12


meanPosCtrl = resultDf.loc[resultDf["Compound ID"] == "CTRL", "yMean"].values[0]
meanNegCtrl = resultDf.loc[resultDf["Compound ID"] == "DMSO", "yMean"].values[0]

resultDf['inhibition'] = 100*(1-(resultDf['yMean']-meanPosCtrl)/(meanNegCtrl-meanPosCtrl))


# Rename columns if needed
resultDf = resultDf.rename(columns={'Batch': 'Batch', 'rawData': 'yMean'})
# Display the result DataFrame
print(resultDf)
excel_file_path = 'finalPreparedDR.xlsx'
resultDf.to_excel(excel_file_path, index=False)
