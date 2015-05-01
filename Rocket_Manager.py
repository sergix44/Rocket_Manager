import sys
import time
import os
import urllib
import zipfile
import shutil
import socket
import apikey

#--Constants
URL_ROCKET_STABLE="http://api.rocket.foundation/release/latest/"+apikey.key
URL_ROCKET_BETA="http://api.rocket.foundation/beta/latest/"+apikey.key
URL_STEAM="http://media.steampowered.com/installer/steamcmd.zip"

OUTPUT_ZIP_STEAM="steam_temp.zip"
OUTPUT_ZIP_ROCKET="rocket_temp.zip"

PROCNAME = "Unturned.exe"

def writeConfig(name):
    f=open(name,"w")
    f.write("reboot_after_seconds=3600\n")
    f.write("notify_before_seconds=60\n")
    f.write("unturned_folder_path=.\\unturned\n")
    f.write("servers_to_launch(separed_by_a_'|')=server1|server2\n")
    f.write("enable_rcon_reboot_notify=false")
    f.write("rcon_port(separed_by_a_'|')=27013|27014\n")
    f.write("rcon_password(separed_by_a_'|')=rmanager|rmanager\n")
    f.write("use_rocket_beta_updates=true\n")
    f.write("update_validate(unturned_updates)=true\n")
    f.write("steam_username=changeme\n")
    f.write("steam_password=changeme\n")
    f.close()

def loadConfig(name):
    global REBOOT_TIME
    global NOTIFY_TIME
    global SERVERS_TO_LAUNCH
    global RCON_ENABLED
    global RCON_PORT
    global RCON_PASSWORD
    global UNTURNED_PATH
    global USE_BETA
    global VALIDATE_AT_BOOT
    global STEAM_USER
    global STEAM_PASS
    
    if (not os.path.isfile(name)):
        writeConfig(name)
        return True
        
    try:    
        f=open(name, "r")

        #reboot time
        ln=f.readline()
        REBOOT_TIME=int(ln.split("=")[1])

        #notify time
        ln=f.readline()
        NOTIFY_TIME=int(ln.split("=")[1])
        if(NOTIFY_TIME>REBOOT_TIME):
            NOTIFY_TIME=REBOOT_TIME
        
        #unturned path
        ln=f.readline()
        UNTURNED_PATH=ln.split("=")[1].rstrip()

        #servers to launch array
        ln=f.readline()
        SERVERS_TO_LAUNCH=ln.split("=")[1].split("|")
        SERVERS_TO_LAUNCH[len(SERVERS_TO_LAUNCH)-1]=SERVERS_TO_LAUNCH[len(SERVERS_TO_LAUNCH)-1].rstrip()

        #rcon enabled
        ln=f.readline()
        RCON_ENABLED=ln.split("=")[1].rstrip()
        
        #rcon port
        ln=f.readline()
        RCON_PORT=[]
        for i in range(0,len(ln.split("=")[1].split("|"))):
            RCON_PORT.append(int(ln.split("=")[1].split("|")[i]))

        #rcon password
        ln=f.readline()
        RCON_PASSWORD=ln.split("=")[1].split("|")
        RCON_PASSWORD[len(RCON_PASSWORD)-1]=RCON_PASSWORD[len(RCON_PASSWORD)-1].rstrip()
        
        #use beta
        ln=f.readline()
        USE_BETA=ln.split("=")[1].rstrip()

        #validate updates
        ln=f.readline()
        VALIDATE_AT_BOOT=ln.split("=")[1].rstrip()
        
        #steam username
        ln=f.readline()
        STEAM_USER=ln.split("=")[1].rstrip()
        
        #steam password
        ln=f.readline()
        STEAM_PASS=ln.split("=")[1].rstrip()
        
        f.close()
        return False
    
    except:
        writeConfig(name)
        return True
    
    
