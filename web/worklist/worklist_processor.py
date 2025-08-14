import pandas as pd
import os
import csv
import random
import sys

### User Inputs
output_folder = "files/output"
# Create output folder if not exists
os.makedirs(output_folder, exist_ok=True)

### Functions

def generate_seed(run_seed = None):
    if not run_seed:
        run_seed = random.randrange(sys.maxsize)
    random.seed(run_seed)
    print(run_seed)

def read_excel_to_df(filename):
    try:
        dataframe = pd.read_excel(filename)
        return dataframe
    except FileNotFoundError:
        raise ValueError(f"File {filename} not found.")
    except ValueError as e:
        raise ValueError(f"Invalid file format: {e}")
    except Exception as e:
        raise ValueError(f"Unexpected error reading Excel file: {e}")

def condition_dict(dataframe):
    conditions = {}
    for i in range(0, 51):
        key = dataframe.iloc[i, 29]
        if pd.notna(dataframe.iloc[i,30]):
            value = dataframe.iloc[i,30:41].tolist()
            try:
                value[10] = int(value[10])
            except:
                raise ValueError("Wet sample amount must be a whole number or blank")
            conditions[key] = value
    return conditions

def separate_plates(dataframe):
    nbcode = dataframe.columns[1]
    pathway = dataframe.iloc[0,1] # Not used for anything currently, could be changed to a new variable
    if dataframe.iloc[1,1] == '1 column':
        lc_column_number = 1
    elif dataframe.iloc[1,1] == '2 column':
        lc_column_number = 2
    else:
        raise ValueError(
            f"System type must either be \"1 column\" or \"2 column\", but got {dataframe.iloc[2,0]}"
        )
    plates = {}
    for i in range(1,4): # plates 1-3
        if i == 1:
            name_row = 4
            row_min = 3
        elif i == 2:
            name_row = 22
            row_min = 21
        elif i == 3:
            name_row = 40
            row_min = 39
        name_values = dataframe.iloc[name_row, [0, 1]]
        name = "_".join(str(x).strip() for x in name_values if pd.notna(x))
        plate = dataframe.iloc[row_min:row_min+18, 3:28]

        # Validate plate values
        max_row = min(row_min + 18, len(dataframe))
        max_col = min(28, dataframe.shape[1])
        for r in range(row_min + 1, max_row):
            for c in range(4, max_col):
                val = dataframe.iloc[r, c]
                if pd.notna(val):
                    if not isinstance(val, (int, float)) or not float(val).is_integer() or not (1 <= int(val) <= 30):
                        raise ValueError(
                            f"Invalid well value '{val}' in plate '{name}' at row {r+1}, column {c+1}: "
                            "must be an integer between 1 and 30."
                        )


        plate.columns = plate.iloc[0, :] # Set column names as index
        plate.index = plate.iloc[:, 0] # Set row names as index
        plate = plate.iloc[1:, 1:]
        # with open (f"output/worklist/plate{i}.tsv", 'w') as outfile:
        #     plate.to_csv(outfile, sep = '\t')
        if plate.isna().all().all():
            # print(f"Plate {i} is empty (all NaN). Skipping.")
            continue
        plates[name] = plate
    
    num_to_run = {}
    for i in range(0, 51):
        if pd.notna(dataframe.iloc[i, 41]) & pd.notna(dataframe.iloc[i, 30]):
            if dataframe.iloc[i, 41] == 'all':
                num_to_run[dataframe.iloc[i, 29]] = dataframe.iloc[i, 41]
            else:
                try:
                    num_to_run[dataframe.iloc[i, 29]] = int(dataframe.iloc[i, 41])
                except ValueError:
                    raise ValueError("Number of samples to run must be a whole number or 'all'")
    return nbcode, pathway, lc_column_number, plates

def validate_and_convert_spacing(lst, name):
    converted = []
    for i, val in enumerate(lst):
        if isinstance(val, (int, float)) and float(val).is_integer():
            converted.append(int(val))
        else:
            raise ValueError(f"Invalid value in {name}[{i}]: {val} (not a whole number)")
    return converted

