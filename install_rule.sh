#!/bin/bash
# Install udev rule for Volume OSD (safe + strict: only keyboards)
# Adds user to osdinput group and verifies device permissions

set -e

USER_NAME=${SUDO_USER:-$USER}
GROUP_NAME="osdinput"
RULE_FILE="/etc/udev/rules.d/99-osdinput.rules"

echo "[INFO] Installing OSD udev rules (strict)..."

# Create group if it does not exist
if ! getent group "$GROUP_NAME" >/dev/null; then
    echo "[INFO] Creating group '$GROUP_NAME'..."
    sudo groupadd "$GROUP_NAME"
fi

# Add user to group
echo "[INFO] Adding user '$USER_NAME' to group '$GROUP_NAME'..."
sudo gpasswd --add "$USER_NAME" "$GROUP_NAME"

# Create strict udev rule (only keyboards)
echo "[INFO] Writing udev rule to $RULE_FILE ..."
sudo bash -c "cat > $RULE_FILE" <<EOF
# Volume OSD: grant access only to keyboard input devices
KERNEL=="event*", SUBSYSTEM=="input", ENV{ID_INPUT_KEYBOARD}=="1", GROUP="$GROUP_NAME", MODE="660"
EOF

# Reload udev rules
echo "[INFO] Reloading udev rules..."
sudo udevadm control --reload-rules
sudo udevadm trigger

# Verification
echo "[INFO] Verifying permissions on keyboard devices..."
KEYBOARD_DEVS=$(grep -l "Handlers=.*kbd" /proc/bus/input/devices | sed 's/.*event/event/')
for dev in $KEYBOARD_DEVS; do
    DEV_PATH="/dev/input/$dev"
    if [ -e "$DEV_PATH" ]; then
        ls -l "$DEV_PATH"
    else
        echo "[WARN] Could not find $DEV_PATH"
    fi
done

echo
echo "[INFO] Done."
echo "       - Devices above should now belong to group '$GROUP_NAME' and be mode 660."
echo "       - User '$USER_NAME' must log out and back in for group changes to take effect. Sometimes Wayland might require a reboot."
