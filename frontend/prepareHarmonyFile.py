import re
import os
import pandas as pd
import assaylib
import dbInterface

def number_to_alphabet(sRow):
    if 1 <= sRow <= 26:
        alphabet_letter = chr(64 + sRow)
        return alphabet_letter
    else:
        return "Invalid input"


def createPlatemap(self, platesDf, subdirectory_path):
    columns = ['Platt ID', 'Well', 'Compound ID', 'Batch nr', 'Conc mM', 'volume nL']
    platemapDf = pd.DataFrame(columns=columns)
    
    assaylib.printPrepLog(self, f'Fetching plate data for plates:')
    for index, row in platesDf.iterrows():
        df = pd.DataFrame()
        plate_value = row['plate']
        plate_data, lSuccess = dbInterface.getPlate(self.token, plate_value)
        if lSuccess:
            assaylib.printPrepLog(self, f'Plate: {plate_value}')

            df = pd.DataFrame(plate_data, columns=columns)
        else:
            assaylib.printPrepLog(self, f'Error getting plate {plate_value} {plate_data}', 'error')
        platemapDf = pd.concat([platemapDf if not platemapDf.empty else None, df], ignore_index=True)

    excel_filename = 'PLATEMAP.xlsx'
    full_path = os.path.join(subdirectory_path, excel_filename)
    platemapDf.to_excel(full_path, index=False)
    assaylib.printPrepLog(self, f'Created platemap-file:\n{full_path}')
    

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
        #self.printQcLog(f"File '{sFullFileName}' not found.", 'error')
        return ""
    except Exception as e:
        assaylib.printPrepLog(self, f"An error occurred: {e}", 'error')

    long_string = ''.join(saOutput)

    sFile = 'prepared_' + filename
    sFile = sPlate + '.txt'
    sOutFile = os.path.join('/', sDestDir, sFile)
    
    with open(sOutFile, 'w') as file:
        file.write(long_string)
    #self.printQcLog(f'Parsing {sFullFileName} into {sFile}')
    return sFile


def find_files(directory, filename_start, filename_end):
    matching_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith(filename_start) and file.endswith(filename_end):
                matching_files.append(os.path.join(root, file))
    return matching_files
            

def findHarmonyFiles(self, subdirectory_path, selected_directory):
    data = {
        "plate": [],
        "file": []
    }

    try:
        os.makedirs(subdirectory_path)
    except:
        pass

    # Harmony names all raw datafiles to 'PlateResults.txt'
    filename_start = 'PlateResults'
    filename_end = '.txt'
    harmony_files = find_files(selected_directory, filename_start, filename_end)

    pattern = re.compile(r'P\d{6}')
    assaylib.printPrepLog(self, f"Searching for Harmony files in {selected_directory}")
    for file_name in harmony_files:
        with open(file_name, 'r') as file:
            content = file.read()
            match = re.search(pattern, content)
            if match:
                sPlate = match.group()
                assaylib.printPrepLog(self, f"Found plate: {sPlate}")
                preparedFile = parseHarmonyFile(self, subdirectory_path, file_name, sPlate)

                data['plate'].append(sPlate)
                data['file'].append(preparedFile)
            else:
                assaylib.printPrepLog(self, f"No plate in {file_name}", 'error')

    sOutFile = os.path.join('/', subdirectory_path, "prepared_plate_to_file.xlsx")
    assaylib.printPrepLog(self, f'Created file to platemapping-file:\n{sOutFile}\n')
    df = pd.DataFrame(data)
    df = df.sort_values(by='plate')
    createPlatemap(self, df, subdirectory_path)
    excel_writer = pd.ExcelWriter(sOutFile, engine="openpyxl")
    df.to_excel(excel_writer, sheet_name="Sheet1", index=False)
    excel_writer.close()
