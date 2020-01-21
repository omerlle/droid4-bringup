# droid4-bringup
a Newbies Guide of how to make your phone(droid 4) to linux phone
<p style="text-align:left;">
<h1>Note:Modifying or replacing your device's software will void your device's warranty, and can cause to damage to the device and to your computer or losing data(of device and computer), execute the following commands is entirely at your own risk.</h1><br><br>
<h2>Note:this guide try to apply the bringup of droid4 flowing <a href="http://muru.com/linux/d4/">Tony Lindgren</a> blog. there still missing parts such as camera or connact to internet, that i hope that will fill up in the next time </h2>
requires:linux computer,Motorola Droid4(XT894),sdcard(more then 3G),usb cable.
<h3>optional-Debug UART</h3>
you need also a micro-USB-B breakout board and USB-TTL Adapter with 3.3V signal-A detailed explanation is available in Tony Lindgren blog <a href="http://muru.com/linux/d4/">Debug UART</a>.<br>

<h2>get started</h2>
go to the path that you want  to create the project(replace "/path/to/project/" with the path):<br>
<code>pushd /path/to/project/</code><br>
create directory hierarchy structure for boot components:<br>
<code>install -d bringup/{linux/{linux-stable,images},mnt,archives/{stock_rom/droid4,kexecboot/droid4,buildroot,firmware,basic_rootfs/{ubuntu-base,alpine}},mnt,rootfs/{alpine,ubuntu,buildroot}}</code><br>
go into bringup directory:<br>
<code>cd bringup</code><br>
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
go into VRZ_XT894_9.8.2O-72_VZW-18-8_CFC.xml directory:<br>
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

<h4>build kernel</h4>
if you don't have the following tools you can install it by:<br>
<code>sudo apt-get install libncurses5-dev make exuberant-ctags bc libssl-dev</code><br>
and the arm cross compailer:<br>
<code>apt-get install gcc-arm-linux-gnueabihf</code><br>
clone upstream repository:<br>
<code>git clone git://git.kernel.org/pub/scm/linux/kernel/git/stable/linux-stable.git linux/linux-stable</code><br>
go into linux-stable:<br>
<code>pushd linux/linux-stable</code><br>
checkout the latest stable kernel branch(you can see the tag via "<code>git tag -l</code>")<br>
<code>git checkout -b local/v5.4.13 v5.4.13</code><br>
fetch Tony Lindgren repository for voice calls and gnss serdev driver patches:<br>
<code>git remote add linux-omap git://git.kernel.org/pub/scm/linux/kernel/git/tmlind/linux-omap.git<br>
git fetch linux-omap</code><br>
merge mdm branch:<br>
<code>git merge linux-omap/droid4-pending-v5.4 -m "Merge remote-tracking branch 'linux-omap/droid4-pending-v5.4' into local/v5.4.13"</code><br>
setup your default kernel configuration:<br>
<code>make ARCH=arm omap2plus_defconfig</code><br>
compaile the kernel:<br>
<code>make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- omap4-droid4-xt894.dtb bzImage modules -j9</code><br>
return to base directory by:<br>
<code>popd</code><br>



<h4>build rootfs</h4>
<h5>you can build rootfs by one of the following branches:</h5><br>
<a href="https://github.com/omerlle/droid4-bringup/tree/alpine/">alpine</a><br>
<a href="https://github.com/omerlle/droid4-bringup/tree/ubuntu/">ubuntu</a><br>

<h3>create bootable sd</h3>
format the sdcard:<br>
<h4>note:this part is very dangerous because you can erase your hard disk if you will not do it right</h4>
use this command to figure out your sdcard name, you need be sure it appear and disappear when you connect it and disconnect it otherwise you can erase important data:<br>
<code>lsblk</code><br>
when you are sure what the name of the sd replace the "mmcblk0" keyword with your name and run the following commands:<br>
<code>sdcard="mmcblk0"<br>
set -u<br>
mount | grep /dev/$sdcard | cut -d ' ' -f 3 | xargs umount<br>
echo "1 : start=        2048, size=     102400, type=83<br>
2 : start=        104448, size=     4194304, type=83<br>
3 : start=     4298752, size=     $(($(cat /sys/block/$sdcard/size)-4298752)), type=83" | sudo sfdisk /dev/$sdcard<br>
sudo partprobe /dev/${sdcard}<br>
sudo mkfs.vfat /dev/${sdcard}p1 -n BOOT<br>
sudo mkfs.ext4 /dev/${sdcard}p2 -L rootfs<br>
sudo mkfs.vfat /dev/${sdcard}p3 -n USER_DATA<br>
set +u</code><br>
mount the first partition of sdcard:<br>
<code>sudo mount /dev/${sdcard}p1 mnt</code><br>
copy the boot components:<br>
<code>sudo rsync --chown=root:root archives/droid4_bringup/boot/boot.cfg linux/linux-stable/arch/arm/boot/zImage linux/linux-stable/arch/arm/boot/dts/omap4-droid4-xt894.dtb mnt/boot</code><br>
[for uart debug:<code>sudo rsync --chown=root:root archives/droid4_bringup/boot/boot.cfg.uart mnt/boot/boot.cfg </code>]<br>
unmount the first partition of sdcard and mount the second partition:<br>
<code>sync<br>
sudo umount mnt<br>
sudo mount /dev/${sdcard}p2 mnt</code><br>
copy the rootfs to the second partition:<br>
<code>sudo rsync --delete -av ${droid_rootfs}/ mnt/</code><br>
install the modules in the rootfs:<br>
<code>sudo make -j8 ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- modules_install INSTALL_MOD_PATH=${PWD}/mnt/ -C linux/linux-stable</code><br>
save and umount the second partition of sdcard and mount the third partition:<br>
<code>sync<br>
sudo umount mnt<br>
sudo mount /dev/${sdcard}p3 mnt</code><br>
copy the rootfs to the third partition:<br>
<code>sudo install -d mnt/droid4/modem/{dynamic_data,logs}<br>
sudo mv ${droid_rootfs}/tmp/modem.db mnt/droid4/modem/dynamic_data/</code><br>
save and umount the third partition:<br>
<code>sync<br>
sudo umount mnt</code><br>
return to your original path:<br>
<code>popd</code><br>
that it, insert the sdcard to the phone and turn it on(you need to wait couple of minute.<br>
for droid4 usage you can see <a href="https://guidelinuxphone.wordpress.com">
droid4 linux guide</a>.<br>
