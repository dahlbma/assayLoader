import os
import numpy as np
import pandas as pd
import openpyxl
from openpyxl import Workbook


def getDataStart(file, sDataColumn):
    lines = file.readlines()
    for line in lines:
        saLine = line.split(',')

        if sDataColumn in saLine:
            if 'PlateNumber' in saLine:
                dataPosition = saLine.index(sDataColumn)
                print(dataPosition)


# Directory path where your CSV files are located
directory_path = 'screen_raw_data'

# List all files in the directory
file_list = [file for file in os.listdir(directory_path) if file.endswith('.csv')]

# Read each CSV file and store it in the list
for csv_file in file_list:
    file_path = os.path.join(directory_path, csv_file)
    with open(file_path, 'r') as file:
        getDataStart(file, 'Signal')
