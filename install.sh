#!/bin/bash

apt-get install python-pil
cp -v pictureframe.py /opt/
cp -v pictureframe.service /etc/systemd/system
systemctl enable pictureframe
systemctl start pictureframe
systemctl status pictureframe
