import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Alignment
import openpyxl

outFile = 'colored_cells.xlsx'

def generate_gradient(end_color, start_color, num_steps):
    # Parse the start and end colors into RGB components
    start_r = int(start_color[1:3], 16)
    start_g = int(start_color[3:5], 16)
    start_b = int(start_color[5:7], 16)

    end_r = int(end_color[1:3], 16)
    end_g = int(end_color[3:5], 16)
    end_b = int(end_color[5:7], 16)

    # Calculate the step size for each RGB component
    r_step = (end_r - start_r) / num_steps
    g_step = (end_g - start_g) / num_steps
    b_step = (end_b - start_b) / num_steps

    # Generate the gradient colors and store them in a list
    gradient = []
    for i in range(num_steps + 1):
        r = int(start_r + i * r_step)
        g = int(start_g + i * g_step)
        b = int(start_b + i * b_step)
        color_hex = "{:02X}{:02X}{:02X}".format(r, g, b)
        gradient.append(color_hex)

    return gradient

# Generate the gradient from white to blue in 10 steps
gradient_white_to_blue = generate_gradient(start_color="#0000FF", end_color="#FFFFFF", num_steps=10)

# Generate the gradient from white to red in 10 steps
gradient_white_to_red = generate_gradient(start_color="#FF0000", end_color="#FFFFFF", num_steps=10)

print(gradient_white_to_red)

# Create a sample DataFrame with integers between 1 and 100
data = {'Values': range(1, 101)}
df = pd.DataFrame(data)

# Create a Pandas Excel writer using openpyxl
writer = pd.ExcelWriter(outFile, engine='openpyxl')
df.to_excel(writer, sheet_name='Sheet1', index=False)

writer.close()



workbook = openpyxl.load_workbook(outFile)
worksheet = workbook['Sheet1']


# Create a blue-to-red gradient fill for cells
gradient_fill = PatternFill(start_color="0000FF", end_color="FF0000", fill_type="solid")

# Iterate through the cells in the 'Values' column
for row_idx, row in enumerate(worksheet.iter_rows(min_row=2, max_row=len(df) + 1, min_col=1, max_col=1)):
    cell = row[0]
    value = cell.value
    # Apply the gradient fill based on the integer value
    if isinstance(value, int) and 1 <= value <= 100:
        
        percentage = (value - 1) / 99  # Normalize value to range [0, 1]
        #color = gradient_fill.start_color.rgb
        #red = int(int(color[2:], 16) + percentage * (int(gradient_fill.end_color.rgb[2:], 16) - int(color[2:], 16)))
        #blue= int(int(color[:2], 16) + percentage * (int(gradient_fill.end_color.rgb[:2], 16) - int(color[:2], 16)))
        #print(int(color[2:], 16), percentage, percentage * (int(gradient_fill.end_color.rgb[2:], 16)), (gradient_fill.end_color.rgb[2:], 16), int(color[2:], 16))
        #print(int(color[2:], 16), int(color[:2], 16), int(gradient_fill.end_color.rgb[:2], 16))
        #green = 0
        #fill_color = f"{blue:02X}{green:02X}{red:02X}"
        
        #print(value, red, blue, fill_color)
        #print(fill_color)
        if value < 11:
            cell.fill = PatternFill(start_color=gradient_white_to_red[value], end_color=gradient_white_to_red[value], fill_type="solid")
        elif value > 90:
            print(value)
            cell.fill = PatternFill(start_color=gradient_white_to_blue[100-value], end_color=gradient_white_to_blue[100-value], fill_type="solid")

    # Center-align the cell contents
    cell.alignment = Alignment(horizontal='center', vertical='center')


#workbook.close()
workbook.save(outFile)

# Save the workbook
#writer.close()
