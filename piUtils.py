import os
import threading,json
from time import sleep

class TempProbe(threading.Thread):
    """
     A class for getting the current temp of a DS18B20
    """

    def __init__(self, msgCallback):
        threading.Thread.__init__(self)
        self.tempDir = '/sys/bus/w1/devices/'
        list = os.listdir(self.tempDir)
        self.fileName=''
	print list
	for file in list:
	  print file,file[:2]
	  if(file[:2]=="28"):
           self.fileName=file
	#print 
        #self.fileName = fileName
        self.currentTemp = -999
        self.correctionFactor = 1
        self.enabled = True
	self.change=msgCallback
	
    def run(self):
        oldtemp=0.0
        while self.isEnabled():
                try:
                    f = open(self.tempDir + self.fileName + "/w1_slave", 'r')
                except IOError as e:
                    print "Error: File " + self.tempDir + self.fileName + "/w1_slave" + " does not exist"
                    return;

                lines=f.readlines()
                crcLine=lines[0]
                tempLine=lines[1]
                result_list = tempLine.split("=")
                temp = float(result_list[-1])/1000 # temp in Celcius
                temp = temp + self.correctionFactor # correction factor
                #if you want to convert to Celcius, comment this line
                temp = (9.0/5.0)*temp + 32
                if crcLine.find("NO") > -1:
                    temp = -999
                self.currentTemp = round(temp*100)/100
		if(self.currentTemp!=oldtemp):
			oldtemp=self.currentTemp
			self.change(json.dumps({'temperature':self.currentTemp}))
		        #print "Current: " + str(self.currentTemp) + " " + str(self.fileName)
		sleep(1)
    #returns the current temp for the probe
    def getCurrentTemp(self):
        return self.currentTemp

    #setter to enable this probe
    def setEnabled(self, enabled):
        self.enabled = enabled
    #getter
    def isEnabled(self):
        return self.enabled
