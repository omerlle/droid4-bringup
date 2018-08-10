# droid4-bringup
## a Newbies Guide of how to make your phone(droid 4) to linux phone
This Guide is also available in [wordpress](https://guidelinuxphone.wordpress.com/2018/06/26/bringup/).
<p style="text-align: left;">
<h1>Note:Modifying or replacing your device's software will void your device's warranty, and can cause to damage to the device and to your computer or losing data(of device and computer), execute the following commands is entirely at your own risk.</h1><br><br>
<h2>Note:this guide try to apply the bringup of droid4 flowing <a href="http://elektranox.org">Sebastian Reichel</a> and <a href="http://muru.com/linux/d4/">Tony Lindgren</a> blog. there still missing parts such as dial or receive sms, that i hope that will fill up in the next chapters </h2>
requires:linux computer,Motorola Droid4(XT894),sdcard(more then 3G),usb cable,(optional)micro-USB-B breakout
board and USB-TTL Adapter with 3.3V signal.<br>
<h2>get started</h2>
create directory hierarchy structure for boot components:<br>
<code>install -d boot/{linux/linux-stable.git,rootfs,archives/{stock_rom/droid4,kexecboot/droid4,ubuntu-base},images,scripts/droid4,overlays/droid4}</code><br>
go into boot directory:
<code>cd boot</code><br>
<h3>update stock rom</h3>
<p>this part is also describe in Sebastian Reichel blog in <a href="http://elektranox.org/2017/02/0009-droid-4-root/">
elektranox.org</a></p>
first of all we need to update the stock rom to VRZ_XT894_9.8.2O-72_VZW-18-8_CFC.xml.zip.<br>
for that we need fastboot, if you don't have fastboot you can install it by:<br>
<code>sudo apt-get install android-tools-fastboot</code><br>
you can download VRZ_XT894_9.8.2O-72_VZW-18-8_CFC.xml.zip from <a href="https://mega.nz/#F!5UZAGQbb!QItoPY1oIS-pu3JJIBmxJw!gUR3hBZK">
mega.nz</a>(you can find more site in <a href="https://forum.xda-developers.com/droid-4/general/droid-4-xt894-firmware-mirrors-2015-t3004048">
forum.xda-developers.com</a>) extract it into droid4/archives/stock_rom<br>
after download you can use the command(you can replace "~/Downloads" in your download path):<br>
<code>unzip ~/Downloads/VRZ_XT894_9.8.2O-72_VZW-18-8_CFC.xml.zip -d archives/stock_rom/droid4</code><br>
download Tony Lindgren script for update the stock_rom:<br>
<code>wget -P archives/stock_rom/droid4 -c http://elektranox.org/files/flash-droid-4-fw.sh</code><br>
turn on the device by press on Vol Down & Power buttons this will go into Fastboot mode(the first line in the screen is:"AP Fastboot Flash Mode (S)") <br>
connect the device to the computer via usb and make sure the bottom lines are "Transfer Mode: USB Connected"<br>
make sure you see the device by the command:<br>
<code>fastboot devices</code><br>
the output supposed to be something like:<br>
<code>0123456789ABCDEF	fastboot</code><br>
if you get this output:<br>
<code>permissions	fastboot</code><br>
try:<br>
<code>sudo fastboot devices</code><br>
if it solve the problem change the script to run "sudo fastboot" by the command:<br>
<code>sed -i 's/fastboot=fastboot/fastboot="sudo fastboot"/' archives/stock_rom/droid4/flash-droid-4-fw.sh</code><br>
go into VRZ_XT894_9.8.2O-72_VZW-18-8_CFC.xml dir:<br>
<code>pushd archives/stock_rom/droid4/VRZ_XT894_9.8.2O-72_VZW-18-8_CFC.xml</code><br>
and run the script:<br>
<code>bash ../flash-droid-4-fw.sh</code><br>
return to base directory by:<br>
<code>popd</code><br>

<h3>install Kexecboot bootloader</h3>
if you don't have git you can install it by:<br>
<code>sudo apt-get install git</code><br>
clone Tony Lindgren repository for droid4 kexecboot by the command:<br>
<code>git clone https://github.com/tmlind/droid4-kexecboot.git archives/kexecboot/droid4/</code><br>
install the Kexecboot by the commands(you can remove sudo keyword if you don't need sudo for fastboot)[my current version is 2018-05-06]:<br>
<code>sudo fastboot flash mbm archives/stock_rom/droid4/VRZ_XT894_9.8.2O-72_VZW-18-8_CFC.xml/allow-mbmloader-flashing-mbm.bin<br>
sudo fastboot reboot bootloader<br>
sudo fastboot flash bpsw archives/kexecboot/droid4/current/droid4-kexecboot.img<br>
sudo fastboot flash utags archives/kexecboot/droid4/utags-mmcblk1p13.bin<br>
sudo fastboot flash mbm archives/stock_rom/droid4/VRZ_XT894_9.8.2O-72_VZW-18-8_CFC.xml/mbm.bin</code><br>
you can poweroff the device for now by press Power button<br>

<h3>create bootable image</h3>
create an bootable image for the first partition of the sdcard with 2G size: <br>
<code>dd if=/dev/zero of=images/dd if=/dev/zero of=images/droid4_01012018.img bs=1M count=0 seek=2000</code><br>
add filesystem to the image:<br>
<code>mkfs.ext4 -F -L droid4_rootfs images/droid4_01012018.img</code><br>
mount the image to rootfs:<br>
<code>sudo mount -o loop images/droid4_01012018.img rootfs</code><br>
delete unused directory:<br> 
<code>sudo rm -rf rootfs/lost+found</code><br>

<h4>build rootfs</h4>
install qemu-user-static arm emulator:
<code>sudo apt-get install qemu-user-static</code><br>
download the ubuntu minimal rootfs archive:<br>
<code>wget -P archives/ubuntu-base -c http://cdimage.ubuntu.com/ubuntu-base/releases/16.04.1/release/ubuntu-base-16.04.4-base-armhf.tar.gz</code>
extract ubuntu minimal rootfs into the image:<br>
<code>sudo tar -xzf archives/ubuntu-base/ubuntu-base-16.04.4-base-armhf.tar.gz -C rootfs/</code><br>
copy qemu-arm-static to the image:<br>
<code>sudo cp -a /usr/bin/qemu-arm-static rootfs/usr/bin/</code><br>
run chroot to config the image on pc:<br>
<code>sudo chroot rootfs/</code><br>
add new user and set password for root and user:<br>
<code>passwd root<br>
useradd -G sudo -m -s /bin/bash droid4_user<br>
echo droid4_user:1234 | chpasswd</code><br>
config network:<br>
<code>echo droid4 > /etc/hostname<br>
echo "127.0.0.1    localhost.localdomain localhost" > /etc/hosts<br>
echo "127.0.0.1    droid4" >> /etc/hosts<br>
echo "nameserver 127.0.1.1" > /etc/resolv.conf</code><br>
install useful packages:<br>
<code>apt-get update<br>
apt-get upgrade<br>
apt-get install language-pack-en-base python-gobject-2 libqmi-utils lsof rsync psmisc modemmanager ifupdown udev vim openssh-server openssh-client net-tools ethtool wireless-tools network-manager iputils-ping rsyslog alsa-utils bash-completion resolvconf htop xinit xorg wpasupplicant tmux zsh eog evince sqlite3 bluez-tools linux-firmware bluez mpg123 --no-install-recommends</code><br>
configure packages:<br>
<code>dpkg-reconfigure x11-common<br>
dpkg-reconfigure resolvconf</code><br>
exit fron chroot:<br>
<code>exit</code><br>
allow ssh to user root:<br>
<code>sudo sed -i 's/^PermitRootLogin prohibit-password/PermitRootLogin yes/' rootfs/etc/ssh/sshd_config</code><br>
override rc.local:<br>
<code>wget -P overlays/droid4/etc/ https://guidelinuxphone.files.wordpress.com/2018/06/rc-local.doc<br>
sudo cp overlays/droid4/etc/rc-local.doc rootfs/etc/rc.local</code><br>
add omap.conf:<br>
<code>wget -P overlays/droid4/etc/modules-load.d/ https://guidelinuxphone.files.wordpress.com/2018/06/omap-conf.doc<br>
sudo cp overlays/droid4/etc/modules-load.d/omap-conf.doc rootfs/etc/modules-load.d/omap.conf</code><br>

<h4>build kernel</h4>
if you don't have the following tools you can install it by:<br>
<code>sudo apt-get install libncurses5-dev make exuberant-ctags bc libssl-dev</code><br>
and the arm cross compailer:<br>
<code>apt-get install gcc-arm-linux-gnueabihf</code><br>
clone upstream repository:<br>
<code>git clone git://git.kernel.org/pub/scm/linux/kernel/git/stable/linux-stable.git linux/linux-stable.git</code><br>
go into linux-stable.git:<br>
<code>pushd linux/linux-stable.git</code><br>
checkout the latest stable kernel branch(you can see the tag via "git tag -l")<br>
<code>git checkout -b local/v4.17.9 v4.17.9</code><br>
add patches:<br>
<code>i=1;for p in 67 63 66 65 62 61 60 57 58 59 ;do <br>
wget -c https://lkml.org/lkml/diff/2018/3/30/4${p}/1 -P ../patches/droid4/Keyboard_and_Display_Backlight_2018-03-30/$((i++));done<br>
for i in $(seq 1 10) ; do <br> patch -p1 < ../patches/droid4/Keyboard_and_Display_Backlight_2018-03-30/${i}/1;done<br>
i=1;for p in 54 53 52 50 51 49 47 48 ;do <br> wget -c https://lkml.org/lkml/diff/2018/3/30/4${p}/1 -P ../patches/droid4/LCD_2018-03-30/$((i++));done<br>
for i in $(seq 1 8) ; do <br>patch -p1 < ../patches/droid4/LCD_2018-03-30/${i}/1;done<br>
i=1;for p in 318 317;do <br>wget -c https://lkml.org/lkml/diff/2018/3/30/${p}/1 -P ../patches/droid4/audio_codec/$((i++));done<br>
for i in $(seq 1 2) ; do <br>patch -p1 < ../patches/droid4/audio_codec/${i}/1;done</code><br>
setup your default kernel configuration:<br>
<code>make ARCH=arm omap2plus_defconfig</code><br>
add modules:<br>
<code>echo "CONFIG_BACKLIGHT_TI_LMU=m<br>
CONFIG_USB_ETH=m" >> .config</code><br>
compaile the kernel:<br>
<code>make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- omap4-droid4-xt894.dtb bzImage modules -j9</code><br>
install the modules in the rootfs:<br>
<code>sudo make -j8 ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- modules_install INSTALL_MOD_PATH=../../rootfs</code><br>
return to base directory by:<br>
<code>popd</code><br>
copy the kernel and the dtb to the image:<br>
<code>sudo cp linux/linux-stable.git/arch/arm/boot/zImage rootfs/boot/vmlinuz<br>
sudo cp linux/linux-stable.git/arch/arm/boot/dts/omap4-droid4-xt894.dtb rootfs/boot/</code><br>



<h4>add boot.cfg</h4>
add omap.conf:<br>
<code>wget -P overlays/droid4/boot/ https://guidelinuxphone.files.wordpress.com/2018/06/boot-cfg.doc<br>
sudo cp overlays/droid4/boot/boot-cfg.doc rootfs/boot/boot.cfg</code><br>
save and umount the image:<br>
<code>sudo sync<br>
sudo umount rootfs/</code><br>

<h3>copy image to sd</h3>
<h4>note:this part is very dangerous because you can erase your hard disk if you will not do it right</h4>
use this command to figure out your sdcard name, you need be sure it appear and disappear when you connect it and disconnect it otherwise you can erase important data:<br>
<code>lsblk</code><br>
when you are sure what the name of the sd replace the "mmcblk0" keyword with your name and run the following commands:<br>
<code>sdcard="mmcblk0"<br>
echo "1 : start=        2048, size=     5120000, type=83<br>
2 : start=     5122048, size=     $(($(cat /sys/block/$sdcard/size)-5122048)), type=83" | sudo sfdisk /dev/$sdcard<br>
sudo mkfs.ext4 /dev/${sdcard}p2 -L droid4<br>
sudo dd if=images/droid4_01012018.img of=/dev/${sdcard}p1<br>
sync</code><br><br>

that it insert the sdcard to the phone and turn it on.<br>


