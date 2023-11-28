import re
import os

def number_to_alphabet(sRow):
    if 1 <= sRow <= 26:
        alphabet_letter = chr(64 + sRow)
        return alphabet_letter
    else:
        return "Invalid input"


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
        self.printQcLog(f"File '{sFullFileName}' not found.", 'error')
        return ""
    except Exception as e:
        self.printPrepLog(f"An error occurred: {e}", 'error')

    long_string = ''.join(saOutput)

    sFile = 'prepared_' + filename
    sFile = sPlate + '.txt'
    sOutFile = os.path.join('/', sDestDir, sFile)
    
    with open(sOutFile, 'w') as file:
        file.write(long_string)
    self.printQcLog(f'Parsing {sFullFileName} into {sFile}')
    return sFile

