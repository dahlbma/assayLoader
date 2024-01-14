import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import os
os.environ["XDG_SESSION_TYPE"] = "xcb"



'''
{"x":[5.00E-05,2.50E-05,1.25E-05,6.25E-06,3.13E-06,1.56E-06,7.81E-07,3.91E-07,1.95E-07,9.77E-08,4.88E-08],
"y":[18.44,35.11,2.88,24.96,-6.15,-5.70,0.44,10.67,-12.45,6.33,-5.37],
"yErr":[1.03,22.95,31.44,22.88,22.62,15.60,15.14,26.54,24.09,5.25,0.35],
"Hill":{"top":20.3,"bottom":-1,"slope":103.609,"IC50":4.821698e-6}}


{"x":[1.56E-04,7.80E-05,3.90E-05,1.95E-05,9.75E-06,4.88E-06,2.44E-06,1.22E-06,6.09E-07,3.05E-07,1.52E-07],
"y":[99.08,98.25,94.71,84.24,61.81,40.18,23.30,13.93,9.33,5.16,-2.04],
"yErr":[0.49,0.83,1.10,1.09,0.30,2.45,0.77,0.51,1.33,0.95,1.53],
"Hill":{"top":102.8, "bottom":2, "slope":1.277, "IC50":6.842267e-6}}


{"x":[5.00E-05,2.50E-05,1.25E-05,6.25E-06,3.13E-06,1.56E-06,7.81E-07,3.91E-07,1.95E-07,9.77E-08,4.88E-08],
"y":[77.37,73.55,52.81,42.33,26.02,26.57,19.16,20.49,6.12,6.38,20.28],
"yErr":[3.85,3.74,4.05,1.09,3.10,5.43,8.35,1.54,10.92,12.11,2.43],
"Hill":{"top":94.6,"bottom":12.5,"slope":1.003,"IC50":0.000011}}

'''






# Define the 4-PL model function
def fourpl(x, a, b, c, d):
    return c + (d - c) / (1 + (x / b)**a)

# Function to calculate Hill slope
def calculate_hill_slope(a):
    return a

# Function to calculate IC50
def calculate_ic50(a, b, c, d):
    return b

# Generate example data
x_data = [1.56E-04,7.80E-05,3.90E-05,1.95E-05,9.75E-06,4.88E-06,2.44E-06,1.22E-06,6.09E-07,3.05E-07,1.52E-07][::-1]
x_data = [value * 10000000 for value in x_data]
x_data = np.array(x_data, dtype=float)

y_data = [99.08,98.25,94.71,84.24,61.81,40.18,23.30,13.93,9.33,5.16,-2.04][::-1]
y_data = np.array(y_data)

#x_data = np.array([5.00E-05,2.50E-05,1.25E-05,6.25E-06,3.13E-06,1.56E-06,7.81E-07,3.91E-07,1.95E-07,9.77E-08,4.88E-08][::-1], dtype=float)
#x_data = [value * 1000000 for value in x_data]
#y_data = np.array([18.44,35.11,2.88,24.96,-6.15,-5.70,0.44,10.67,-12.45,6.33,-5.37][::-1], dtype=float)

#x_data = np.array([0.1, 1, 10, 100, 1000, 10000, 100000])
#x_data = np.array([1.0E-06, 0.00001, 0.0001, 0.001, 0.01, 0.1, 1, 10])
#y_data = np.array([0.041, 0.1, 0.3, 0.6, 0.9, 0.9, 1.100, 1.104])


# Fit the data to the 4-PL model
params, covariance = curve_fit(fourpl, x_data, y_data, p0=[1, 3, 0, 1])
#params, covariance = curve_fit(fourpl, x_data, y_data)

# Extract the fitted parameters
a_fit, b_fit, c_fit, d_fit = params

# Calculate the Hill slope
hill_slope = calculate_hill_slope(a_fit)

# Calculate the IC50
ic50 = calculate_ic50(a_fit, b_fit, c_fit, d_fit)

# Generate a curve using the fitted parameters
x_curve = np.logspace(np.log10(min(x_data)), np.log10(max(x_data)), 100)
y_curve_fit = fourpl(x_curve, a_fit, b_fit, c_fit, d_fit)



# Plot the original data and the fitted curve with a logarithmic x-axis
plt.scatter(x_data, y_data, label='Original Data')
plt.plot(x_curve, y_curve_fit, label='Fitted 4-PL Curve')
plt.axvline(ic50, color='r', linestyle='--', label=f'IC50 = {ic50:.4f}')
plt.xscale('log')  # Set x-axis to logarithmic scale
plt.xlabel('Dose or Concentration (log scale)')
plt.ylabel('Response')
plt.legend()

# Print the fitted parameters, Hill slope, and IC50
print(f"Fitted Parameters: a={a_fit:.4f}, b={b_fit:.4f}, c={c_fit:.4f}, d={d_fit:.4f}")
print(f"Hill Slope: {hill_slope:.4f}")
print(f"IC50: {ic50:.4f}")

plt.show()



quit()



###################################################





from lmfit.models import LinearModel, StepModel
from lmfit import Model

x = np.array([1.0E-06, 0.00001, 0.0001, 0.001, 0.01, 0.1, 1, 10])
y = np.array([0.041, 0.1, 0.3, 0.6, 0.9, 0.9, 1.100, 1.104])


def func(x, u, s, l, i):
    return u + (l-u)/(1.0+((x/i)**s))

fmodel = Model(func)

params = fmodel.make_params(u=1, i=50, s=-1, l=0.00)
params['i'].min=0

result = fmodel.fit(y, params, x=x)

print(result.fit_report())

plt.plot(x, y, 'o', label='data')
plt.plot(x, result.best_fit, 'ro', label='fit')
plt.xscale('log')
plt.legend()
plt.show()





#####################################################
import neutcurve


curve = neutcurve.HillCurve(x, y)

print(
    f"The top (t) is {curve.top:.3g}\n"
    f"The bottom (b) is {curve.bottom:.3g}\n"
    f"The midpoint (m) is {curve.midpoint:.3g}\n"
    f"The slope (Hill coefficient)s is {curve.slope:.3g}"
)

fig, ax = curve.plot(xlabel="concentration (ug/ml)")
fig.show()

print(round(curve.r2, 3))
