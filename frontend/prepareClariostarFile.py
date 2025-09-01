import re
import os
import pandas as pd
import assaylib

def number_to_alphabet(sRow):
    if 1 <= sRow <= 26:
        alphabet_letter = chr(64 + sRow)
        return alphabet_letter
    else:
        return "Invalid input"

def parseClariostarFile(self, sDestDir, sFullFileName, sPlate):
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
                line = line.replace(',', '.')
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


def findClariostarFiles(self, subdirectory_path, selected_directory):
    data = {
        "plate": [],
        "file": []
    }

    try:
        os.makedirs(subdirectory_path)
    except:
        pass

    # Clariostar names all raw datafiles to 'PlateResults.txt'
    filename_start = 'PlateResults'
    filename_end = '.txt'
    clariostar_files = find_files(selected_directory, filename_start, filename_end)

    pattern = re.compile(r'P\d{6}')
    assaylib.printPrepLog(self, f"Searching for Clariostar files in {selected_directory}")
    iCount = 0
    for file_name in clariostar_files:
        with open(file_name, 'r') as file:
            content = file.read()
            match = re.search(pattern, content)
            if match:
                sPlate = match.group()
                assaylib.printPrepLog(self, f"{sPlate}")
                preparedFile = parseClariostarFile(self, subdirectory_path, file_name, sPlate)
                data['plate'].append(sPlate)
                data['file'].append(preparedFile)
                iCount += 1
            else:
                assaylib.printPrepLog(self, f"No plate in {file_name}", 'error')

    plateIdToFileMapping = os.path.join('/', subdirectory_path, "prepared_plate_to_file.xlsx")
    assaylib.printPrepLog(self, f'Created file to platemapping-file with {iCount} plates:')
    assaylib.printPrepLog(self, f'{plateIdToFileMapping}\n', type='bold')

    df = pd.DataFrame(data)
    df = df.sort_values(by='plate')
    sPlatemapFile = assaylib.createPlatemap(self, df, subdirectory_path)
    excel_writer = pd.ExcelWriter(plateIdToFileMapping, engine="openpyxl")
    df.to_excel(excel_writer, sheet_name="Sheet1", index=False)
    excel_writer.close()
    return sPlatemapFile, plateIdToFileMapping