def spacing(dataframe):
    qc_spacing = validate_and_convert_spacing(dataframe.iloc[51:54, 30].tolist(), "qc_spacing")
    wet_qc_spacing = validate_and_convert_spacing(dataframe.iloc[54:57, 30].tolist(), "wet_qc_spacing")
    blank_spacing = validate_and_convert_spacing(dataframe.iloc[57:60, 30].tolist(), "blank_spacing")
    true_blank_spacing = validate_and_convert_spacing(dataframe.iloc[60:63, 30].tolist(), "true_blank_spacing")
    # Each of the spacing lists should have 3 values: before, after, between
    return [qc_spacing, wet_qc_spacing, blank_spacing, true_blank_spacing]

def process_plate(plate, plate_name, conditions):
    wells_list = []
    RGB = plate_name.split("_")[0]
    for r_idx, row_series in plate.iterrows():
        for c_idx, col_name in enumerate(plate.columns):
            if c_idx == 0:
                continue
            try:
                col_num = int(col_name)
            except ValueError:
                raise ValueError(f"Column name '{col_name}' is not convertible to int in plate '{plate_name}'")
            value = row_series[col_name]
            if pd.isna(row_series[col_name]):
                continue
            plate_location = f"{r_idx}{col_num}" # well location (e.g. A1)
            abs_location = RGB + plate_location
            for i in range(0, int(conditions[int(value)][10])):
                wells_list.append([int(value), abs_location]) # value, absolute location (e.g. RA1)
    #print(wells_list)
    return wells_list

def compare_wells_and_counts(wells_list, conditions, spacing):
    # attaches 'QC', 'Blank', 'TrueBlank' and 'Lib' to their number in conditions dictionary
    #QC_num = wet_QC_num = Blank_num = TrueBlank_num = Lib_num = None
    list_of_keys = list(conditions.keys())
    for key in list_of_keys:
        if conditions[key][0] == 'QC':
            QC_num = key
        if conditions[key][0] == 'WetQC':
            wet_QC_num = key
        if conditions[key][0] == 'Blank':
            Blank_num = key
        if conditions[key][0] == 'TrueBlank':
            TrueBlank_num = key
    #check that QC, Blank, and TrueBlank numbers align with before/between/after inputs
    total_QC = 0
    total_wet_QC = 0
    total_Blank = 0
    total_TrueBlank = 0
    for well in wells_list:
        if QC_num is not None and well[0] == QC_num:
            total_QC += 1
        if wet_QC_num is not None and well[0] == wet_QC_num:
            total_wet_QC += 1
        if Blank_num is not None and well[0] == Blank_num:
            total_Blank += 1
        if TrueBlank_num is not None and well[0] == TrueBlank_num:
            total_TrueBlank += 1
    # some checks
    if total_QC < (spacing[0][0] + spacing[0][1] + spacing[0][2]):
        raise ValueError ("Error: Number of dry QCs does not match between wells and excel sheet input.")
    if total_wet_QC * conditions[wet_QC_num][10] < (spacing[1][0] + spacing[1][1] + spacing[1][2]):
        raise ValueError ("Error: Number of wet QCs does not match between wells and excel sheet input.")
    if total_Blank * conditions[Blank_num][10] < (spacing[2][0] + spacing[2][1] + spacing[2][2]):
        raise ValueError ("Error: Number of blanks in wells does not match excel sheet input.")
    if total_TrueBlank * conditions[TrueBlank_num][10] < (spacing[3][0] + spacing[3][1] + spacing[3][2]):
        raise ValueError ("Error: Number of TrueBlanks in wells does not match excel sheet input.")
    return ("Alles gut und richtig")

