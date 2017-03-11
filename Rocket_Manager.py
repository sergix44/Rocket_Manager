import os
import platform
import shutil
import socket
import sys
import time
import urllib
import zipfile
from xml.etree import ElementTree

# --Constants

MANAGER_FOLDER = os.path.join(".", "RocketManager")
STEAM_FOLDER = os.path.join(".", "steamcmd")
TMP_FOLDER = os.path.join(".", "temp")
UNTURNED_PATH = os.path.join(".", "unturned")

ROCKET_EXTRACT_FOLDER = os.path.join(MANAGER_FOLDER, "last_rocket_download")
BACKUP_BUNDLES_FOLDER = os.path.join(MANAGER_FOLDER, "bundles_backup")

STEAM_EXECUTABLE = "steamcmd.exe" if platform.system() == "Windows" else "steamcmd.sh"
STEAM_EXECUTABLE = os.path.join(STEAM_FOLDER, STEAM_EXECUTABLE)

# For Win
URL_ROCKET_BETA = "https://ci.rocketmod.net/job/Rocket.Unturned/lastSuccessfulBuild/artifact/Rocket.Unturned/bin/Release/Rocket.zip"
URL_STEAM_WIN = "http://media.steampowered.com/installer/steamcmd.zip"

OUTPUT_ZIP_STEAM_WIN = os.path.join(TMP_FOLDER, "steam_temp.zip")
OUTPUT_ZIP_STEAM_LINUX = os.path.join(TMP_FOLDER, "steamcmd_temp.tar.gz")
OUTPUT_ZIP_ROCKET = os.path.join(TMP_FOLDER, "rocket_temp.zip")

# For Linux

URL_ROCKET_LINUX = "https://ci.rocketmod.net/job/Rocket.Unturned%20Linux/lastSuccessfulBuild/artifact/Rocket.Unturned/bin/Release/Rocket.zip"
URL_STEAM_LINUX = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz"

PROCNAME_WIN = "Unturned.exe"

socket.setdefaulttimeout(10)


# --Functions
def write_config(name):
    f = open(name, "w")
    f.write('''<?xml version="1.0" encoding="UTF-8"?>
<config>
	<rebootEvery seconds="3600" />
	<unturnedFolder recoveryBundlesAfterUpdates="false" />
	<rocket useRocket="true"/>
	<steam username="" password="" />
	<steamUpdates validate="true" />
	<servers rconEnabled="false">
		<server name="server1" rconPort="27013" rconPassword="pass" />
		<server name="server2" rconPort="27014" rconPassword="pass" />
	</servers>
	<notifyBefore seconds="60" />
</config>''')
    f.close()


def load_config(name):
    global REBOOT_TIME
    global NOTIFY_TIME
    global SERVERS_TO_LAUNCH
    global RCON_ENABLED
    global RCON_PORT
    global RCON_PASSWORD
    global VALIDATE_AT_BOOT
    global STEAM_USER
    global STEAM_PASS
    global BACKUP_BUNDLES
    global ROCKET_ENABLED
    
    if not os.path.isfile(name):
        write_config(name)
        return True
    try:
        with open(name, 'rt') as f:
            tree = ElementTree.parse(f)
        
        node = tree.find("rebootEvery")
        REBOOT_TIME = int(node.attrib.get("seconds"))
        
        node = tree.find("steamUpdates")
        VALIDATE_AT_BOOT = node.attrib.get("validate")
        
        node = tree.find("unturnedFolder")
        BACKUP_BUNDLES = node.attrib.get("recoveryBundlesAfterUpdates")
        if VALIDATE_AT_BOOT != "true":
            BACKUP_BUNDLES = "false"
        
        node = tree.find("rocket")
        ROCKET_ENABLED = node.attrib.get("useRocket")
        
        node = tree.find("steam")
        STEAM_USER = node.attrib.get("username")
        STEAM_PASS = node.attrib.get("password")
        
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
        if NOTIFY_TIME > REBOOT_TIME:
            NOTIFY_TIME = REBOOT_TIME
        return False
    
    except:
        write_config(name)
        return True


