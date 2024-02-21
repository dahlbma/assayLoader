import os

# Old Plate = New Plate
oldToNewPlate = {'P103808':'P104378',
'P103811':'P104379',
'P103840':'P104380',
'P103841':'P104381',
'P103842':'P104382',
'P103843':'P104383',
'P103844':'P104384',
'P103845':'P104385',
'P103846':'P104386',
'P103847':'P104387',
'P103848':'P104388',
'P103855':'P104389',
'P103864':'P104390',
'P103867':'P104391',
'P103877':'P104392',
'P103879':'P104393',
'P103882':'P104394',
'P103883':'P104395',
'P103884':'P104396',
'P103885':'P104397',
'P103886':'P104398',
'P103887':'P104399',
'P103888':'P104400',
'P103889':'P104401',
'P103890':'P104402',
'P103891':'P104403',
'P103892':'P104404',
'P103893':'P104405',
'P103894':'P104406',
'P103895':'P104407',
'P103896':'P104408',
'P103902':'P104409',
'P103909':'P104410',
'P103922':'P104411',
'P103923':'P104412',
'P103924':'P104413',
'P103925':'P104414',
'P103926':'P104415',
'P103927':'P104416',
'P103928':'P104417',
'P103929':'P104418',
'P103930':'P104419'}


def find_plate_results(directory):
    keywords = ['P103808', 'P103811', 'P103840', 'P103841', 'P103842', 'P103843', 'P103844', 'P103845', 'P103846', 'P103847', 'P103848', 'P103855', 'P103864', 'P103867', 'P103877', 'P103879', 'P103882', 'P103883', 'P103884', 'P103885', 'P103886', 'P103887', 'P103888', 'P103889', 'P103890', 'P103891', 'P103892', 'P103893', 'P103894', 'P103895', 'P103896', 'P103902', 'P103909', 'P103922', 'P103923', 'P103924', 'P103925', 'P103926', 'P103927', 'P103928', 'P103929', 'P103930']

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file == 'PlateResults.txt':
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    for line in f:
                        
                        if line.startswith('Plate Name'):
                            for keyword in keywords:
                                if keyword in line:
                                    dir_name, file_name = os.path.split(filepath)
                                    new_file_name = os.path.join(dir_name, 'old_' + file_name)
                                    print(f"################### New Plate: {oldToNewPlate[keyword]} Old Plate: {line.strip()} Filename:{new_file_name}", )
                                    os.rename(filepath, new_file_name)
                                    break
                    break
# Specify the directory where you want to start searching
starting_directory = './vicky'



find_plate_results(starting_directory)



