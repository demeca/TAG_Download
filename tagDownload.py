"""TAG Minitimer Downloader
This script will recieve a download from a serial connected
TAG Minitimer. The data is then exported to a CSV.
Run the command with no options to list available COM ports
Run the command with a com port or com device to recieve a download

Usage:
    tagDownload.py
    tagDownload.py COM [options]

Options:
    -h, --help                    Show this screen
    --version                     Show version
    -b BAUD --baud=BAUD           Serial speed [default: 9600]
    -s STOP --stopbits=STOP       Serial stopbits [default: 1]
    -e BYTES --bytsize=BYTES      Serial bytesize [default: 8]
    -p PARITY --parity PARITY     Serail parity [default: N]
    -t TIMEOUT --timeout TIMEOUT  Seiral timeout [default: 3]

"""
import csv
import re
import serial
import sys
from datetime import date, timedelta
from docopt import docopt
from serial.tools.list_ports import comports

# Tag Heuer Defaults/Descriptions

THStartDate = date(2000,1,1)
THLineType = {
    'ID': 'Serial',
    'DL': 'Download',
    'AN': 'Original Time',
    'A-': 'Time With Removed Identification',
    'A*': 'Time With A new Identification',
    'A+': 'Inserted Time',
    'A=': 'Duplicated Time',
    'AC': 'Cancelled Time',
}

def listPorts():
    '''
    List all COM ports or Device Paths
    Print the list to the console
    '''
    print("Available COM Ports:")
    ports = comports()
    for port, desc, hwid in sorted(ports):
            print(f"{port}: {desc} [{hwid}]")

def setupSerial(args):
    '''
    Setup the serial connection paremeters
    Input is a dictionary of command line arguments
    Returns a serial object
    '''
    ser = serial.Serial()
    ser.port = args['COM']
    ser.baudrate = int(args.get("--baud", 9600))
    ser.stopbits= int(args.get("--stopbits", 1))
    ser.bytesize= int(args.get("--bytezise", 8))
    ser.parity= args.get("--parity", 'N')
    ser.timeout= int(args.get("--timeout", 8))
    ser.xonxoff=0
    ser.rtscts=0
    return ser

def processData(ser):
    '''
    Read data from a serial connection, looking for
    data in a standard format
    Input is an open serial object
    Returns a tuple of the data as a List of Dictionaries,
    the device serial string, and the run number string
    '''
    ctrl = True
    downloadData = []
    print("Waiting for data...")

    # Loop till we see the end of download characters from the TAG device
    while ctrl:
        # Read each line
        line = ser.readline()
        # Convert the UTF-8 line to a string
        strLine = line.decode("utf-8")
        if strLine:
            # Process the ID line, usually the first line of a download command
            if strLine.startswith('ID'):
                devSerial = re.search(r"ID\s*(\d+)\t.*", strLine).group(1)

            # Process Download Start command, contains the download number
            if strLine.startswith('DS'):
                print("Processing Run ", end="")
                runNumber = re.search(r"DS\s*(\d+)\s*.*", strLine).group(1)
                print(f"{runNumber}...", end="")
                sys.stdout.flush()
            
            # Process each time from the system. Download times start with 'A'
            if strLine.startswith('A'):
                print(".", end="")
                # sys.stdout.flush()
                # Regex to split the line
                # Line format is <S>Ax_NNNN_SSSS_CC_HH:MM:SS.FFFFF_DDDDD<E>
                # See documentation for details
                # Example line: "AN  700    3 M4 19:20:15.83400  7749    06C8"
                searchObj = re.search(r"(A.)\s+(\d{0,4}|\s{0,4})\s+(\d+)\s+(\w{0,1}\d+)\s+(\d+):(\d+):(\d+)\.(\d+)\s+(\d+)\s+.*", strLine)
                if searchObj:
                    dictLine = {
                        'Line Type': THLineType.get(searchObj.group(1), "N/A"),
                        'Candidate': searchObj.group(2),
                        'Sequence': searchObj.group(3),
                        'Channel': searchObj.group(4),
                        'Hours': searchObj.group(5),
                        'Minutes': searchObj.group(6),
                        'Seconds': searchObj.group(7),
                        'Decimal': searchObj.group(8),
                        'Days': searchObj.group(9),
                        'Date': THStartDate + timedelta(days=int(searchObj.group(9)))
                    }
                    dictLine['Time'] = dictLine['Hours'] + ":" + dictLine['Minutes'] + ":" + dictLine['Seconds'] + "." + dictLine['Decimal']
                    downloadData.append(dictLine)
            if strLine.startswith('DE'):
                ctrl = False
    print()
    print("Finished Data Ingest")
    ser.close()

    # Append extra info to the CSV about the data ingest
    downloadData.append({
        'Line Type': "Download INFO",
        'Candidate': f"Device Serial: {devSerial}",
        'Sequence': f"Device Run Number: {runNumber}"
        })
    return downloadData, devSerial, runNumber


def writeTAGCSV(data, ser, run):
    '''
    Writes a list of dictionaries to a csv
    It takes in the data, a serial string and
    a run string that will be used to make the
    filename
    '''
    fileName = "TAGPY_"
    if ser:
        fileName += str(ser) + "_"
    if run:
        fileName += "RUN_" + str(run) + "_"
    fileName += str(data[0].get('Date', ""))
    fileName += ".csv"
    print(f"Writing {fileName}")
    with open (fileName, 'w+', newline='') as outFile:
        fc = csv.DictWriter(outFile, fieldnames=data[0].keys())
        fc.writeheader()
        fc.writerows(data)


if __name__ == '__main__':
    arguments = docopt(__doc__, version='1.0')
    if not arguments['COM']:
        # List ports if none is given
        listPorts()
    else:
        # Create a serial object
        ser = setupSerial(arguments)
        # Attempt to open the serial device
        # Exit if that is not successful
        try:
            ser.open()
        except serial.SerialException as e:
            print(f"Could not open serial port {ser.name}: {e}")
            sys.exit(1)
        # Recieve and process data
        dlData, devSer, runNum = processData(ser)
        # If data is recieved, write it to a CSV
        if dlData:
            writeTAGCSV(dlData, devSer, runNum)