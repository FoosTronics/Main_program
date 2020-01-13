import cv2
import imutils
import usb1
from src.usb import *

driver = Driver(1)
driver.stepper_init()

print("test geslaagd!")