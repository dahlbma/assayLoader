import numpy as np
import matplotlib.pyplot as plt
from itertools import product
import pandas as pd


BOUNDS = {
    'slope': {'MIN': -90.1, 'MAX': 100},
    'ic50': {'MIN': 5.00e-08, 'MAX': 0.01},
    'top': {'MIN': 129, 'MAX': 300},
    'bot': {'MIN': 0.0, 'MAX': 5}
}


parameters = ['grad_slope', 'grad_ic50', 'grad_bottom', 'grad_top']

# Generate all possible combinations of signs (+ or -)
sign_combinations = product([-1, 0, 1], repeat=len(parameters))

# List to store permutations of parameter values
permutations = []

# Loop through each sign combination
for signs in sign_combinations:
    # Create a dictionary to hold the parameter values for this combination of signs
    params = {}
    # Loop through each parameter and assign the value with the corresponding sign
    for param, sign in zip(parameters, signs):
        params[param] = sign
        # Append the parameter values to the permutations list
    permutations.append(params)

def calculate_distr(val, x):
    distr = []
    lower_bound = val - 0.2 * val
    upper_bound = val + 0.2 * val
    distr =  [lower_bound, val, upper_bound]
    return distr

def getLinReg(x, y):
    # Remove the last element in the arrays
    if len(x) > 3:
        x = x[:-1]
        y = y[:-1]
    elif len(x) == 1:
        return 1, y[0]

    # Perform linear regression
    coefficients = np.polyfit(x, y, 1)
    slope, intercept = coefficients  # m is the slope, b is the intercept

    # Create fitted line
    fitted_line_x = np.linspace(min(x), max(x), 100)
    fitted_line_y = slope * fitted_line_x + intercept

    # Find the x value where (max(y) - min(y))/2 occurs
    midpoint_y = ((max(y) - min(y)) / 2) + intercept
    # Use numpy's interp function to find the corresponding x value
    x_midpoint = np.interp(midpoint_y, y, x)

    if slope > 0:
        slope = 1
    else:
        slope = -1
    return slope, x_midpoint


def check_bounds(val, param):
    min = BOUNDS[param]['MIN']
    max = BOUNDS[param]['MAX']

    if val > max: return max
    if val < min: return min

    return val


def sigmoid_derivative(x, slope, ic50, bottom, top):
    """Derivative of the 4PL sigmoid function."""
    exponent = slope * np.log(x / ic50)
    denominator = (1 + np.exp(exponent))**2
    return (top - bottom) * slope * (1 / x) * (x / ic50)**slope / denominator


# Step 1: Define the 4-PL model
def four_parameter_logistic(x, slope, ic50, bottom, top):
    return bottom + (top - bottom) / (1 + (x / ic50) ** -slope)

# Step 2: Define the cost function
def cost_function(y_true, y_pred):
    return ((y_true - y_pred) ** 2).mean()

# Step 3: Compute the gradient analytically
def compute_gradient(iCount, x, y, slope, ic50, bottom, top, learning_rate):
    # Compute predictions
    y_pred = four_parameter_logistic(x, slope, ic50, bottom, top)
    #print(f'y_pred {y_pred}')
    # Compute errors
    error = abs_error = cost_function(y, y_pred)
    print(f'error: {abs_error}')

    if abs_error < 10:
        learning_rate *= 0.95
    
    # Compute partial derivatives of the cost function with respect to each parameter
    grad_slope = (2 / len(x)) * np.sum(error * ((top - bottom) / (1 + (x / ic50) ** -slope) ** 2) * (1 + (x / ic50) ** -slope))
    grad_ic50 = (2 / len(x)) * np.sum(error * ((top - bottom) / (1 + (x / ic50) ** -slope) ** 2) * (-slope * (x / ic50) ** -(-slope - 1)) * (-x / (ic50 ** -2)))
    grad_bottom = (2 / len(x)) * np.sum(error)
    grad_top = (2 / len(x)) * np.sum(error * (1 / (1 + (x / ic50) ** -slope)))

    #print(f'grad_top {grad_top} grad_slope: {grad_slope} grad_bottom: {grad_bottom} grad_ic50: {grad_ic50}')
    return grad_slope, grad_ic50, grad_bottom, grad_top, learning_rate

