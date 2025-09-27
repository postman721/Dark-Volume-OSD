#!/bin/bash
# Uninstall udev rule for Volume OSD (strict)

set -e

USER_NAME=${SUDO_USER:-$USER}
GROUP_NAME="osdinput"
RULE_FILE="/etc/udev/rules.d/99-osdinput.rules"

echo "[INFO] Uninstalling OSD udev rules..."

# Remove udev rule
if [ -f "$RULE_FILE" ]; then
    echo "[INFO] Removing $RULE_FILE ..."
    sudo rm -f "$RULE_FILE"
    sudo udevadm control --reload-rules
    sudo udevadm trigger
else
    echo "[WARN] No udev rule found at $RULE_FILE"
fi

# Remove user from group
echo "[INFO] Removing user '$USER_NAME' from group '$GROUP_NAME'..."
if getent group "$GROUP_NAME" >/dev/null; then
    sudo gpasswd --delete "$USER_NAME" "$GROUP_NAME" || true
else
    echo "[WARN] Group '$GROUP_NAME' does not exist"
fi

echo "[INFO] Done."
echo "       You may also delete the group with: sudo groupdel $GROUP_NAME (if no longer needed). Logout or reboot might be needed."
