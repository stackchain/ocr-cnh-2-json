import cv2
import numpy as np
import datetime


def rect2Box(rect):
  box = cv2.boxPoints(rect)
  box = np.int0(box)
  return box

def shoWait(image, title = "Image"):
  cv2.imshow(title, image)
  cv2.waitKey(0)

def validDateString(dateText):
  try:
    return datetime.datetime.strptime(dateText, '%d/%m/%Y')
  except ValueError:
    print("Unable to parse this string to date: ", dateText)