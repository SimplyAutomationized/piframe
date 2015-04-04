import cuter as cut
from os import path
from piUtils import *
import sys, json, os, stat, base64
import sys, random, time
from StringIO import StringIO
from time import strftime, sleep
from time import sleep
from PIL import Image
from twisted.internet import reactor
from twisted.python import log
from twisted.web.server import Site
from fractions import Fraction
from twisted.web.static import File
from autobahn.twisted.websocket import WebSocketServerFactory, \
    WebSocketServerProtocol, \
    listenWS

clients = []
picframeclients=[]
localclient = None
startdir = '/home/pi/piframe/www/pics/'
configdir='/home/pi/piframe/www/config.json'
file_list = []
current_img= ''

class frameconfig():
	def __init__(self,configfile):
		self.dir = configfile
		if not self.configExist():
			self.createConfigJSON()
	def getConfigJSON(self):
		print self.dir
		file = open(self.dir,'r')
		jsondata = file.read()
		file.close()
		return jsondata
	def createConfigJSON(self):
		config = json.dumps({'showclock':'true','showtemp':'true','transitiontime':60})
		file = open(self.dir,'w+')
		file.write(config)
		file.close()
	def changeKey(self,key,newval):
		file = open(self.dir,'r')
		jsondata = json.loads(file.read())
		file.close
		file =  open(self.dir,'w')
		jsondata[key]=newval
		file.write(json.dumps(jsondata))
		file.close()
	def configExist(self):
		return (path.isfile(self.dir))


def walktree(top, callback):
    """recursively descend the directory tree rooted at top, calling the
    callback function for each regular file. Taken from the module-stat
    example at: http://docs.python.org/lib/module-stat.html
    """
    for f in os.listdir(top):
        pathname = os.path.join(top, f)
        mode = os.stat(pathname)[stat.ST_MODE]
        if stat.S_ISDIR(mode):
            # It's a directory, recurse into it
            walktree(pathname, callback)
        elif stat.S_ISREG(mode):
            # It's a file, call the callback function
            callback(pathname)
        else:
            # Unknown file type, print a message
            print 'Skipping %s' % pathname

def addtolist(file, extensions=['.png', '.jpg', '.jpeg', '.gif', '.bmp']):
    """Add a file to a global list of image files."""
    global file_list  
    filename, ext = os.path.splitext(file)
    e = ext.lower()
    # Only add common image types to the list.
    if e in extensions:
        parsedFile=file.replace('/home/pi/piframe/www/','')
        if (parsedFile not in file_list):
            file_list.append(parsedFile)
            #print 'Adding to list: ', parsedFile
    else:
        print 'Skipping: ', file, ' (NOT a supported image)'
def rotateimage(img,deg,makeThumb=True):
		im = Image.open(img)
		newimg = im.rotate(float(deg))
		newfile,ext =img.split('.')
		newfilename=startdir+str(time.time()).replace('.','')+'.'+ext
		newimg.save(newfilename)
		if(makeThumb):
			thumb,newthumb_ext = newfilename.replace('pics/','thumb/').split('.')
			cut.resize_and_crop(newfilename,thumb+'_thumb.'+newthumb_ext,[320,240])
			oldthumb,old_ext=img.replace('pics/','thumb/').split('.')
			os.remove(oldthumb+"_thumb."+old_ext)
		os.remove(img)
		print 'rotation',img
		return newfilename.replace(startdir,'')
class BroadcastServerProtocol(WebSocketServerProtocol):
    def onOpen(self):
        #print self.__dict__
        self.factory.register(self)

    def onMessage(self, payload, isBinary):
        global current_img,file_list
        if not isBinary:
            msg = "{} from {}".format(payload.decode('utf8'), self.peer)
            # self.factory.broadcast(msg)
            cmd = json.loads(payload)
            if (cmd.has_key("cmd")):
				if(cmd.has_key("img")):#grab actual filename if json time was appended
					oldname = cmd["img"]
					cmd["img"]=cmd["img"].split('?')[0] 
				if(cmd["cmd"]=="getImages"):
					print 'getting images'
					self.sendMessage(json.dumps({"images":[w.replace('pics/','thumb/').replace('.','_thumb.') for w in file_list]}));
					print 'sent images'
				if(cmd["cmd"]=="getCurrentImage"):
					self.sendMessage(json.dumps({"currentImg":current_img}))
				if(cmd["cmd"]=="setCurrentImage"):
					current_img=cmd["value"].replace('_thumb','').replace('thumb/','pics/')
					self.factory.picChange(current_img)
				if(cmd["cmd"]=="remove"):
					img2remove=cmd["img"].replace('_thumb','').replace('thumb/',startdir)
					thumb2remove = startdir.replace('pics','')+cmd["img"];
					os.remove(img2remove)
					os.remove(thumb2remove)
					self.sendMessage(json.dumps({"imageRemoved:'"+oldname+"'"}))
				if(cmd["cmd"]=="rotateImage"):
					img = cmd["img"].replace('_thumb','').replace('thumb/',startdir)
					thumb = startdir.replace('pics','')+cmd["img"];
					newfilename,ext=rotateimage(img,int(cmd["value"])).split('.')
					self.sendMessage(json.dumps({"imageUpdate":'thumb/'+newfilename+"_thumb."+ext,"oldname":oldname}))
				if(cmd["cmd"]=="setConfig"):
					self.factory.frameconfig.changeKey(cmd['change'].keys()[0],cmd['change'].values()[0])
					self.factory.sendNewConfig(self)
					self.factory.callID.cancel()#cancel any async calls for the picture frame ticks
					self.factory.timeout = json.loads(self.frameconfig.getConfigJSON())["transitiontime"]
					self.factory.tick()
				if(cmd["cmd"]=="getConfig"):
					self.factory.sendNewConfig(self)
            if (cmd.has_key("upload")):
                imgstring = cmd["upload"]
                appendage = str(time.time()).replace('.', '')
                strio = StringIO(imgstring.decode('base64'))
                strpath = startdir.replace('pics','thumb') + appendage + '_thumb.'+cmd['file_type']
				#create thumbnail
                if(cmd['file_type']!="gif"):
                    cut.resize_and_crop(strio, strpath, [320, 240])  # ,crop_type='middle')
                else:
                    fh = open("/home/pi/piframe/www/thumb/" + appendage + "_thumb.gif", "wb")
                    fh.write(imgstring.decode('base64'))
                    fh.close()
                #create original
                fh = open("/home/pi/piframe/www/thumb/" + appendage+ '.'+cmd['file_type'], "wb")
                fh.write(imgstring.decode('base64'))
                fh.close()
                os.system('chown pi /home/pi/piframe/www/thumb/' + appendage + '_thumb.'+cmd['file_type']);
    def connectionLost(self, reason):
        WebSocketServerProtocol.connectionLost(self, reason)
        self.factory.unregister(self)


