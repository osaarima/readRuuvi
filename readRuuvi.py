
#Assume format: 35.89mC where unit can be any
#length. No space between unit and number Works 
#´for int as well
def findUnit(strNum):
    pos = -1
    posNow = 0
    sUnit = ''
    for iLetter in strNum:
        if not iLetter.isnumeric():
            if iLetter!='.':
                sUnit += iLetter
                if pos==-1:
                    pos=posNow
        posNow+=1

    return (pos, sUnit)

if __name__ == "__main__":
    #import sys
    import argparse
    #import os
    import subprocess
    from statistics import median

    parser = argparse.ArgumentParser(description="Reads RuuviTag information once every five minutes and saves it in a file.",
                                     epilog="Created by OS")
    parser.add_argument("--duration",
                        "-d",
                        help="How many seconds RuuviTags are being listened",
                        type=int,
                        nargs='?',
                        default=5)
    parser.add_argument("--init",
                        "-i",
                        help="Initialize a new file",
                        action="store_true",
                        default=False)
    parser.add_argument("--file",
                        "-f",
                        help="Filename for output",
                        type=str,
                        nargs='?',
                        default="out.csv")
    parser.add_argument("--debug",
                        help="Flag for debugging purposes",
                        action="store_true",
                        default=False)

    args = parser.parse_args()

    print("Reading RuuviTags for {} seconds".format(args.duration))

    #TODO: Check if stderr gives "Command LE Set Scan Enable execution timed out" and if so, abort.
    #if it gives "Can't down device hci0: Device or resource busy (16" restart device?
    #Requires the installation of bluewalker
    command = 'sudo hciconfig hci0 down && sudo /home/pi/go/bin/bluewalker -device hci0 -ruuvi -duration {}'.format(args.duration)
    #os.system(command)
    shOutput = subprocess.check_output(command, shell=True, universal_newlines=True)

    #Todo: how to handle this without writing to a file?
    #with open("ruuviOut.json", 'r', encoding="us-ascii") as fil:
    #    jsonOut = json.loads(fil.read())
    #    print(jsonOut)

    lines = shOutput.split("\n")
        
    bDevice=False
    devices    = []
    humidities = []
    temps      = []
    pressures  = []
    voltages   = []
    names      = []
    units      = []
    for line in lines:
        if args.debug:
            print(line)
        splitted = line.split(' ')
        if splitted[0].__contains__("Ruuvi"):
            dev = line[line.find("device")+7:line.find(",")]
            if len(devices)==0:
                devices.append(dev)
                humidities.append([])
                temps.append([])
                pressures.append([])
                voltages.append([])
                if args.debug:
                    print("Found a new device:",dev)
            else:
                if devices.count(dev)==0:
                    devices.append(dev)
                    humidities.append([])
                    temps.append([])
                    pressures.append([])
                    voltages.append([])
                    if args.debug:
                        print("Found a new device:",dev)
        elif splitted[0].__contains__("Humidity"):
            bCheckUnits=False
            if len(names)==0:
                names.append(splitted[0][1:len(splitted[0])-1]) #First one has tab in front
                names.append(splitted[2][:len(splitted[2])-1])
                names.append(splitted[4][:len(splitted[4])-1])
                names.append(splitted[6]+' '+splitted[7][:len(splitted[7])-1])
                bCheckUnits=True
            (pos, unit) = findUnit(splitted[1])
            if bCheckUnits:
                units.append(unit)
            humidities[devices.index(dev)].append(float(splitted[1][:pos]))
            (pos, unit) = findUnit(splitted[3])
            if bCheckUnits:
                units.append(unit)
            temps[devices.index(dev)].append(float(splitted[3][:pos]))
            (pos, unit) = findUnit(splitted[5])
            if bCheckUnits:
                units.append(unit)
            pressures[devices.index(dev)].append(int(splitted[5][:pos]))
            (pos, unit) = findUnit(splitted[8])
            if bCheckUnits:
                units.append(unit)
            voltages[devices.index(dev)].append(int(splitted[8][:pos]))
            
    if args.debug:
        print("Printing medians and values gathered")
        print(names)
        print(units)
        print(median(humidities[0]),median(humidities[1]),humidities)
        print(median(temps[0]),median(temps[1]),temps)
        print(median(pressures[0]),median(pressures[1]),pressures)
        print(median(voltages[0]),median(voltages[1]),voltages)

    if args.init:
        print("Initializing a new file {}...".format(args.file))
        #TODO: check if file exists already.
        with open(args.file, 'w', encoding="utf-8") as fil:
            for devnum,iDev in enumerate(devices):
                fil.write(iDev)
                if devnum!=len(devices)-1:
                    fil.write(',')
            fil.write('\n')
            for devnum,iDev in enumerate(devices):
                for num,(iName,iUnit) in enumerate(zip(names,units)):
                    fil.write("{}[{}]".format(iName,iUnit))
                    if devnum!=len(devices)-1 or num!=len(names)-1:
                        fil.write(',')
            fil.write('\n')
    else:
        #Check that the devices and units are the same.
        pass

    #TODO: Need a check for the order of devices.

    with open(args.file, 'a', encoding="utf-8") as fil:
        for devnum,iDev in enumerate(devices):
            fil.write("{:.2f}".format(median(humidities[devnum])))
            fil.write(',')
            fil.write("{:.2f}".format(median(temps[devnum])))
            fil.write(',')
            fil.write("{:.0f}".format(median(pressures[devnum])))
            fil.write(',')
            fil.write("{:.0f}".format(median(voltages[devnum])))
            if devnum!=len(devices)-1:
                fil.write(',')
        fil.write('\n')

