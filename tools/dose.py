import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import os
import json

# Define the 4-PL model function
def fourpl(x, slope, ic50, bottom, top):
    return bottom + (top - bottom) / (1 + (x / ic50)**slope)

# Function to calculate Hill slope
def calculate_hill_slope(a):
    return a

# Function to calculate IC50
def calculate_ic50(a, b, c, d):
    return b

file_path = "Dose_response_Query.csv"

try:
    with open(file_path, 'r') as file:
        # Read the file line by line
        for line_number, line in enumerate(file, start=1):

            # Parse the line as JSON
            try:
                data_dict = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON in line {line_number}: {e}")
                continue

            # Extract the 'x' and 'y' arrays
            x_values = np.array(data_dict.get('x', []))
            y_values = np.array(data_dict.get('y', []))
            
            print('############################')
            try:
                oldHillParams = data_dict.get('Hill', [])
            except:
                print(f'Failed with old Hill values')
                print(data_dict)
                continue
            oldBottom = oldHillParams['bottom']
            oldTop = oldHillParams['top']
            oldSlope = oldHillParams['slope']
            oldIC50 = oldHillParams['IC50']
            print(data_dict.get('Hill', []))
            print(oldBottom)

            try:
                top = np.max(y_values)
                bottom = np.min(y_values)
                # Fit the data to the 4-PL model                               slope  ic50  bottom  top
                #a=0.8317, b=0.0000, c=86.0716, d=2.1349
                #params, covariance = curve_fit(fourpl, x_values, y_values, p0=[bottom, np.mean(x_values), top, 0.8])
                params, covariance = curve_fit(fourpl, x_values, y_values, p0=[0, np.mean(x_values), 0, 100])
                #print(f'covariance: {covariance}')
            except:
                print('''Can't fit parameters''')
                continue

            # Extract the fitted parameters
            a_fit, b_fit, c_fit, d_fit = params

            # Calculate the Hill slope
            hill_slope = calculate_hill_slope(a_fit)

            # Calculate the IC50
            ic50 = calculate_ic50(a_fit, b_fit, c_fit, d_fit)


            # Extract the fitted parameters
            a_fit, b_fit, c_fit, d_fit = params
            
            ## Calculate the Hill slope
            #hill_slope = calculate_hill_slope(a_fit)
            
            ## Calculate the IC50
            #ic50 = calculate_ic50(a_fit, b_fit, c_fit, d_fit)
            
            # Generate a curve using the fitted parameters
            x_curve = np.logspace(np.log10(min(x_values)), np.log10(max(x_values)), 100)
            y_curve_fit = fourpl(x_curve, a_fit, b_fit, c_fit, d_fit)
            y_old_fit = fourpl(x_curve, oldSlope, oldIC50, oldTop, oldBottom)


            # Plot the original data and the fitted curve with a logarithmic x-axis
            plt.scatter(x_values, y_values, label='Original Data')
            plt.plot(x_curve, y_curve_fit, label='Fitted 4-PL Curve')
            plt.plot(x_curve, y_old_fit, label='Old Fitted 4-PL Curve')
            if ic50 > 0.001:
                plt.axvline(ic50, color='r', linestyle='--', label=f'IC50 = {ic50:.2f} M')
                plt.axvline(oldIC50, color='g', linestyle='--', label=f'Old IC50 = {oldIC50:.2f} M')
            else:
                plt.axvline(ic50, color='r', linestyle='--', label=f'IC50 = {ic50*1e6:.2f} uM')
                plt.axvline(oldIC50, color='g', linestyle='--', label=f'Old IC50 = {oldIC50*1e6:.2f} M')
            plt.xscale('log')  # Set x-axis to logarithmic scale
            plt.xlabel('Concentration')
            plt.ylabel('Response')
            plt.legend()

            # Print the fitted parameters, Hill slope, and IC50
            print(f"Fitted Parameters: a={a_fit:.4f}, b={b_fit:.4f}, c={c_fit:.4f}, d={d_fit:.4f}")
            print(f"Hill Slope: {hill_slope:.4f}")
            print(f"IC50: {ic50:.2e}")
            
            plt.show()





            
            #print(f"Line {line_number}:")
            #print("x values:", x_values)
            #print("y values:", y_values)
            #print()

except FileNotFoundError:
    print(f"Error: File '{file_path}' not found.")
except Exception as e:
    print(f"Error: {e}")


