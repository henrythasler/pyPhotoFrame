#!/usr/bin/env python
import sys
import struct
import usb1
import time
import string
import random
import Image, ImageDraw, ImageFilter, ImageFont
import StringIO
from os import walk
from datetime import datetime, timedelta
from time import mktime
import feedparser
import textwrap
import re
import urllib2
import HTMLParser



StorageDevice = {"vid": 0x04e8, "pid": 0x200c}
CustomDevice = {"vid": 0x04e8, "pid": 0x200d, "width": 800, "height": 600}

DEBUG = 0

Sequence = [
 
  #Webcams
  {"type":"URLIMAGE", "source": "http://www.foto-webcam.org/webcam/buchstein2/${Y}/${m}/${d}/${LASTFULLTENMINUTES}_la.jpg", "resize": "fit"},
  {"type":"URLIMAGE", "source": "http://www.foto-webcam.eu/webcam/garland/${Y}/${m}/${d}/${LASTFULLTENMINUTES}_la.jpg", "resize": "fit"},
  {"type":"URLIMAGE", "source": "http://www.foto-webcam.eu/webcam/kochelsee/${Y}/${m}/${d}/${LASTFULLTENMINUTES}_la.jpg", "resize": "fit"},  
  {"type":"URLIMAGE", "source": "http://www.foto-webcam.eu/webcam/herzogstand/${Y}/${m}/${d}/${LASTFULLTENMINUTES}_la.jpg", "resize": "fit"},
  {"type":"URLIMAGE", "source": "http://www.foto-webcam.eu/webcam/wank/${Y}/${m}/${d}/${LASTFULLTENMINUTES}_la.jpg", "resize": "fit"},  
  {"type":"URLIMAGE", "source": "http://www.foto-webcam.eu/webcam/tegelberg/${Y}/${m}/${d}/${LASTFULLTENMINUTES}_la.jpg", "resize": "fit"},

  # Cloud and Rain
  {"type":"URLIMAGE", "source": "http://www.wetteronline.de/?pid=p_sat_image&ireq=true&src=sat/vermarktung/p_sat_image/geostationary/createImages/wom/${Y}/${m}/${d}/CloudMask/BAY/${TODAY}${LASTFULLHOUR_UTC}_BAY_CloudMask.jpeg&version=0", "resize": None},
#  {"type":"URLIMAGE", "source": "http://www.wetteronline.de/?pid=p_sat_image&ireq=true&src=sat/vermarktung/p_sat_image/geostationary/createImages/wom/${Y}/${m}/${d}/CloudTops/BAY/${TODAY}${LASTFULLHOUR_UTC}_BAY_CloudTops.jpeg&version=0", "resize": None},
  {"type":"URLIMAGE", "source": "http://www.wetteronline.de/?ireq=true&pid=p_radar_map&src=radar/vermarktung/p_radar_map/wom/${Y}/${m}/${d}/Intensity/BAY/grey_shaded/${TODAY}${LASTFULLFIVEMINUTES_UTC}_BAY_Intensity.jpeg&version=0", "resize": None},
#  {"type":"URLIMAGE", "source": "http://www.wetteronline.de/?pid=p_aktuell_local&sid=Map&aktuellmap=true&iid=BAY&gid=BAY&paraid=WW&year=${Y}&month=${m}&day=${d}&time=${LASTFULLTHIRTYMINUTES_UTC}&baselayer=oro", "resize": None},
  
  # Weather Forecast
  {"type":"URLIMAGE", "source": "http://www.wetteronline.de/?daytime=day&diagram=true&fcdatstr=${TODAY}&iid=BAY&pid=p_city_local&sid=Pictogram", "resize": None},
  {"type":"URLIMAGE", "source": "http://www.wetteronline.de/?daytime=day&diagram=true&fcdatstr=${TOMORROW}&iid=BAY&pid=p_city_local&sid=Pictogram", "resize": None},
  {"type":"URLIMAGE", "source": "http://www.wetteronline.de/?daytime=day&diagram=true&fcdatstr=${DAYAFTERTOMORROW}&iid=BAY&pid=p_city_local&sid=Pictogram", "resize": None},
  {"type":"URLIMAGE", "source": "http://www.unwetterzentrale.de/images/map/bayern_index.png", "resize": "fit"},
  {"type":"URLIMAGE", "source": "http://www.wetteronline.de/?diagram=true&gid=10852&pid=p_city_local&trendchart=true", "resize": "fit"},
  

#  {"type":"URLIMAGE", "source": "http://www.dwd.de/DWD/wetter/aktuell/deutschland/bilder/wx_deutschland.jpg", "resize": None},

  {"type":"URLIMAGE", "source": "http://images2.wetterdienst.de/maps/germany/temp_aktuell.jpg", "resize": None},
  {"type":"URLIMAGE", "source": "http://www.wetteronline.de/?pid=p_aktuell_local&ireq=true&src=aktuell/vermarktung/p_aktuell_local/ColorMap/wom/de/DL/${Y}/${m}/${d}/TT/DL_${TODAY}_${LASTFULLHOUR_UTC}.gif", "resize": None},

#  {"type":"URLIMAGE", "source": "http://www.dwd.de/DE/wetter/wetterundklima_vorort/bayern/_functions/bildgalerie/wetter_aktuell.jpg;jsessionid=093CBDB1B55B16EDD545DE5360F24A97.live21062?view=nasImage&nn=560252", "resize": "fit"},
#  {"type":"URLIMAGE", "source": "http://images2.wetterdienst.de/maps/radar/Radarbild_Suedost.jpg?1451898124", "resize": "fit"},
  {"type":"URLIMAGE", "source": "http://nc.wetter-rosstal.de/blitzortung/bo.php?map=3", "resize": "fit"},
  
  {"type":"URLIMAGE", "source": "http://www.wetteronline.de/?ireq=true&pid=p_sat_image&src=sat/vermarktung/p_sat_image/geostationary/createImages/wom/${Y}/${m}/${d}/CloudMask/euro/${TODAY}${LASTFULLHOUR_UTC}_euro_CloudMask.jpeg", "resize": None},
   
#  {"type":"URLIMAGE", "source": "http://www.dwd.de/DWD/wetter/sat/bilder/meteosat/rgb/METE_RGB_wwwCeur1500m_aktuell_m00h.png", "resize": "fit"},
#  {"type":"URLIMAGE", "source": "http://www.dwd.de/DWD/wetter/sat/bilder/komposit/ir/KOMP_IR_wwwHammer40km_aktuell_m00s.png", "resize": "fit"},


  # RSS-Feed  
  {"type":"RSS"},
  {"type":"RSS"},
  
  # Images  
  {"type":"IMAGE", "name": "Mallorca 2015", "resize": "fill", "timeout": 4},
  {"type":"IMAGE", "name": "Mallorca 2015", "resize": "fill", "timeout": 4},
  {"type":"IMAGE", "name": "Mallorca 2015", "resize": "fill", "timeout": 4},
  
  #RSS-Feed
  {"type":"RSS"},
  {"type":"RSS"},
  
  #Simple Clock
  {"type":"TEXT", "content": "${H}:${M}", "size": 200, "timeout": 4},
            ]