def downloader(i):
    err = False
    if i == "steam":
        try:
            if platform.system() == "Windows":
                urllib.urlretrieve(URL_STEAM_WIN, OUTPUT_ZIP_STEAM_WIN)
            else:
                urllib.urlretrieve(URL_STEAM_LINUX, OUTPUT_ZIP_STEAM_LINUX)
        
        except:
            err = True
    
    if i == "rocket":
        try:
            if platform.system() == "Windows":
                urllib.urlretrieve(URL_ROCKET_BETA, OUTPUT_ZIP_ROCKET)
            else:
                urllib.urlretrieve(URL_ROCKET_LINUX, OUTPUT_ZIP_ROCKET)
        except:
            err = True
    return err


def extractor(namezip, folder):
    zfile = zipfile.ZipFile(namezip)
    if not os.path.exists(folder):
        os.makedirs(folder)
    zfile.extractall(folder)
    zfile.close()


def test_zip(namezip):
    try:
        zzip = zipfile.ZipFile(namezip)
        checkzip = zzip.testzip()
        zzip.close()
        if checkzip is None:
            return True
        else:
            return False
    except zipfile.BadZipfile:
        return False
    except IOError:
        return False


def clean_up():
    for the_file in os.listdir(TMP_FOLDER):
        file_path = os.path.join(TMP_FOLDER, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception:
            pass


def installer(folder):
    try:
        shutil.rmtree(os.path.join(folder, 'Scripts'))
        return merge_files(folder, UNTURNED_PATH)
    except IOError:
        return True


def merge_files(root_src_dir, root_dst_dir):
    try:
        for src_dir, dirs, files in os.walk(root_src_dir):
            dst_dir = src_dir.replace(root_src_dir, root_dst_dir)
            if not os.path.exists(dst_dir):
                os.mkdir(dst_dir)
            for file_ in files:
                src_file = os.path.join(src_dir, file_)
                dst_file = os.path.join(dst_dir, file_)
                if os.path.exists(dst_file):
                    os.remove(dst_file)
                shutil.move(src_file, dst_dir)
        return False
    except:
        return True


def rcon(port, passw, message=None, command=None):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("127.0.0.1", port))
        s.settimeout(5)
        s.send("login " + passw + "\n")
        s.recv(1024)
        if message is not None:
            s.send("broadcast {0}\n".format(message))
            s.recv(1024)
        if command is not None:
            s.send("{0}\n".format(command))
            s.recv(1024)
        s.send("quit\n")
        s.recv(1024)
        time.sleep(1.5)
        s.close()
        
        return False
    except Exception:
        return True


def kill_server(item=None):
    if platform.system() == "Windows":
        os.system("taskkill /f /im " + PROCNAME_WIN)
    else:
        os.system("screen -S " + item + ' -X stuff "save^M"')
        time.sleep(5)
        os.system("screen -S " + item + ' -X stuff "shutdown^M"')


def start_server(server):
    if platform.system() == "Windows":
        os.system("cd " + UNTURNED_PATH + "\ & start Unturned.exe -nographics -batchmode -silent-crashes +secureserver/" + server)
    else:
        st_api = os.path.join(STEAM_FOLDER, "linux32", "steamclient.so")
        ut_api = os.path.join(UNTURNED_PATH, "Unturned_Data", "Plugins", "x86", "steamclient.so")
        os.system("if [ -f " + st_api + " ]; then if ! diff " + st_api + " " + ut_api + " >/dev/null; then cp " + st_api + " " + ut_api + "; fi fi")
        os.system("cd " + UNTURNED_PATH + " && ulimit -n 2048 && screen -dmS " + server + " mono RocketLauncher.exe " + server)


def steamcmd_run():
    print ("------------------------------------SteamCMD------------------------------------\n")
    if platform.system() == "Windows":
        os.system(STEAM_EXECUTABLE + " +login " + STEAM_USER + " " + STEAM_PASS + " +force_install_dir " + os.path.join("..", UNTURNED_PATH) + " +app_update 304930 validate +exit")
    else:
        os.system(STEAM_EXECUTABLE + " +@sSteamCmdForcePlatformBitness 32 \
         +login " + STEAM_USER + " " + STEAM_PASS + " +force_install_dir " + os.path.join("..", UNTURNED_PATH) + " +app_update 304930 validate +exit")
    print ("\n------------------------------------END-----------------------------------------\n\n")


