# importing libraries
import cv2
import time
import os
import serial
import PySimpleGUI as sg
from tkinter import *
import xlsxwriter


# (1) create layout for the GUI window and reading GPS and webcams settings
sg.ChangeLookAndFeel('SystemDefault')
form = sg.FlexForm('', default_element_size=(20, 1))
layout = [
    [sg.Text('Loop Delay(ms)', size=(15, 1)), sg.InputText('500')],
    [sg.Text('GPS Baud Rate', size=(15, 1)), sg.InputText('38400')],
    [sg.Text('Webcam 1 Directory', size=(15, 1)), sg.InputText('New Folder 1')],
    [sg.Text('Webcam 2 Directory', size=(15, 1)), sg.InputText('New Folder 2')],
    [sg.Text('Image Format', size=(15, 1)), sg.Spin(values=('.png', '.jpg'), initial_value='.png')],
    [sg.Text('Image Resolution', size=(15, 1)),
     sg.Spin(values=('640*480', '1280*720', '1080*1920'), initial_value='640*480')],
    [sg.Text('COM Port', size=(15, 1)),
     sg.Spin(values=('COM1', 'COM2', 'COM3', 'COM4', 'COM5'), initial_value='COM3')],
    [sg.Submit()]
]

window = sg.Window('Data entry form', layout)
event, values = window.read()
ValueX = values[5]
br = values[1]
DelayValue = str(values[0])
DelayValue2 = float(DelayValue)
DelayValue2 = float(DelayValue2 / 1000)
loop_delay = DelayValue2
port = values[6]
ext = values[4]

# (2) creating a directory to save the images
path = str(values[2])
path2 = str(values[3])
try:
    os.mkdir(path)
    os.mkdir(path2)
except OSError:
    print("The directories already exist")
else:
    print("Successfully created the directories")

# (3) create camera objects and Defining functions for webcam resolution

webcam_L = cv2.VideoCapture(2)
webcam_R = cv2.VideoCapture(1)


def make_1080p():
    webcam_R.set(3, 1920)
    webcam_R.set(4, 1080)
    webcam_L.set(3, 1920)
    webcam_L.set(4, 1080)


def make_720p():
    webcam_R.set(3, 1280)
    webcam_R.set(4, 720)
    webcam_L.set(3, 1280)
    webcam_L.set(4, 720)


def make_480p():
    webcam_R.set(3, 640)
    webcam_R.set(4, 480)
    webcam_L.set(3, 640)
    webcam_L.set(4, 480)


if int(ValueX[1]) == 4:
    make_480p()
    if int(ValueX[1]) == 2:
        make_720p()
else:
    make_1080p()

# (4) Create serial port object and read GPS data at a specific baud rate (38400), setting port number and byte size
ser = serial.Serial(
    port=str(port),
    baudrate=br,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    xonxoff=False
)
ser.write(str.encode('A'))
line = ser.readline()


# defining Start, Stop and pause buttons using Tkinter library


def start():
    global running
    running = 1


def stop():
    global running
    running = 2


def pause():
    global running
    running = 3


root = Tk()
root.title("Camera")
root.geometry("250x100")

app = Frame(root)
app.grid()

start = Button(app, text="                  START DATA ACQUISITION               ", command=start)
pause = Button(app, text="  PAUSE / DISPLAY WEBCAMS VIDEO STREAM  ", command=pause)
stop = Button(app, text="                            STOP / EXIT                              ", command=stop)


start.grid()
stop.grid()
pause.grid()

GPS_DATA = xlsxwriter.Workbook('GPS.xlsx')
sheet = GPS_DATA.add_worksheet()

i = 1
running = 0
delay = 0
# (5) send command to cameras to continuously capture images and display it
while webcam_L.isOpened() & webcam_R.isOpened():
    # with every loop, a single frame of each webcam stream is saved to
    # variables "frameL" and "frameR"
    retL, frameL = webcam_L.read()
    retR, frameR = webcam_R.read()

    # single frames of left and right webcams are displayed
    cv2.imshow('Left Webcam', frameL)
    cv2.imshow('Right Webcam', frameR)
    # (6) check what button was pressed
    if running == 1:

        while True:
            t1 = time.time()
            # (6) check what button was pressed
            if running == 2:
                webcam_L.release()
                webcam_R.release()
                cv2.destroyAllWindows()
                break

            if running == 3:
                break

            # (7) Reading the computer time
            t = time.localtime()

            # (8) Parse gps data
            ser.write(str.encode('A'))


            # (9)left and right captured frames are saved in variables frameL and
            # frameR
            retR, frameR = webcam_R.read()
            retL, frameL = webcam_L.read()

            # the gps data is changed into a string so we can extract the latitudes
            # and longitudes and angle information from the data.
            # (the delay is needed for the GPS device to answer)

            line = ser.readline()
            line = str(line)
            lat = str(line[18:24])
            lo = str(line[27:34])
            ang = str(line[44:49])

            #  extracting computer time information
            hr = str(time.asctime(t)[11:13])
            m = str(time.asctime(t)[14:16])
            s = str(time.asctime(t)[17:19])

            # (10)each image is saved in the desired folder and tagged with gps string

            cv2.imwrite(os.path.join(path, hr + '.' + m + '.' + s + ' GPS_' + lat + ',' + lo + ',' + ang +
                                     str(ext)), frameL)

            cv2.imwrite(os.path.join(path2, hr + '.' + m + '.' + s + ' GPS_' + lat + ',' + lo + ',' + ang +
                                     str(ext)), frameR)

            sheet.write(i-1, 0, line)


            # (11)the captured frames of each webcam stream is showed in every loop
            cv2.imshow("Left Webcam", frameL)
            cv2.imshow("Right Webcam", frameR)

            # (6) check the buttons
            root.update()
            # delay in this loop
            time.sleep(loop_delay + delay)
            i += 1

            # (12) Check that each loop will execute as specified by user
            t2 = time.time()
            tt = float(t2-t1)
            print(tt)
            # (13) compare the delay value specified by user and the loop execution time
            if tt < (loop_delay - 0.02):
                delay = delay + 0.01
            if tt > (loop_delay + 0.02):
                delay = delay - 0.01

    if running == 2:
        webcam_L.release()
        webcam_R.release()
        cv2.destroyAllWindows()
        break

    root.update()

GPS_DATA.close()

print(str(i*2 - 2)+' images have been saved.')