class BroadcastServerFactory(WebSocketServerFactory):
	def __init__(self, url, debug=False, debugCodePaths=False):
		WebSocketServerFactory.__init__(self, url, debug=debug, debugCodePaths=debugCodePaths)
		global clients,picframeclients,current_img
		self.current_img=current_img
		self.frameconfig = frameconfig(configdir)
		config = json.loads(self.frameconfig.getConfigJSON())
		self.picframeclients=picframeclients
		self.clients = clients
		self.timeout = config['transitiontime']
		self.tempProbe = TempProbe(self.broadcast)
		self.tempProbe.start()
		self.callID=None
		self.tick()
	def stopProbe():
		self.tempProbe.setEnabled(False)
	def tick(self):
		# check directory for new files
		self.getRandomPic()
		self.picChange(self.current_img)
		self.callID=reactor.callLater(self.timeout, self.tick)
	def getRandomPic(self):
		walktree(startdir, addtolist)
		# grab random image from array
		num_files = len(file_list)
		print num_files
		current = random.randint(1, num_files) - 1
		self.current_img=file_list[current]
	def register(self, client):
		peer = client.peer
		client.showcamera=False
		client.sendMessage(json.dumps({'temperature':self.tempProbe.getCurrentTemp()}))
		if (client.http_request_uri == "/?picframe"):
			print peer
			self.picframeclients.append(client)
			client.sendMessage(json.dumps({'img':self.current_img}))
		else:
			if not client in self.clients:
				print("registered client {}".format(client.peer))
				self.clients.append(client)

	def unregister(self, client):
		if client in self.clients:
			print("unregistered client {}".format(client.peer))
			self.clients.remove(client)
		elif client in self.picframeclients:
			print("unregistered picframe client ",client.peer)
			self.picframeclients.remove(client)
	def picChange(self, img):
		if (len(self.picframeclients)>0):
			for c in self.picframeclients:
				print 'sending to: ',c.peer
				c.sendMessage(json.dumps({'img':img}),isBinary=False)
	def broadcast(self, msg, forclient=None):
		for c in self.clients:
			if (forclient != None):
				c.sendMessage(msg)
			elif (c.http_request_uri == forclient):
				c.sendMessage(msg)                
		for b in self.picframeclients:
				b.sendMessage(msg)
				
			# print("message sent to {}".format(c.peer))
	def sendNewConfig(self,client,all=False):
		if not all:
			client.sendMessage(json.dumps({"config":json.loads(self.frameconfig.getConfigJSON())}),isBinary=False)
		else:
			for c in self.picframesclients:
				c.sendMessage(json.dumps({"config":json.loads(self.frameconfig.getConfigJSON())}),isBinary=False)
		

if __name__ == '__main__':
    walktree(startdir, addtolist)
    if len(sys.argv) > 1 and sys.argv[1] == 'debug':
        log.startLogging(sys.stdout)
        debug = True
    else:
        debug = False
    debug = True
    ServerFactory = BroadcastServerFactory
    # ServerFactory = BroadcastPreparedServerFactory
	
    factory = ServerFactory("ws://localhost:9000",
                            debug=debug,
                            debugCodePaths=debug)
    print "starting"
    factory.protocol = BroadcastServerProtocol
    factory.setProtocolOptions(allowHixie76=True)
	
    listenWS(factory)
    webdir = File("/home/pi/piframe/www/")
    web = Site(webdir)
    reactor.listenTCP(80, web)
    print "running.."
    reactor.run()
    ServerFactory.tempProbe.setEnabled(False)
