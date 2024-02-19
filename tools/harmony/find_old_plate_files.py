import os

def find_plate_results(directory):
    keywords = ['P103808', 'P103811', 'P103840', 'P103841', 'P103842', 'P103843', 'P103844', 'P103845', 'P103846', 'P103847', 'P103848', 'P103855', 'P103864', 'P103867', 'P103877', 'P103879', 'P103882', 'P103883', 'P103884', 'P103885', 'P103886', 'P103887', 'P103888', 'P103889', 'P103890', 'P103891', 'P103892', 'P103893', 'P103894', 'P103895', 'P103896', 'P103902', 'P103909', 'P103922', 'P103923', 'P103924', 'P103925', 'P103926', 'P103927', 'P103928', 'P103929', 'P103930']

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file == 'PlateResults.txt':
                filepath = os.path.join(root, file)
                print(filepath)
                with open(filepath, 'r') as f:
                    for line in f:
                        
                        if line.startswith('Plate Name'):
                            print(f'################## Found Plate ############# {line.strip()}')
                            for keyword in keywords:
                                if keyword in line:
                                    print("Filename:", filepath)
                                    print("Line containing 'Plate Name':", line.strip())
                                    break
                    break
# Specify the directory where you want to start searching
starting_directory = '.'



find_plate_results(starting_directory)


