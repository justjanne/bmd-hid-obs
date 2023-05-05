# Installing hidapi

## Windows

Binary distributions are provided by [libusb/hidapi](https://github.com/libusb/hidapi/releases/latest)

## Linux

Create `/etc/udev/rules.d/70-blackmagic.rules` with the following content:
```
# Editor Keyboard
SUBSYSTEM=="hidraw", KERNEL=="hidraw*", ATTRS{idVendor}=="1edb", ATTRS{idProduct}=="da0b", MODE="0666"
SUBSYSTEM=="hidraw", KERNEL=="hidraw*", KERNELS=="*:1EDB:DA0B.*", MODE="0666"

# Speed Editor
SUBSYSTEM=="hidraw", KERNEL=="hidraw*", ATTRS{idVendor}=="1edb", ATTRS{idProduct}=="da0e", MODE="0666"
SUBSYSTEM=="hidraw", KERNEL=="hidraw*", KERNELS=="*:1EDB:DA0E.*", MODE="0666"
```

Then you'll need to install hidapi:

### Ubuntu/Debian

```bash
apt install libhidapi-hidraw0 libhidapi-libusb0
```

### Fedora

```bash
dnf install hidapi
```

### Arch Linux

1. Enable the community repository in `/etc/pacman.conf`

```ini
[community]
Include = /etc/pacman.d/mirrorlist
```

2. Install hidapi

```bash
pacman -Sy hidapi
```

## FreeBSD

Binary distributions are available.

```
pkg install -g 'py3*-hid'
```
