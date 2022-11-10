
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
    from datetime import datetime

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
    parser.add_argument("--ignore",
                        "-g",
                        help="If more devices are found than what is listed in the given file, ignore them.",
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

    if args.debug:
        print("Reading RuuviTags for {} seconds".format(args.duration))

    #TODO: Check if stderr gives "Command LE Set Scan Enable execution timed out" and if so, abort.
    #if it gives "Can't down device hci0: Device or resource busy (16" restart device?
    #Requires the installation of bluewalker
    command = 'sudo hciconfig hci0 down && sudo /home/pi/go/bin/bluewalker -device hci0 -ruuvi -duration {}'.format(args.duration)
    currTime = datetime.now() #TODO: implement daylight savings
    if args.debug:
        print(currTime)
    #os.system(command)
    try:
        shOutput = subprocess.check_output(command, shell=True, universal_newlines=True)
    except subprocess.CalledProcessError as err:
        print("Error:",err)
        shOutput = subprocess.check_output("sudo shutdown -r +1", shell=True, universal_newlines=True)
        with open("/home/pi/readRuuvi/err.log", 'a', encoding="utf-8") as fil:
            fil.write("{} {} {}, {}\n".format(currTime,"Error:",err,shOutput))
        exit()

    #Todo: how to handle this without writing to a file?
    #with open("ruuviOut.json", 'r', encoding="us-ascii") as fil:
    #    jsonOut = json.loads(fil.read())
    #    print(jsonOut)

    lines = shOutput.split("\n")
        
    bDevice=False
    devOnAir   = []
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
            if len(devOnAir)==0:
                devOnAir.append(dev)
                humidities.append([])
                temps.append([])
                pressures.append([])
                voltages.append([])
                if args.debug:
                    print("Found a new device:",dev)
            else:
                if devOnAir.count(dev)==0:
                    devOnAir.append(dev)
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
            humidities[devOnAir.index(dev)].append(float(splitted[1][:pos]))
            (pos, unit) = findUnit(splitted[3])
            if bCheckUnits:
                units.append(unit)
            temps[devOnAir.index(dev)].append(float(splitted[3][:pos]))
            (pos, unit) = findUnit(splitted[5])
            if bCheckUnits:
                units.append(unit)
            pressures[devOnAir.index(dev)].append(int(splitted[5][:pos]))
            (pos, unit) = findUnit(splitted[8])
            if bCheckUnits:
                units.append(unit)
            voltages[devOnAir.index(dev)].append(int(splitted[8][:pos]))
            
    if args.debug:
        print("Printing medians and values gathered")
        print(names)
        print(units)
        print(median(humidities[0]),median(humidities[1]),humidities)
        print(median(temps[0]),median(temps[1]),temps)
        print(median(pressures[0]),median(pressures[1]),pressures)
        print(median(voltages[0]),median(voltages[1]),voltages)

    devInList    = []
    devPosInList = []
    if args.init:
        print("Initializing a new file {}...".format(args.file))
        try:
            with open(args.file, 'x', encoding="utf-8") as fil:
                for devnum,iDev in enumerate(devOnAir):
                    devPosInList.append(devnum)
                    devInList.append(iDev)
                    fil.write(iDev)
                    if devnum!=len(devOnAir)-1:
                        fil.write(',')
                fil.write('\n')
                fil.write("Date[yyyy-m-d],Time[h:m],")
                for devnum,iDev in enumerate(devOnAir):
                    for num,(iName,iUnit) in enumerate(zip(names,units)):
                        fil.write("{}[{}]".format(iName,iUnit))
                        if devnum!=len(devOnAir)-1 or num!=len(names)-1:
                            fil.write(',')
                fil.write('\n')
        except OSError as err:
            print("Error:",err)
            exit()
    else:
        #TODO: Check that the units are the same.
        try:
            with open(args.file, 'r', encoding="utf-8") as fil:
                for line in fil:
                    readDews = line.split(',')
                    for devNum,readDew in enumerate(readDews):
                        #Last dev has a \n in the end which we remove
                        if devNum==len(readDews)-1:
                            readDew = readDew[:len(readDew)-1]
                        try:
                            devPosInList.append(devOnAir.index(readDew))
                            devInList.append(readDew)
                        except ValueError as err:
                            print("Error:",err)
                            print("Device",readDew,"not available. Check that device is on range and powered")
                            exit()
                    #The devOnAir are listed in the first line, we can break
                    break
        except OSError as err:
            print("Error:",err)
            exit()

        #Here check that we have as many devices in list and on air
        if len(devOnAir)!=len(devPosInList):
            if args.ignore:
                pass
            else:
                devCopy = devOnAir.copy()
                for readDew in devInList:
                    try:
                        devCopy.remove(readDew)
                    except ValueError as err:
                        print(err)
                        pass #We are fine if we cannot find everything in list
                print("A device(s) was found which is not on the list:")
                print(devCopy)
                print("If you added a new device, please init a new file")
                print("If you wish to ignore other devOnAir than the ones in the list, use --ignore flag")
                exit()

    #TODO: Need a check for the order of devOnAir.

    if args.debug:
        print("Device orders in list:",devPosInList)

    #In format 2022-11-08 22:34:59.328995
    dateSep = str(currTime).split(' ')
    timeSep = dateSep[1].split(':')

    try:
        with open(args.file, 'a', encoding="utf-8") as fil:
            fil.write("{},{}:{},".format(dateSep[0],timeSep[0],timeSep[1]))
            for devnum,iDev in enumerate(devPosInList):
                fil.write("{:.2f}".format(median(humidities[iDev])))
                fil.write(',')
                fil.write("{:.2f}".format(median(temps[iDev])))
                fil.write(',')
                fil.write("{:.0f}".format(median(pressures[iDev])))
                fil.write(',')
                fil.write("{:.0f}".format(median(voltages[iDev])))
                if devnum!=len(devPosInList)-1:
                    fil.write(',')
            fil.write('\n')
    except OSError as err:
        print("Error",err)
        exit()