# Step 4: Update parameters using gradient descent
def update_parameters(iCount, x, y, slope, ic50, bottom, top, learning_rate, ic50_step):
    # Compute gradients
    #grad_slope, grad_ic50, grad_bottom, grad_top, learning_rate = compute_gradient(iCount, x, y, slope, ic50, bottom, top, learning_rate)

    y_pred = four_parameter_logistic(x, slope, ic50, bottom, top)
    org_error = old_error = abs_error = cost_function(y, y_pred)

    best_slope = slope
    best_ic50 = ic50
    best_bottom = bottom
    best_top = top

    if iCount < 2:
        old_error *= 2
    
    for perm in permutations:
        # Optimized parameters:
        # Tested slope:0.015 ic50:0.5 bottom:0.5 top:2.5 -> avg RMSE: 1402.6
        new_slope = check_bounds(slope - learning_rate * 0.015 * perm['grad_slope'], 'slope')
        new_ic50 = check_bounds(ic50 - learning_rate * ic50_step * 0.5 * perm['grad_ic50'], 'ic50')
        new_bottom = check_bounds(bottom - learning_rate * 0.5 * perm['grad_bottom'], 'bot')
        new_top = check_bounds(top - learning_rate * 2.5 * perm['grad_top'], 'top')

        x_div_ic50 = x / new_ic50
        # Inline 4-parameter logistic function
        y_pred = new_bottom + (new_top - new_bottom) / (1 + x_div_ic50 ** -new_slope)
        #y_pred = four_parameter_logistic(x, new_slope, new_ic50, new_bottom, new_top)
        error = cost_function(y, y_pred)
        if error < old_error:
            best_slope = new_slope
            best_ic50 = new_ic50
            best_bottom = new_bottom
            best_top = new_top
            old_error = error
    stop = False
    if org_error == old_error:
        stop = True
    if abs_error < 10:
        learning_rate *= 0.94
    else:
        learning_rate = learning_rate * 0.995
    #ic50_step = ic50_step * 0.99
    return best_slope, best_ic50, best_bottom, best_top, learning_rate, stop, abs_error

# Step 5: Implement gradient descent
def gradient_descent(x, y, learning_rate, num_iterations, slope, ic50, bottom, top):
    ic50_step = ic50
    old_rmse = np.inf
    x_curve = np.logspace(np.log10(min(x)), np.log10(max(x)), 100)
    iCount = 0

    for _ in range(num_iterations):
        iCount += 1
        # Compute predictions
        y_pred = four_parameter_logistic(x, slope, ic50, bottom, top)
        
        # Compute gradients (analytically or numerically)
        new_slope, new_ic50, new_bottom, new_top, learning_rate, lStop, rmse = update_parameters(iCount,
                                                                                                 x,
                                                                                                 y,
                                                                                                 slope,
                                                                                                 ic50,
                                                                                                 bottom,
                                                                                                 top,
                                                                                                 learning_rate,
                                                                                                 ic50_step)
        if abs(old_rmse - rmse) < 1:
            learning_rate *= 0.98
        if lStop:
            learning_rate = learning_rate / 1.1
        if learning_rate < 0.001:
            break
        
        # Update parameters using gradient descent
        slope = new_slope
        ic50 = new_ic50
        ic50 = abs(ic50)
        bottom = new_bottom
        top = new_top
        if rmse < old_rmse:
            old_rmse = rmse
        
        #print(f'slope:{slope} ic50:{ic50} bottom:{bottom} top:{top}')
        y_curve_fit = four_parameter_logistic(x_curve, slope, ic50, bottom, top)
        
    return slope, ic50, bottom, top, rmse, iCount

