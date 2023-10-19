import os
import numpy as np
import pandas as pd
import openpyxl
from openpyxl import Workbook
import re


def getData(file, sDataColumn, plateId):

    def getDataLines(plateId, saInData, iDataCol, iWellCol):
        columns = ['plate', 'well', 'raw_data', 'type']
        df = pd.DataFrame(columns=columns)
        
        for line in saInData:
            if line.isspace():
                return df
            else:
                saValues = line.split(',')
                try:
                    iCol = int(re.search(r'\d+', saValues[iWellCol]).group())
                except:
                    print(line)
                    print(saValues[iWellCol])
                    continue
                sType = 'Data'
                if iCol == 23:
                    sType = 'Pos'
                elif iCol == 24:
                    sType = 'Neg'
                data = {'plate': plateId, 'well': saValues[iWellCol], 'raw_data': saValues[iDataCol], 'type': sType}
                df.loc[len(df.index)] = data
            
    
    def getDataStart(file, sDataColumn):
        saLines = file.readlines()
        iLineNumber = 0
        saRes = ''
        for line in saLines:
            saLine = line.split(',')
            iLineNumber += 1
            if sDataColumn in saLine:
                if 'PlateNumber' in saLine:
                    iDataColPosition = saLine.index(sDataColumn)
                    iWellColPosition = saLine.index('Well')
                    #saRes.append(line)
                    return saLines[iLineNumber:], iDataColPosition, iWellColPosition


    saData, iResultColumn, iWellColumn = getDataStart(file, sDataColumn)
    dfData = getDataLines(plateId, saData, iResultColumn, iWellColumn)
    return dfData


# Directory path where your CSV files are located
directory_path = 'screen_raw_data'

# List all files in the directory
file_list = [file for file in os.listdir(directory_path) if file.endswith('.csv')]

frames = []
plateId = 0
# Read each CSV file and store it in the list
for csv_file in file_list:
    plateId += 1
    file_path = os.path.join(directory_path, csv_file)
    print(file_path)

    #columns = ['plate', 'well', 'raw_data', 'type']
    #resDf = pd.DataFrame(columns=columns)
    with open(file_path, 'r') as file:
        tmpDf = getData(file, 'Signal', plateId)
        frames.append(tmpDf)

resDf = pd.concat(frames)
# Save the DataFrame to a CSV file
resDf.to_csv("raw.csv", sep='\t', index=False)  # Set index=False to exclude the index column

print(resDf)