def column_sorter(wells_list, conditions, spacings, lc_number): #split the wells list evenly between the two columns
    column1 = []
    column2 = []
    extras = [] # these are the odds ones out to attach at the end to run anyways if wanted
    nonsample_before = []
    nonsample_after = []
    nonsample_other = []

    # find number associated with each nonsample well type
    list_of_keys = list(conditions.keys())
    for key in list_of_keys:
        if conditions[key][0] == 'QC':
            QC_num = int(key)
        if conditions[key][0] == 'WetQC':
            wet_QC_num = int(key)
        if conditions[key][0] == 'Blank':
            Blank_num = int(key)
        if conditions[key][0] == 'TrueBlank':
            TrueBlank_num = int(key)
        if conditions[key][0] == 'Lib':
            Lib_num = int(key)

    # remove non sample wells into new list
    QC_list = []
    wet_QC_list = []
    Blank_list = []
    TrueBlank_list = []
    Lib_list = []
    for well in wells_list[:]:
        if int(well[0]) == QC_num:
            QC_list.append(well)
            wells_list.remove(well)
        elif well[0] == wet_QC_num:
            for i in range(conditions[wet_QC_num][10]):                        #### fix this ####
                # add wet QCs to the list for every uL in each well
                wet_QC_list.append(well)
            wells_list.remove(well)
        elif well[0] == Blank_num:
            Blank_list.append(well)
            wells_list.remove(well)
        elif well[0] == TrueBlank_num:
            TrueBlank_list.append(well)
            wells_list.remove(well)
        elif well[0] == Lib_num:
            Lib_list.append(well)
            wells_list.remove(well)


    # randomize the nonsamples
    random.shuffle(QC_list)
    random.shuffle(wet_QC_list)
    random.shuffle(Blank_list)
    random.shuffle(TrueBlank_list)
    random.shuffle(Lib_list)

    # move a well to 'extras' if a list has an odd number of wells and it uses a 2 column system
    if lc_number == 2:
        if len(QC_list) %2 != 0:
            extras.append(QC_list[-1:])
            QC_list = QC_list[:-1]
        if len(wet_QC_list) %2 != 0:
            extras.append(wet_QC_list[-1:])
            wet_QC_list = wet_QC_list[:-1]
        if len(Blank_list) %2 != 0:
            extras.append(Blank_list[-1:])
            Blank_list = Blank_list[:-1]
        if len(TrueBlank_list) %2 != 0:
            extras.append(TrueBlank_list[-1:])
            TrueBlank_list = TrueBlank_list[:-1]
        if len(Lib_list) %2 != 0:
            extras.append(Lib_list[-1:])
            Lib_list = Lib_list[:-1]

    # divide them into their respective nonsample lists based on user inputs
    # add nonsamples to 'nonsample_before' list
    if QC_list:
        nonsample_before.append(QC_list[:spacings[0][0]])
        QC_list = QC_list[spacings[0][0]:]
    if wet_QC_list:
        nonsample_before.append(wet_QC_list[:spacings[1][0]])
        wet_QC_list = wet_QC_list[spacings[1][0]:]
    if Blank_list:
        nonsample_before.append(Blank_list[:spacings[2][0]])
        Blank_list = Blank_list[spacings[2][0]:]
    if TrueBlank_list:
        nonsample_before.append(TrueBlank_list[:spacings[3][0]])
        TrueBlank_list = TrueBlank_list[spacings[3][0]:]
    if Lib_list:
        nonsample_before.append(Lib_list)

    # add nonsamples to 'nonsample_after' list
    if QC_list:
        nonsample_after.append(QC_list[:spacings[0][1]])
        QC_list = QC_list[spacings[0][1]:]
    if wet_QC_list:
        nonsample_after.append(wet_QC_list[:spacings[1][1]])
        wet_QC_list = wet_QC_list[spacings[1][1]:]
    if Blank_list:
        nonsample_after.append(Blank_list[:spacings[2][1]])
        Blank_list = Blank_list[spacings[2][1]:]
    if TrueBlank_list:
        nonsample_after.append(TrueBlank_list[:spacings[3][1]])
        TrueBlank_list = TrueBlank_list[spacings[3][1]:]

    # add nonsamples to 'nonsample_other' list
    if QC_list:
        nonsample_other.append(QC_list[:spacings[0][2]])
        QC_list = QC_list[spacings[0][2]:]
    if wet_QC_list:
        nonsample_other.append(wet_QC_list[:spacings[1][2]])
        wet_QC_list = wet_QC_list[spacings[1][2]:]
    if Blank_list:
        nonsample_other.append(Blank_list[:spacings[2][2]])
        Blank_list = Blank_list[spacings[2][2]:]
    if TrueBlank_list:
        nonsample_other.append(TrueBlank_list[:spacings[3][2]])
        TrueBlank_list = TrueBlank_list[spacings[3][2]:]

    ### handle divide sample lists into columns ###

    # remove the values from conditions dict that are in the between blocks
    sample_keys = list(conditions.keys())
    new_keys = sample_keys.copy()
    between_keys = [QC_num, Blank_num, TrueBlank_num, Lib_num, wet_QC_num]
    for sample in sample_keys:
        if sample in between_keys:
            new_keys.remove(sample)

    if lc_number == 2:
        sample_dict = {}
        for sample in new_keys:
            #Count number of sample wells in wells list
            count = 0
            for well in wells_list:
                if well[0] == sample:
                    count += 1
            sample_dict[sample] = [conditions[sample], count] # key is number from well plate, value is list containg
        # info from conditions then number of wells of that sample

        # put samples into respective lists and randomize lists
        for sample in sample_dict.keys(): # sample is an integer
            sample_list = []
            for well in wells_list:
                if sample == well[0]:
                    sample_list.append(well)
            # randomize list of wells
            random.shuffle(sample_list)
            # remove extra samples
            if len(sample_list) %2 != 0:
                extras.append(sample_list[-1:])
                sample_list = sample_list[:-1]
            # divide the samples evenly between the two columns
            even = True
            for sample in sample_list:
                if even == True:
                    column1.append(sample)
                    even = False
                elif even == False:
                    column2.append(sample)
                    even = True

        return (nonsample_before, nonsample_after, nonsample_other, column1, column2, extras)

    elif lc_number == 1:
        column1 = wells_list
        return (nonsample_before, nonsample_after, nonsample_other, column1)