def fit_curve(x, y):
    BOUNDS['top']['MIN'] = max(y) * 0.7
    BOUNDS['top']['MAX'] = max(y) * 1.8
    BOUNDS['bot']['MIN'] = min(min(y) - 0.4 * abs(min(y)), -50)
    BOUNDS['bot']['MAX'] =  min(y) + 0.4 * abs(min(y))
    BOUNDS['ic50']['MIN'] = min(x) * 0.7
    BOUNDS['ic50']['MAX'] = max(x) * 1.5

    BOUNDS['slope']['MIN'] = -30
    BOUNDS['slope']['MAX'] = 30

    learning_rate = 10
    num_iterations = 2000

    slope, ic50 = getLinReg(x, y)
    bottom, top = min(y), max(y)

    slopes = calculate_distr(slope, x)
    tops = calculate_distr(max(y), x)
    bottoms = calculate_distr(min(y), x)
    ic50s = x

    min_cost = float('inf')
    best_combination = None

    # Iterate over all combinations of parameters
    for slope_val in slopes:
        for ic50_val in ic50s:
            for bottom_val in bottoms:
                for top_val in tops:
                    # Calculate y_pred using four_parameter_logistic function
                    y_pred = four_parameter_logistic(x, slope_val, ic50_val, bottom_val, top_val)
                    # Calculate cost using cost_function
                    cost = cost_function(y, y_pred)
                    #print(f'#######\ncost {cost}\nslope_val {slope_val}\n ic50_val {ic50_val}\n bottom_val {bottom_val}\n top_val {top_val}\n')
                    # Check if current combination gives lower cost
                    if cost < min_cost:
                        min_cost = cost
                        best_combination = (slope_val, ic50_val, bottom_val, top_val)
                    
    slope = best_combination[0]
    ic50 = best_combination[1]
    bottom = best_combination[2]
    top = best_combination[3]

    slope, ic50, bottom, top, rmse, iCount = gradient_descent(x,
                                                y,
                                                learning_rate,
                                                num_iterations,
                                                slope,
                                                ic50/10,
                                                bottom,
                                                top)
    
    der_bottom = sigmoid_derivative(x[0], slope, ic50, bottom, top)
    der_top = sigmoid_derivative(x[-1], slope, ic50, bottom, top)
    der_ic50 = sigmoid_derivative(ic50, slope, ic50, bottom, top)

    derivative_ic50_div_top = 0
    derivative_ic50_div_bot = 0
    try:
        derivative_ic50_div_top = der_ic50 / der_top
    except Exception:
        derivative_ic50_div_top = 0
    try:
        derivative_ic50_div_bot = der_ic50 / der_bottom
    except Exception:
        derivative_ic50_div_bot = 0

    #sInfo = f'''RMSE: {"{:.1f}".format(rmse)}\nIteration: {iCount}\n {"{:.1f}".format(der_bottom)}\n{"{:.1f}".format(der_ic50)}\n{"{:.1f}".format(der_top)}\n{"{:.1f}".format(derivative_ic50_div_bot)}\n{"{:.1f}".format(derivative_ic50_div_top)}'''
    sInfo = f'''RMSE: {"{:.1f}".format(rmse)}\nIteration: {iCount}\nDer bot: {"{:.1f}".format(derivative_ic50_div_bot)}\nDer top: {"{:.1f}".format(derivative_ic50_div_top)}'''
    return -slope, ic50, bottom, top, sInfo, derivative_ic50_div_bot, derivative_ic50_div_top
    
