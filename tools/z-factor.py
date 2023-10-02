import numpy as np
import pandas as pd
import numpy
import matplotlib.pyplot as plt
import openpyxl
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.drawing.image import Image


import io

pd.set_option('mode.chained_assignment', None)


excel_file_path = 'screenresults.xlsx'
df = pd.read_csv("plate_Raw_data.csv", delimiter='\t')


def addPlotToSheet(ws, cell, plt):
    plt.seek(0)
    img = Image(plt)
    img.width = 1400  # Set the width of the image in Excel
    img.height = 700  # Set the height of the image in Excel
    ws.add_image(img, cell)

    
def calculatePlateData(df, plate, ws):
    dataDf = df.loc[df['Type'].isna()]
    posDf = df.loc[df['Type'] == 'Pos']
    negDf = df.loc[df['Type'] == 'Neg']

    meanInhib = dataDf['Raw_data'].mean()
    stdInhib = dataDf['Raw_data'].std()

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

    return df, Z, meanPosCtrl, stdPosCtrl, meanNegCtrl, stdNegCtrl, meanInhib, stdInhib


def plotData(values, stds, sHeader):
    x_values = range(1, len(values) + 1 )
    plt.errorbar(x_values, values, yerr=stds, fmt='o', capsize=5,
                 label='Value with Std Dev')

    # Add labels and title
    plt.xlabel('Plate')
    plt.ylabel('Value')
    plt.title(sHeader)
    
    # Add a legend
    plt.legend()
    plt.grid()

    image_buffer = io.BytesIO()
    plt.savefig(image_buffer, format='png', dpi=300, bbox_inches='tight')
    plt.close()
    return image_buffer


def calcData(df, ws):
    columns = ['Plate', 'meanRaw', 'stdRaw', 'meanNegCtrl', 'stdNegCtrl', 'meanPosCtrl', 'stdPosCtrl', 'Z-factor']
    df_summary = pd.DataFrame(columns=columns)
    df_inhibition = pd.DataFrame(columns=['inhibition'])
    df_inhibition_calculated = pd.DataFrame(columns=df.columns)
    
    for plate in df['plate'].unique():
        plate_df = df[df['plate'] == plate]
        (df_plate,
         Z,
         meanPosCtrl,
         stdPosCtrl,
         meanNegCtrl,
         stdNegCtrl,
         meanRaw,
         stdRaw) = calculatePlateData(plate_df, plate, ws)
        new_row = {'Plate': int(plate),
                   'meanRaw': meanRaw,
                   'stdRaw': stdRaw,
                   'meanNegCtrl': meanNegCtrl,
                   'stdNegCtrl': stdNegCtrl,
                   'meanPosCtrl': meanPosCtrl,
                   'stdPosCtrl': stdPosCtrl,
                   'Z-factor': Z}
        df_summary.loc[len(df_summary)] = new_row
        
        df_plate_inhibition = df_plate[(df_plate['Type'] != 'Neg') & (df_plate['Type'] != 'Pos')]
        df_inhibition = pd.concat([df_inhibition, df_plate_inhibition])
        df_inhibition_calculated = pd.concat([df_inhibition_calculated, df_plate])

    meanInhibition = df_inhibition['inhibition'].mean()
    stdInhibition = df_inhibition['inhibition'].std()
    hitLimit = meanInhibition + 3*stdInhibition
    minInhib = df_inhibition['inhibition'].min()
    maxInhib = df_inhibition['inhibition'].max()

    def calculate_hit(row):
        if row['inhibition'] is None:
            return 0
        elif row['inhibition'] > hitLimit:
            return 1
        else:
            return 0

    df_inhibition_calculated['hit'] = df_inhibition_calculated.apply(calculate_hit, axis=1)
    for row in dataframe_to_rows(df_inhibition_calculated, index=False, header=True):
        ws.append(row)

    ws['I1'] = f' Hit limit: {hitLimit}'
    ws['I2'] = f'Min inhib: {minInhib}'
    ws['I3'] = f'Max inhib: {maxInhib}'
    ws['I4'] = f'Mean inhib: {meanInhibition}'
    ws['I5'] = f'STD inhib: {stdInhibition}'
    '''
    print(minInhib)
    print(maxInhib)
    print(hitLimit)
    print(stdInhibition)
    print(meanInhibition)
    '''
    inhibPlt = plotData(df_summary['meanRaw'], df_summary['stdRaw'], 'Raw data')
    negPlt = plotData(df_summary['meanNegCtrl'], df_summary['stdNegCtrl'], 'NegCtrl')
    posPlt = plotData(df_summary['meanPosCtrl'], df_summary['stdPosCtrl'], 'PosCtrl')

    addPlotToSheet(ws, 'S1', inhibPlt)
    addPlotToSheet(ws, 'S40', negPlt)
    addPlotToSheet(ws, 'S80', posPlt)
    
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
