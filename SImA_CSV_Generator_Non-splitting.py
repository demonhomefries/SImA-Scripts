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

def create_append_SIMA_CSV_tuple(filepath, data):
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

def create_append_SIMA_CSV_dict(filepath, data_dict):
    # Define the headers
    headers = [
        "PlateName", "MeasurementDate", "Row", "Column", "Field", "Timepoint", "Plane", "Channel",
        "ChannelName", "ChannelColor", "ChannelType", "ImageResolutionX@um", "ImageResolutionY@um",
        "ExposureTime[s]", "MainEmissionWavelength@nm", "MainExcitationWavelength@nm",
        "PositionX@um", "PositionY@um", "TimeOffset@s", "AbsoluteTime@s", "ImageWidth",
        "ImageHeight", "NumberOfFields", "NumberOfTimepoints", "ObjectiveMagnification",
        "ObjectiveNA", "AcquisitionType", "OrientationMatrix", "SourceFilename"
    ]
    # Map incoming dictionary keys to the headers
    row = [
        data_dict.get("plateName", ""),                 # PlateName
        data_dict.get("measurementDate", ""),          # MeasurementDate
        data_dict.get("row", ""),                      # Row
        data_dict.get("column", ""),                   # Column
        data_dict.get("field", ""),                    # Field
        data_dict.get("timepoint", ""),                # Timepoint
        data_dict.get("plane", ""),                    # Plane
        data_dict.get("channel", ""),                  # Channel
        data_dict.get("channelName", ""),              # ChannelName
        data_dict.get("channelColor", ""),             # ChannelColor
        data_dict.get("channelType", ""),              # ChannelType
        data_dict.get("resolutionX", ""),              # ImageResolutionX@um
        data_dict.get("resolutionY", ""),              # ImageResolutionY@um
        data_dict.get("exposureTimeS", ""),            # ExposureTime[s]
        data_dict.get("emissionWavelength", ""),       # MainEmissionWavelength@nm
        data_dict.get("excitationWavelength", ""),     # MainExcitationWavelength@nm
        data_dict.get("positionX", ""),                # PositionX@um
        data_dict.get("positionY", ""),                # PositionY@um
        data_dict.get("timeOffset", ""),               # TimeOffset@s
        data_dict.get("absoluteTime", ""),             # AbsoluteTime@s
        data_dict.get("imageWidth", ""),               # ImageWidth
        data_dict.get("imageHeight", ""),              # ImageHeight
        data_dict.get("numFields", ""),                # NumberOfFields
        data_dict.get("num_timepoints", ""),           # NumberOfTimepoints
        data_dict.get("objectiveMagnification", ""),   # ObjectiveMagnification
        data_dict.get("objectiveNA", ""),              # ObjectiveNA
        data_dict.get("acquisitionType", ""),          # AcquisitionType
        data_dict.get("orientationMatrix", ""),        # OrientationMatrix
        data_dict.get("sourceFilename", "")            # SourceFilename
    ]

    try:
        with open(filepath, mode='a+', newline='') as file:
            writer = csv.writer(file)
            
            # Write headers if the file is empty
            file.seek(0)
            if file.read(1) == '':
                writer.writerow(headers)
            
            # Write the row mapped from the dictionary
            writer.writerow(row)

    except Exception as e:
        print(f"ERROR create_append_SIMA_CSV: {e}")

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





def extract_metadata_as_dict(tiff_path):

    with tifffile.TiffFile(tiff_path) as tif:
        # Check for OME metadata and parse if available
        if tif.ome_metadata:
            ome_dict = xmltodict.parse(tif.ome_metadata)
            return get_clean_metadata_dict(clean_dict_keys(ome_dict))

        # If OME metadata is not available, extract and parse metadata from page 0
        if tif.pages:
            page_0 = tif.pages[0]
            page_0_metadata_xml = page_0.description  # Assuming XML metadata is in the description field
            if page_0_metadata_xml:
                try:
                    page_0_dict = xmltodict.parse(page_0_metadata_xml)
                    return get_clean_metadata_dict(clean_dict_keys(page_0_dict))
                except Exception as e:
                    if "IJMetadata" in page_0.tags:
                        ij_metadata = page_0.tags["IJMetadata"].value["Info"]
                        start_index = ij_metadata.find("<OME")
                        if start_index != -1:
                            ij_metadata = ij_metadata[start_index:]
                        ome_dict = xmltodict.parse(ij_metadata)
                        return get_clean_metadata_dict(clean_dict_keys(ome_dict))
                    
                    else:
                        return None

        return None
    
