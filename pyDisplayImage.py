#!/usr/bin/env python
# -*- coding: utf-8 -*-

import settings
import time
from datetime import datetime, timedelta
import usb1
import Image, ImageDraw, ImageFilter, ImageFont
import StringIO
import struct
import csv
import string
import re
import urllib2
import subprocess
import os
import paho.mqtt.client as mqtt
import json

seconds = lambda: int(round(time.time()))

class DisplayThread:
  def __init__(self, settings):
    self.settings = settings
        
    self.FrameReady = False
    self.FrameCounter = 0
    
    self.start_time = seconds()
    self.display_next = 0
    self.display_active = False
    self.lastStatePublished = 0
    
    #setup mqtt stuff
    self.client = mqtt.Client('pyDisplayImage-%s' % os.getpid())
    self.client.on_connect = self.on_connect
    self.client.on_message = self.on_message

    self.client.connect(self.settings.BrokerURL)
    self.client.loop_start()
    

    
  def debug(self, message):
    if self.settings.debug:
      print datetime.now().strftime("%H:%M") + ' ' + str(message)

      
  # The callback for when the client receives a CONNACK response from the server.
  def on_connect(self, client, userdata, flags, rc):
    self.debug("Connected to mqtt broker with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
#    client.subscribe("home/display/active")


  # The callback for when a PUBLISH message is received from the server.
  def on_message(self, client, userdata, msg):
    self.debug(msg.topic + ': ' + msg.payload);
      
      
  def setCustomMode(self, dev):
    hndl = self.context.openByVendorIDAndProductID(
      dev['vid'], dev['pid'],
      skip_on_error=True)
    
    if not hndl:
      debug_print('StorageDevice Not found')
      return False
      
    try:
      hndl.controlWrite(        0x80,           0x06,       0xfe,   0xfe,   b'\x00'*254,1000)
#          controlWrite(self,   request_type,   request,    value,  index,  data,       timeout=0):
    except:  
      pass
    return True


  def sendJPEG(self, hndl, pic):
    # The photo frame expects a header of 12 bytes, followed by the picture data.
    # The first 4 and the last 4 bytes are always the same.
    # The middle 4 bytes are the picture size (excluding the header) with the least significant byte first
    rawdata = b"\xa5\x5a\x18\x04" + struct.pack('<I', len(pic)) + b"\x48\x00\x00\x00" + pic

    # The photo frame expects transfers in complete chunks of 16384 bytes (=2^14 bytes).
    # If last chunk of rawdata is not complete, then make it complete by padding with zeros.
    pad = 16384 - (len(rawdata) % 16384)
    tdata = rawdata + pad * b'\x00'

    # For unknown reasons, some pictures will only transfer successfully, when at least one
    # additional zero byte is added. Possibly a firmware bug of the frame?
    tdata = tdata + b'\x00'
    
    try:
      hndl.bulkWrite(0x02, tdata)
    except:
      pass      
      
      
  def sendImage(self, hndl, item):
    do_display = False
    if "schedule" in item:
      day = datetime.now().strftime("%w")
      if day in item["schedule"]:
        self.debug("Schedule for today: " + item["schedule"][day])
        s_array = item["schedule"][day].split('-')
        if (datetime.now().hour >= int(s_array[0])) & (datetime.now().hour < int(s_array[1])):
          self.debug("now displaying!")
          do_display = True
      else:
        do_display = True
    else:
      do_display = True
        

    if do_display:
      screenSize = (self.settings.CustomDevice["width"], self.settings.CustomDevice["height"])
      canvas = Image.new("RGB", screenSize, "black")
      res = True
      
      url = self.settings.OUTDIR+"/"+item["id"]+".jpg"

      if os.access(url, os.F_OK):
        self.debug("Display: " + url)
        self.debug(item)
        if (seconds() - os.stat(url).st_mtime) > item["refresh"]:
          self.debug("File outdated: " + url)
          res = False
        else:
          try:
            image = Image.open(url)
          except:
            image = Image.new("RGB", screenSize, "red")
      else:
        self.debug("Image not found: " + url)
        res = False
        
      if res == False:  
        image = Image.new("RGB", screenSize, "black")
        TextFont=ImageFont.truetype(self.settings.ROOTDIR+"/fonts/OpenSans-Light.ttf", 30)
        text = Image.Image()._new(TextFont.getmask(url, mode="L"))
        image.paste("#ddd", (0,0), text)

      try:
        canvas.paste(image, ( (self.settings.CustomDevice["width"]-image.size[0])/2,(self.settings.CustomDevice["height"]-image.size[1])/2))
      except:
        pass
      output = StringIO.StringIO()
      canvas.save(output, "JPEG", quality=94)
      
      pic  = output.getvalue()
      self.sendJPEG(hndl,pic)
      output.close()
      return res
    else: 
      return True
      
      
  def loop(self):
    while True:
      if seconds() >= self.display_next:
        self.FrameReady = False
        self.context = usb1.USBContext()
        deviceList = self.context.getDeviceList(skip_on_error=True)
        for device in deviceList:
#          self.debug(device)
          if device.getVendorID() == self.settings.StorageDevice['vid']:
            if device.getProductID() == self.settings.StorageDevice['pid']:
              self.debug("Found '%s' in storage mode" % device.getProduct())
              if self.setCustomMode(self.settings.StorageDevice) == True:
                time.sleep(1)
                self.debug("custom mode set")
                self.FrameReady = True
                self.FrameCounter = 0
            elif device.getProductID() == self.settings.CustomDevice['pid']:
              self.debug("Found '%s' in custom mode" % device.getProduct())
              self.FrameReady = True
              break
            
        if self.FrameReady == True:
          self.display_active = True
          self.client.publish('home/display/active', self.display_active, retain=True)
          self.lastStatePublished = 0
          
          hndl = self.context.openByVendorIDAndProductID(
              self.settings.CustomDevice['vid'], self.settings.CustomDevice['pid'],
              skip_on_error=True)
          if not hndl:
              self.debug('Error opening device')
          else:   
            hndl.claimInterface(0)
            seqItem = self.settings.sequence[self.FrameCounter % len(self.settings.sequence)]

            res = self.sendImage(hndl, seqItem)
            
            if res == False:
              # set short timeout
              self.display_next = seconds() + 1
              if "skip" in seqItem:
                if seqItem["skip"] <> False:
                  self.FrameCounter += 1
              else:
                self.FrameCounter += 1
                
            elif "timeout" in seqItem:
              self.FrameCounter += 1
              self.display_next = seconds() + seqItem["timeout"]
            else:
              self.FrameCounter += 1
              self.display_next = seconds() + 10
            
        else:
#          self.debug("No device found")
          self.display_active = False
          if seconds() > self.lastStatePublished + 1200:
            self.debug('setting "home/display/active" to "False"')
            self.client.publish('home/display/active', self.display_active, qos=1, retain=True)
            self.lastStatePublished = seconds()

      time.sleep(0.5)

      
if __name__ == '__main__':

  for item in settings.sequence:
    if not 'refresh' in item:
      item["refresh"] = 600
    item["last_refresh"] = 0
 
  display = DisplayThread(settings)
  
  try:
    display.loop()
  except (KeyboardInterrupt, SystemExit):
    pass