def blocker(conditions, column1, column2 = None):
    # find which sample has the smallest amount
    # use that to make blocks of the correct numbers
    #print("column1")
    #print(column1)
    #print("column2")
    #print(column2)
    if column2:
        columns = [column1, column2]
    if not column2:
        columns = [column1]
    both_blocks = []
    extras_dict = {} #stores uneven samples so that the second column can use same block assignments
    for column in columns:
        sample_dict = {}
        for well in column:
            if well[0] not in sample_dict.keys():
                sample_dict[well[0]] = 1
            elif well[0] in sample_dict.keys():
                sample_dict[well[0]] += 1
        sample_amounts = list(sample_dict.values())
        sample_block_num = min(sample_amounts)

        sample_keys = list(sample_dict.keys())
        for sample in sample_keys:
            #Count number of sample wells in wells list
            count = 0
            for well in column:
                if well[0] == sample:
                    count += 1
            to_add = count // sample_block_num
            sample_dict[sample] = [conditions[sample], to_add, count]
        # create list of sample well blocks
        sample_blocks = []
        blocks_created = 0
        while blocks_created < sample_block_num:
            block = [] # create each block for the samples
            for sample in sample_dict.keys(): # go through each sample, create temporary list
                sample_list = []
                for well in column:
                    if well[0] == sample:
                        sample_list.append(well)
                block.extend(sample_list[:sample_dict[sample][1]])
            for item in block:
                if item in column:
                    column.remove(item)
            random.shuffle(block)
            sample_blocks.append(block)
            blocks_created += 1
        if blocks_created == sample_block_num:
            # assigns leftover samples randomly to blocks
            num_of_blocks = len(sample_blocks)
            for sample in sample_dict.keys(): # go through each sample, create temporary list
                sample_list = []
                for well in column:
                    if well[0] == sample:
                        sample_list.append(well)
                for item in sample_list:
                    if column == column1:
                        placement = random.randint(0, num_of_blocks-1)
                        sample_blocks[placement].append(item)
                        try:# extras_dict[item[0]]:
                            extras_dict[item[0]] += 1
                            extras_dict[item[0]][1].append(placement)
                        except KeyError:
                            extras_dict[item[0]] = [1,[]]
                            extras_dict[item[0]][1].append(placement)
                    else:
                        placement = extras_dict[item[0]][1][0]
                        sample_blocks[placement].append(item)
                        extras_dict[item[0]][0] -= 1
        for block in sample_blocks:
            random.shuffle(block)
        both_blocks.append(sample_blocks)
    # puts both columns into one list to be returned
        # if lc_number == 1:
        #     both_blocks =
    return(both_blocks, num_of_blocks)

