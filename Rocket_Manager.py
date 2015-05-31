import sys
import time
import os
import urllib
import zipfile
import shutil
import socket
from xml.etree import ElementTree

# --Constants
URL_ROCKET_STABLE = "http://api.rocket.foundation/release/latest/"
URL_ROCKET_BETA = "http://api.rocket.foundation/beta/latest/"
URL_ROCKET_LINUX = "http://api.rocket.foundation/linux-beta/latest/"
URL_STEAM = "http://media.steampowered.com/installer/steamcmd.zip"

OUTPUT_ZIP_STEAM = "steam_temp.zip"
OUTPUT_ZIP_ROCKET = "rocket_temp.zip"

PROCNAME = "Unturned.exe"


def writeConfig(name):
    f=open(name,"w")
    f.write('''<?xml version="1.0" encoding="UTF-8"?>
<config>
	<rebootEvery seconds="3600" />
	<unturnedFolder path=".\unturned" />
	<rocket updateBranch="release" apikey=""/>
	<steam username="" password="" />
	<steamUpdates validate="true" />
	<servers rconEnabled="false">
		<server name="server1" rconPort="27013" rconPassword="pass" />
		<server name="server2" rconPort="27014" rconPassword="pass" />
	</servers>
	<notifyBefore seconds="60" />
</config>''')
    f.close()


def loadConfig(name):
    global REBOOT_TIME
    global NOTIFY_TIME
    global SERVERS_TO_LAUNCH
    global RCON_ENABLED
    global RCON_PORT
    global RCON_PASSWORD
    global UNTURNED_PATH
    global UPDATE_BRANCH
    global VALIDATE_AT_BOOT
    global STEAM_USER
    global STEAM_PASS
    global APIKEY

    if (not os.path.isfile(name)):
        writeConfig(name)
        return True
    try:
        with open(name, 'rt') as f:
            tree = ElementTree.parse(f)

        node = tree.find("rebootEvery")
        REBOOT_TIME = int(node.attrib.get("seconds"))

        node = tree.find("unturnedFolder")
        UNTURNED_PATH = node.attrib.get("path")

        node = tree.find("rocket")
        APIKEY = node.attrib.get("apikey")
        UPDATE_BRANCH = node.attrib.get("updateBranch")

        node = tree.find("steam")
        STEAM_USER = node.attrib.get("username")
        STEAM_PASS = node.attrib.get("password")

        node = tree.find("steamUpdates")
        VALIDATE_AT_BOOT = node.attrib.get("validate")

        SERVERS_TO_LAUNCH = []
        RCON_PASSWORD = []
        RCON_PORT = []
        for node in tree.iter("server"):
            SERVERS_TO_LAUNCH.append(node.attrib.get("name"))
            RCON_PORT.append(int(node.attrib.get("rconPort")))
            RCON_PASSWORD.append(node.attrib.get("rconPassword"))

        node = tree.find("servers")
        RCON_ENABLED = node.attrib.get("rconEnabled")

        node = tree.find("notifyBefore")
        NOTIFY_TIME = int(node.attrib.get("seconds"))
        if (NOTIFY_TIME > REBOOT_TIME):
            NOTIFY_TIME = REBOOT_TIME
        return False

    except:
        writeConfig(name)
        return True


def downloader(i):
    err = False
    if (i == "steam"):
        try:
            urllib.urlretrieve(URL_STEAM, OUTPUT_ZIP_STEAM)
        except:
            err = True

    if (i == "rocket"):
        try:
            if (UPDATE_BRANCH == "release"):
                urllib.urlretrieve(URL_ROCKET_STABLE + APIKEY, OUTPUT_ZIP_ROCKET)
            if (UPDATE_BRANCH == "beta"):
                urllib.urlretrieve(URL_ROCKET_BETA + APIKEY, OUTPUT_ZIP_ROCKET)
            if (UPDATE_BRANCH == "linux"):
                urllib.urlretrieve(URL_ROCKET_LINUX + APIKEY, OUTPUT_ZIP_ROCKET)
        except:
            err = True
    return err


def extractor(name):
    zfile = zipfile.ZipFile(name)
    if not os.path.exists("rocket"):
        os.makedirs("rocket")
    zfile.extractall("rocket")
    zfile.close()


def cleanUp():
    try:
        shutil.rmtree("rocket")
        os.remove(OUTPUT_ZIP_ROCKET)
        os.remove(OUTPUT_ZIP_STEAM)
    except:
        None

def installer():
    try:
        for f in os.listdir("rocket\\"):
            if(not os.path.isdir(f)):
                src_file = os.path.join("rocket\\", f)
                dst_file = os.path.join(UNTURNED_PATH + "\\Unturned_Data\\Managed\\", f)
                shutil.copyfile(src_file, dst_file)
                return False
    except IOError:
        return True

