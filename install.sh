#!/bin/bash

apt-get install python3-pygame
cp -v pictureframe.py /opt/
cp -v pictureframe.service /etc/systemd/system
systemctl enable pictureframe
systemctl restart pictureframe
systemctl status pictureframe
