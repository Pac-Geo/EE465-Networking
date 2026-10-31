from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from gpiozero import Button
import subprocess
import time
import re

# Initializations 
#OLED
serial = i2c(port=1, address=0x3C)
device = ssd1306(serial)
#GPIO 23 Switch
button = Button(23, pull_up=True, bounce_time=0.05)
# Select your network interface
interface = "wlan0"

# Obtain the current network IP
def get_ip():
    result = subprocess.run(
        ["ip", "-4", "route", "get", "1.1.1.1"],
        capture_output=True,
        text=True
    )

    match = re.search(r"\bsrc\s+(\d+\.\d+\.\d+\.\d+)", result.stdout)

    return match.group(1) if match else "Waiting for IP"
# Obtain current MAC address
def get_mac():
    with open(f"/sys/class/net/{interface}/address") as file:
        return file.read().strip()
# Continuously monitor the IP address
last_display = None

while True:

    if button.is_pressed:
        label = "MAC Address:"
        value = get_mac()
    else:
        label = "IP Address:"
        value = get_ip()

    # Update display when information changes
    current_display = (label, value)

    if current_display != last_display:
        with canvas(device) as draw:
            draw.text((2, 2), label, fill="white")
            draw.text((2, 20), value, fill="white")

        last_display = current_display

    time.sleep(0.5)
