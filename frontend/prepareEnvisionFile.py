import re
import os
import pandas as pd
import assaylib
import dbInterface
import openpyxl
import csv

def createPlatemap(self, platesDf, subdirectory_path):
    columns = ['Platt ID', 'Well', 'Compound ID', 'Batch nr', 'Conc mM', 'volume nL']
    platemapDf = pd.DataFrame(columns=columns)
    
    assaylib.printPrepLog(self, f'Fetching plate data for plates:')
    iNrOfPlates = 0
    for index, row in platesDf.iterrows():
        df = pd.DataFrame()
        plate_value = row['plate']
        plate_data, lSuccess = dbInterface.getPlate(self.token, plate_value)
        if lSuccess:
            iNrOfPlates += 1
            assaylib.printPrepLog(self, f'{plate_value}')

            df = pd.DataFrame(plate_data, columns=columns)
        else:
            assaylib.printPrepLog(self, f'Error getting plate {plate_value} {plate_data}', 'error')
        platemapDf = pd.concat([platemapDf if not platemapDf.empty else None, df], ignore_index=True)

    assaylib.printPrepLog(self, f'Found {iNrOfPlates} plate files')

    excel_filename = 'PLATEMAP.xlsx'
    full_path = os.path.join(subdirectory_path, excel_filename)
    platemapDf.to_excel(full_path, index=False)
    assaylib.printPrepLog(self, f'Created platemap-file:')
    assaylib.printPrepLog(self, f'{full_path}', type='bold')

    return full_path


def find_files(directory, filename_start, filename_end):
    matching_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith(filename_start) and file.endswith(filename_end):
                matching_files.append(os.path.join(root, file))
    return matching_files


def extractPlate(file, preparedDirectory, plateId):
    saLines = []
    
    # Skip the first line
    next(file)

    # Read lines until we find the word "well"
    for line in file:
        if "well" in line.lower():  # If the line is empty
            saLines.append(line.rstrip() + '\n')
            break

    # Read lines until we find empty lines
    for line in file:
        line = line.strip()  # Remove leading/trailing whitespace
        if not line or line.startswith('Plate info'):  # If the line is empty
            break
        saLines.append(line)

    sFullPath = os.path.join(preparedDirectory, f'{plateId}.txt')

    with open(sFullPath, 'w', newline='') as file:
        iCount = 0
        for line in saLines:
            if iCount == 0:
                file.write(line)
            else:
                file.write(line + '\n')
            iCount += 1
            
    return plateId, sFullPath


def findEnvisionFiles(self, subdirectory_path, plate_to_file_mapping):
    envision_dir = os.path.dirname(plate_to_file_mapping)
    data = {
        "plate": [],
        "file": []
    }

    try:
        os.makedirs(subdirectory_path)
    except:
        pass

    # Load the Excel file
    workbook = openpyxl.load_workbook(plate_to_file_mapping)

    # Select the worksheet by name
    worksheet = workbook.worksheets[0]

    # Initialize a list to store plate:file pairs
    plate_file_pairs = []

    # Iterate over rows in the worksheet, starting from the second row (assuming the first row is header)
    for row in worksheet.iter_rows(min_row=2, values_only=True):
        plate, file = row[0], row[1]  # Assuming "Plate" is in the first column and "File" is in the second column
        if isinstance(plate, str) and plate.lower().startswith('p'):
            plate_file_pairs.append((plate, file))

    saPreparedPlateMapping = {
        "plate": [],
        "file": []
    }

    for plate, plate_file in plate_file_pairs:
        with open(envision_dir + '/' + plate_file, 'r') as file:
            sPlate, sPlateFile = extractPlate(file, subdirectory_path, plate)

            saPreparedPlateMapping['plate'].append(sPlate)
            saPreparedPlateMapping['file'].append(sPlateFile)

    df = pd.DataFrame(saPreparedPlateMapping)
    df = df.sort_values(by='plate')
    sPlatemapFile = assaylib.createPlatemap(self, df, subdirectory_path)
    # Close the workbook
    workbook.close()
    fileName = "prepared_plate_to_file.xlsx"
    fullFileName = os.path.join(subdirectory_path, fileName)
    df.to_excel(fullFileName, index=False)
    return sPlatemapFile, fullFileName
