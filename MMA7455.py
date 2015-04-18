# I2C writes =D0=0
# MMA7455 I2C address 1D (3A ,3B) write , read
# AN3745 app note for calibration
# byte read , write 1D , write address, read 1D ,DATA
# Byte write, write 1D , write address, write data.
# addresses,
# 06 XOUT8
# 07 YOUT8
# 08 ZOUT8
# 09 STATUS  D0 1=data ready
# 0A detection source
# 0F who am i
# 16 Mode Control  x1000101 measure 2gmode
# 18 Control1  D7 filter 0=62Hz,1=125Hz other 0
# 19 Control2  default 0

#!/usr/bin/python
import smbus
import time
import threading
import RPi.GPIO as GPIO

# TiltSensor
 
class TiltSensor(threading.Thread):
	def __init__(self,onChangeCallback=None):
		threading.Thread.__init__(self)
		myBus=""
		if GPIO.RPI_REVISION == 1:
			myBus=0
		elif GPIO.RPI_REVISION == 2:
			myBus=1
		elif GPIO.RPI_REVISION == 3:
			myBus=1
		self.b = smbus.SMBus(myBus)
		self.callback=onChangeCallback
		self.Enabled=True
		self.setUp()
	def run(self):
		oldvalue=0
		newvalue=0
		while self.Enabled:
			v = self.getValueX()
			if(v > 180 and v < 210):
				newvalue=1
			else:
				newvalue=0
			if(oldvalue!=newvalue):
				oldvalue=newvalue
				if(self.callback!=None):
					self.callback(newvalue)
				else:
					print newvalue
			time.sleep(.5)
	# Setup and Calibrate
	def setUp(self):
		self.b.write_byte_data(0x1D,0x16,0x55) # Setup the Mode
		self.b.write_byte_data(0x1D,0x10,0) # Calibrate
		self.b.write_byte_data(0x1D,0x11,0) # Calibrate
		self.b.write_byte_data(0x1D,0x12,0) # Calibrate
		self.b.write_byte_data(0x1D,0x13,0) # Calibrate
		self.b.write_byte_data(0x1D,0x14,0) # Calibrate
		self.b.write_byte_data(0x1D,0x15,0) # Calibrate
	def getValueX(self):
		return self.b.read_byte_data(0x1D,0x06)
	def getValueY(self):
		return self.b.read_byte_data(0x1D,0x07)
	def getValueZ(self):
		return self.b.read_byte_data(0x1D,0x08)
	def getXYZ(self):
		return [self.getValueX(),self.getValueY(),self.getValueZ()]
if __name__ == "__main__":
	tilt=TiltSensor()
	tilt.start()
	for a in range(1,100):
		time.sleep(1)
	tilt.Enabled=False
		
	