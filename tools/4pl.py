import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import os
os.environ["XDG_SESSION_TYPE"] = "xcb"


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
x_data = np.array([0.1, 1, 10, 100, 1000, 10000, 100000])
y_data = np.array([0.041, 0.1, 0.3, 0.6, 0.9, 0.9, 1.100])


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
