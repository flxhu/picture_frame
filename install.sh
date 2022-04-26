#!/bin/bash

apt-get install python-pygame python-pil
cp -v pictureframe.py /opt/
cp -v pictureframe.service /etc/systemd/system
