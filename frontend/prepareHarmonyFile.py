import re
import os

def number_to_alphabet(sRow):
    if 1 <= sRow <= 26:
        alphabet_letter = chr(64 + sRow)
        return alphabet_letter
    else:
        return "Invalid input"


def parseHarmonyFile(self, sDir, sFileName):
    pattern = r'(\d+)\t(\d+)'    
    saOutput = []
    iLine = 0
    
    try:
        with open(sDir + '/' + sFileName, 'r') as file:
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
        self.printPrepLog(f"File '{sFileName}' not found.", 'error')
    except Exception as e:
        self.printPrepLog(f"An error occurred: {e}", 'error')

    long_string = ''.join(saOutput)

    sFile = 'prepared_' + sFileName
    sOutFile = os.path.join('/', sDir, sFile)
    
    with open(sOutFile, 'w') as file:
        file.write(long_string)
    self.printPrepLog(f'Parsing {sFileName} into {sFile}')
    return sFile

