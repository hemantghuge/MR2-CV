import numpy as np
import cv2 as cv
import RPi.GPIO as gpio
import time

import signal
import sys
import threading

width = 320
height = 240
fps = 30

video_capture = cv.VideoCapture(-1)
video_capture.set(3,width)
video_capture.set(4,height)
video_capture.set(5,fps)

lower_white = np.array([100, 0, 200]) # 150 or 200
upper_white = np.array([118, 100, 255]) # S = white and blue V = white and yellow
shape_white = (10,10)
    
lower_blue = np.array([100, 150, 50])
upper_blue = np.array([118, 255, 255])
shape_blue = (3,3)

area_white_threshold = 1200
area_blue_threshold = 2200

ctrl = 0
flag = 0

a=22 # colour line (red and blue)
b=19 
c=21
d=23

turn_90=24 # 90 degree turn

# led
green_led=11
blue_led=13
red_led=15

gpio.setwarnings(False)
gpio.setmode(gpio.BOARD)

gpio.setup(a,gpio.OUT)
gpio.setup(b,gpio.OUT)
gpio.setup(c,gpio.OUT)
gpio.setup(d,gpio.OUT)

gpio.setup(turn_90,gpio.OUT)

gpio.setup(green_led, gpio.OUT)
gpio.setup(blue_led, gpio.OUT)
gpio.setup(red_led, gpio.OUT)

gpio.output(a,gpio.LOW)
gpio.output(b,gpio.LOW)
gpio.output(c,gpio.LOW)
gpio.output(d,gpio.LOW)

gpio.output(turn_90,gpio.LOW)

gpio.output(green_led,gpio.HIGH)
gpio.output(blue_led,gpio.HIGH)
gpio.output(red_led,gpio.HIGH)

def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    gpio.output(green_led,gpio.HIGH)
    gpio.output(blue_led,gpio.HIGH)
    gpio.output(red_led,gpio.HIGH)
    sys.exit(0)

def line_follow(cx):
    
    if cx >= 0 and cx < 46:              
        flag = 1
        gpio.output(b,gpio.LOW)
        gpio.output(c,gpio.LOW)
        gpio.output(d,gpio.HIGH)

        ####

        gpio.output(blue_led,gpio.LOW)
        gpio.output(green_led,gpio.HIGH)
        gpio.output(red_led,gpio.HIGH)
        
    elif cx >= 46 and cx < 92:        
        flag = 2
        gpio.output(b,gpio.LOW)
        gpio.output(c,gpio.HIGH)
        gpio.output(d,gpio.LOW)

        ####

        gpio.output(blue_led,gpio.LOW)
        gpio.output(green_led,gpio.HIGH)
        gpio.output(red_led,gpio.HIGH)
            
    elif cx >= 92 and cx < 137: # forward       
        flag = 3
        gpio.output(b,gpio.LOW)
        gpio.output(c,gpio.HIGH)
        gpio.output(d,gpio.HIGH)           

        ####

        gpio.output(blue_led,gpio.LOW)
        gpio.output(green_led,gpio.LOW)
        gpio.output(red_led,gpio.HIGH)
                       
    elif cx >= 137 and cx < 183: # slight right turn        
        flag = 4
        gpio.output(b,gpio.HIGH)
        gpio.output(c,gpio.LOW)
        gpio.output(d,gpio.LOW)            

        ####

        gpio.output(blue_led,gpio.HIGH)
        gpio.output(green_led,gpio.LOW)
        gpio.output(red_led,gpio.HIGH)

    elif cx >= 183 and cx < 229:
        flag = 5
        gpio.output(b,gpio.HIGH)
        gpio.output(c,gpio.LOW)
        gpio.output(d,gpio.HIGH)

        ####

        gpio.output(blue_led,gpio.HIGH)
        gpio.output(green_led,gpio.LOW)
        gpio.output(red_led,gpio.LOW)
        
    elif cx >= 229 and cx < 274:       
        flag = 6
        gpio.output(b,gpio.HIGH)
        gpio.output(c,gpio.HIGH)
        gpio.output(d,gpio.LOW)            

        ####

        gpio.output(blue_led,gpio.HIGH)
        gpio.output(green_led,gpio.HIGH)
        gpio.output(red_led,gpio.LOW)

    elif cx >= 274 and cx < width:
        flag = 7
        gpio.output(b,gpio.HIGH)
        gpio.output(c,gpio.HIGH)
        gpio.output(d,gpio.HIGH)

        ####

        gpio.output(blue_led,gpio.HIGH)
        gpio.output(green_led,gpio.HIGH)
        gpio.output(red_led,gpio.LOW)

    return(flag)

