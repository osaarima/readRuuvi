
if __name__ == "__main__":
    #import sys
    import argparse
    #import os
    import subprocess
    import json

    parser = argparse.ArgumentParser(description="Reads RuuviTag information once every five minutes and saves it in a file.",
                                     epilog="Created by OS")

    parser.add_argument("--duration",
                        "-d",
                        help="How many seconds RuuviTags are being listened",
                        type=int,
                        nargs='?',
                        default=5)

    args = parser.parse_args()

    print("Reading RuuviTags for {} seconds".format(args.duration))

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
    for line in lines:
        if not bDevice:
            print(line[line.find("device")+7:line.find(",")])
            bDevice=True

    #print(shOutput)

    #jsonOut = json.loads(shOutput)