context = usb1.USBContext()
active = True

h = HTMLParser.HTMLParser()

def hotplug_callback(context, device, event):
    print "%02x" % (event)
    if event == usb1.HOTPLUG_EVENT_DEVICE_ARRIVED:
      print "Manufacturer: %s" % device.getManufacturer()
      print "%04x:%04x" % (device.getVendorID(), device.getProductID())
      print "Product: %s" % device.getProduct()
      print "SerialNumber: %s" % device.getSerialNumber()
      print "DeviceSpeed: %s" % device.getDeviceSpeed()
    return False

def setCustomMode(dev):
    hndl = context.openByVendorIDAndProductID(
        dev['vid'], dev['pid'],
        skip_on_error=True)
    
    if not hndl:
        if DEBUG:
          print('StorageDevice Not found')
        return 0
      
    try:
      hndl.controlWrite(        0x80,           0x06,       0xfe,   0xfe,   b'\x00'*254,1000)
#          controlWrite(self,   request_type,   request,    value,  index,  data,       timeout=0):
    except:  
      pass
#      print('Set to custom mode')
    return 1
  
def sendJPEG(hndl, pic):
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

def ResizeImage(image, screenSize, method):
    screenFactor = float(screenSize[0])/float(screenSize[1])
    imageFactor = float(image.size[0])/float(image.size[1])
#    print "Screen %0.2f, Image %0.2f" % (screenFactor, imageFactor)
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
    
#    print image.size
#    print stretchedSize
#    print " "
    
    # apply resize operation and return result
    return image.resize(stretchedSize, Image.ANTIALIAS)