def get_value_from_metadata_dict(final_key, data):
    """Recursively search for the final key in a nested dictionary and return its value."""
    if isinstance(data, dict):
        for key, value in data.items():
            if key == final_key:
                return value
            elif isinstance(value, dict):
                result = get_value_from_metadata_dict(final_key, value)
                if result is not None:
                    return result
            elif isinstance(value, list):
                for item in value:
                    result = get_value_from_metadata_dict(final_key, item)
                    if result is not None:
                        return result
    return None

def get_clean_metadata_dict(original_metadata_dict):    

    # Calculated/Derived
    
    verticalTotal = get_value_from_metadata_dict("VerticalTotal", original_metadata_dict)
    if verticalTotal is None:
        verticalTotal = get_value_from_metadata_dict("verticalTotal", original_metadata_dict)

    horizTotal = get_value_from_metadata_dict("HorizontalTotal", original_metadata_dict)
    if horizTotal is None:
        horizTotal = get_value_from_metadata_dict("horizontalTotal", original_metadata_dict)


    numFields = int(verticalTotal) * int(horizTotal)

    exposureTimeMS = get_value_from_metadata_dict("ShutterSpeedMS", original_metadata_dict)
    exposureTimeS = int(exposureTimeMS) / 1000

    measurementDate = get_value_from_metadata_dict("Date", original_metadata_dict)
    measurementDate, absoluteTime = convert_date_format(measurementDate)

    wellID = get_value_from_metadata_dict("Well", original_metadata_dict)
    row, column = well_id_to_row_col(wellID)

    objectiveMagnification = get_value_from_metadata_dict("ObjectiveSize", original_metadata_dict)

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


    image_width = get_value_from_metadata_dict("SizeX", original_metadata_dict)
    if image_width == None or image_width == "":
        image_width = get_value_from_metadata_dict("PixelWidth", original_metadata_dict)

    image_height = get_value_from_metadata_dict("SizeY", original_metadata_dict)
    if image_height == None or image_height == "":
        image_height = get_value_from_metadata_dict("PixelHeight", original_metadata_dict)

    clean_metadata_dict = {
        "plateName" : get_value_from_metadata_dict("Plate", original_metadata_dict),
        "measurementDate" : measurementDate,
        "absoluteTime" : absoluteTime,
        "wellID" : wellID,
        "row" : row,
        "column" : column,
        "verticalTotal" : verticalTotal,
        "horizTotal" : horizTotal,
        "numFields": numFields,
        "exposureTimeS" : exposureTimeS,
        "channelName" : get_value_from_metadata_dict("Color", original_metadata_dict),
        "emissionWavelength" : get_value_from_metadata_dict("EmissionWavelength", original_metadata_dict),
        "excitationWavelength" : get_value_from_metadata_dict("ExcitationWavelength", original_metadata_dict),
        "num_channels" : get_value_from_metadata_dict("SizeC", original_metadata_dict),
        "num_timepoints" : get_value_from_metadata_dict("SizeT", original_metadata_dict),
        "imageWidth" : image_width,
        "imageHeight" : image_height,
        "resolutionX" : resolution,
        "resolutionY" : resolution,
        "objectiveNA" : get_value_from_metadata_dict("NumericalAperture", original_metadata_dict),
        "objectiveMagnification" : objectiveSizeInt,
        "field" : "1",
        "plane" : "1",
        "channel" : "",
        "timeOffset" : "0",
        "orientationMatrix" : "[[1,0,0],[0,1,0],[0,0,1]]",
        "acquisitionType" : "",
        "sourceFilename" : "",
        "timepoint" : "",
        "channelColor" : "#0035FF",
        "channelType" : "Fluoresence",
        "positionX" : "0",
        "positionY" : "0",

    }

    return clean_metadata_dict

