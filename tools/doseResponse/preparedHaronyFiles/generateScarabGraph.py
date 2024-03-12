import pandas as pd
import math

sTemplate = """{{{{name = 'raw'
style = 'dot'
x_lable = 'conc'
x_unit = 'M'
x_values = {}
y_label = 'Inhibition'
y_unit = '%'
y_values = {}
y_error = {}
}}
{{name = 'fitsigmoidal'
style = 'dot'
x_lable = 'conc'
x_unit = 'M'
x_values = {}
y_label = 'Inhibition'
y_unit = '%'
logic50={}
hillslope={}
bottom={}
top={}
}}}}
"""

# Define the 4-PL model function
def fourpl(x, slope, ic50, bottom, top):
    return bottom + (top - bottom) / (1 + (x / ic50)**slope)

ic50 = 8.134780465561142e-06
slope = -3.1686899815408385
top = 119.99999999999999
bottom = -1.1167663135143078

df = pd.read_csv('dr.csv')

yMean_string = '{' + ', '.join(str(value) for value in df['yMean']) + '}'
yStd_string = '{' + ', '.join(str(value) for value in df['yStd']) + '}'
xvalues_string = '{' + ', '.join(str(value/1000000000) for value in df['finalConc_nM']) + '}'

logic50 = math.log(ic50, 10)


sRaw = sTemplate.format(xvalues_string, yMean_string, yStd_string, xvalues_string, logic50, slope*-1, bottom, top)
print(sRaw)


print(df)

'''
{{name='raw' style='dot' x_label='conc' x_unit='M'
x_values={4.00E-05,1.33E-05,4.44E-06,1.48E-06,4.94E-07,1.65E-07,5.49E-08,1.83E-08,6.10E-09,2.03E-09,6.77E-10}
y_label='Inhibition' y_unit='%'
y_values={20.65,23.25,26.64,21.33,18.27,19.07,14.42,10.97,11.03,9.40,14.51}
y_error={3.54,4.30,1.70,3.58,2.84,0.07,2.44,1.59,2.69,1.85,3.06} }

{name='fitsigmoidal' style='line' x_label='conc' x_unit='M'
x_values={4.00E-05,1.33E-05,4.44E-06,1.48E-06,4.94E-07,1.65E-07,5.49E-08,1.83E-08,6.10E-09,2.03E-09,6.77E-10}
y_label='inhibition' y_unit='%' logic50=-6.8044 hillslope=1.13 bottom=11.3 top=23}}

{
   {
      name='raw' style='dot' x_label='conc' x_unit='M'
      x_values={1.25E-04, 4.17E-05, 1.39E-05, 4.63E-06, 1.54E-06, 5.14E-07, 1.71E-07, 5.72E-08, 1.91E-08, 6.35E-09, 2.12E-09 }
      y_label='Inhibition'
      y_unit='%'
      y_values={105.07, 94.19, 65.84, 23.12, 1.48, -9.46, -13.04, -11.79, -10.53, -12.85, -15.35 }
      y_error={0.42, 1.23, 3.24, 2.85, 1.32, 1.18, 0.28, 0.93, 1.27, 1.53, 1.12 }
   }{
      name='fitsigmoidal' style='line' x_label='conc' x_unit='M'
      x_values={1.25E-04, 4.17E-05, 1.39E-05, 4.63E-06, 1.54E-06, 5.14E-07, 1.71E-07, 5.72E-08, 1.91E-08, 6.35E-09, 2.12E-09 }
      y_label='inhibition'
      y_unit='%'
      logic50=-5.0512
      hillslope=1.252
      bottom=-12.8
      top=109.6
   }
}
'''