def ReplaceText(source):    
    dictionary = {
        "m": datetime.now().strftime("%m"), 
        "d": datetime.now().strftime("%d"), 
        "Y": datetime.now().strftime("%Y"),
        "H": datetime.now().strftime("%H"),
        "M": datetime.now().strftime("%M"),
        "LASTFULLHOUR": (datetime.now() - timedelta(minutes=(datetime.now().minute))).strftime("%H%M"),
        "LASTFULLHOUR_UTC": (datetime.now() - timedelta(hours=1, minutes=(datetime.now().minute))).strftime("%H%M"),
        "LASTFULLTHIRTYMINUTES": (datetime.now() - timedelta(minutes=(datetime.now().minute%30))).strftime("%H%M"),
        "LASTFULLTHIRTYMINUTES_UTC": (datetime.utcnow() - timedelta(minutes=(datetime.now().minute%30))).strftime("%H%M"),
        "LASTFULLTENMINUTES": (datetime.now() - timedelta(minutes=(datetime.now().minute%10))).strftime("%H%M"),
        "LASTFULLFIVEMINUTES_UTC": (datetime.utcnow() - timedelta(minutes=(5+datetime.now().minute%5))).strftime("%H%M"),
        "TODAY": datetime.now().strftime("%Y%m%d"),
        "TOMORROW": (datetime.now() + timedelta(days=1)).strftime("%Y%m%d"),
        "DAYAFTERTOMORROW": (datetime.now() + timedelta(days=2)).strftime("%Y%m%d"),
        
        }
    
    txtTemplate = string.Template(source)
    return txtTemplate.substitute(dictionary)

## URL can be local (filesystem) or remote (http)
def sendURLJPEG(hndl, url, resizeMethod=None):
    screenSize = (CustomDevice["width"],CustomDevice["height"])
    canvas = Image.new("RGB", screenSize, "black")

    if re.search(r"http", url):

        request = urllib2.Request(ReplaceText(url))
        request.add_header('User-agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:35.0) Gecko/20100101 Firefox/35.0')

        try: 
            response = urllib2.urlopen(request)
            headers = response.info()
    #        print headers
            if re.search(r"image", headers.getheader('Content-Type')):
                result = response.read()
                image = Image.open(StringIO.StringIO(result))
            else:
                image = Image.new("RGB",(100, 100), "red");    
        except urllib2.HTTPError as e:
            print 'The server couldn\'t fulfill the request.'+url
            print 'Error code: ', e.code
            return False;
        except urllib2.URLError as e:
            print 'We failed to reach a server.'+url
            print 'Reason: ', e.reason            
            return False;
        
    else:
        image = Image.open(url)
    
    if resizeMethod:
        image = ResizeImage(image, screenSize, resizeMethod)
        
    canvas.paste(image, ( (CustomDevice["width"]-image.size[0])/2,(CustomDevice["height"]-image.size[1])/2))
    
    output = StringIO.StringIO()
    canvas.save(output, "JPEG", quality=94)
    pic  = output.getvalue()
    output.close()
    sendJPEG(hndl,pic)
    return True;

def sendText(hdnl, content, fontsize):
    screenSize = (CustomDevice["width"],CustomDevice["height"])
    canvas = Image.new("RGB", screenSize, "black")
    draw = ImageDraw.Draw(canvas)

    fontFace = "OpenSans"
    fontType = "Regular"
    
    content = ReplaceText(content)
    
    TextFont=ImageFont.truetype("fonts/"+fontFace+"-"+fontType+".ttf", fontsize)
    textsize = TextFont.getsize(content)
    draw.text( ( (CustomDevice["width"] - textsize[0])/2, (CustomDevice["height"] - textsize[1])/2), content, font=TextFont, fill="#ddd")
    del draw    
    
    output = StringIO.StringIO()
    canvas.save(output, "JPEG", quality=94)
    pic  = output.getvalue()
    output.close()
    sendJPEG(hndl,pic)

    
