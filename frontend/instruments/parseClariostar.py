import sys
import os
import numpy as np
import pandas as pd
import openpyxl
from openpyxl import Workbook
import re
import fnmatch



def getPlateMap(sPlateId, dfPlatemap):
    new_df = dfPlatemap[dfPlatemap.iloc[:, 0] == sPlateId]
    return new_df


def getData(file, dfPlatemap, sDataColumn, plateId, sCtrl):

    def getDataLines(plateId, saInData, iDataCol, iWellCol, dfPlatemap, sCtrl):
        columns = ['plate', 'well', 'raw_data', 'type']
        df = pd.DataFrame(columns=columns)

        for line in saInData:
            if line.isspace():
                return df
            
            saValues = line.split(',')
            try:
                iCol = int(re.search(r'\d+', saValues[iWellCol]).group())
            except:
                print(line)
                print(saValues[iWellCol])
                continue

            
            sType = 'Data'
            selected_row = dfPlatemap[dfPlatemap['Well'] == saValues[iWellCol]].copy()
            selected_row = selected_row.reset_index(drop=True)

            if selected_row.loc[0, 'Compound ID'] == sCtrl:
                sType = 'Pos'
            elif selected_row['Compound ID'][0] == 'DMSO':
                sType = 'Neg'
            elif selected_row['Compound ID'][0].startswith('CBK'):
                sType = 'Data'
            else:
                print(f'''Skipping well {selected_row['Well'][0]} with compound_id = {selected_row['Compound ID'][0]}''')
                continue

            data = {'plate': plateId,
                    'well': saValues[iWellCol],
                    'raw_data': saValues[iDataCol],
                    'type': sType}
            df.loc[len(df.index)] = data
        return df

    def getDataStart(file, sDataColumn):
        saLines = file.readlines()
        iLineNumber = 0
        saRes = ''
        for line in saLines:
            saLine = line.split(',')
            iLineNumber += 1
            if sDataColumn in saLine:
                if 'Well' in saLine:
                    iDataColPosition = saLine.index(sDataColumn)
                    iWellColPosition = saLine.index('Well')
                    return saLines[iLineNumber:], iDataColPosition, iWellColPosition

    saData, iResultColumn, iWellColumn = getDataStart(file, sDataColumn)
    dfData = getDataLines(plateId, saData, iResultColumn, iWellColumn, dfPlatemap, sCtrl)
    return dfData


# Check if at least one command-line argument is provided
if len(sys.argv) < 2:
    print("Usage: python parseClariostar.py posCtrlName")
    sys.exit(1)

# Get the first command-line argument as the input file
sCtrl = sys.argv[1]


# Directory path where your CSV files are located
directory_path = 'clariostar'
all_files = os.listdir(directory_path)
# Filter the files that end with "csv" (case-insensitive)
file_list = [file for file in all_files if fnmatch.fnmatch(file.lower(), '*.csv')]


# Read platemap
platemap_file = directory_path + '/platemap.xlsx'  # Replace 'your_file.xlsx' with the actual file path
# Read the Excel file into a DataFrame
platemapDf = pd.read_excel(platemap_file)

# Get all plate names from the first column of the platemap
saPlates = platemapDf.iloc[:, 0].unique()


frames = []
plateIndex = 0
# Read each CSV file and store it in the list
for csv_file in file_list:
    plateId = saPlates[plateIndex]
    plateIndex += 1

    file_path = os.path.join(directory_path, csv_file)
    print(file_path)

    dfThisPlateMap = getPlateMap(plateId, platemapDf)
    
    #columns = ['plate', 'well', 'raw_data', 'type']
    #resDf = pd.DataFrame(columns=columns)
    with open(file_path, 'r') as file:
        tmpDf = getData(file, dfThisPlateMap, 'Signal', plateId, sCtrl)
        frames.append(tmpDf)

resDf = pd.concat(frames)
# Save the DataFrame to a CSV file
resDf.to_csv("rawClariostar.csv", sep='\t', index=False)  # Set index=False to exclude the index column