def append_more_metadata_from_filename(filepath, metadata_dict, num_timepoints):
    """"
    okay, a lot of this information is going to be based on the filename since that data can't AUTOMATICALLY be extracted from the metadata
    That info can be MANUALLY extracted with user input, but that's a pain and I dont want to code that.
    """

    sourceFilename = os.path.basename(filepath)
    sourceFilename_without_extension = os.path.basename(filepath).split(".")[0]

    sourceFilename_split_list = sourceFilename_without_extension.split("_")

    current_timepoint = int(sourceFilename_without_extension.split("_")[len(sourceFilename_split_list) - 1])
    channel_number = sourceFilename_without_extension.split("_")[2]



    metadata_dict["sourceFilename"] = sourceFilename
    metadata_dict["timepoint"] = current_timepoint
    metadata_dict["channel"] = channel_number # this is the channel number
    if "phase" in metadata_dict["channelName"].lower() or "bright" in metadata_dict["channelName"].lower():
        acquisition_type = "Nonconfocal"
    else:
        acquisition_type = "Confocal"

    metadata_dict["acquisitionType"] = acquisition_type
    metadata_dict["num_timepoints"] = num_timepoints

    # num_channels is assumed to be 1 because this function is invoked when NOT splitting stacks (when they are already split)
    metadata_dict["num_channels"] = 1

    if metadata_dict["emissionWavelength"] == None and metadata_dict["excitationWavelength"] == None:
        metadata_dict["emissionWavelength"] = 0
        metadata_dict["excitationWavelength"] = 0

    missing_values = []
    for tag in metadata_dict.keys():
        if metadata_dict[tag] == None or metadata_dict[tag] == "":
            missing_values.append((tag, metadata_dict[tag]))

    if len(missing_values) > 0:
        print("MISSING ELEMENTS")
        for element in missing_values:
            tag, value = element
            print(f"{tag}: {value}")
    
    return metadata_dict

def get_total_num_timepoints(filepath_list):
    largest_number = 0
    for filepath in filepath_list:
        sourceFilename_split_list = os.path.basename(filepath).split(".")[0].split("_")
        current_timepoint = int(sourceFilename_split_list[len(sourceFilename_split_list) - 1])

        if current_timepoint > largest_number:
            largest_number = current_timepoint

    if largest_number < 1:
        return None
    else:
        return largest_number



tiff_filepaths, output_directory = get_input_output()

print(f"OUTPUT: {output_directory}")


headers = [
    "PlateName", "MeasurementDate", "Row", "Column", "Field", "Timepoint", "Plane", "Channel",
    "ChannelName", "ChannelColor", "ChannelType", "ImageResolutionX@um", "ImageResolutionY@um", 
    "ExposureTime[s]", "MainEmissionWavelength@nm", "MainExcitationWavelength@nm", 
    "PositionX@um", "PositionY@um", "TimeOffset@s", "AbsoluteTime@s", "ImageWidth", 
    "ImageHeight", "NumberOfFields", "NumberOfTimepoints", "ObjectiveMagnification", 
    "ObjectiveNA", "AcquisitionType", "OrientationMatrix", "SourceFilename"
]

num_timepoints = get_total_num_timepoints(tiff_filepaths)
if num_timepoints == None:
    print(f"ERROR: Could not parse the number of time points in the folder. Is the time point number the last element of the filename? {os.path.basename(tiff_filepaths[0])}")
    exit()


csv_filepath = os.path.join(output_directory, "ImageIndex.ColumbusIDX.csv")

for filepath in tiff_filepaths:
    print(f"Processing {os.path.basename(filepath)}")
    metadata_dict = extract_metadata_as_dict(filepath)
    completed_metadata_dict = append_more_metadata_from_filename(filepath, metadata_dict, num_timepoints)
    if completed_metadata_dict is None:
        print("METADATA IS NONE!!")
    create_append_SIMA_CSV_dict(csv_filepath, completed_metadata_dict)
    
