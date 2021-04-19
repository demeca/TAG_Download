# TAG Timing Data Downloader
This script is designed to recieve data via a serial connected TAG Minitimer. The data is then exported to a CSV. The goal is to be able to get a dump of the data from a device in the event of a timing computer crash, a missing time in the computer or data misalignment.

## Installation
The script is desinged for python 3.6 and higher.  
To install the requirements run
```
pip install -r requirements.txt
```
## Usage
Running the script with no arguments, as shown below, will output the available system COM ports
```
python tagDownload.py
```
Run the script with a com port (e.g. COM7 on Windows or /dev/ttyUSB1 on Linux)
```
python tagDownload.py COM7 -b 9600
```
All serial options are in the help scripting
```
python tagDownload.py -h
```
```
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
```