def nonsample_blocker(nonsample_other, num_of_blocks, conditions):
    """ Will divide the QC, Blanks, Trueblanks etc, reserved to be between the runs, into blocks
        Make sure that number of nonsample blocks does not exceed number of sample blocks
        These blocks should not be randomized"""
    nonsample_other = [item for block in nonsample_other for item in block] # flattens list

    sample_dict = {}
    for well in nonsample_other:
        if well[0] not in sample_dict.keys():
            sample_dict[well[0]] = 1
        elif well[0] in sample_dict.keys():
            sample_dict[well[0]] += 1
    sample_amounts = list(sample_dict.values())
    nonsample_block_num = min(sample_amounts) // 2
    # '//2' ensures that nonsamples can come in pairs of two by
    # preventing blocks of only one of each nonsample condition

    # set 'sample_block_num' to correct number, max is one less than the sample_block number from 'blocker' function
    if num_of_blocks == 1:
        block_num = 1
    elif nonsample_block_num < num_of_blocks:
        block_num = nonsample_block_num
    elif nonsample_block_num >= num_of_blocks:
        block_num = num_of_blocks - 1

    sample_keys = list(sample_dict.keys())
    for sample in sample_keys:
        #Count number of sample wells in wells list
        count = 0
        for well in nonsample_other:
            if well[0] == sample:
                count += 1
        to_add = count // block_num
        if to_add == 1:
            raise ValueError("ValueError: If you want to include nonsample wells between sample/condition wells," \
            "you must include at least two of each.")
        sample_dict[sample] = [conditions[sample], to_add, count]
    nonsample_blocks = []
    blocks_created = 0
    while blocks_created < block_num:
        block = [] # create each block for the samples
        for sample in sample_dict.keys(): # go through each sample, create temporary list
            sample_list = []
            for well in nonsample_other:
                if well[0] == sample:
                    sample_list.append(well)
            block.extend(sample_list[:sample_dict[sample][1]])
        for item in block:
            if item in nonsample_other:
                nonsample_other.remove(item)
        #random.shuffle(block)
        nonsample_blocks.append(block)
        blocks_created += 1
    if blocks_created == block_num:
        # assigns leftover samples randomly to blocks
        num_of_blocks = len(nonsample_blocks)
        for sample in sample_dict.keys(): # go through each sample, create temporary list
            sample_list = []
            for well in nonsample_other:
                if well[0] == sample:
                    sample_list.append(well)
            for item in sample_list:
                placement = random.randint(0, num_of_blocks-1)
                nonsample_blocks[placement].append(item)
    return(nonsample_blocks)

def zipper(both_blocks): # zips column1 and column2 together
    if len(both_blocks) == 1:
        both_blocks = [item for block in both_blocks for item in block]
        return both_blocks
    else:
        column1 = both_blocks[0]
        column2 = both_blocks[1]
        sample_blocks = []
        max_length = max(len(column1), len(column2))
        for i in range(0, max_length):
            block = []
            for x in range(0, len(column1[i])):
                block.append(column1[i][x])
                block.append(column2[i][x])
            sample_blocks.append(block)
    return sample_blocks

# def zipper(both_blocks): # new zipper to make sure blocks are truly empty
#     if len(both_blocks) == 1:
#         both_blocks = [item for block in both_blocks for item in block]
#         return both_blocks
#     else:
#         column1 = both_blocks[0]
#         column2 = both_blocks[1]
#         sample_blocks = []
#         while len(column1) != 0 and len(column2) != 0:



def block_zipper(nonsample_before, nonsample_after, sample_blocks, non_sample_blocks):
    final_flat_list = []

    # Add the pre-block if provided
    if nonsample_before:
        final_flat_list.append(nonsample_before)

    total_blocks = len(sample_blocks) + len(non_sample_blocks)
    sample_i = 0
    nonsample_i = 0

    # Interleave using even spacing
    for i in range(total_blocks):
        # Compute where the next non-sample block *should* go based on spacing
        expected_nonsample_pos = (nonsample_i + 1) * total_blocks / (len(non_sample_blocks) + 1) if non_sample_blocks else float('inf')

        if i + 1 >= expected_nonsample_pos and nonsample_i < len(non_sample_blocks):
            final_flat_list.append([non_sample_blocks[nonsample_i]])
            nonsample_i += 1
        elif sample_i < len(sample_blocks):
            final_flat_list.append([sample_blocks[sample_i]])
            sample_i += 1

    # Add the post-block if provided
    if nonsample_after:
        final_flat_list.append(nonsample_after)

    return final_flat_list


