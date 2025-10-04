#!/usr/bin/env python3
import sys
import os
import subprocess

def install_systemd_service():
    # Prevent running as root (would install into /root)
    if os.getuid() == 0:
        print("[ERROR] Please run this script as a regular user, not as root.")
        sys.exit(1)

    # Ensure $HOME/.config/systemd/user exists
    home = os.path.expanduser("~")
    service_dir = os.path.join(home, ".config", "systemd", "user")
    print("[INFO] Ensuring systemd service directory exists:", service_dir)
    try:
        os.makedirs(service_dir, exist_ok=True)
    except Exception as e:
        print(f"[ERROR] Failed to create directory {service_dir}: {e}")
        sys.exit(1)

    service_path = os.path.join(service_dir, "volume-osd.service")
    print("[INFO] Service file target:", service_path)

    # Hard-coded path to your osd.py script
    script_path = "/usr/share/osd.py"
    if not os.path.exists(script_path):
        print("[ERROR] osd.py not found at:", script_path)
        sys.exit(1)

    # Get current DISPLAY, default to :0
    display_env = os.environ.get("DISPLAY", ":0")

    # Service file content with HOME + XDG_CONFIG_HOME set
    service_file_content = f"""[Unit]
Description=Volume OSD Service
After=graphical-session.target

[Service]
Type=simple
# Delay startup to allow the desktop environment to fully initialize
ExecStartPre=/bin/sleep 5
ExecStart={sys.executable} {script_path}
Restart=always
RestartSec=5
Environment=DISPLAY={display_env}
Environment=HOME=%h
Environment=XDG_RUNTIME_DIR=/run/user/%U
Environment=XDG_CONFIG_HOME=%h/.config

[Install]
WantedBy=default.target
"""

    # Always overwrite
    try:
        if os.path.exists(service_path):
            print("[INFO] Overwriting existing service file.")
        else:
            print("[INFO] Creating new service file.")
        with open(service_path, "w") as f:
            f.write(service_file_content)
        print("[INFO] Service file written to:", service_path)
    except Exception as e:
        print(f"[ERROR] Could not write service file: {e}")
        sys.exit(1)

    # Reload + enable + restart (idempotent)
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
    subprocess.run(["systemctl", "--user", "enable", "volume-osd.service"], check=False)
    subprocess.run(["systemctl", "--user", "restart", "volume-osd.service"], check=False)
    print("[INFO] Systemd service installed and restarted.")

if __name__ == "__main__":
    install_systemd_service()
