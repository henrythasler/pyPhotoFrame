#!/usr/bin/env python
# -*- coding: utf-8 -*-

import settings
import multiprocessing
import threading
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

MULTIPROCESSING = True # True=multiprocessing; False=treading

seconds = lambda: int(round(time.time()))

class DownloadThread:
  def __init__(self, settings, lock, run_event, display_active):
    self.lock = lock
    self.settings = settings
    self.debugActive = settings.debug

    self.data = {
        'T_IN': 0.0,
        'T_OUT': 0.0
        }

    #setup mqtt stuff
    self.client = mqtt.Client("pyPhotoFrame")
    self.client.on_connect = self.on_connect
    self.client.on_message = self.on_message

    self.client.connect("127.0.0.1")
    self.client.loop_start()

  # The callback for when the client receives a CONNACK response from the server.
  def on_connect(self, client, userdata, flags, rc):
      self.debug("Connected to mqtt broker with result code "+str(rc))

      # Subscribing in on_connect() means that if we lose the connection and
      # reconnect then subscriptions will be renewed.
      client.subscribe("home/out/temp")
      client.subscribe("home/in/temp")

  # The callback for when a PUBLISH message is received from the server.
  def on_message(self, client, userdata, msg):
      if msg.topic == 'home/out/temp':
        self.data['T_OUT'] = float(json.loads(msg.payload)['value'])
        
      if msg.topic == 'home/in/temp':
        self.data['T_IN'] = float(json.loads(msg.payload)['value'])
      
      #self.debug('on_message: '+str(self.item))
      #print(msg.topic+" "+msg.payload)
  #    ext_temperature = json.loads(msg.payload)
      #print(" "+str(ext_temperature))

    
  def debug(self, message):
    if self.debugActive:
      self.lock.acquire()
      try:
        print datetime.now().strftime("%H:%M") + ' ' + str(message)
      except:
        pass
      self.lock.release()

      
  def getSensorData(self):
    with open(self.settings.DATADIR+'/data.csv', 'rb') as csvfile:
      reader = csv.reader(csvfile, delimiter=';')
      last_entry = None
      for row in reader:
        last_entry = row
        
      t_in = -273
      h_in = 0
      t_out = -273
      try:
        t_in = float(last_entry[1])
        h_in = float(last_entry[2])
        t_out = float(last_entry[3])
      except: 
        pass
    return (t_out, t_in, h_in)  

  def ResizeImage(self, image, screenSize, method):
    screenFactor = float(screenSize[0])/float(screenSize[1])
    imageFactor = float(image.size[0])/float(image.size[1])
    stretchedSize = image.size
    
    if method == "fill":
      # fill whole screen with image. Leave no borders. Image may be larger than Screen
      if screenFactor > imageFactor:
        # portrait
        stretchedSize = (screenSize[0], screenSize[0]*image.size[1]/image.size[0])
      else: 
        # landscape
        stretchedSize = (screenSize[1]*image.size[0]/image.size[1], screenSize[1])
    elif method == "fit":
      # fit image to screen. Leave borders. Whole Image is displayed
      if screenFactor < imageFactor:
        # portrait
        stretchedSize = (screenSize[0], screenSize[0]*image.size[1]/image.size[0])
      else: 
        # landscape
        stretchedSize = (screenSize[1]*image.size[0]/image.size[1], screenSize[1])
      pass
    elif method == "stretch":
        pass
    else:       
        # noop, return original
        return image
          
    # apply resize operation and return result
    return image.resize(stretchedSize, Image.ANTIALIAS)  


  def ReplaceText(self, text):
      t_out, t_in, h_in = self.getSensorData()
      #self.debug('ReplaceText: '+str(self.item))

      dictionary = {
          "m": datetime.now().strftime("%m"), 
          "d": datetime.now().strftime("%d"), 
          "Y": datetime.now().strftime("%Y"),
          "H": datetime.now().strftime("%H"),
          "M": datetime.now().strftime("%M"),
          "LASTFULLHOUR": (datetime.now() - timedelta(minutes=(datetime.now().minute))).strftime("%H%M"),
          "LASTFULLHOUR_UTC": (datetime.utcnow() - timedelta(hours=1, minutes=(datetime.utcnow().minute))).strftime("%H%M"),
          "LASTFULLTHIRTYMINUTES": (datetime.now() - timedelta(minutes=(datetime.now().minute%30))).strftime("%H%M"),
          "LASTFULLTHIRTYMINUTES_UTC": (datetime.utcnow() - timedelta(minutes=(datetime.now().minute%30))).strftime("%H%M"),
          "LASTFULLTENMINUTES": (datetime.now() - timedelta(minutes=(datetime.now().minute%10))).strftime("%H%M"),
          "LASTFULLTENMINUTES_UTC": (datetime.utcnow() - timedelta(minutes=(datetime.utcnow().minute%10))).strftime("%H%M"),
          "LASTFULLFIVEMINUTES_UTC": (datetime.utcnow() - timedelta(minutes=(5+datetime.now().minute%5))).strftime("%H%M"),
          "TODAY": datetime.now().strftime("%Y%m%d"),
          "TOMORROW": (datetime.now() + timedelta(days=1)).strftime("%Y%m%d"),
          "DAYAFTERTOMORROW": (datetime.now() + timedelta(days=2)).strftime("%Y%m%d"),
          "T_OUT": '{0:0.1f}'.format(t_out),
          "T_IN": '{0:0.1f}'.format(t_in)
          }
      txtTemplate = string.Template(text)
      return txtTemplate.substitute(dictionary)