def find_contours(lower, upper, shape):

    mask = cv.inRange(hsv, lower, upper)

    kernel = np.ones(shape, np.uint8)
    line = cv.morphologyEx(mask, cv.MORPH_OPEN, kernel)

    _, contours, _= cv.findContours(line.copy(), 1, cv.CHAIN_APPROX_NONE)
    
    return(contours)

def calculate_angle(points):
            
    blackbox = cv.minAreaRect(points)
    #print('blackbox= '+ str(blackbox))
    (x_min, y_min), (w_min, h_min), ang = blackbox

    if ang < -45 :
        ang = 90 + ang
          
    if w_min < h_min and ang > 0:    
        ang = (90-ang)*-1
                      
    if w_min > h_min and ang < 0:
        ang = 90 + ang
            
    ang = int(ang)
    print('ang = '+ str(ang))
    cv.putText(crop_img, str(ang),(50,50), cv.FONT_HERSHEY_SIMPLEX, 2, (20, 20, 250), 4)
        
    return(ang)

while(video_capture.isOpened()):

    start = time.time()        
    
    ret, frame = video_capture.read()

    crop_img = frame[0:height, 0:width]

    hsv = cv.cvtColor(crop_img, cv.COLOR_BGR2HSV)
    
    contours_white = find_contours(lower_white, upper_white, shape_white)

    contours_blue = find_contours(lower_blue, upper_blue, shape_blue)
    
    if len(contours_white) > 0:
        
        con_white = max(contours_white, key = cv.contourArea)
        area_white = cv.contourArea(con_white)
        print('area_white = ' + str(area_white))

        if (area_white > area_white_threshold):
            
            ang = calculate_angle(con_white)

            if (ang > 75 and ang < 100) or (ang < -75 and ang > -100):
                gpio.output(turn_90,gpio.HIGH)
                gpio.output(green_led,gpio.LOW)
                ctrl+=1
                print('90 turn signal angle detection')
                time.sleep(0.001)
                
            else:
                gpio.output(turn_90,gpio.LOW)
                gpio.output(green_led,gpio.HIGH)

            M_white = cv.moments(con_white)
            
            if M_white['m00'] == 0:
                M_white['m00'] == 0.0000001;

            cx_white = int(M_white['m10']/M_white['m00'])
            cy_white = int(M_white['m01']/M_white['m00'])

            cv.line(crop_img, (cx_white,0), (cx_white, height), (255,0,0),3)
            cv.line(crop_img, (0,cy_white), (width, cy_white), (255,0,0),3)

            cv.drawContours(crop_img, contours_white, -1, (0,255,0), 3)

            print ("cx_white = " +str(cx_white))
            
            flag = line_follow(cx_white)
            
        else:
            print ('area less than ' + str(area_white_threshold))
    else:
        print ('length of white contours < 0')

    if len(contours_blue) > 0:
        
        con_blue = max(contours_blue, key = cv.contourArea)
        area_blue = cv.contourArea(con_blue)
        print('area_blue = ' + str(area_blue))

        if (area_blue > area_blue_threshold):
            M_blue = cv.moments(con_blue)

            if M_blue['m00'] == 0:
                M_blue['m00'] == 0.0000001;

            cx_blue = int(M_blue['m10']/M_blue['m00'])
            cy_blue = int(M_blue['m01']/M_blue['m00'])

            cv.line(crop_img, (cx_blue,0), (cx_blue,height), (0,0,200),3)
            cv.line(crop_img, (0,cy_blue), (width,cy_blue), (0,0,200),3)

            cv.drawContours(crop_img, contours_blue, -1, (0,255,255), 3)
            
            gpio.output(a, gpio.HIGH)
            gpio.output(blue_led,gpio.LOW)
            print('blue detected area more than '  + str(area_blue_threshold))

        else:
            gpio.output(a, gpio.LOW)
            gpio.output(blue_led,gpio.HIGH)
            print('area less than (blue) ' + str(area_blue_threshold))

    else:
        gpio.output(a, gpio.LOW)
        gpio.output(blue_led,gpio.HIGH)
        print('length of blue contours < 0')


    cv.imshow('crop_img', crop_img)
    
    print('ctrl = ' + str(ctrl))
    print('flag = ' + str(flag))
    end = time.time()

    print("time execution " + str(end-start))
    
    if cv.waitKey(1) & 0x77 == ord('q'): # if quit debugging led will be off
        gpio.output(green_led,gpio.HIGH)
        gpio.output(blue_led,gpio.HIGH)
        gpio.output(red_led,gpio.HIGH)
        break
    
    signal.signal(signal.SIGINT, signal_handler) # for keyboard interrupt