def rconNotify(port, passw):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", port))
    s.recv(2048)
    s.send(passw)
    time.sleep(0.2)
    s.send("\r\n")
    time.sleep(0.2)
    s.recv(2048)
    s.send("say [Manager] This server will restart in " + str(NOTIFY_TIME) + " seconds")
    time.sleep(0.2)
    s.send("\r\n")
    time.sleep(0.2)
    s.recv(2048)
    s.close()


def rconShutdown(port, passw):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", port))
    s.recv(2048)

    s.send(passw)
    time.sleep(0.2)
    s.send("\r\n")
    time.sleep(0.2)
    s.recv(2048)
    time.sleep(0.2)

    s.send("say Rebooting...")
    time.sleep(0.2)
    s.send("\r\n")
    time.sleep(0.2)
    s.recv(2048)
    time.sleep(0.2)

    s.send("shutdown")
    time.sleep(0.2)
    s.send("\r\n")
    time.sleep(0.2)
    s.recv(2048)

    s.close()


def main():
    print("--------------------------------------------------------------------------------")
    print("                          SergiX44's Rocket Manager 1.6                         ")
    print("--------------------------------------------------------------------------------\n\n")
    print("Loading config...")

    if (loadConfig("config_RocketManager.xml")):
        print("Close and edit config_RocketManager.xml, then restart me!")
        raw_input("Press any key to continue...")
        sys.exit(1)

    if (not os.path.isfile("steamcmd.exe")):
        ex = True
        while (ex):
            sel = raw_input("SteamCMD not found! Would you like download it? (y/n) ")
            if (sel == "y"):

                print("Downloading steamcmd...")
                if (downloader("steam")):
                    print("ERROR: Unable to download steam! Please check your internet settings!")
                    raw_input("Press any key to continue...")
                    sys.exit(3)

                zfile = zipfile.ZipFile(OUTPUT_ZIP_STEAM)
                zfile.extractall()
                zfile.close()
                ex = False
            if (sel == "n"):
                ex = False
                print("Closing...")
                time.sleep(1)
                sys.exit(1)

    while 1:
        #reloading config
        if (loadConfig("config_RocketManager.xml")):
            print("Failed loading config! :( \nConfig file regenerated, edit config_RocketManager.xml, then restart me!")
            raw_input("Press any key to continue...")
            sys.exit(2)

        #launch steam cmd
        if ((not os.path.isdir(UNTURNED_PATH)) or (VALIDATE_AT_BOOT == "true")):
            print("Launching steam...")
            print "--------------------------------------------------------------------------------\n\n"
            os.system(
                "steamcmd.exe +login " + STEAM_USER + " " + STEAM_PASS + " +force_install_dir " + UNTURNED_PATH + " +app_update 304930 -beta preview -betapassword OPERATIONMAPLELEAF validate +exit")
            print "--------------------------------------------------------------------------------\n\n"

        #download and extract
        print("Downloading rocket...")
        if (downloader("rocket")):
            print("ERROR: Unable to download rocket! Please check your internet settings!")
            raw_input("Press any key to continue...")
            sys.exit(3)

        print("Extracting rocket...")
        extractor(OUTPUT_ZIP_ROCKET)

        #Moving files
        print("Installing Rocket...")
        if (installer()):
            print("Unable to install rocket! try to revalidate the installation!")
            cleanUp()
            raw_input("Press any key to continue...")
            sys.exit(4)

        #clean up zips and extracted files
        print("Cleaning up...")
        cleanUp()

        #launching servers
        print("Launching servers...")
        for i in range(0, len(SERVERS_TO_LAUNCH)):
            print("    - Launching " + SERVERS_TO_LAUNCH[i])
            os.system("cd " + UNTURNED_PATH + "\ & start Unturned.exe -nographics -batchmode +secureserver/" +
                      SERVERS_TO_LAUNCH[i])

        #timer
        counter = REBOOT_TIME
        while (counter >= 0):
            sys.stdout.write('Waiting %s ...\r' % str(counter))
            sys.stdout.flush()
            time.sleep(1)
            counter -= 1
            if (RCON_ENABLED == "true"):
                    if (counter == NOTIFY_TIME):
                        for i in range(0, len(RCON_PORT)):
                            try:
                                rconNotify(RCON_PORT[i], RCON_PASSWORD[i])
                                print("    -Reboot Notified on port " + str(RCON_PORT[i]))
                            except:
                                print("Unable to notify the reboot on port "+str(RCON_PORT[i])+"! Check your config!")


        if (RCON_ENABLED == "true"):
            try:
                for i in range(0, len(RCON_PORT)):
                    rconShutdown(RCON_PORT[i], RCON_PASSWORD[i])
            except:
                print("Unable to stopping the server using rcon, using the classic method...")
                os.system("taskkill /f /im " + PROCNAME)
        else:
            os.system("taskkill /f /im " + PROCNAME)


if (__name__ == '__main__'):
    main()