def bundles(mode):
    try:
        if mode == "save":
            if not os.path.exists(BACKUP_BUNDLES_FOLDER):
                os.makedirs(BACKUP_BUNDLES_FOLDER)
            bundles_folder = os.path.join(BACKUP_BUNDLES_FOLDER, "Bundles")
            if os.path.exists(bundles_folder):
                shutil.rmtree(bundles_folder)
            shutil.copytree(os.path.join(UNTURNED_PATH, "Bundles"), bundles_folder)
            return False
        if mode == "restore":
            return merge_files(os.path.join(BACKUP_BUNDLES_FOLDER, "Bundles"), os.path.join(UNTURNED_PATH, "Bundles"))
    except Exception:
        return True


def bootstrap():
    print("--------------------------------------------------------------------------------")
    print("                          SergiX44's Rocket Manager 1.9.5                       ")
    print("--------------------------------------------------------------------------------\n\n")
    
    print("> Checking folders...")
    if not os.path.exists(MANAGER_FOLDER):
        os.makedirs(MANAGER_FOLDER)
    if not os.path.exists(STEAM_FOLDER):
        os.makedirs(STEAM_FOLDER)
    if not os.path.exists(TMP_FOLDER):
        os.makedirs(TMP_FOLDER)
    
    print("> Loading config...")
    if load_config(os.path.join(MANAGER_FOLDER, "config_RocketManager.xml")):
        print("Close and edit config_RocketManager.xml, then restart me!")
        raw_input("Press any key to continue...")
        sys.exit(1)
    
    if not os.path.isfile(STEAM_EXECUTABLE):
        ex = True
        while ex:
            sel = raw_input("> SteamCMD not found! Would you like download it? (y/n) ")
            if sel == "y":
                print("> Downloading steamcmd...")
                if downloader("steam"):
                    print("ERROR: Unable to download steam! Please check your internet settings!")
                    raw_input("Press any key to continue...")
                    sys.exit(3)
                
                if platform.system() == "Windows":
                    extractor(OUTPUT_ZIP_STEAM_WIN, STEAM_FOLDER)
                else:
                    os.system("tar -xzf " + OUTPUT_ZIP_STEAM_LINUX + " -C " + STEAM_FOLDER)
                    os.system("chmod 755 " + STEAM_EXECUTABLE)
                    os.system("dpkg --add-architecture i386")
                    os.system("apt-get update")
                    os.system(
                        "apt-get -y install libmono2.0-cil mono-runtime screen htop unzip lib32gcc1 lib32stdc++6 libglu1-mesa libxcursor1 libxrandr2 libc6:i386 libgl1-mesa-glx:i386 libxcursor1:i386 libxrandr2:i386")
                ex = False
            if sel == "n":
                ex = False
                print("Closing...")
                time.sleep(1)
                sys.exit(1)
    if (platform.system() != "Windows") and ROCKET_ENABLED == "false":
        print("ERROR: This tool can run under Linux only with Rocket enabled, due a bug with the Unturned console. Please enable Rocket.")
        sys.exit(100)


