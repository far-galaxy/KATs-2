print('Hello, world!')

import interfaces
import sensors
from multiprocessing import Process
import math
 

tmfile = open('telemetry.csv','w')

vysotomer = interfaces.Pin(30,False)
ardupter = sensors.Ardupter(1)
offswicth = interfaces.Pin(5,False)
parashute = interfaces.Pin(10,True)
parashute.set_pin(False)

sim808 = sensors.SIM808()
phone = "+78005553535"
nrf0 = interfaces.NRF24L01(0)



distlas = sensors.getDist()
undock_dist = 1000
is300m = vysotomer.readpin()
x,y,z = ardupter.get_accel()
vector = (x**2+y**2+z**2)**0.5

picam = interfaces.PiCam((800,600))
usbcam = interfaces.USBcam()


num_p = 0
temp = sensors.getP_Tv()
p0 = temp[0]*256+temp[1]
time_ff = 0

def Read_TM():
    date = sensors.getDate()
    p1,p2,Tv = sensors.getP_Tv()
    Tn = sensors.getTn()
    H = sensors.getH()
    accel = ardupter.get_raw_accel()
	if num_p%20==0:
		coord = sim808.get_position()
		sim808.send_sms(phone,coord)
		return [date,p,Tv,Tn,H,accel,coord]
    return date+[p1,p2,Tv,Tn,H]+accel+[0,0,0,0,0,0,0,0]

def Send_TM():
    TM1 = Read_TM()
    TM2 = [0]*16
    TM = [128, num_p]+TM1+TM2 #checksum: 128 - first part, 255 - second, 1 - photo
	tmfile.write(' '.join(TM))
    print(TM, nrf0.send(TM))
    #print(TM)
    return TM

def Check_SD():
    if offswitch.readpin():
        picam.stop_record()
        tmfile.close()
        call('sudo','shutdown')
		
def Time_of_FF(height):
    v = 0.0
    a = g = 9.8
    t = 0
    while height>250:
        Fx = (1.23*(v**2))/2*0.005541
        v += a
        a = g-Fx/1.1
        height -= v+(a/2)
        t += 1
    return t
	    

print("I'm ready!")    
#--------------------MAIN PROGRAM-------------------------------

		
# checking status (0 - waiting start, 1 - flight, 2 - undocking, 3 - decrease, 4 - landing)
if distlas < undock_dist :
    status = 0
elif distlas > undock_dist and is300m:
    status = 3
elif distlas > undock_dist and is300m == False:
    status = 2
 

if status == 0:
    text = "Status: waiting to the start"
    print(text)
	tmfile.write(text)
    cam = Process(target=picam.start_record, args=('/home/pi/Dektop/1'))
    cam.start()
    while vector < 2000:
        Send_TM()
        x,y,z = ardupter.get_accel()
        vector = (x**2+y**2+z**2)**0.5
        num_p+=1
		Check_SD()
    picam.start_record('/home/pi/Desktop/video')
    status=1

if status == 1:
    text = "Status: flight"
    print(text)
	tmfile.write(text)
    while distlas < undock_dist:
        Send_TM()
        distlas = sensors.getDist()
        num_p+=1
        Check_SD()
    status = 2

if status == 2:
    text = "Status: undocking"
    print (text)
	tmfile.write(text)
    num_photo = 0
	
	temp = sensors.getP_Tv()
    p = temp[0]*256+temp[1]
	h = 18400*(1.0733)*(log10(p0/p))
	
	time_ff = Time_of_FF(h)
	text = "Apogee: " + h + " m. The maximum estimated time of free fall: " + time_ff + " seconds. "
	print (text)
	tmfile.write(text)
    while is300m==False:
	    photo = Process(target=usbcam.make_photo, args=(num_photo,))
	    photo.start()
	    Send_TM()
	    num_p+=1
	    is300m = vysotomer.readpin()
        photo.join()
	
    status = 3
	
if status == 3
picam.stop_record()