def fully_flatten(final_list):
    while isinstance(final_list, list) and len(final_list) == 1 and isinstance(final_list[0], list):
        final_list = final_list[0]
    return [
        pair
        for block in final_list
        for group in block
        for pair in group
    ]

def rep_tracker(flattened, conditions):
    reps = []
    rep_counters = {}
    for well in flattened:
        if isinstance(well, list) and len(well) > 2:
            try:
                condition = int(well[0])
                if condition in conditions:
                    if condition not in rep_counters:
                        rep_counters[condition] = 1

                    elif condition in rep_counters:
                        rep_counters[condition] += 1
                    reps.append(rep_counters[condition])
                else:
                    raise KeyError(f"Condition {condition} not found in conditions dictionary.")
            except ValueError:
                raise ValueError(f"Invalid condition value '{well[0]}' in well {well}.")
        else:
            reps.append(None)  # If well is not a valid list or doesn't have enough elements
    return reps

def extract_file_info(non_flat_list, conditions):
    for index, block in enumerate(non_flat_list):
        index += 1
        for part in block:
            for well in part:
                if isinstance(well, list) and len(well) < 3:
                    well.append(f"blo{index}")
    flattened = fully_flatten(non_flat_list)
    well_conditions, block_runs, positions, reps, msmethods = [], [], [], [], []
    well_conditions.extend([int(w[0]) for w in flattened])
    block_runs.extend([w[2] for w in flattened])
    positions.extend([w[1] for w in flattened])
    reps = rep_tracker(flattened, conditions)
    msmethods.extend([conditions[int(w[0])][4] for w in flattened])
    return well_conditions, block_runs, positions, reps, msmethods

def create_filenames(lc_number, conditions, nbcode, well_conditions, block_runs, positions, reps, msmethods):
    # creates a list of filenames
    filenames = []
    if lc_number == 1:
        columns = ['nbcode', 'conditions', 'block and run', 'position', 'rep','msmethod']
    elif lc_number == 2:
        columns = ['nbcode', 'conditions', 'block and run', 'position', 'rep', 'channel', 'msmethod']
    df = pd.DataFrame(columns=columns)
    for index, block_run in enumerate(block_runs):
        try:
            condition = conditions[well_conditions[index]][1]
        except KeyError:
            raise KeyError(f"Condition {well_conditions[index]} not found in conditions dictionary.")
        if lc_number == 1:
            df.loc[len(df)] = [nbcode, condition, block_runs[index],
                      positions[index], f"rep{reps[index]}", msmethods[index]]
        elif lc_number == 2:
            df.loc[len(df)] = [nbcode, condition, block_runs[index],
                      positions[index], f"rep{reps[index]}", f"ch{(index%2)+1}", msmethods[index]]
    for _, row in df.iterrows():
        joined = "_".join(str(x).strip() for x in row if pd.notna(x))
        filenames.append(joined)
    return filenames

def create_instrument_methods(lc_number, methodpaths, methods, csv_file):
    inst_methods = []
    counter = 0
    for index, path in enumerate(methodpaths):
        if csv_file == 'LC':
            if lc_number == 2:
                if counter%2 == 0:
                    methods[index] = "ChannelA_" + methods[index]
                elif counter%2 == 1:
                    methods[index] = "ChannelB_" + methods[index]
        inst_methods.append("\\".join([path, methods[index]]))
        counter+=1
    return inst_methods

