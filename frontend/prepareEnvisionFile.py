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
    

def parseHarmonyFile(self, sDestDir, sFullFileName, sPlate):
    pattern = r'(\d+)\t(\d+)'
    saOutput = []
    iLine = 0
    
    directory, filename = os.path.split(sFullFileName)

    try:
        with open(sFullFileName, 'r') as file:
            lines = file.readlines()
            for line in lines:
                iLine += 1
                if line.startswith("Row\tColumn"):
                    saOutput.append(line.replace("Row\tColumn", 'Well').replace('\t', ','))
                    break
            iLinesAgain = 0
            for line in lines:
                iLinesAgain += 1
                if iLinesAgain > iLine:
                    number_list = line.split('\t')
                    sRow = number_to_alphabet(int(number_list[0]))
                    sColumn = str(f"{int(number_list[1]):02}")
                    sWell = f'{sRow}{sColumn}'
                    output_string = re.sub(pattern, sWell, line, count=1)
                    saOutput.append(output_string.replace('\t', ','))

    except FileNotFoundError:
        assaylib.printPrepLog(self, f"File '{sFullFileName}' not found.", 'error')
        return ""
    except Exception as e:
        assaylib.printPrepLog(self, f"An error occurred: {e}", 'error')

    long_string = ''.join(saOutput)

    sFile = sPlate + '.txt'
    sOutFile = os.path.join('/', sDestDir, sFile)
    fullPath = os.path.abspath(sOutFile)

    with open(sOutFile, 'w') as file:
        file.write(long_string)
    #self.printQcLog(f'Parsing {sFullFileName} into {sFile}')
    return fullPath


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
    
    # Read lines until an empty row
    for line in file:
        line = line.strip()  # Remove leading/trailing whitespace
        if not line:  # If the line is empty
            break
        saLines.append(line)

    sFullPath = os.path.join(preparedDirectory, f'{plateId}.txt')

    with open(sFullPath, 'w', newline='') as file:
        writer = csv.writer(file, delimiter=',')
        for line in saLines:
            writer.writerow(line.split(','))
    return plateId, sFullPath


def findEnvisionFiles(self, subdirectory_path, plate_to_file_mapping):
    print(subdirectory_path, plate_to_file_mapping)
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
        plate_file_pairs.append((plate, file))

    saPreparedPlateMapping = {
        "plate": [],
        "file": []
    }

    # Loop over the plate:file pairs and print each pair to the terminal
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
