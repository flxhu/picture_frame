#! /usr/bin/python3

import os
import subprocess
import threading
import time
import pygame
import signal
import shlex
import socket
import urllib, json
import random
from PIL import Image, ExifTags
from collections import deque

os.environ["DISPLAY"] = ":0"
SHOW_AFTER_SECS=60
NEXT_IMAGE_AFTER_SECS=20
IMAGE_DIR="/home/felix/wallpaper/"
EXTENSIONS=['.jpg', '.jpeg', '.png']
VOLUMIO_STATUS_URL="http://volumio.local:3000/api/v1/getSystemInfo"
DISPLAY_ON=False
MPD_PORT=6600

import signal
def handler(signum, frame):
    pass

try:
    signal.signal(signal.SIGHUP, handler)
except AttributeError:
    # Windows compatibility
    pass


class ActivityDetector(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    self.daemon = True
    self.last_activity = 0

  def run(self):
    while True:
      try:
        with open("/dev/input/event0", "rb") as f:
          while True:
            f.read(1)
            self.last_activity = time.time()
      except Exception as e:
        print("Error reading /dev/input/event0", e)
        continue

def get_volumio_status():
  try:
    response = urllib.urlopen(VOLUMIO_STATUS_URL)
    data = json.loads(response.read())
    return data['state']['status'] == 'play'
  except Exception as e:
    print("Exception on volumio status get", e)

def get_mpd_status():
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect(("localhost", MPD_PORT))
    hello = socket.SocketIO(s,'rb').readline()
    if not hello.startswith(b"OK MPD"):
      return False
    s.sendall(b"status\n")
    data = s.recv(1024)
    return b"state: play" in data

def image_list_generator():
  while True:
    for root, subdirs, files in os.walk(IMAGE_DIR, topdown=False):
      print("Showing everything in", root, ", which has", len(files), "files")
      for filename in files:
        if os.path.splitext(filename)[1].lower() in EXTENSIONS:
          yield os.path.join(root, filename)

def get_orientation(filename):
  """
  :return: 3 180deg, 6 270deg, 8 90deg
  """
  image=None
  try:
    image=Image.open(filename)
    for orientation in ExifTags.TAGS.keys():
        if ExifTags.TAGS[orientation]=='Orientation':
            break
    exif=dict(image._getexif().items())
    if exif[orientation] == 3:
      return 180
    if exif[orientation] == 6:
      return 270
    if exif[orientation] == 8:
      return 90
    return 0
  except (AttributeError, KeyError, IndexError) as e:
    print("No orientiation", filename, e)
    return None
  finally:
    if image:
      image.close()

def display_next_image(filename):
  screen = display_enable()

  angle = get_orientation(filename)
  print(filename, angle)
  screen_width = pygame.display.Info().current_w
  screen_height = pygame.display.Info().current_h
  picture = pygame.image.load(filename)
  if angle and angle > 0:
    picture = pygame.transform.rotate(picture, angle)

  pic_width = picture.get_width()
  pic_height = picture.get_height()
  width = screen_width
  height = screen_width * pic_height / pic_width

  if height > screen_height:
    width = width * screen_height / height
    height = screen_height

  picture = pygame.transform.smoothscale(picture, (int(width), int(height)))

  position = (
      int((screen_width - width) / 2),
      int((screen_height - height) / 2))

  screen.fill((0, 0, 0))
  screen.blit(picture, position)
  pygame.display.flip()

def display_enable():
  global DISPLAY_ON
  if not DISPLAY_ON:
    pygame.display.init()
    pygame.mixer.quit()
    pygame.mouse.set_visible(False)
    width = pygame.display.Info().current_w
    height = pygame.display.Info().current_h
    screen = pygame.display.set_mode((width, height))
    DISPLAY_ON=screen
  return DISPLAY_ON

def display_off():
  global DISPLAY_ON
  if DISPLAY_ON:
    pygame.display.quit()
    DISPLAY_ON=None

if __name__ == "__main__":
  pygame.init()
  os.putenv('SDL_VIDEO_DRIVER', 'directfb')

  a = ActivityDetector()
  a.start()

  last_image_switch_secs = time.time()
  last_player_activity = time.time()
  image_list = image_list_generator()
  while True:
    time.sleep(1)

    now = time.time()
    idle_for_secs = min(now - a.last_activity, now - last_player_activity)

    if idle_for_secs < SHOW_AFTER_SECS:
      display_off()
      continue

    is_playing = get_mpd_status()
    if is_playing:
      display_off()
      last_player_activity = time.time()
      continue

    if now - last_image_switch_secs > NEXT_IMAGE_AFTER_SECS:
      last_image_switch_secs = now
      display_next_image(next(image_list))
