#!/usr/bin/env python
# -*- coding: utf-8 -*-

ROOTDIR = "/home/henry/pyPhotoFrame"
DATADIR = "/home/henry/pyLogger"
OUTDIR = "/home/henry/pyPhotoFrame/html"

#PHANTOMJS = "/home/henry/jsPhotoFrame/phantomjs-armv7/bin/phantomjs"

# from: https://github.com/mecrazy/phantomjs-binaries
PHANTOMJS = "/home/henry/pyPhotoFrame/phantomjs-2.1.1/phantomjs-2.1.1-linux-armhf"

debug = False

BrokerURL = 'localhost'

StorageDevice = {"vid": 0x04e8, "pid": 0x200c}
CustomDevice = {"vid": 0x04e8, "pid": 0x200d, "width": 800, "height": 600}

id = 0

def autoid(): 
  global id
  id += 1
  return '{0:04.0f}'.format(id)

# https://docs.python.org/2/tutorial/datastructures.html#dictionaries
test = [
  {
   "id": autoid(), 
   "type":"website", 
   "source": "file:///"+ROOTDIR+"/index.html?hour=${H}&minute=${M}&temp_in=${T_IN}&temp_out=${T_OUT}", 
   "resize": None,
   "skip": False,
   "timeout": 8,
   "refresh": 60,
   },
  {
    "id": autoid(), 
    "type":"urlimage", 
    "source": "/home/henry/pyLogger/out.png", 
    "resize": None,
    "timeout": 10,
    "refresh": 600,
  },
]

