# OBS Plugin for Blackmagic HID Devices

## Prerequisites

1. `sudo apt install libhidapi-hidraw0 libhidapi-libusb0`
2. Create `/etc/udev/rules.d/70-blackmagic.rules` with the following content:
```
# Editor Keyboard
SUBSYSTEM=="hidraw", KERNEL=="hidraw*", ATTRS{idVendor}=="1edb", ATTRS{idProduct}=="da0b", MODE="0666"

# Speed Editor Keyboard
SUBSYSTEM=="hidraw", KERNEL=="hidraw*", ATTRS{idVendor}=="1edb", ATTRS{idProduct}=="da0e", MODE="0666"
```

## Installation

1. `git clone https://github.com/justjanne/bmd-hid-obs.git`
2. `pipenv install`
3. Open OBS, navigate to Tools › Scripts and add the script
   `bmd-hid-obs/main.py`

## Usage

Just connect your Resolve SpeedEditor. The script automatically discovers all
attached devices.

### Scene Switching

<kbd>CAM1</kbd> through <kbd>CAM9</kbd> allow you to choose the first 9 scenes
in your scene collection.

By default, these buttons switch the preview scene. You can then use 
<kbd>STOP/PLAY</kbd> to switch them onto the program output.  
If <kbd>LIVE O/WR</kbd> is enabled, these buttons directly affect the program 
output.

### Transitions

Via the properties, you can choose custom transitions for the buttons 
<kbd>CUT</kbd>, <kbd>DIS</kbd> and <kbd>SMTH CUT</kbd>.

These buttons allow you to easily toggle the currently selected transition.
