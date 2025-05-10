from tkinter import messagebox
from httpx import get
from subprocess import run
from sys import exit

class VersionCheck:
    def __init__(self):
        self.url = "https://pastebin.com/raw/BvDwf63w"
        self.current_version = 1.0
    
    def checkForUpdates(self):
        version = float(get(self.url).text)
        
        if self.current_version != version:
            if messagebox.askyesno("Update available", f"Version {version} is now available. Would you like to download it?"):
                run("start https://github.com/snytex/song-pitcher", shell=True)
                exit(1)