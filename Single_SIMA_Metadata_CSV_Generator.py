# The input file
tiff_filepath = r"C:\Users\akmishra\A5.tif"

# The folder everything gets output to
output_directory = r"C:\Users\akmishra\SImA Tiff Upload Testing\Test_output"

# Each of the following rows indicates a channel present in the image
# name the channel prefix and then indicate if it is confocal or nonconfocal (case sensitive)
channel_names_inorder = [("DRAQ7", "Confocal"),
                         ("DAPI", "Confocal"),
                         ("Bright Field", "NonConfocal"),
                         ("High Contrast", "NonConfocal"),
                         ("Texas Red", "Confocal"),
                         ("GFP", "Confocal")]

# This value should be "True" if you want to create a new folder for the split images according to wellID
# it will be more useful when Amit implements multi-stack support for this script.
create_well_folder = True



















import tifffile
import xml.etree.ElementTree as ET
import json
from PIL import Image
import os
import xmltodict
from datetime import datetime
import csv

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
        print(f"TIFF File: {tiff_path}")
        print(f"Number of pages (frames): {len(tif.pages)}\n")
        
        # Check for OME metadata
        if tif.ome_metadata:
            print("\n--- OME Metadata ---")
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

    field = ""
    timepoint = ""
    plane = ""
    channel = ""
    channelColor = "#0035FF"
    channelType = "Fluoresence"
    timeOffset = "0"
    orientationMatrix = "[[1,0,0],[0,1,0],[0,0,1]]"
    acquisitionType = ""
    sourceFilename = ""


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
            output_filename = f"{well_ID}_{channel_prefix}_{time_point_index+1:03d}.tif" 
            output_filepath = os.path.join(output_directory, output_filename)
            
            img.seek(i)
            img.save(output_filepath)
            print(f"Saved frame {i+1} as {output_filename}")

            # Create the metadata tuples and output
            sourceFilename = output_filename 
            acquisitionType = channel_names_inorder[channel_name_index][1]
            timepoint = time_point_index + 1
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
    
    # try:
    with open(filepath, mode='a+', newline='') as file:
        writer = csv.writer(file)
        
        file.seek(0)
        if file.read(1) == '':
            writer.writerow(headers)
        
        writer.writerows(data)

    # except Exception as e:
    #     print(f"ERROR create_append_SIMA_CSV: {e}")



if not os.path.isfile(tiff_filepath):
    print(f"\n\nERROR {tiff_filepath} is not a valid tiff file. Check to make sure it exists.")
    exit()
if not tiff_filepath.endswith(".tif"):
    print(f"\n\nERROR {tiff_filepath} is not a tiff file. Enter a .tif filepath and retry.\n")
    exit()

if not os.path.isdir(tiff_filepath):
    print(f"\n\nERROR {output_directory} is not a valid output directory. Check to make sure it exists and is where you want to output the files.")

output_csv_fp = os.path.join(output_directory, "ImageIndex.ColumbusIDX.csv")

image_metadata = extract_ome_metadata_as_dict(tiff_filepath)

split_metadata = split_stack_channels_timepoints(tiff_filepath, image_metadata, channel_names_inorder, output_directory, create_well_folder)

create_append_SIMA_CSV(output_csv_fp, split_metadata)

print("Finished process successfully")
