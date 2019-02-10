#!/usr/bin/env python
# -*- coding: utf-8 -*-

import settings
import time
from datetime import datetime, timedelta
import Image, ImageDraw, ImageFilter, ImageFont
import StringIO
import struct
import csv
import string
import re
import io
import urllib2
import subprocess
import os
import paho.mqtt.client as mqtt
import json
import socket


seconds = lambda: int(round(time.time()))

class DownloadThread:
  def __init__(self, settings):
    self.settings = settings
    self.active = True
    self.idletime = 1
    self.lastConnectionCheck = 0
    self.connected = False
    self.topics = []

    self.sensordata = {
        'T_IN': 0.0,
        'T_OUT': 0.0
        }

    #setup mqtt stuff
    for item in self.settings.sequence:
        if item["type"] == 'mqttimage':
            self.topics.append(item)
    
    self.client = mqtt.Client('pyImageGenerator-%s' % os.getpid())
    self.client.on_connect = self.on_connect
    self.client.on_message = self.on_message

    self.client.connect(self.settings.BrokerURL)
    self.client.loop_start()
    
    
  def debug(self, message):
    if self.settings.debug:
      try:
        print datetime.now().strftime("%H:%M") + ' ' + str(message)
      except:
        pass

  def is_connected(self, hostname):
    try:
      host = socket.gethostbyname(hostname)
      s = socket.create_connection((host, 80), 2)
      return True
    except:
      pass
    return False

  # The callback for when the client receives a CONNACK response from the server.
  def on_connect(self, client, userdata, flags, rc):
    self.debug("Connected to mqtt broker with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("home/out/temp")
    client.subscribe("home/in/temp")
    client.subscribe("home/display/active")
    for topic in self.topics:
        client.subscribe(topic["source"])

  # The callback for when a PUBLISH message is received from the server.
  def on_message(self, client, userdata, msg):
    if msg.topic.startswith('home/out/temp'):
      self.sensordata['T_OUT'] = float(json.loads(msg.payload)['value'])
      
    elif msg.topic.startswith('home/in/temp'):
      self.sensordata['T_IN'] = float(json.loads(msg.payload)['value'])

    elif msg.topic.startswith('home/display/active'):
      self.active = msg.payload.lower() in ('1', '1.0', 'true', 'on', 'active')
      self.idletime = 1
      
    else:
        for topic in self.topics:
            if msg.topic.startswith(topic["source"]):
                self.debug(topic["source"])
                buffer = io.BytesIO(msg.payload)
                img = Image.open(buffer)
                screenSize = (self.settings.CustomDevice["width"],self.settings.CustomDevice["height"])
                img = self.ResizeImage(img, screenSize, topic["resize"])
                img.convert("RGB").save(self.settings.OUTDIR+"/"+topic["id"]+".jpg", "JPEG", quality=94)
                
    
    #self.debug(msg.topic + ': ' + msg.payload);


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
#      self.debug('ReplaceText'+str(self.sensordata))

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
          "T_OUT": '{0:0.1f}'.format(self.sensordata['T_OUT']),
          "T_IN": '{0:0.1f}'.format(self.sensordata['T_IN'])
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
      if 'header' in item:
          for key, value in item["header"].iteritems():
              self.debug('Adding header ' + key + ": " + value)
              request.add_header(key, value)

      try: 
        response = urllib2.urlopen(request, timeout = 5)
        headers = response.info()
        #print headers
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
      except (KeyboardInterrupt, SystemExit):
        pass
      except:  
        self.debug('Other Error: '+url)
        return False
    elif os.path.exists(url):
      image = Image.open(url)
    else:
      return False
    
    with io.BytesIO() as output:
      image.convert("RGB").save(output, "JPEG", quality=94)
      byteArray = bytearray(output.getvalue())
      self.client.publish('home/display/images/'+item['id'], byteArray, retain=True)    
    
    if 'resize' in item:
      image = self.ResizeImage(image, screenSize, item["resize"])

    try:  
      image.convert("RGB").save(self.settings.OUTDIR+"/"+item["id"]+".jpg", "JPEG", quality=94)
    except:
      pass    
    return True


  def getWebsite(self, item):
    url = self.ReplaceText(item["source"])
    self.debug('retrieving: '+url)
    res = None
    if 'element' in item:
      self.debug('element "'+ item["element"] + '"found')
      try: 
        res = subprocess.call([self.settings.PHANTOMJS,self.settings.ROOTDIR+"/capture.js", url, item["element"]]) 
      except (KeyboardInterrupt, SystemExit):
        pass
      except:
        self.debug('PHANTOMJS Error')
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
    
    # wait for MQTT-Sensordata
    time.sleep(.2)    
    

    while True:
      if self.active:
        if seconds() - self.lastConnectionCheck > 30: 
            self.connected = self.is_connected("www.heise.de")
        for item in self.settings.sequence:
          if self.connected or "http" not in item["source"]:
            if (seconds() - item["last_refresh"]) > item["refresh"]:
              if item["type"] == 'urlimage':
                res = self.getImage(item)
              elif item["type"] == 'website':
                res = self.getWebsite(item)
              elif item["type"] == 'mqttimage':
                res = True
              else:  
                # ignore unknown items
                self.debug("Unknown"+item["type"])
                res = True
              
              
              if res == True:  
                item["last_refresh"] = seconds()
              else:
                self.debug("Error downloading " + item["source"])
          else:
              self.debug("No internet connection " + item["source"])
      else:
        self.debug('sleeping...')
        self.idletime = 5
      time.sleep(self.idletime)

      
if __name__ == '__main__':

  for item in settings.sequence:
    if not 'refresh' in item:
      item["refresh"] = 600
    item["last_refresh"] = 0
 
  downloader = DownloadThread(settings)
  
  try:
    downloader.loop()
  except (KeyboardInterrupt, SystemExit):
    pass