if __name__ == "__main__":

    # Read the tab-separated file
    df = pd.read_excel('finalPreparedDR.xlsx')
    df['finalConc_nM'] /= 1000000
    df.drop(columns=['Batch nr', 'yMean', 'yStd'], inplace=True)

    # Group by 'Compound_id' and aggregate the 'Conc' and 'Inhibition' columns
    grouped = df.groupby('Compound ID').agg(lambda x: tuple(x))

    # Save the transformed data to a CSV file
    grouped.to_csv('transformed.csv', sep='\t')

    BOUNDS = {
        'slope': {'MIN': -90.1, 'MAX': 100},
        'ic50': {'MIN': 5.00e-08, 'MAX': 0.01},
        'top': {'MIN': 80, 'MAX': 300},
        'bot': {'MIN': -3.0, 'MAX': 10}
    }

    parameters = ['grad_slope', 'grad_ic50', 'grad_bottom', 'grad_top']

    # Generate all possible combinations of signs (+ or -)
    sign_combinations = product([-1, 0, 1], repeat=len(parameters))

    # List to store permutations of parameter values
    permutations = []

    # Loop through each sign combination
    for signs in sign_combinations:
        # Skip the all-zeros permutation
        if all(sign == 0 for sign in signs):
            continue

        # Create a dictionary to hold the parameter values for this combination of signs
        params = {}
        # Loop through each parameter and assign the value with the corresponding sign
        for param, sign in zip(parameters, signs):
            params[param] = sign
            # Append the parameter values to the permutations list
        permutations.append(params)

    iPlotNr = 0
    with open('transformed.csv', 'r') as file:
        # Skip the header line
        next(file)

        # Iterate over each line
        for line in file:
            iPlotNr += 1
            print(f'Plot nr: {iPlotNr}')
            # Split the line based on the tab character
            parts = line.strip().split('\t')
            # Extract compound ID
            compound_id = parts[0]
            # Convert concentrations to a numpy array of floats
            conc = np.array([float(value) for value in parts[1].strip("()").split(", ")])
            # Convert y values to a numpy array of floats
            y_val = np.array([float(value) for value in parts[-1].strip("()").split(", ")])
        
            # Print or do whatever you want with the variables
            print("Compound ID:", compound_id)
            print("Concentration:", conc)
            print("Y Value:", y_val)
            (slope, ic50, bottom, top, sInfo, derivative_ic50_div_bot, derivative_ic50_div_top) = fit_curve(conc, y_val)
            print(f'slope: {-slope} ic50: {ic50} bottom: {bottom} top: {top}')
            print(f'sInfo: {sInfo}')




            param_ranges = {
                'slope': np.linspace(slope * 0.5, slope * 1.5, 50),
                'ic50': np.linspace(ic50 * 0.5, ic50 * 1.5, 50),
                'bottom': np.linspace(bottom - abs(bottom) * 0.5, bottom + abs(bottom) * 0.5, 50),
                'top': np.linspace(top - abs(top) * 0.5, top + abs(top) * 0.5, 50)
            }

            fixed_params = {'slope': slope, 'ic50': ic50, 'bottom': bottom, 'top': top}
            x = conc
            y = y_val

            for param in ['slope', 'ic50', 'bottom', 'top']:
                costs = []
                for val in param_ranges[param]:
                    params = fixed_params.copy()
                    params[param] = val
                    y_pred = four_parameter_logistic(x, params['slope'], params['ic50'], params['bottom'], params['top'])
                    cost = cost_function(y, y_pred)
                    costs.append(cost)
                plt.figure()
                plt.plot(param_ranges[param], costs)
                plt.xlabel(param)
                plt.ylabel('RMSE')
                plt.title(f'RMSE vs {param} for {compound_id}')
                plt.show()





            fig, ax = plt.subplots(figsize=(7, 5))
            ax.set_xscale('log')
            ax.scatter(conc, y_val, label=compound_id)
            ax.set_xlabel('Concentration (M)')
            ax.set_ylabel('Inhibition (%)')
            ax.set_title('Inhibition vs Concentration')
            ax.set_ylim(min(-5, np.min(y_val)-5), max(100, np.max(y_val)+3))  # Set y-axis from 0 to max(y_val) or 100, whichever is greater
            x_curve = np.logspace(np.log10(min(conc)), np.log10(max(conc)), 100)
            y_curve_fit = four_parameter_logistic(x_curve, -slope, ic50, bottom, top)
            ax.plot(x_curve, y_curve_fit, label=f'Fit {compound_id}')
            ax.legend()
            plt.show()  # This will block until you close the window
            plt.close(fig)  # Close the figure to free memory
            print('##########################################################')            #quit()

    #plt.ioff()  # Disable interactive mode
    #plt.show()  # Show all plots at the end (optional)
