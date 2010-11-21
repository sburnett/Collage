#!/bin/bash

UNIVERSE=`grep "^[^#]" /etc/apt/sources.list | grep -c " universe$"`
if [ "$UNIVERSE" == "0" ]
then
    clear
    echo "This script will automatically install the Collage demo on your computer."
    echo "It is assumed you are running a recent version of Ubuntu."
    echo
    echo "Before continuing, we will enable the Universe repository."
    echo "This change will only be in effect during this installation."
    echo "Your /etc/apt/sources.list will not be permanently altered."
    echo
    echo "To enable the Universe repository, press <ENTER>."
    read

    sudo cp /etc/apt/sources.list /etc/apt/sources.list.collage_backup
    RELEASE=`lsb_release -s -c`
    sudo bash -c "echo deb http://archive.ubuntu.com/ubuntu $RELEASE universe >> /etc/apt/sources.list"
else
    clear
    echo "This script will automatically install the Collage demo on your computer."
    echo
    echo "Press <ENTER> to continue."
    read
fi

clear
echo "First we are going to install the following packages if they are not"
echo "already installed:"
echo
echo "     python-dev python-setuptools python-numpy outguess python-wxgtk2.8"
echo
echo "Press <ENTER> to begin installation of these packages."
read
sudo apt-get update
sudo apt-get install python-dev python-setuptools python-numpy outguess python-wxgtk2.8

clear
echo "We are now going to install PyCrypto, a Python cryptography package."
echo
echo "Press <ENTER> to continue."
read
SETUPDIR=`mktemp -d`
cd $SETUPDIR
wget http://ftp.dlitz.net/pub/dlitz/crypto/pycrypto/pycrypto-2.2.tar.gz
tar -zxvf pycrypto-2.2.tar.gz
cd pycrypto-2.2
python setup.py build
sudo python setup.py install
cd -

clear
echo "We are now going to install Selenium, a Web automation package for Python."
echo
echo "Press <ENTER> to continue."
read
wget http://www.cc.gatech.edu/~sburnett/collage/selenium-2.0-dev-collage.tar.gz
tar -zxvf selenium-2.0-dev-collage.tar.gz
cd selenium-2.0-dev-9341
python setup.py build
sudo python setup.py install
cd -

clear
echo "We have now installed all prequisites."
echo "We will now download and install the Collage demo."
echo
echo "Press <ENTER> to continue."
read
wget http://www.cc.gatech.edu/~sburnett/collage/CollageProxyClient-1.0.tar.gz
tar -zxvf CollageProxyClient-1.0.tar.gz
cd CollageProxyClient-1.0
python setup_proxy_client.py build
sudo python setup_proxy_client.py install
cd -

clear
echo "Installation is complete. We will now clean up temporary files."
echo
echo "Press <ENTER> to continue."
read
rm -rf $SETUPDIR
if [ "$UNIVERSE" == "0" ]
then
    sudo mv /etc/apt/sources.list.collage_backup /etc/apt/sources.list
fi

clear
echo "Installation is complete."
echo
echo "To start the demo, just run 'collage_demo'."
echo "If you have issues, please see our Web page for contact information:"
echo
echo "    http://gtnoise.net/collage"
echo
