import socket
import json
from src.roboclaw_3 import Roboclaw
from pyfirmata import Arduino, util




def readLine(soc):
    inc = b''
    message = b''
    while inc is not b'\n':
        inc = soc.recv(1)
        message += inc
    return message


def control_speed(rc, adr, speedM1, speedM2):
    # speedM1 = leftMotorSpeed, speedM2 = rightMotorSpeed
    if speedM1 > 0:
        rc.ForwardM1(adr, speedM1)
    elif speedM1 < 0:
        speedM1 = speedM1 * (-1)
        rc.BackwardM1(adr, speedM1)
    else:
        rc.ForwardM1(adr, 0)

    if speedM2 > 0:
        rc.ForwardM2(adr, speedM2)
    elif speedM2 < 0:
        speedM2 = speedM2 * (-1)
        rc.BackwardM2(adr, speedM2)
    else:
        rc.ForwardM2(adr, 0)


def control_gripper(command,gripperLeft,gripperRight):
    if command is True:
        print('Command is true')
        gripperLeft.write(0)
        gripperRight.write(160)
    else:
        print('Command is false')
        gripperLeft.write(160)
        gripperRight.write(0)


# Setup the Roboclaw
rc = Roboclaw("/dev/ttyACM1", 115200)  # Linux comport name
address = 0x80
rc.Open()
print('Details about the Robobclaw: ')
version = rc.ReadVersion(address)
if not version[0]:
    print("GETVERSION Failed")
    exit()
else:
    print(repr(version[1]))
    print("Car main battery voltage at start of script: ", rc.ReadMainBatteryVoltage(address))


# Setup the Arduino and define pins used
board = Arduino('/dev/ttyACM0')
print('Print details about arduino connected: ')
print(board)
gripperRight = board.get_pin('d:11:s')
gripperLeft = board.get_pin('d:10:s')

# Setup the tcp com to the server.
TCP_IP = '192.168.0.50'
TCP_PORT = 9876
BUFFER_SIZE = 1024
subStringREG = 'SUB::REG_OUTPUT\n'
subStringGripper = 'SUB::GRIPPER_COMMANDS\n'


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as soc:
    soc.connect((TCP_IP, TCP_PORT))
    soc.settimeout(None)
    soc.sendall(subStringREG.encode('utf-8'))
    soc.sendall(subStringGripper.encode('utf-8'))

    loop = True  # exit condition
    while loop:

        message = soc.recv(BUFFER_SIZE)
        if message is b'':
            loop = False
            print('Received: b'' and stopped the loop')
            break

        try:
            msg = json.loads(message)
            topic = msg['topic']
            if str(topic).__eq__('GRIPPER_COMMANDS'):
                data = msg['data']
                gripper = data['command']
                control_gripper(gripper,gripperLeft,gripperRight)
            if str(topic).__eq__('REG_OUTPUT'):
                data = msg['data']
                rightMotorSpeed = data['rightMotor']
                leftMotorSpeed = data['leftMotor']
                control_speed(rc, address, leftMotorSpeed, rightMotorSpeed)
        except json.decoder.JSONDecodeError:
            print("json.decoder.JSONDecodeError")
            pass


rc.ForwardM1(address, 0)
rc.ForwardM2(address, 0)
soc.close()
