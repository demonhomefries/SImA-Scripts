"""
E407.4 order:
1. draq7
2. dapi
3. phase
4. high contrast phase
5. confocal tritc
6. confocal dapi
"""

channel_presets = {
"Confocal DRAQ7": {
    "ChannelName": "DRAQ7",
    "Color": "#dd00ff",
    "AcquisitionType": "Confocal",
    "ChannelType": "Fluoresence"},

"Nonconfocal DAPI": {
    "ChannelName": "DAPI",
    "Color": "#0035ff",
    "AcquisitionType": "NonConfocal",
    "ChannelType": "Fluoresence"},

"Confocal DAPI": {
    "ChannelName": "DAPI",
    "Color": "#0035ff",
    "AcquisitionType": "Confocal",
    "ChannelType": "Fluoresence"},

"NonConfocal Bright Field": {
    "ChannelName": "Bright Field",
    "Color": "#888a8c",
    "AcquisitionType": "NonConfocal",
    "ChannelType": "Fluoresence"},

"NonConfocal Bright Field-High Contrast": {
    "ChannelName": "Bright Field-High Contrast",
    "Color": "#48494a",
    "AcquisitionType": "NonConfocal",
    "ChannelType": "Fluoresence"},

"Confocal Texas Red": {
    "ChannelName": "Texas Red",
    "Color": "#ed0707",
    "AcquisitionType": "Confocal",
    "ChannelType": "Fluoresence"},

"Confocal GFP": {
    "ChannelName": "GFP",
    "Color": "#07ed07",
    "AcquisitionType": "Confocal",
    "ChannelType": "Fluoresence"},

"Confocal CY5": {
    "ChannelName": "CY5",
    "Color": "#dd00ff",
    "AcquisitionType": "Confocal",
    "ChannelType": "Fluoresence"},

"Confocal TRITC": {
    "ChannelName": "TRITC", 
    "Color": "#ed0707",
    "AcquisitionType": "Confocal",
    "ChannelType": "Fluoresence"},
}

import tifffile
import xml.etree.ElementTree as ET
import json
from PIL import Image
import os
import xmltodict
from datetime import datetime
import csv

def get_input_output():
    print("\nPress Ctrl + C to exit anytime.")
    tiff_filepaths = []
    while True:
        input_directory = input("\nINPUT - Enter an input folder with aligned kinetic stacks to split/generate a SImA Upload CSV: ")
        if not os.path.isdir(input_directory):
            print(f"ERROR: The folder '{input_directory}' does not exist.")
            continue
        else:
            # Walk through the directory and get .tif files
            for root, dirs, files in os.walk(input_directory):
                for file in files:
                    if file.endswith(".tif") or file.endswith(".tiff"):
                        tiff_filepaths.append(os.path.join(root, file))
            if not len(tiff_filepaths) > 0:
                print(f"ERROR: The folder '{input_directory}' does not contain any .tif files, please try again.")
                continue
            else:
                break

    while True:
        output_directory = input("\nOUTPUT - Enter an folder to output the CSV and split stacks: ")
        if not os.path.isdir(output_directory):
            print(f"ERROR: The folder '{output_directory}' does not exist, try again.")
            continue
        else:
            break

    
    return tiff_filepaths, output_directory

def well_id_to_row_col(well_id):
    rows = "ABCDEFGHIJKLMNOP"
    
    row_letter = well_id[0].upper()
    column_number = int(well_id[1:])
    row_number = rows.index(row_letter) + 1
    
    return row_number, column_number

def convert_date_format(date_str):
    date_obj = datetime.strptime(date_str, '%m/%d/%y')
    formatted_date = date_obj.strftime('%Y-%m-%dT%H:%M:%SZ')
    unix_time = int(date_obj.timestamp())
    return formatted_date, unix_time

