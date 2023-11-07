import re
import os

def number_to_alphabet(sRow):
    if 1 <= sRow <= 26:
        alphabet_letter = chr(64 + sRow)
        return alphabet_letter
    else:
        return "Invalid input"


def parseHarmonyFile(sDir, sFileName):
    pattern = r'(\d+)\t(\d+)'    
    saOutput = []
    iLine = 0
    
    try:
        with open(sDir + '/' + sFileName, 'r') as file:
            lines = file.readlines()
            for line in lines:
                iLine += 1
                if line.startswith("Row\tColumn"):
                    saOutput.append(line.replace("Row\tColumn", 'Well'))
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
                    saOutput.append(output_string)

    except FileNotFoundError:
        print(f"File '{sFileName}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

    long_string = ''.join(saOutput)

    sFile = 'prepared_' + sFileName
    sOutFile = os.path.join('/', sDir, sFile)
    
    with open(sOutFile, 'w') as file:
        file.write(long_string)
    print(f'Parsing {sFileName} into {sOutFile}')
    return sFile

