# Used Raspian Image: Stretch @ 2019-04-08
Link
https://downloads.raspberrypi.org/raspbian/images/raspbian-2019-04-09/2019-04-08-raspbian-stretch.zip



todo:
https://blog.bigbinary.com/2018/09/12/configuring-memory-allocation-in-imagemagick.html


# Photobooth

## Description

Photobooth based on Raspberry Pi + RaspiCam + Canon Selphy CP1300 printer

### see also:
https://www.hackster.io/ericBcreator/photo-booth-powered-by-a-raspberry-pi-23b491


## Components
Raspberry PI 3
Display: 10.1 Inch with HDMI converter (Resolution: 1024x600)
Printer: Canon Selphy CP1300
Buttons: Arcade Buttons
Housing: Plastic Box
Power: 5V/5A Powersupply (5Amps not needed, 2Amps should be enough)

### todo - Blockschaltbild

## Install

- download raspbian stretch lite image
- install to SD Card
- boot raspberry the first time
- login with pi/rasperry


### config raspberry
- sudo raspi-config
- setup `Boot Options` -> `Desktop/CLI` -> `Console Autologin`
- setup `locals` / `network (incl Hostname)` / `keyboard layout`
- setup `interfacing` -> `Camera enable` / `SSH enable` / `I2C enable`
- setup `Advanced Options` -> `Overscan enable (if necessary)` / `Memory Split to 256 MB`
- exit raspi-config

### Change resolution (if necessary)
- sudo nano `/boot/config.txt`

- add

    `# uncomment to force a console size. By default it will be display's size minus`

	`# overscan.`

	`#framebuffer_width=1024`

	`#framebuffer_height=600`

	`#hdmi_ignore_edid=0xa5000080`

	`hdmi_cvt=1024 600 60 3 0 0 0`

	`# uncomment to force a specific HDMI mode (this will force VGA)`

	`hdmi_group=2`

	`hdmi_mode=87`

- see also:
	https://www.raspberrypi.org/forums/viewtopic.php?t=14914

- also add `dispmanx_offline=1` to /boot/config.txt

- see also:
	https://github.com/raspberrypi/userland/issues/232


- sudo reboot


### Update software
- `sudo rpi-udpate` - uodate firmware of raspberry to newer version (at this moment, 4.19 is new released)
- `sudo apt-get update`
- `sudo apt-get upgrade`
- `sudo apt-get install cups python3-dev python3-pip imagemagick python3-cups python3-picamera python3-rpi.gpio git install libusb-1.0 install libcups2-dev python3-usb python3-pil.imagetk`

- if RPGPIO fails, try `sudo pip3 install RPi.GPIO`

### install needed python packages
- `sudo pip3 install pyudev`
- `sudo pip3 install psutil`
- `sudo pip3 install transitions`
- `sudo pip3 install Wand`




### install newer Gutenprint Driver (V 5.3)
- `https://www.raspberrypi.org/forums/viewtopic.php?t=219763`
- Add new unstable Source
 - `sudo nano /etc/apt/sources.list`
- Add the following lines:
 - `deb [trusted=yes] http://ftp.us.debian.org/debian sid main`
 - `deb-src [trusted=yes] http://ftp.us.debian.org/debian sid main`
 - close
- `sudo apt-get update`
- `sudo apt-get -t sid install printer-driver-gutenprint`
- `sudo reboot`
- after installing Gutenprint, uncomment in /etc/apt/sources.list
- `deb [trusted=yes] http://ftp.us.debian.org/debian sid main`
- `deb-src [trusted=yes] http://ftp.us.debian.org/debian sid main`


### setup cups 
- edit cups config file
- `sudo nano /etc/cups/cupsd.conf`
- -> change `Listen localhost:631` to `Port 631` -> Save and exit
- add following line to  `Location /` and `Location /admin` and `Location /admin/conf`

  - `Allow @LOCAL`

- add user pi to group lpadmin
- `sudo usermod -aG lpadmin pi`

- `sudo service cups restart`
- browse to `IPaddress of Raspi:631/admin/`
- login with pi/raspberry
- click `add printer`
- choose `local printer` ->  `Canon SELPHY CP1300 (Canon SELPHY CP1300)` (if not listed - is the printer connected and powered on?)
- `change standardsettings` ->  `Printer Features Common` -> `Borderless` -> `Yes`


