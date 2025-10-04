# Dark Volume OSD (PyQt6 / PyQt5) — README

A slick, black, shiny on-screen display (OSD) for system volume on Linux.

## Default theme:
</br>
<img width="556" height="438" alt="Image" src="https://github.com/user-attachments/assets/5be9f3cf-1df4-43ac-8569-dfd61e47b6d9" />

## Alternative themes:
</br>
<img width="758" height="422" alt="Image" src="https://github.com/user-attachments/assets/b0c32aa4-cd40-4f04-b7ee-e4932888628f" />

</br>
</br>
</br>
<img width="444" height="452" alt="Image" src="https://github.com/user-attachments/assets/6c56235f-5746-46d2-894a-930dcecca6a9" />
</br>
</br>
<img width="502" height="465" alt="Image" src="https://github.com/user-attachments/assets/3e0437eb-f2bf-47b5-88a7-09f980d6309c" />
</br>
</br>

## Features

Works with PyQt6 or PyQt5 (auto-fallback).

Listens to media keys and Alt+↑ / Alt+↓ / Alt+M via evdev.

Controls all active PulseAudio/PipeWire sinks (every playback device).

Glossy black progress bar; centered near bottom; auto-hides.

Graceful fallback when window opacity/animations aren’t supported.

Multiple themes to choose from.

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

### Using themes

How to use

Default theme (dark):
		python3 osd.py


### Select a theme:

		python3 osd.py --theme=blue   # futuristic blue

		python3 osd.py --theme=grey   # grey worn-out

		python3 osd.py --theme=wood   # wood-like

		python3 osd.py --theme=dark   # dark this is the default

### Customizing via Systemd

		mkdir -p ~/.config/volume-osd
		printf 'theme=blue\n' > ~/.config/volume-osd/osd.conf
		systemctl --user restart volume-osd


##### Tip: On Wayland I have found that the best way to get the osd working or deactivated is to reboot after running the scripts.

##### Running the Volume OSD via .xinitrc or .config/openbox/autostart etc. is also possible by adding the line: python3 osd.py & 

Copyright (c) 2025 JJ Posti <techtimejourney.net> This program comes with ABSOLUTELY NO WARRANTY; for details see: http://www.gnu.org/copyleft/gpl.html.  
This is free software, and you are welcome to redistribute it under GPL Version 2, June 1991")
