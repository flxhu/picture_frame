#! /usr/bin/python

import os
import subprocess
import threading
import time
import signal
import shlex

FBI="fbi -T 2 -a -noverbose -t 20 -u /home/volumio/Wallpaper/*"

SHOW_AFTER_SECS=120

class ActivityDetector(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    self.last_activity = 0

  def run(self):
    print "Running"
    f = open("/dev/input/event0", "r")
    while True:
      f.read(1)
      self.last_activity = time.time()

a = ActivityDetector()
a.daemon = True
a.start()

fbi_proc = None

while True:
  time.sleep(1)
  idle_for_secs = time.time() - a.last_activity
  if idle_for_secs < SHOW_AFTER_SECS and fbi_proc != None:
    print "Activity, killing fbi"
    fbi_proc.send_signal(signal.SIGINT)
    fbi_proc.terminate()
    fbi_proc.kill()
    fbi_proc = None
    os.system("killall fbi")

  if idle_for_secs > SHOW_AFTER_SECS and fbi_proc == None:
    cmd = shlex.split(FBI)
    print cmd
    fbi_proc = subprocess.Popen(args=FBI, shell=True)
    print "Idle, starting fbi", fbi_proc.pid