## URL can be local (filesystem) or remote (http)
  def getImage(self, item):
    screenSize = (self.settings.CustomDevice["width"],self.settings.CustomDevice["height"])
    canvas = Image.new("RGB", screenSize, "black")
    
    url = self.ReplaceText(item["source"])
    self.debug(url)

    if re.search(r"http", url):
      request = urllib2.Request(url)
      request.add_header('User-agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:46.0) Gecko/20100101 Firefox/46.0')

      try: 
        response = urllib2.urlopen(request, timeout = 5)
        headers = response.info()
#        print headers
        if re.search(r"image", headers.getheader('Content-Type')):
          result = response.read()
          image = Image.open(StringIO.StringIO(result))
        else:
          return False
      except urllib2.HTTPError as e:
        self.debug('The server couldn\'t fulfill the request: '+url)
        self.debug(e.code)
        return False
      except urllib2.URLError as e:
        self.debug('We failed to reach a server: '+url)
        self.debug(e.reason)
        return False
      except:  
        self.debug('Other Error: '+url)
        return False
    else:
      self.lock.acquire()
      image = Image.open(url)
      self.lock.release()
    
    if 'resize' in item:
      image = self.ResizeImage(image, screenSize, item["resize"])

    try:  
#      self.lock.acquire()
      image.convert("RGB").save(self.settings.OUTDIR+"/"+item["id"]+".jpg", "JPEG", quality=94)
#      self.lock.release()
    except:
      pass    
    return True


  def getWebsite(self, item):
    url = self.ReplaceText(item["source"])
    self.debug('retrieving: '+url)
    if 'element' in item:
      self.debug('element "'+ item["element"] + '"found')
      try: 
        res = subprocess.call([self.settings.PHANTOMJS,self.settings.ROOTDIR+"/capture.js", url, item["element"]]) 
      except:
        pass    
    else: 
      self.debug('whole page')
      try: 
        res = subprocess.call([self.settings.PHANTOMJS,self.settings.ROOTDIR+"/capture.js", url])
      except:
        pass    
    
    if res == 0:
      tmp = item.copy()  
      tmp["source"] = self.settings.ROOTDIR+"/out.png"
      self.getImage(tmp)
      return True
    else:
      return False


  def loop(self):
    # set up sequence
    html_snippet = ""
    for item in self.settings.sequence:
      html_snippet += '<div><img src="'+item["id"]+'.jpg"/></div>\n'

    #self.debug(self.settings.sequence)
    
    f_in = open(self.settings.OUTDIR+"/template.html", 'r')
    f_out = open(self.settings.OUTDIR+"/index.html", 'w')
    for line in f_in:
            f_out.write(line.replace('<!--<img src="000.png"/>-->', html_snippet))
    f_out.close()
    f_in.close()
    
    while run_event.is_set():
      if display_active.is_set():
        for item in self.settings.sequence:
          if (seconds() - item["last_refresh"]) > item["refresh"]:
            
            if item["type"] == 'urlimage':
              res = self.getImage(item)
            elif item["type"] == 'website':
              res = self.getWebsite(item)
            else:  
              # ignore unknown items
              res = True
              
              
            if res == True:  
              item["last_refresh"] = seconds()
            else:
              self.debug("Error downloading " + item["source"])
      time.sleep(1)


class DisplayThread:
  def __init__(self, settings, lock, run_event, display_active):
    self.lock = lock
    self.settings = settings
    self.debugActive = settings.debug
        
    self.FrameReady = False
    self.FrameCounter = 0
    
    self.start_time = seconds()
    self.display_next = 0;

    
  def debug(self, message):
    if self.debugActive:
      self.lock.acquire()
      print datetime.now().strftime("%H:%M") + ' ' + str(message)
      self.lock.release()       
      
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
    while run_event.is_set():
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
          display_active.set()
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
          display_active.clear()
      time.sleep(0.5)

      
if __name__ == '__main__':

  for item in settings.sequence:
    if not 'refresh' in item:
      item["refresh"] = 600
    item["last_refresh"] = 0
 
  if MULTIPROCESSING:
    run_event = multiprocessing.Event()
    run_event.set()  
    display_active = multiprocessing.Event()
    display_active.clear()  
    lock = multiprocessing.Lock()        # threading  
  else:  
    run_event = threading.Event()
    run_event.set()  
    display_active = threading.Event()
    display_active.clear()  
    lock = threading.Lock()        # threading  

  downloader = DownloadThread(settings, lock, run_event, display_active)
  display = DisplayThread(settings, lock, run_event, display_active)
  
  if MULTIPROCESSING:
    download_thread = multiprocessing.Process(target=downloader.loop)
    display_thread = multiprocessing.Process(target=display.loop)
  else:  
    download_thread = threading.Thread(target=downloader.loop)
    display_thread = threading.Thread(target=display.loop)

  download_thread.start()
  display_thread.start()
  
  try:
    while 1:
      time.sleep(1)

  except (KeyboardInterrupt, SystemExit):
    run_event.clear()
    download_thread.join()   
    display_thread.join()   