def clean_dict_keys(d):
    """Recursively remove '@' from keys in a dictionary."""
    if isinstance(d, dict):
        return {k.lstrip('@'): clean_dict_keys(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [clean_dict_keys(i) for i in d]
    else:
        return d

def extract_ome_metadata_as_dict(tiff_path):
    with tifffile.TiffFile(tiff_path) as tif:
        #print(f"TIFF File: {tiff_path}")
        #print(f"Number of pages (frames): {len(tif.pages)}\n")
        
        # Check for OME metadata
        if tif.ome_metadata:
            #print("\nOME Metadata Found")
            # Convert OME XML to dictionary
            ome_dict = xmltodict.parse(tif.ome_metadata)
            
            # Clean the dictionary keys to remove '@' from attribute names
            cleaned_ome_dict = clean_dict_keys(ome_dict)
            
            return cleaned_ome_dict
        else:
            print("No OME metadata found.")
            return None

def get_metadata_info(image_metadata):
    plateName = image_metadata["OME"]["StructuredAnnotations"]["XMLAnnotation"]["Value"]["BTIImageMetaData"]["ImageReference"]["Plate"]
    channelName = image_metadata["OME"]["StructuredAnnotations"]["XMLAnnotation"]["Value"]["BTIImageMetaData"]["ImageAcquisition"]["Channel"]["Color"]
    emissionWavelength = image_metadata["OME"]["StructuredAnnotations"]["XMLAnnotation"]["Value"]["BTIImageMetaData"]["ImageAcquisition"]["Channel"]["EmissionWavelength"]
    excitationWavelength = image_metadata["OME"]["StructuredAnnotations"]["XMLAnnotation"]["Value"]["BTIImageMetaData"]["ImageAcquisition"]["Channel"]["ExcitationWavelength"]

    num_channels = image_metadata["OME"]["Image"]["Pixels"]["SizeC"]
    num_timepoints = image_metadata["OME"]["Image"]["Pixels"]["SizeT"]
    imageWidth = image_metadata["OME"]["Image"]["Pixels"]["SizeX"]
    imageHeight = image_metadata["OME"]["Image"]["Pixels"]["SizeY"]

    objectiveMagnification = image_metadata["OME"]["StructuredAnnotations"]["XMLAnnotation"]["Value"]["BTIImageMetaData"]["ImageAcquisition"]["ObjectiveSize"]
    objectiveNA = image_metadata["OME"]["StructuredAnnotations"]["XMLAnnotation"]["Value"]["BTIImageMetaData"]["ImageAcquisition"]["NumericalAperture"]

    positionX = image_metadata["OME"]["StructuredAnnotations"]["XMLAnnotation"]["Value"]["BTIImageMetaData"]["ImageReference"]["HorizontalTotal"]
    positionY = image_metadata["OME"]["StructuredAnnotations"]["XMLAnnotation"]["Value"]["BTIImageMetaData"]["ImageReference"]["HorizontalTotal"]
    # Calculated/Derived
    verticalTotal = image_metadata["OME"]["StructuredAnnotations"]["XMLAnnotation"]["Value"]["BTIImageMetaData"]["ImageReference"]["VerticalTotal"]
    horizTotal = image_metadata["OME"]["StructuredAnnotations"]["XMLAnnotation"]["Value"]["BTIImageMetaData"]["ImageReference"]["HorizontalTotal"]
    numFields = int(verticalTotal) * int(horizTotal)

    exposureTimeMS = image_metadata["OME"]["StructuredAnnotations"]["XMLAnnotation"]["Value"]["BTIImageMetaData"]["ImageAcquisition"]["ShutterSpeedMS"]
    exposureTimeS = int(exposureTimeMS) / 1000

    measurementDate = image_metadata["OME"]["StructuredAnnotations"]["XMLAnnotation"]["Value"]["BTIImageMetaData"]["ImageReference"]["Date"]
    measurementDate, absoluteTime = convert_date_format(measurementDate)

    wellID = image_metadata["OME"]["StructuredAnnotations"]["XMLAnnotation"]["Value"]["BTIImageMetaData"]["ImageReference"]["Well"]
    row, column = well_id_to_row_col(wellID)


    objectiveSizeInt = int(objectiveMagnification)
    if objectiveSizeInt == 4:
        resolution = "1.6286"
    elif objectiveSizeInt == 10:
        resolution = "0.6500"
    elif objectiveSizeInt == 20:
        resolution = "0.3250"
    elif objectiveSizeInt == 40:
        resolution = "0.1612"
    elif objectiveSizeInt == 60:
        resolution = "0.1082"
    resolutionX = resolution
    resolutionY = resolution

    field = "1"
    plane = "1"
    channel = ""
    timeOffset = "0"
    orientationMatrix = "[[1,0,0],[0,1,0],[0,0,1]]"
    acquisitionType = ""
    # Replaced later:
    sourceFilename = ""
    timepoint = ""
    channelColor = "#0035FF"
    channelType = "Fluoresence"


    return plateName, measurementDate, row, column, field, timepoint, plane, channel, channelName, channelColor,channelType, resolutionX, resolutionY, exposureTimeS, emissionWavelength, excitationWavelength, positionX, positionY, timeOffset, absoluteTime, imageWidth, imageHeight, numFields, num_timepoints, objectiveMagnification, objectiveNA, acquisitionType, orientationMatrix, sourceFilename, wellID

def split_stack_channels_timepoints(tiff_filepath, image_metadata, channel_names_inorder, output_directory, create_well_folder):

    plateName, measurementDate, row, column, field, timepoint, plane, channel, channelName, channelColor, channelType, resolutionX, resolutionY, exposureTimeS, emissionWavelength, excitationWavelength, positionX, positionY, timeOffset, absoluteTime, imageWidth, imageHeight, numFields, num_timepoints, objectiveMagnification, objectiveNA, acquisitionType, orientationMatrix, sourceFilename, well_ID = get_metadata_info(image_metadata)
    if create_well_folder:
        output_directory = os.path.join(output_directory, well_ID)
        if not os.path.isdir(output_directory):
            os.mkdir(output_directory)

    output_filepaths = []
    time_point_index = 0
    channel_name_index = 0
    
    with Image.open(tiff_filepath) as img:
        

        channel_name_index_max = len(channel_names_inorder)

        num_frames = img.n_frames
        time_point_index_max = int(num_frames / channel_name_index_max)

        if num_frames % channel_name_index_max != 0:
            print(f"ERROR split_stack_channels_timepoints: The number of frames ({num_frames}) divided by number of channels ({channel_name_index_max}) was not zero-divisible for {tiff_filepath}.\n\tCannot split stack evenly without matching number of frames and number of channels")
            exit()

        for i in range(num_frames):

            # Save the frame with correct channel and time point
            channel_prefix = channel_names_inorder[channel_name_index][0]
            
            field_num = 1
            read_step = "RS"
            output_filename = f"{well_ID}_{read_step}_{channel_name_index + 1}_{field_num}_{channel_prefix}_{time_point_index+1:03d}.tif" 
            output_filepath = os.path.join(output_directory, output_filename)
            
            img.seek(i)
            img.save(output_filepath)
            print(f"\tSaved frame {i+1} as {output_filename}")

            # Create the metadata tuples and output
            sourceFilename = output_filename 
            acquisitionType = channel_names_inorder[channel_name_index][1]
            timepoint = time_point_index + 1
            channel = channel_name_index + 1
            channelColor = channel_names_inorder[channel_name_index][2]
            channelName = channel_names_inorder[channel_name_index][0]

            metadata_tuple = (plateName, measurementDate, row, column, field, timepoint, plane, channel, channelName, channelColor, channelType, resolutionX, resolutionY, exposureTimeS, emissionWavelength, excitationWavelength, positionX, positionY, timeOffset, absoluteTime, imageWidth, imageHeight, numFields, num_timepoints, objectiveMagnification, objectiveNA, acquisitionType, orientationMatrix, sourceFilename)

            output_filepaths.append(metadata_tuple)

            # Increment indices and reset if necessary
            channel_name_index = (channel_name_index + 1) % channel_name_index_max
            if channel_name_index == 0:  # This means channel_name_index has reset
                time_point_index = (time_point_index + 1) % time_point_index_max
        
            
    return output_filepaths

def create_append_SIMA_CSV(filepath, data):
    headers = [
        "PlateName", "MeasurementDate", "Row", "Column", "Field", "Timepoint", "Plane", "Channel",
        "ChannelName", "ChannelColor", "ChannelType", "ImageResolutionX@um", "ImageResolutionY@um", 
        "ExposureTime[s]", "MainEmissionWavelength@nm", "MainExcitationWavelength@nm", 
        "PositionX@um", "PositionY@um", "TimeOffset@s", "AbsoluteTime@s", "ImageWidth", 
        "ImageHeight", "NumberOfFields", "NumberOfTimepoints", "ObjectiveMagnification", 
        "ObjectiveNA", "AcquisitionType", "OrientationMatrix", "SourceFilename"
    ]
    
    try:
        with open(filepath, mode='a+', newline='') as file:
            writer = csv.writer(file)
            
            file.seek(0)
            if file.read(1) == '':
                writer.writerow(headers)
            
            writer.writerows(data)

    except Exception as e:
        print(f"ERROR create_append_SIMA_CSV: {e}")

def colored_text(text, hex_color):
    # Remove '#' if present in the hex string
    hex_color = hex_color.lstrip('#')
    
    # Convert the hex color to RGB
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    # Return the colored text string with ANSI escape codes
    return f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m{text}\033[0m"
    
def get_channel_settings(image_metadata, channel_presets):
    num_channels = int(image_metadata["OME"]["Image"]["Pixels"]["SizeC"])

    channel_names = list(channel_presets.keys())
    print("\n")

    for channelName_index, channel in enumerate(channel_names):
        acquisitionType = channel_presets[channel_names[channelName_index]]["AcquisitionType"]
        hex_color = channel_presets[channel_names[channelName_index]]["Color"]
        print(colored_text(f"{channelName_index + 1}. {channel:<40} {acquisitionType:<15} {hex_color:<10}", hex_color))

    print(f"\nEnter the number of your channel ID for the {num_channels} channels in each stack (e.g. Enter \"6\" for Confocal Texas Red)")

    chosen_channel_ids = []
    for i in range (0, num_channels):
        while True:
            channel_id = input(f"\nChannel {i+1} ID: ")

            if not channel_id.isdigit():
                print("WARNING: Your entry was not a number, please try again:\n")
                continue
            else:
                channel_id = int(channel_id)
            
            if not (((channel_id - 1) >= 0) and ((channel_id - 1) <= len(channel_names))):
                print("WARNING: Your entry was not in range of the available options, please try again:\n")
                continue
            
            chosen_channel_name = channel_names[channel_id-1]
            chosen_channel_ids.append((i, chosen_channel_name))
            print(f"\tChannel {i+1} is {channel_names[channel_id - 1]}")
            break
    
    return chosen_channel_ids


print("\n\n\nCAUTION: All the tifs in your input directory must have the same number of separate \nimage channels or else the split naming convention will not be accurate to the actual channel.\n")
# Get the inputs and outputs
tiff_filepath_list, output_directory = get_input_output()
print(f"\n\nSelected input contains {len(tiff_filepath_list)} tifs to be processed.\nSelected output: {output_directory}")


# Select a tiff to make sure everything checks out
test_tiff_filepath = tiff_filepath_list[0]
if not os.path.isfile(test_tiff_filepath):
    print(f"\n\nERROR {test_tiff_filepath} is not a valid tiff file. Check to make sure it exists.")
    exit()
if not test_tiff_filepath.endswith(".tif"):
    print(f"\n\nERROR {test_tiff_filepath} is not a tiff file. Enter a .tif filepath and retry.\n")
    exit()
image_metadata = extract_ome_metadata_as_dict(test_tiff_filepath)
if image_metadata is None:
    print(f"ERROR extract_ome_metadata_as_dict: No OME Metadata was found for {test_tiff_filepath}. Exiting script...")
    exit()


image_metadata = extract_ome_metadata_as_dict(test_tiff_filepath)
if image_metadata is None:
    print(f"ERROR extract_ome_metadata_as_dict: No OME Metadata was found for {test_tiff_filepath}. Exiting script...")
    exit()

# Get the settings for each channel according to the presets and convert it into a list to pass onto split_stack_channels_timepoints
chosen_channel_ids = get_channel_settings(image_metadata, channel_presets)

num_channels = image_metadata["OME"]["Image"]["Pixels"]["SizeC"]
channel_names_inorder = []
for channel in chosen_channel_ids:

    index, channel_key = channel

    # channel[1] is the channel key name, channel[1] is the respective index of the channel
    preset = channel_presets[channel[1]]
    name = preset["ChannelName"]
    acquisitionType = preset["AcquisitionType"]
    color = preset["Color"]

    channel_names_inorder.append((name, acquisitionType, color))



confirmation = input("Confirm that the above settings are correct (\"n\" for no, any other key to continue):")
if confirmation.lower == "n":
    print("Exiting script. Please restart the script manually.")
    exit()


output_csv_fp = os.path.join(output_directory, "ImageIndex.ColumbusIDX.csv")


for tiff_filepath in tiff_filepath_list[0:2]:
    # Reset the data for the new image
    split_metadata = ""
    print(f"Parsing {tiff_filepath}...")

    
    # Extract the metadata
    print("\tExtracting metadata")
    image_metadata = extract_ome_metadata_as_dict(tiff_filepath)
    if image_metadata is None:
        print(f"ERROR extract_ome_metadata_as_dict: No OME Metadata was found for {tiff_filepath}. Exiting script...")
        exit()

    # Parse the metadata to write to the CSV
    print("\tParsing metadata and splitting channels to output...")
    split_metadata = split_stack_channels_timepoints(tiff_filepath, image_metadata, channel_names_inorder, output_directory, create_well_folder=False)

    # Throw the data into the CSV
    print("\tAdding data to CSV...")
    create_append_SIMA_CSV(output_csv_fp, split_metadata)

print("Finished process successfully")
