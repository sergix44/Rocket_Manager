import sys
import time
import os
import urllib
import zipfile
import shutil

#--Constants
URL_ROCKET_STABLE="https://ci.rocket.foundation/view/Rocket.Foundation/job/Rocket%20Release/lastSuccessfulBuild/artifact/RocketLoader/bin/Release/Rocket.zip"
URL_ROCKET_BETA="https://ci.rocket.foundation/view/Rocket.Foundation/job/Rocket%20Beta/lastSuccessfulBuild/artifact/RocketLoader/bin/Release/Rocket.zip"
URL_STEAM="http://media.steampowered.com/installer/steamcmd.zip"

OUTPUT_ZIP_STEAM="steam_temp.zip"
OUTPUT_ZIP_ROCKET="rocket_temp.zip"

PROCNAME = "Unturned.exe"

def loadConfig(name):
    global rebootTime
    global serversToLaunch
    global unturnedPath
    global useBeta
    global steamUser
    global steamPass
    
    if (not os.path.isfile(name)):
        f=open(name,"w")
        f.write("reboot_after_seconds=3600\n")
        f.write("unturned_folder_path=.\\unturned\n")
        f.write("servers_to_launch(separed by a '|')=server1|server2\n")
        f.write("use_rocket_beta_updates=true\n")
        f.write("steam_username=changeme\n")
        f.write("steam_password=changeme\n")
        f.close()
        return True
        
        
    f=open(name, "r")
    ln=f.readline()
    rebootTime=int(ln.split("=")[1])
    ln=f.readline()
    unturnedPath=ln.split("=")[1].rstrip()
    ln=f.readline()
    serversToLaunch=ln.split("=")[1].split("|")
    serversToLaunch[len(serversToLaunch)-1]=serversToLaunch[len(serversToLaunch)-1].rstrip()
    ln=f.readline()
    useBeta=ln.split("=")[1].rstrip()
    ln=f.readline()
    steamUser=ln.split("=")[1].rstrip()
    ln=f.readline()
    steamPass=ln.split("=")[1].rstrip()
    f.close()
    return False
    
def downloader(i):
    err=False
    if (i=="steam"):
        try:
            urllib.urlretrieve (URL_STEAM, OUTPUT_ZIP_STEAM)
        except:
            err=True
            
    if (i=="rocket"):
        try:
            if(useBeta=="false"):
                urllib.urlretrieve (URL_ROCKET_STABLE, OUTPUT_ZIP_ROCKET)
            if(useBeta=="true"):
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

def main():
    print("--------------------------------------------------------------------------------")
    print("                          SergiX44's Rocket Manager 1.3                         ")
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
        print("Launching steam...")
        print "--------------------------------------------------------------------------------\n\n"
        os.system("steamcmd.exe +login "+steamUser+" "+steamPass+" +force_install_dir "+unturnedPath+" +app_update 304930 -beta preview -betapassword OPERATIONMAPLELEAF validate +exit")
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
        print("Installing Rocket...")
        for f in os.listdir("rocket\\"):
            src_file = os.path.join("rocket\\", f)
            dst_file = os.path.join(unturnedPath+"\\Unturned_Data\\Managed\\", f)
            shutil.copyfile(src_file, dst_file)

        #clean up zips and extracted files
        print("Cleaning up...")
        cleanUp()

        #launching servers
        print("Launching servers...")
        for i in range(0, len(serversToLaunch)):
            print("    - Launching "+serversToLaunch[i])
            os.system("start "+unturnedPath+"\Unturned.exe -nographics -batchmode +secureserver/"+serversToLaunch[i])

        #timer
        counter=rebootTime
        while(counter>=0):
                sys.stdout.write('Waiting %s ...\r' % str(counter))
                sys.stdout.flush()
                time.sleep(1)
                counter-=1

        os.system("taskkill /f /im "+PROCNAME)



if (__name__ == '__main__'):
    main()







