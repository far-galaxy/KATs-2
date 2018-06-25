import interfaces
import time

#---------MS5611--------
ms5611 = interfaces.I2Cobj(0x77)
ms5611.write_byte(0x1E)
time.sleep(0.5)
data = ms5611.read_data(0xA2, 2)
ms5611.C1 = data[0] * 256 + data[1]
data = ms5611.read_data(0xA4, 2)
ms5611.C2 = data[0] * 256 + data[1]
data = ms5611.read_data(0xA6, 2)
ms5611.C3 = data[0] * 256 + data[1]
data = ms5611.read_data(0xA8, 2)
ms5611.C4 = data[0] * 256 + data[1]
data = ms5611.read_data(0xAA, 2)
ms5611.C5 = data[0] * 256 + data[1]
data = ms5611.read_data(0xAC, 2)
ms5611.C6 = data[0] * 256 + data[1]
time.sleep(0.5)
#---------MS5611 end--------

sht21 = interfaces.I2Cobj(0x40)

pcf8583 = interfaces.I2Cobj(0x50)

laser = interfaces.I2Cobj(0x29)

def getP_Tv():
    ms5611.write_byte(0x40)
    time.sleep(0.05)
    value = ms5611.read_data(0x00, 3)
    D1 = value[0] * 65536 + value[1] * 256 + value[2]
    ms5611.write_byte(0x50)
    time.sleep(0.05)
    value = ms5611.read_data(0x00, 3)
    D2 = value[0] * 65536 + value[1] * 256 + value[2]
    dT = D2 - ms5611.C5 * 256
    TEMP = 2000 + dT * ms5611.C6 / 8388608
    OFF = ms5611.C2 * 65536 + (ms5611.C4 * dT) / 128
    SENS = ms5611.C1 * 32778 + (ms5611.C3 * dT ) / 256
    T2 = 0
    OFF2 = 0
    SENS2 = 0

    if TEMP >= 2000 :
        T2 = 0
        OFF2 = 0
        SENS2 = 0
    elif TEMP < 2000 :
        T2 = (dT * dT) / 2147483648
        OFF2 = 5 * ((TEMP - 2000) * (TEMP - 2000)) / 2
        SENS2 = 5 * ((TEMP - 2000) * (TEMP - 2000)) / 4
        if TEMP < -1500 :
            OFF2 = OFF2 + 7 * ((TEMP + 1500) * (TEMP + 1500))
            SENS2 = SENS2 + 11 * ((TEMP + 1500) * (TEMP + 1500)) / 2

    TEMP = TEMP - T2
    OFF = OFF - OFF2
    SENS = SENS - SENS2
    pressure = ((((D1 * SENS) / 2097152) - OFF) / 32778.0) // 100.0
    cTemp = TEMP / 100.0

    return pressure//256,pressure%256, cTemp

def getH():
    sht21.write_byte(0xF5)
    time.sleep(0.250)
    raw=[0,0]
    raw[0] = sht21.read_byte()
    raw[1]= sht21.read_byte()
    hum = (raw[0] << 8) + raw[1]
    hum *= 125
    hum /= 1 << 16
    hum -= 6
    return hum

def getTn():
    sht21.write_byte(0xF3)
    time.sleep(0.250)
    raw=[0,0]
    raw[0] = sht21.read_byte()
    raw[1]= sht21.read_byte()
    temp = (raw[0] << 8) + raw[1]
    temp *= 175.72
    temp /= 1 << 16 
    temp -= 46.85
    return temp

def getDate():
    
    sec=format(pcf8583.read_data(0x02)[0],'08b')
    sec=format(int(sec[:4],2)*10+int(sec[4:],2),'02')

    mns=format(pcf8583.read_data(0x03)[0],'08b')
    mns=format(int(mns[:4],2)*10+int(mns[4:],2),'02')

    hour=format(pcf8583.read_data(0x04)[0],'08b')
    hour=format(int(hour[2:4],2)*10+int(hour[4:],2),'02')

    yeardate=format(pcf8583.read_data(0x05)[0],'08b')
    day=format(int(yeardate[2:4],2)*10+int(yeardate[4:],2),'02')

    time=[day, hour, mns, sec]
    return time
	
def getSec():
    sec=format(pcf8583.read_data(0x02)[0],'08b')
    sec=format(int(sec[:4],2)*10+int(sec[4:],2),'02')
    return sec
	
def getDist():
    laser.write_data(0x00, 0x01)
    data = laser.read_data(0x14, 12)
    return ((data[10] & 0xFF) << 8)  | (data[11] & 0xFF)

class Ardupter():
    def __init__(self,port):
        self.ardupter = interfaces.SPIobj(port)
    def get_accel(self):
        data = self.ardupter.get_data()
        x = data[5]*256 + data[4]
        y = data[7]*256 + data[6]
        z = data[9]*256 + data[8]
        return [x,y,z]
    def get_raw_accel(self):
        data = self.ardupter.get_data()
        x = data[5] + data[4]
        y = data[7]+ data[6]
        z = data[9]+ data[8]
        return [x,y,z]

class SIM808():
    def __init__(self):
        self.asw="OK"
        self.at="AT"+0x0d+0x0a
        self.gpspwr="AT+CGPSRST=0"0x0d+0x0a
        self.gps="AT+CGPSINF=0"0x0d+0x0a
        self.typeSMS="AT+CMGF=1"0x0d+0x0a
        self.send='AT+CMGS='
		
        self.gps = interfaces.UART()
        print(self.gps.getAT(self.at,self.asw))
        sleep(1)
        print(self.gps.getAT(self.gpspwr,self.asw))
        sleep(1)
        print(self.gps.getAT(self.typeSMS,self.asw))
        sleep(1)
    def get_position(self):
        coord = self.gps.waitAT(self.gps,1).split(",")
        long = coord[1]*(10**6)
        long = [long >> 24,long >> 16, long >> 8, long+0xFFFF]
        lat = coord[2]*(10**6)
        lat = [lat >> 24,lat >> 16, lat >> 8, lat+0xFFFF]
        return long+lat
	
    def send_sms(self, phonenumber, text):
        self.gps.getAT(self.send+phonenumber+0x0d+0x0a,">")
        self.gps.waitAT(text+0x1a,1)
        print("SMS")
