import numpy as np
import pandas as pd
import numpy
import matplotlib.pyplot as plt
import openpyxl
from openpyxl.styles import PatternFill
import io


df = pd.read_csv("plate_Raw_data.csv", delimiter='\t')


def calculateZfactor(df):
    posDf = df.loc[df['Type'] == 'Pos']
    negDf = df.loc[df['Type'] == 'Neg']

    mean_pos = posDf['Raw_data'].mean()
    std_pos = posDf['Raw_data'].std()

    mean_neg = negDf['Raw_data'].mean()
    std_neg = negDf['Raw_data'].std()

    pos3SD = 3 * std_pos
    neg3SD = 3 * std_neg

    Z = 1 - (pos3SD + neg3SD)/abs(mean_pos - mean_neg)
    return Z


for plate in df['plate'].unique():
    # Create a new DataFrame for the current category
    plate_df = df[df['plate'] == plate]
    z = calculateZfactor(plate_df)
    print(f'Z for {plate} = {z}')
    # Store the category DataFrame in the dictionary
    #category_dataframes[category] = category_df





'''
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
'''





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
