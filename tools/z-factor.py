import numpy as np
import pandas as pd
import numpy
import matplotlib.pyplot as plt
import openpyxl
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

import io

pd.set_option('mode.chained_assignment', None)


excel_file_path = 'screenresults.xlsx'
df = pd.read_csv("plate_Raw_data.csv", delimiter='\t')


def calculatePlateData(df, plate, ws):
    posDf = df.loc[df['Type'] == 'Pos']
    negDf = df.loc[df['Type'] == 'Neg']

    meanPosCtrl = posDf['Raw_data'].mean()
    stdPosCtrl = posDf['Raw_data'].std()

    meanNegCtrl = negDf['Raw_data'].mean()
    stdNegCtrl = negDf['Raw_data'].std()

    pos3SD = 3 * stdPosCtrl
    neg3SD = 3 * stdNegCtrl

    Z = 1 - (pos3SD + neg3SD)/abs(meanPosCtrl - meanNegCtrl)
    
    condition = (df['Type'] == 'Neg') | (df['Type'] == 'Pos')
    df['inhibition'] = np.where(condition, None, 100*(1-(df['Raw_data']-meanPosCtrl)/(meanNegCtrl-meanPosCtrl)))

    df['negCtrlInhibition'] = np.where(df['Type'] == 'Neg', 100*(1-(df['Raw_data']-meanPosCtrl)/(meanNegCtrl-meanPosCtrl)), None)
    df['posCtrlInhibition'] = np.where(df['Type'] == 'Pos', 100*(1-(df['Raw_data']-meanPosCtrl)/(meanNegCtrl-meanPosCtrl)), None)

    lHeader = False
    if plate == 1:
        lHeader = True
    for row in dataframe_to_rows(df, index=False, header=lHeader):
        ws.append(row)

    return df, Z, meanPosCtrl, stdPosCtrl, meanNegCtrl, stdNegCtrl


def calcData(df, ws):
    columns = ['Plate', 'meanNegCtrl', 'stdNegCtrl', 'meanPosCtrl', 'stdPosCtrl', 'Z-factor']
    df_summary = pd.DataFrame(columns=columns)

    for plate in df['plate'].unique():
        plate_df = df[df['plate'] == plate]
        df_plate, Z, meanPosCtrl, stdPosCtrl, meanNegCtrl, stdNegCtrl = calculatePlateData(plate_df, plate, ws)
        new_row = {'Plate': int(plate),
                   'meanNegCtrl': meanNegCtrl,
                   'stdNegCtrl': stdNegCtrl,
                   'meanPosCtrl': meanPosCtrl,
                   'stdPosCtrl': stdPosCtrl,
                   'Z-factor': Z}
        df_summary = df_summary.append(new_row, ignore_index=True)

        print(f'Z for plate {plate} = {Z}')

    print(df_summary)
    start_column = 'J'

    # Convert the DataFrame to rows and write them to the Excel sheet
    for r_idx, row in enumerate(dataframe_to_rows(df_summary, index=False, header=True), 1):
        for c_idx, value in enumerate(row, 1):
            cell = ws.cell(row=r_idx, column=c_idx + ord(start_column) - ord('A'))
            cell.value = value



wb = Workbook()
ws = wb.active
ws.title = 'ScreenDataAnalysis'
calcData(df, ws)

for column in ws.columns:
    max_length = 0
    column_letter = column[0].column_letter  # Get the column letter
    for cell in column:
        try:
            if len(str(cell.value)) > max_length:
                max_length = len(cell.value)
        except:
            pass
    adjusted_width = max(max_length + 2, 10)  # Minimum width of 10 characters
    ws.column_dimensions[column_letter].width = adjusted_width


wb.save(excel_file_path)








'''
100*(1-(A31-J216)/(G24-J216)))

Percent Inhibition:
100 * (1- (DataPoint - AVG(PosCtrl))/(AVG(NegCtrl)-AVG(PosCtrl)))

NegCtrl, 0% Control (F24):
100 * (1-(NegCtrlDataPoint-AVG(PosCtrl)) /(Avg(NegCtrl) - AVG(PosCtrl)))


PosCtrl, 100% Ctrl, 100*(1-(A25-J216)/(G24-J216)))
I25:


StdDev(NegCtrl): H24
G24 = Avg(NegCtrl)
J216 = AVG(PosCtrl)
K216 = STD(PosCtrl)

# Create a new workbook and select the active sheet
workbook = openpyxl.Workbook()
sheet = workbook.active
sheet.title = "Heatmap"


# Set the background color of cell A1 to red
cell = sheet['A1']
red_fill = PatternFill(start_color='FFFF0000', end_color='FFFF0000', fill_type='solid')
cell.fill = red_fill

# Save the workbook to a file
workbook.save('screenresults.xlsx')


'''