id = 0
sequence = [
  # Time and Temperature
  {
   "id": autoid(), 
   "type":"website", 
   "source": "file:///"+ROOTDIR+"/index.html?hour=${H}&minute=${M}&temp_in=${T_IN}&temp_out=${T_OUT}", 
   "resize": None,
   "skip": False,
   "timeout": 8,
   "refresh": 60,
   },
    
  # Temperature Chart
  {
    "id": autoid(), 
    "type":"urlimage", 
    "source": "/home/henry/pyLogger/out.png", 
    "resize": None,
    "refresh": 600,
  },
  
  # Train
  {
   "id": autoid(), 
   "type":"website", 
   "source": "http://127.0.0.1:3000/MMR?hide_opts=1", 
   "resize": None, 
   "skip": False,
   "timeout": 8,
   "refresh": 60,
    "schedule": {
      "0": "13-17",
      "1": "6-8",
      "2": "6-8",
      "3": "6-8",
      "4": "6-8",
      "5": "6-8",
      "6": "13-17",
      },
   },
   
  # Traffic
  {
   "id": autoid(), 
   "type":"urlimage", 
   "source": "http://dev.virtualearth.net/REST/V1/Imagery/Map/Road/48.24,11.20/10/?mapLayer=TrafficFlow&fmt=png&mapSize=800,600&key=AhQ0xaa4zjCPOgZCFhgav_B_wXcMD5KfMSui003rLZx6BzZg3Gh63utlCv4c40mj", 
   "resize": None,
   "skip": True,
   "timeout": 5,
   "refresh": 300,
    "schedule": {
      "0": "0-0",
      "1": "6-8",
      "2": "6-8",
      "3": "6-8",
      "4": "6-8",
      "5": "6-8",
      "6": "0-0",
      }
   },


  #Webcams
  {
    "id": autoid(), 
    "type":"urlimage", 
    "source": "https://www.foto-webcam.eu/webcam/peissenberg/current/720.jpg", 
    "resize": "fit", 
    "refresh": 600,
  },
  {
    "id": autoid(), 
    "type":"urlimage", 
    "source": "http://www.addicted-sports.com/fileadmin/webcam/ammersee/${Y}/${m}/${d}/${LASTFULLTENMINUTES}_ld.jpg", 
    "resize": "fit",
    "refresh": 600,
  },
  {
    "id": autoid(), 
    "type":"urlimage", 
    "source": "http://www.addicted-sports.com/fileadmin/webcam/starnbergersee/${Y}/${m}/${d}/${LASTFULLTHIRTYMINUTES}_ld.jpg", 
    "resize": "fit",
    "refresh": 600,
  },
  {
    "id": autoid(), 
    "type":"urlimage", 
    "source": "https://www.foto-webcam.eu/webcam/wendelstein-ost/current/720.jpg", 
    "resize": "fit", 
    "refresh": 600,
  },
  {
    "id": autoid(), 
    "type":"urlimage", 
    "source": "https://www.foto-webcam.eu/webcam/garland/current/720.jpg", 
    "resize": "fit", 
    "refresh": 600,
  },
  {
    "id": autoid(), 
    "type":"urlimage", 
    "source": "https://www.foto-webcam.eu/webcam/kochelsee/current/720.jpg", 
    "resize": "fit", 
    "refresh": 600,
  },  
  {
    "id": autoid(), 
    "type":"urlimage", 
    "source": "https://www.foto-webcam.eu/webcam/herzogstand/current/720.jpg", 
    "resize": "fit", 
    "refresh": 600,
  },
  {
    "id": autoid(), 
    "type":"urlimage", 
    "source": "http://www.addicted-sports.com/fileadmin/webcam/walchensee/${Y}/${m}/${d}/${LASTFULLTHIRTYMINUTES}_ld.jpg", 
    "resize": "fit",
    "refresh": 600,
  },
  {
    "id": autoid(), 
    "type":"urlimage", 
    "source": "https://www.foto-webcam.eu/webcam/wank/current/720.jpg", 
    "resize": "fit",
    "refresh": 600,
  },  
  {
    "id": autoid(), 
    "type":"urlimage", 
    "source": "https://www.foto-webcam.eu/webcam/tegelberg/current/720.jpg", 
    "resize": "fit",
    "refresh": 600,
  },
  {
    "id": autoid(), 
    "type":"urlimage", 
    "source": "https://www.foto-webcam.eu/webcam/furkajoch/current/720.jpg", 
    "resize": "fit", 
    "refresh": 600,
  },


  # Cloud and Rain
  {
    "id": autoid(), 
    "type":"urlimage", 
    "source": "http://www.wetteronline.de/?ireq=true&pid=p_radar_map&src=wmapsextract/vermarktung/global2maps/${Y}/${m}/${d}/BAY/composite/${TODAY}${LASTFULLFIVEMINUTES_UTC}_BAY.jpeg", 
    "resize": None,
    "refresh": 3600,
  },
    
  # Weather Forecast
  {
    "id": autoid(), 
    "type":"website", 
    "source": "http://www.wetteronline.de/wetter/mering", 
    "element": "mediumtermforecast", 
    "resize": "fit", 
    "timeout": 10,
    "refresh": 3600,
  },
  {
    "id": autoid(), 
    "type":"website", 
    "source": "http://www.wetteronline.de/wetter/mering?prefpar=wind", 
    "element": "mediumtermforecast", 
    "resize": "fit", 
    "timeout": 5,
    "refresh": 3600,
  },
  {
    "id": autoid(), 
    "type":"website", 
    "source": "http://www.wetteronline.de/wetter/mering?prefpar=precipitation", 
    "element": "mediumtermforecast", 
    "resize": "fit", 
    "timeout": 5,
    "refresh": 3600,
  },
  {
    "id": autoid(), 
    "type":"website", 
    "source": "http://www.wetteronline.de/wetter/mering?prefpar=sun", 
    "element": "mediumtermforecast", 
    "resize": "fit", 
    "timeout": 5,
    "refresh": 3600,
  },
  
  {
    "id": autoid(), 
    "type":"urlimage", 
    "source": "http://www.wetteronline.de/?daytime=day&diagram=true&fcdatstr=${TODAY}&iid=BAY&pid=p_city_local&sid=Pictogram", 
    "resize": None,
    "refresh": 3600,
  },
  {
    "id": autoid(), 
    "type":"urlimage", 
    "source": "http://www.wetteronline.de/?daytime=day&diagram=true&fcdatstr=${TOMORROW}&iid=BAY&pid=p_city_local&sid=Pictogram", 
    "resize": None,
    "refresh": 3600,
  },
  {
    "id": autoid(), 
    "type":"urlimage", 
    "source": "http://www.wetteronline.de/?daytime=day&diagram=true&fcdatstr=${DAYAFTERTOMORROW}&iid=BAY&pid=p_city_local&sid=Pictogram", 
    "resize": None,
    "refresh": 3600,
  },
  {
    "id": autoid(), 
    "type":"urlimage", 
    "source": "http://www.unwetterzentrale.de/images/map/bayern_index.png", 
    "resize": "fit",
    "refresh": 600,
  },
  {
    "id": autoid(), 
    "type":"urlimage", 
    "source": "http://www.wetteronline.de/?diagram=true&gid=10852&pid=p_city_local&trendchart=true", 
    "resize": "fit",
    "refresh": 3600,
  },
  
  {
    "id": autoid(), 
    "type":"urlimage", 
    "source": "http://www.wetteronline.de/?pid=p_aktuell_local&ireq=true&src=aktuell/vermarktung/p_aktuell_local/ColorMap/wom/de/DL/${Y}/${m}/${d}/TT/DL_${TODAY}_${LASTFULLHOUR_UTC}.gif", 
    "resize": None,
    "refresh": 1800,
  },

  {
    "id": autoid(), 
    "type":"urlimage", "source": "http://nc.wetter-rosstal.de/blitzortung/bo.php?map=3", 
    "resize": "fit",
    "refresh": 600,
  },
  
  {
    "id": autoid(), 
    "type":"urlimage", 
    "source": "http://www.wetteronline.de/?ireq=true&pid=p_radar_map&src=wmapsextract/vermarktung/global2maps/${Y}/${m}/${d}/DL/composite/${TODAY}${LASTFULLTENMINUTES_UTC}_DL.jpeg", 
    "resize": None,
    "refresh": 600,
  },
  {
    "id": autoid(), 
    "type":"urlimage", 
    "source": "http://www.wetteronline.de/?ireq=true&pid=p_radar_map&src=wmapsextract/vermarktung/global2maps/${Y}/${m}/${d}/euro/composite/${TODAY}${LASTFULLTENMINUTES_UTC}_euro.jpeg", 
    "resize": None,
    "refresh": 600,
  },
]