## Get the Software
- clone this github (https://github.com/sebmueller/Photobooth) to local folder (/home/pi/Photobooth) 
- If using another folder, change to helper scripts in the Scripts folder



### add script to autostart
- `sudo nano /etc/rc.local`
- add befor exit 0
- `sudo python3 /home/pi/Photobooth/photobooth.py &`
- save and close the file

### make rasberry quiet boot
- `sudo nano /boot/cmdline.txt`
	- Change the console from `tty1` to `console=tty3` 
- add this to end of line:
	- `quiet splash loglevel=0 logo.nologo vt.global_cursor_default=0`

## optional
### RTC (Real Time Clock)
- `sudo nano /etc/modules`
- add `i2c-bcm2708` / Close and save file
- `sudo apt-get install i2c-tools`
- test with `sudo i2cdetect -y 1`

- it shall detect the rtc module at address 0x68
- You can add support for the RTC by adding a device tree overlay. Run
 - `sudo nano /boot/config.txt`
  - add at the end of the file
  - `dtoverlay=i2c-rtc,ds3231`
- `sudo reboot`
- `sudo i2cdetect -y 1`
- now it should print UU at adress 0x68 -> systemdriver is working
- Disable the "fake hwclock" which interferes with the 'real' hwclock
 - `sudo apt-get -y remove fake-hwclock`
 - `sudo update-rc.d -f fake-hwclock remove`
 - `sudo systemctl disable fake-hwclock`
 - `sudo nano /lib/udev/hwclock-set`
  - `#if [ -e /run/systemd/system ] ; then`
  - `# exit 0`
  - `#fi`

- now sync time with the rtc (correct time set in raspi is assumed) 
-  `sudo hwclock -w`
- test with  `sudo hwclock -r`

- That's it! Next time you boot the time will automatically be synced from the RTC module

 - https://cdn-learn.adafruit.com/downloads/pdf/adding-a-real-time-clock-to-raspberry-pi.pdf



## optional
### Samba Server
- `sudo apt-get install samba samba-common smbclient`
- edit /etc/samba/smb.conf
- `sudo nano /etc/samba/smb.conf`
- `section global`
	- [global]
	- workgroup = WORKGROUP
	- wins support = yes
	- dns proxy = no
	- log file = /var/log/samba/log.%m
	- max log size = 1000
	- syslog = 0
	- panic action = /usr/share/samba/panic-action %d
	- server role = standalone server
	- passdb backend = tdbsam
	- obey pam restrictions = yes
	- unix password sync = yes
	- passwd program = /usr/bin/passwd %u
	- passwd chat = *Enter\snew\s*\spassword:* %n\n *Retype\snew\s*\spassword:* %n\n
	- *password\supdated\ssucces$
	- pam password change = yes
	- map to guest = bad user

- printers
	- [printers]
	- comment = All Printers
	- browseable = no
	- path = /var/spool/samba
	- printable = yes
	- guest ok = no
	- read only = yes
	- create mask = 0700

	- [print$]
	- comment = Printer Drivers
	- path = /var/lib/samba/printers
	- browseable = yes
	- read only = yes
	- guest ok = no

- share of folder
	- [PhotoBooth]
	- comment = Development
	- path = /home/pi
	- read only = no
	- guest ok = yes
	- browseable = yes
	- guest only = yes
	- public = yes
	- writable = yes
	- security = share
	- create mask=0777
	- directory mask=0777


### usb automount
- `sudo apt-get install usbmount`
  - `sudo nano /lib/systemd/system/systemd-udevd.service`
	  - changing `MountFlags=slave` to `MountFlags=shared`
  - `sudo nano /etc/usbmount/usbmount.conf`
  - change options
  - `FS_MOUNTOPTIONS="-fstype=vfat,gid=users,dmask=0007,fmask=0117"`
  - remove the `Sync mount option`, this is very slow!

- https://www.raspberrypi.org/forums/viewtopic.php?t=205016#p1271455
- https://www.elektronik-kompendium.de/sites/raspberry-pi/1911271.htm


----------

> http://www.raspberry-pi-geek.de/Magazin/2015/03/Echtzeituhr-Modul-DS3231-sorgt-fuer-genaue-Zeitangaben/(offset)/2

> https://raspberrypi.stackexchange.com/questions/59310/remove-boot-messages-all-text-in-jessie

> further informations are here:

> https://www.elektronik-kompendium.de/sites/raspberry-pi/2007081.htm

> Logos https://de.cooltext.com/Logo-Design-Outline?Font=11391

> https://de.cooltext.com/Render-Image?RenderID=308591325204975&LogoId=3085913252

