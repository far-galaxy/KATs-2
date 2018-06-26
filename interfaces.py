import smbus
import spidev
import nrf24
import serial
import RPi.GPIO as GPIO
from multiprocessing import Process
from subprocess import call
import picamera
import serial
from time import time as timestart
import time

bus=smbus.SMBus(1)
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.cleanup()

class I2Cobj():
    def __init__(self,adress):
        self.bus=bus
        self.adress=adress
        try: #checking device
            self.bus.read_byte(adress)
        except IOError:
            print ("Error: could not find device "+hex(adress))
            
    def write_byte(self,byte):
        self.bus.write_byte(self.adress, byte)

    def write_data(self,num,byte):
        return self.bus.write_byte_data(self.adress, num, byte)

    def read_byte(self):
        return self.bus.read_byte(self.adress)

    def read_data(self,num,count=1):
        return self.bus.read_i2c_block_data(self.adress, num, count)


class SPIobj():
    def __init__(self, port):
        self.spi01 = spidev.SpiDev()
        self.spi01.open(0,port)
        self.spi01.max_speed_hz = 50000
		
    def get_data(self):
        spi01_req = [0]*14
        spi01_req[0] = 1
        spi01_data = self.spi01.xfer(spi01_req)
        return spi01_data[1:]

class UART():
    def __init__(self):
        self.call = call
        self.call (["sudo","systemctl","stop","serial-getty@ttyAMA0.service"])
        self.call (["sudo","systemctl","stop","serial-getty@ttyS0.service"])
        self.port = serial.Serial("/dev/ttyAMA0", baudrate=115200, timeout=None)
    def getAT(self,ask,ans):
        self.port.write(ask.encode())
        rcv=''
        tp=timestart()
        while True:
            if rcv.find(ans)==-1 and timestart()<=tp+2:
                if self.port.inWaiting()!=0:
                    rcv += str(self.port.read())
            else:
                return rcv
                break

    def waitAT(self,ask,tme):
        self.port.write(ask.encode())
        rcv=''
        tp=timestart()
        while timestart()<=tp+tme:
            if self.port.inWaiting()!=0:
                rcv += str(self.port.read())

        return rcv

class Pin():
        def __init__(self,num,out):
            self.GPIO = GPIO 
            self.GPIO.setup(num, GPIO.OUT) if out else self.GPIO.setup(num, GPIO.OUT)
            self.out=out
            self.num=num
		
        def setpin(self, pin):
            if self.out:
                self.GPIO.output(self.num, pin) 

        def readpin(self):
            return False if self.out else  self.GPIO.input(self.num)


class NRF24L01():
    def __init__(self, CSN):
        #NRF24L01_CSN = 8
        NRF24L01_CE = 24
        NRF24L01_IRQ = 21

        pipes = [[0x90, 0x78, 0x56, 0x34, 0x12], [0x90, 0x78, 0x56, 0x34, 0x12]]

        self.radio = nrf24.NRF24()

        time.sleep(0.1)
        self.radio.begin(0, 0, NRF24L01_CE, NRF24L01_IRQ)
        time.sleep(0.1)
        self.radio.setChannel(7)
        time.sleep(0.1)
        self.radio.setDataRate(nrf24.NRF24.BR_1MBPS)
        time.sleep(0.1)
        self.radio.setPALevel(nrf24.NRF24.PA_HIGH)
        time.sleep(0.1)
        self.radio.opnWritingPipe(pipes[0])
        time.sleep(0.1)
        self.radio.setAutoAck(False)
        time.sleep(0.1)
        self.radio.disableCRC()
        time.sleep(0.5)

        self.radio.setRetries(15, 1)
        
    def send(self,data):
        self.radio.clear_irq_flags()
        self.radio.write(data)
        return self.radio.last_error

class PiCam():
    def __init__(self,resolution):
        try:
            self.camera = picamera.PiCamera()
            self.camera.resolution = resolution
            self.camera.framerate = 30
        except:
            pass
    def start_record(self,filename):
        try:
            self.camera.start_recording(filename+'.h264')
        except:
            pass
    def stop_record(self):
        try:
            self.camera.stop_recording()
        except:
            pass

class USBcam():
    def make_photo(self, filename, resolution):
        try:
            self.call("fswebcam", "-r", resolution, "--no-banner", filename+".jpg")
        except:
            pass