def sendRSSItem(hdnl, item):
    screenSize = (CustomDevice["width"],CustomDevice["height"])
    canvas = Image.new("RGB", screenSize, "white")
    draw = ImageDraw.Draw(canvas)

    fontFace = "OpenSans"
    fontType = "Regular"
    
    HeaderFont=ImageFont.truetype("fonts/"+fontFace+"-"+fontType+".ttf", 50)
    TextFont=ImageFont.truetype("fonts/"+fontFace+"-"+fontType+".ttf", 35)
    SmallFont=ImageFont.truetype("fonts/"+fontFace+"-"+fontType+".ttf", 20)

    hasimage = False
    if hasattr(item, 'links'):
      for link in item.links:
        if hasattr(link, 'type'):
          if link.type == "image/jpeg":
            thumbnail = Image.open(StringIO.StringIO(urllib.urlopen(link.href).read()))
            canvas.paste(thumbnail.resize((200,200)), (canvas.size[0]-200, 0))
            hasimage = True

    offset = 0
    wrapwidth = 31
    if hasimage == True:
      wrapwidth = 23
      
    if hasattr(item, 'title'):
      lineheight = HeaderFont.getsize("A")[1]
      text = item.title
      for line in textwrap.wrap(text, width=wrapwidth):
        draw.text((10, offset), line, font=HeaderFont, fill="#222")
        offset += lineheight
    
    offset += 30
    
    if hasimage == True:
      offset = max(offset, 200)

    if hasattr(item, 'summary'):
      lineheight = TextFont.getsize("A")[1]
      text = h.unescape(re.sub("<.*?>", "", item.summary))
      for line in textwrap.wrap(text, width=42):
        draw.text((30, offset), line, font=TextFont, fill="#222")
        offset += lineheight

      offset += 30
      
    try:
      if hasattr(item, 'published_parsed'):
        text = datetime.fromtimestamp(mktime(item.published_parsed)).strftime("%d.%m.%Y %H:%M")
      elif hasattr(item, 'updated_parsed'):
        text = datetime.fromtimestamp(mktime(item.updated_parsed)).strftime("%d.%m.%Y %H:%M")
      else:
        text=""  
    
      for line in textwrap.wrap(text, width=43):
        draw.text((30, offset), line, font=SmallFont, fill="grey")
        offset += SmallFont.getsize(line)[1]
    except:
      pass
   
    del draw    
    
    output = StringIO.StringIO()
    canvas.save(output, "JPEG", quality=94)
    pic  = output.getvalue()
    output.close()
    sendJPEG(hndl,pic)


if __name__ == '__main__':
  
      FrameCounter = 0
      
      feedURLs = [
#                    "http://xkcd.com/atom.xml"
                  "http://www.heise.de/newsticker/heise-atom.xml",
                  "http://www.tagesschau.de/xml/atom"
#                  "http://www.spiegel.de/schlagzeilen/tops/index.rss",
#                  "http://rss.golem.de/rss.php?feed=ATOM1.0",
                  ]
      d = []
      for url in feedURLs:
        d += feedparser.parse(url).entries

      ImageContainer = {"Mallorca 2015":{"source":"/media/Storage64/Bilder/Mallorca 2015", "files":[]}}
      for key,value in ImageContainer.iteritems():
        for (dirpath, dirnames, filenames) in walk(value["source"]):
          value["files"].extend(filenames)
          break
        
#      print ImageContainer
      
      
      try:
          while True:
            FrameReady = False
            deviceList = context.getDeviceList(skip_on_error=True)
            for device in deviceList:
                if device.getVendorID() == StorageDevice['vid']:
                  if device.getProductID() == StorageDevice['pid']:
                    if DEBUG: print "Found '%s' in storage mode" % device.getProduct()
                    if setCustomMode(StorageDevice) == 1:
                      time.sleep(1)
                      if DEBUG: print "custom mode set"
                      FrameReady = True
                      FrameCounter = 0
                  elif device.getProductID() == CustomDevice['pid']:
                    if DEBUG: print "Found '%s' in custom mode" % device.getProduct()
                    FrameReady = True
            if FrameReady == True:
              hndl = context.openByVendorIDAndProductID(
                  CustomDevice['vid'], CustomDevice['pid'],
                  skip_on_error=True)
              if not hndl:
                  if DEBUG: print('Error opening device')
              else:   
                hndl.claimInterface(0)
                seqItem = Sequence[FrameCounter % len(Sequence)]
                
                if "timeout" in seqItem:
                    sleeptime = seqItem["timeout"]
                else:
                    sleeptime = 10
                    
                if seqItem["type"] == "IMAGE":
                  sendURLJPEG(hndl, 
                               ImageContainer[seqItem["name"]]["source"]+ "/" + random.choice(ImageContainer[seqItem["name"]]["files"]), 
                               seqItem["resize"])
                  
                elif seqItem["type"] == "URLIMAGE":
                  if sendURLJPEG(hndl, seqItem["source"], seqItem["resize"]) == False:
                      sleeptime=0;

                elif seqItem["type"] == "TEXT":
                  sendText(hndl, seqItem["content"], seqItem["size"])
                  
                elif seqItem["type"] == "RSS":
                  sendRSSItem(hndl, random.choice(d))
                else:
                  pass
                  
                FrameCounter=FrameCounter+1
                if FrameCounter % 60 == 0:
                    d = []
                    for url in feedURLs:
                      d += feedparser.parse(url).entries
                      
                time.sleep(sleeptime)
                
            else:
              time.sleep(1)
              if DEBUG: print "No device found"
            
      except (KeyboardInterrupt, SystemExit):
          print "done"
          pass