def main():
    bootstrap()
    
    while 1:
        rocket_installed = True
        rocket_downloaded = True
        cycle_interrupted = False
        
        # reloading config
        print("> Reloading config...")
        if load_config(os.path.join(MANAGER_FOLDER, "config_RocketManager.xml")):
            print("> Failed loading config. \n"
                  "Config file regenerated, edit config_RocketManager.xml, then restart.")
            raw_input("Press any key to continue...")
            sys.exit(2)
        
        # saving bundles
        if BACKUP_BUNDLES == "true":
            print("> Saving Bundles...")
            if bundles("save"):
                print("ERROR: Cannot saving Bundles, aborting...")
        
        # launch steam cmd
        if (not os.path.isdir(UNTURNED_PATH)) or (VALIDATE_AT_BOOT == "true"):
            print("> Launching SteamCMD...")
            steamcmd_run()
        
        # recovering bundles
        if BACKUP_BUNDLES == "true":
            print("> Recovering Bundles...")
            if bundles("restore"):
                print("ERROR: Cannot recovering Bundles, aborting...")
        
        if ROCKET_ENABLED == "true":
            # download
            print("> Downloading rocket...")
            count = 5
            while downloader("rocket"):
                print("ERROR: Unable to download rocket! Please check your internet settings!\n"
                      "> Retrying in 5 seconds..")
                if count == 0:
                    print("ERROR: Unable to download rocket after 5 retries, skipping...")
                    break
                count -= 1
                time.sleep(5)
            
            # extract
            print("> Extracting rocket...")
            if test_zip(OUTPUT_ZIP_ROCKET):
                if os.path.exists(ROCKET_EXTRACT_FOLDER):
                    shutil.rmtree(ROCKET_EXTRACT_FOLDER)
                extractor(OUTPUT_ZIP_ROCKET, ROCKET_EXTRACT_FOLDER)
            else:
                print("> Failed to extract Rocket zip (maybe a malformed zip?)")
                if os.path.exists(ROCKET_EXTRACT_FOLDER):
                    print("> Using the lastest correct download...")
                else:
                    print("> Not failover found, launching servers...")
                    rocket_downloaded = False
            
            # Moving files
            if rocket_downloaded:
                print("> Installing rocket...")
                if installer(ROCKET_EXTRACT_FOLDER):
                    print("> Error installing rocket, looking for opened game instances...")
                    kill_server()
                    time.sleep(1)
                    if installer(ROCKET_EXTRACT_FOLDER):
                        print("> Unable to install rocket! Restarting the procedure...")
                        clean_up()
                        rocket_installed = False
            
            # clean up zips and extracted files
            print("> Cleaning up...")
            clean_up()
        
        if (rocket_installed and ROCKET_ENABLED) or (not ROCKET_ENABLED):
            # launching servers
            print("> Launching servers...")
            for i in range(0, len(SERVERS_TO_LAUNCH)):
                print("    - Launching " + SERVERS_TO_LAUNCH[i])
                start_server(SERVERS_TO_LAUNCH[i])
                time.sleep(1)
            
            # timer
            counter = REBOOT_TIME
            while counter >= 0:
                try:
                    sys.stdout.write('> Waiting %s ...\r' % str(counter))
                    sys.stdout.flush()
                    time.sleep(1)
                    counter -= 1
                    if (RCON_ENABLED == "true") and (counter == NOTIFY_TIME) and (ROCKET_ENABLED == "true"):
                        for i in range(0, len(RCON_PORT)):
                            if rcon(RCON_PORT[i], RCON_PASSWORD[i], "[Rocket_Manager] This server will restart in " + str(NOTIFY_TIME) + " seconds"):
                                print("    - Unable to notify the reboot on port " + str(RCON_PORT[i]) + "! Check your config!")
                            else:
                                print("    - Reboot Notified on port " + str(RCON_PORT[i]))
                except KeyboardInterrupt:
                    print("\n> Stopping the counting cycle ...")
                    cycle_interrupted = True
                    break
            
            if cycle_interrupted:
                inp = raw_input("> You have interrupted the cycle, would you like to stop the servers? (Y/n) ")
                if inp.lower() == "n":
                    print("> Bye!")
                    sys.exit(0)
            
            if (RCON_ENABLED == "true") and (ROCKET_ENABLED == "true"):
                for i in range(0, len(RCON_PORT)):
                    if rcon(RCON_PORT[i], RCON_PASSWORD[i], "Rebooting now...", "shutdown"):
                        print("> Unable to stopping the server using rcon, using the classic method...")
                        if platform.system() == "Windows":
                            kill_server()
                        else:
                            for i in range(0, len(SERVERS_TO_LAUNCH)):
                                kill_server(SERVERS_TO_LAUNCH[i])
            else:
                if platform.system() == "Windows":
                    kill_server()
                else:
                    for i in range(0, len(SERVERS_TO_LAUNCH)):
                        kill_server(SERVERS_TO_LAUNCH[i])
            
            if cycle_interrupted:
                inp = raw_input("> You have interrupted the cycle, would you to exit? (y/N) ")
                if inp.lower() == "y":
                    print("> Bye!")
                    sys.exit(0)


if __name__ == '__main__':
    main()