def downloader(i):
    err=False
    if (i=="steam"):
        try:
            urllib.urlretrieve (URL_STEAM, OUTPUT_ZIP_STEAM)
        except:
            err=True
            
    if (i=="rocket"):
        try:
            if(USE_BETA=="false"):
                urllib.urlretrieve (URL_ROCKET_STABLE, OUTPUT_ZIP_ROCKET)
            if(USE_BETA=="true"):
                urllib.urlretrieve (URL_ROCKET_BETA, OUTPUT_ZIP_ROCKET)
        except:
            err=True
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

def rconNotify(port,passw):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", port))
    print s.recv(1024)
    s.send(passw)
    time.sleep(0.5)
    s.send("\r\n")
    time.sleep(0.5)
    print s.recv(1024)
    s.send("say [Manager] This server will restart in "+str(NOTIFY_TIME)+" seconds")
    time.sleep(0.5)
    s.send("\r\n")
    time.sleep(0.5)
    print s.recv(1024)
    s.close()
    

#--MAIN FUNCTION--#

def main():
    print("--------------------------------------------------------------------------------")
    print("                          SergiX44's Rocket Manager 1.4                         ")
    print("--------------------------------------------------------------------------------\n\n")
    print("Loading config...")
    
    if(loadConfig("config.properties")):
        print("Close and edit config.properties, then restart me!")
        raw_input("Press any key to continue...")
        sys.exit(1)


    if (not os.path.isfile("steamcmd.exe")):
        ex=True
        while (ex):
            sel=raw_input("SteamCMD not found! Would you like download it? (y/n) ")
            if(sel=="y"):
                
                print("Downloading steamcmd...")
                if(downloader("steam")):
                    print("ERROR: Unable to download steam! Please check your internet settings!")
                    raw_input("Press any key to continue...")
                    sys.exit(3)
                    
                zfile = zipfile.ZipFile(OUTPUT_ZIP_STEAM)
                zfile.extractall()
                zfile.close()
                ex=False
            if (sel=="n"):
                ex=False
                print("Closing...")
                time.sleep(1)
                sys.exit(1)

    while 1:
        #reloading config
        if(loadConfig("config.properties")):
            print("Failed loading config! :( \nConfig file regenerated, edit config.properties, then restart me!")
            raw_input("Press any key to continue...")
            sys.exit(2)
            
        #launch steam cmd
        if((not os.path.isdir(UNTURNED_PATH)) or (VALIDATE_AT_BOOT=="true")):
            print("Launching steam...")
            print "--------------------------------------------------------------------------------\n\n"
            os.system("steamcmd.exe +login "+STEAM_USER+" "+STEAM_PASS+" +force_install_dir "+UNTURNED_PATH+" +app_update 304930 -beta preview -betapassword OPERATIONMAPLELEAF validate +exit")
            print "--------------------------------------------------------------------------------\n\n"

        #download and extract
        print("Downloading rocket...")
        if(downloader("rocket")):
            print("ERROR: Unable to download rocket! Please check your internet settings!")
            raw_input("Press any key to continue...")
            sys.exit(3)

        print("Extracting rocket...")
        extractor(OUTPUT_ZIP_ROCKET)

        #Moving files
        try:
            print("Installing Rocket...")
            for f in os.listdir("rocket\\"):
                src_file = os.path.join("rocket\\", f)
                dst_file = os.path.join(UNTURNED_PATH+"\\Unturned_Data\\Managed\\", f)
                shutil.copyfile(src_file, dst_file)
        except IOError:
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
            print("    - Launching "+SERVERS_TO_LAUNCH[i])
            os.system("start "+UNTURNED_PATH+"\Unturned.exe -nographics -batchmode +secureserver/"+SERVERS_TO_LAUNCH[i])

        #timer
        counter=REBOOT_TIME
        while(counter>=0):
                sys.stdout.write('Waiting %s ...\r' % str(counter))
                sys.stdout.flush()
                time.sleep(1)
                counter-=1
                if(RCON_ENABLED=="true"):
                    try:
                        if(counter==NOTIFY_TIME):
                            for i in range(0,len(RCON_PORT)):
                                rconNotify(RCON_PORT[i],RCON_PASSWORD[i])
                    except:
                        print("Impossible notify the reboot! Check you config")

        os.system("taskkill /f /im "+PROCNAME)



if (__name__ == '__main__'):
    main()