def create_csv_to_send(csv_file, conditions, nbcode, lc_number, blank_method, sample_type,
                       filenames, well_conditions, positions, inj_vol):
    # Create instrument methods for MS and LC
    method_paths = []
    method_names = []
    data_paths = []
    for index in well_conditions:
        if index not in conditions:
            raise KeyError(f"Condition {index} not found.")
        if len(conditions[index]) < 10:
            raise ValueError(f"Condition {index} is malformed: expected ≥10 fields, got {len(conditions[index])}.")

        if csv_file == 'MS':
            data_paths.append(conditions[index][2])
            method_paths.append(conditions[index][3])
            method_names.append(conditions[index][5])
        elif csv_file == 'LC':
            data_paths.append(conditions[index][6])
            method_paths.append(conditions[index][7])
            method_names.append(conditions[index][9])
    inst_methods = create_instrument_methods(lc_number, method_paths, method_names, csv_file)
    # Offset for 2 column system
    if lc_number == 2:
        filenames.insert(0, f"{nbcode}_Preblank2")
        filenames.insert(0, f"{nbcode}_Preblank1")
        data_paths.insert(0, data_paths[0])
        data_paths.insert(0, data_paths[0])
        if csv_file == 'MS':
            inst_methods.insert(0, blank_method)
            inst_methods.insert(0, blank_method)
        elif csv_file == 'LC':
            inst_methods.append(inst_methods[-1])
            inst_methods.append(inst_methods[-1])
        positions.append(positions[-1])
        positions.append(positions[-1])

    rows = []
    rows.append(['Bracket Type=4', '', '', '', '', ''])
    rows.append(['Sample Type', 'File Name', 'Path', 'Instrument Method', 'Position', 'Inj Vol'])
    for index, filename in enumerate(filenames):
        if index >= len(data_paths) or index >= len(inst_methods) or index >= len(positions):
            raise IndexError(f"More filenames than other fields when creating CSV.")
        rows.append([sample_type, filename, data_paths[index],
                        inst_methods[index], positions[index], inj_vol])

    # According to chatGPT, the following is the exact format excel would give,
    # which is what the undergrads use.
    output_path = f"{output_folder}/{nbcode}_{csv_file}_file_for_export.csv"

    with open(output_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=',', quotechar='"',
                            quoting=csv.QUOTE_MINIMAL, lineterminator='\r\n')
        writer.writerows(rows)

    return output_path

def generate_worklist(file):
    df = read_excel_to_df(file)
    generate_seed()
    if df.shape[0] < 51 or df.shape[1] < 40:
        raise ValueError("Input file must have at least 51 rows and 40 columns.")

    conditions = condition_dict(df)
    nbcode, pathway, lc_number, plates = separate_plates(df)

    spacings = spacing(df)

    sample_type = "Unknown"  # or "Sample", etc.
    blank_method = "Blank_Method"  # fill in with real method if needed
    inj_vol = 1  # injection volume in µL

    all_wells_flat = []

    for key in plates:
        all_wells_flat.extend(process_plate(plates[key], key, conditions))
    compare_wells_and_counts(all_wells_flat, conditions, spacings)
    if lc_number == 1:
        nonsample_before, nonsample_after, nonsample_other, column1 = column_sorter(all_wells_flat, conditions, spacings, lc_number)
        both_blocks, num_of_blocks = blocker(conditions, column1)
    elif lc_number == 2:
        nonsample_before, nonsample_after, nonsample_other, column1, column2, extras = column_sorter(all_wells_flat, conditions, spacings, lc_number)
        both_blocks, num_of_blocks = blocker(conditions, column1, column2)
    nonsample_blocks = nonsample_blocker(nonsample_other, num_of_blocks, conditions)
    sample_blocks = zipper(both_blocks)
    #print(both_blocks)
    non_flat_list = block_zipper(nonsample_before, nonsample_after, sample_blocks, nonsample_blocks)
    well_conditions, block_runs, positions, reps, msmethods = extract_file_info(non_flat_list, conditions)
    #print(non_flat_list)
    # # Build filenames
    filenames = create_filenames(lc_number, conditions, nbcode, well_conditions, block_runs, positions, reps, msmethods)
    # Create and export MS CSV
    ms_path = create_csv_to_send("MS", conditions, nbcode, lc_number, blank_method,
                       sample_type, filenames.copy(), well_conditions.copy(), positions.copy(), inj_vol)
    # Create and export LC CSV
    lc_path = create_csv_to_send("LC", conditions, nbcode, lc_number, blank_method,
                       sample_type, filenames.copy(), well_conditions.copy(), positions.copy(), inj_vol)
    #The files stored in files/output contain what needs to be sent to the mass spec and lc
    #print(lc_number)
    print("Worksheet generation complete! Check the 'files/output' folder for your CSVs.")
    return ms_path, lc_path