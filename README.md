# droid4-bringup
a Newbies Guide of how to make your phone(droid 4) to linux phone
<p style="text-align:left;">
<h4>build rootfs</h4>
install qemu-user-static arm emulator:<br>
<code>sudo apt-get install qemu-user-static</code><br>
download the ubuntu minimal rootfs archive:<br>
<code>wget -P archives/basic_rootfs/ubuntu-base -c http://cdimage.ubuntu.com/ubuntu-base/releases/18.04.2/release/ubuntu-base-18.04.2-base-armhf.tar.gz</code><br>
clone bringup repository for droid4 more rootfs scripts:<br>
<code>git clone https://github.com/omerlle/droid4-bringup.git archives/droid4_bringup</code><br>
checkout the ubuntu branch:<br>
<code>git -C archives/droid4_bringup/ checkout ubuntu</code><br>
choose name to rootfs directory and create it:<br>
<code>droid_rootfs="$PWD/rootfs/ubuntu/18.04.2-base-armhf"<br>
mkdir ${droid_rootfs}</code><br>
extract ubuntu minimal rootfs into the directory:<br>
<code>sudo tar -xzf archives/basic_rootfs/ubuntu-base/ubuntu-base-18.04.2-base-armhf.tar.gz -C ${droid_rootfs}/</code><br>
add usage scripts:<br>
<code>sudo rsync -a --chown=root:root archives/droid4_bringup/overlay/ ${droid_rootfs}</code><br>
add files and mount some directories for chroot work properly:<br>
<code>sudo cp /etc/resolv.conf ${droid_rootfs}/etc/<br>
sudo cp -a /usr/bin/qemu-arm-static ${droid_rootfs}/usr/bin/<br>
sudo mount -t proc /proc ${droid_rootfs}/proc<br>
sudo mount -o bind /dev ${droid_rootfs}/dev</code><br>
run chroot to config the rootfs on pc:<br>
<code>sudo chroot ${droid_rootfs}</code><br>
add new user and set password for root and user(you can replace "droid4_user" with your user name and "1234" with your user password):<br>
<code>passwd root<br>
useradd -G sudo -m -s /bin/bash droid4_user<br>
echo droid4_user:1234 | chpasswd</code><br>
config network:<br>
<code>echo droid4 > /etc/hostname<br>
echo "127.0.0.1    localhost.localdomain localhost" > /etc/hosts<br>
echo "127.0.0.1    droid4" >> /etc/hosts</code><br>
install useful packages:<br>
<code>apt-get update<br>
apt-get upgrade<br>
apt-get install apt-utils language-pack-en-base python-gobject-2 libqmi-utils lsof rsync psmisc ifupdown udev vim openssh-server openssh-client net-tools ethtool wireless-tools network-manager iputils-ping rsyslog alsa-utils bash-completion resolvconf htop xinit xorg wpasupplicant tmux zsh eog evince sqlite3 bluez bluez-tools linux-firmware mpg123 sox libsox-fmt-all minicom emacs pulseaudio pulseaudio-module-bluetooth python3-evdev python3-pip xfce4 fvwm i3 kbd --no-install-recommends<br>
pip3 install evdev</code><br>
configure packages:<br>
<code>dpkg-reconfigure x11-common<br>
dpkg-reconfigure resolvconf</code><br>
allow ssh to user root:<br>
<code>sed -i 's/^#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config</code><br>
set the databases:<br>
<code>sqlite3 /root/.droid4/hardware.db < /usr/local/share/droid4/python3_packages/hardware/config/hardware_db.back<br>
sqlite3 /tmp/modem.db < /usr/local/share/droid4/python3_packages/modem/config/modem_db.back</code><br>
exit from chroot:<br>
<code>exit</code><br>
unmount /proc and /dev from the rootfs:<br>
<code>sudo umount ${droid_rootfs}/dev<br>
sudo umount ${droid_rootfs}/proc</code><br>
add TIInit_10.6.15.bt for bleutooth:<br>
<code>sudo wget -c https://github.com/TI-ECS/bt-firmware/blob/master/am335x/TIInit_10.6.15.bts -P ${droid_rootfs}/lib/firmware/ti-connectivity</code><br>