id = 0
backup = [
  {
    "id": autoid(), 
    "type":"website", 
    "source": "http://iris.noncd.db.de/wbt/js/index.html?typ=ab&bhf=8003982&zugtyp=&platform=4&bhfname=&style=ab&via=1&impressum=1&lang=de&SecLang=&zeilen=5&paging=&pagingdauer=", 
    "resize": "fit", 
    "timeout": 5,
    "refresh": 600,
  },

  #Webcams
  {
    "id": autoid(), 
    "type":"urlimage", 
    "source": "http://www.foto-webcam.org/webcam/buchstein2/${Y}/${m}/${d}/${LASTFULLTENMINUTES}_la.jpg", 
    "resize": "fit",
    "refresh": 600,
  },
  {
    "id": autoid(), 
    "type":"urlimage", 
    "source": "http://www.foto-webcam.eu/webcam/garland/${Y}/${m}/${d}/${LASTFULLTENMINUTES}_la.jpg", 
    "resize": "fit",
    "refresh": 600,
  },
  {
    "id": autoid(), 
    "type":"urlimage", 
    "source": "http://www.foto-webcam.eu/webcam/kochelsee/${Y}/${m}/${d}/${LASTFULLTENMINUTES}_la.jpg", 
    "resize": "fit",
    "refresh": 600,
  },  
  {
    "id": autoid(), 
    "type":"urlimage", 
    "source": "http://www.foto-webcam.eu/webcam/herzogstand/${Y}/${m}/${d}/${LASTFULLTENMINUTES}_la.jpg", 
    "resize": "fit",
    "refresh": 600,
  },
  {
    "id": autoid(), 
    "type":"urlimage", 
    "source": "http://www.foto-webcam.eu/webcam/wank/${Y}/${m}/${d}/${LASTFULLTENMINUTES}_la.jpg", 
    "resize": "fit",
    "refresh": 600,
  },  
  {
    "id": autoid(), 
    "type":"urlimage", 
    "source": "http://www.foto-webcam.eu/webcam/tegelberg/${Y}/${m}/${d}/${LASTFULLTENMINUTES}_la.jpg", 
    "resize": "fit",
    "refresh": 600,
  },
  {
    "id": autoid(), 
    "type":"urlimage", 
    "source": "http://www.foto-webcam.eu/webcam/furkajoch/${Y}/${m}/${d}/${LASTFULLTENMINUTES}_la.jpg", 
    "resize": "fit",
    "refresh": 600,
  },

  # RSS-Feed  
  {
    "id": autoid(), 
    "type":"rss",
  },
  {
    "id": autoid(), 
    "type":"rss",
  },
]
