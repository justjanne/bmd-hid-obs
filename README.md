# OBS Plugin for Blackmagic HID Devices

## Installation

1. Make sure you've installed all [prerequisites](PREREQUISITES.md)
2. `git clone https://github.com/justjanne/bmd-hid-obs.git`
3. `pipenv install`
4. Open OBS, navigate to Tools › Scripts and add the script
   `bmd_obs_plugin.py`

## Usage

Just connect your Resolve SpeedEditor. The script automatically discovers all
attached devices.

### Settings

- **Transition: None**  
  Choose which transition should be used when transitions have been disabled
  with the <kbd>TRANS</kbd> button.
- **Transition: Cut**  
  Choose which transition should be selected when pressing <kbd>CUT</kbd>.
- **Transition: Dis**  
  Choose which transition should be selected when pressing <kbd>DIS</kbd>.
- **Transition: Smth Cut**  
  Choose which transition should be selected when pressing 
  <kbd>SMTH CUT</kbd>. 

### Scene Switching

<kbd>CAM1</kbd> through <kbd>CAM9</kbd> allow you to choose the first 9 scenes
in your scene collection.

By default, these buttons switch the preview scene. Use <kbd>STOP/PLAY</kbd> 
to switch the current preview onto the program output. If <kbd>LIVE O/WR</kbd>
is enabled, these buttons directly affect the program output.

### Transitions

You can use <kbd>TRANS</kbd> to toggle transition animations.

If transitions are enabled, you can use <kbd>CUT</kbd>, <kbd>DIS</kbd> and
<kbd>SMTH CUT</kbd> to quickly choose transition animations.

If the current transition supports configuring the duration, you can hold
<kbd>TRANS DUR</kbd> and use the jog wheel to adjust the transition duration.

