# Dark Volume OSD (PyQt6 / PyQt5) — README

A slick, black, shiny on-screen display (OSD) for system volume on Linux.

<img width="435" height="118" alt="Image" src="https://github.com/user-attachments/assets/a65bc5f5-a28e-4552-a522-5ff40d53099c" />

## Features

Works with PyQt6 or PyQt5 (auto-fallback).

Listens to media keys and Alt+↑ / Alt+↓ / Alt+M via evdev.

Controls all active PulseAudio/PipeWire sinks (every playback device).

Glossy black progress bar; centered near bottom; auto-hides.

Graceful fallback when window opacity/animations aren’t supported.

### Requirements
Debian/Ubuntu packages

Pick one Qt binding (PyQt6 or PyQt5):


sudo apt update

# PyQt6 route:
		sudo apt install -y python3-pyqt6 python3-evdev pulseaudio-utils udev
		
		
# OR PyQt5 route:
		sudo apt install -y python3-pyqt5 python3-evdev pulseaudio-utils udev


### Run:

		sudo bash install_rule.sh #To install the needed rule.
		sudo cp osd.py /usr/share/
		sudo chmod +x  /usr/share/osd.py
		python3 systemd.py
		systemctl --user status volume-osd  # See the status of the service
		systemctl --user enable volume-osd  # Enable the service during system startup
		systemctl --user start volume-osd  # Start the service


Uninstall:
				 sudo bash uninstall_rule.sh  # To uninstall the needed rule.
                 sudo rm osd.py /usr/share/

### Usage  
- ALT arrow up == Volume up.
- ALT arrow down == Volume down.
- ALT m == Volume mute/unmute.

##### Tip: On Wayland I have found that the best way to get the osd working or deactivated is to reboot after running the scripts.

##### Running the Volume OSD via .xinitrc or .config/openbox/autostart etc. is also possible by adding the line: python3 osd.py & 

Copyright (c) 2025 JJ Posti <techtimejourney.net> This program comes with ABSOLUTELY NO WARRANTY; for details see: http://www.gnu.org/copyleft/gpl.html.  
This is free software, and you are welcome to redistribute it under GPL Version 2, June 1991")
