import imutils
from skimage.filters import threshold_local
import cv2
import base64
import os
import argparse
import numpy as np
import random as rng
from stackchain.widgets import rect2Box, shoWait, validDateString
import pytesseract
from skimage import measure
import re
import datetime
import json
import sys

# constants
W = 800 
fontFace = cv2.FONT_HERSHEY_PLAIN # debug text on image
cleanText = r"[^A-Z0-9.,\-\s\/]" # clean data text 

# cmd parser
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=True, help="Path to the image")
args = vars(ap.parse_args())

# load image
image = cv2.imread(args["image"])

# resize 2 and keep one for debuging
resize_proc = imutils.resize(image, width=W)
resize_orig = imutils.resize(image, width=W)

# perform a image cleaning to enhance constrast and borders
def cleanImage(image, stage = 0):
  V = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
  kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
  # applying topHat/blackHat operations
  topHat = cv2.morphologyEx(V, cv2.MORPH_TOPHAT, kernel)
  blackHat = cv2.morphologyEx(V, cv2.MORPH_BLACKHAT, kernel)
  # add and subtract between morphological operations
  add = cv2.add(V, topHat)
  subtract = cv2.subtract(add, blackHat)
  if (stage == 1):
    return subtract
  T = threshold_local(subtract, 29, offset=35, method="gaussian", mode="mirror")
  thresh = (subtract > T).astype("uint8") * 255
  if (stage == 2):
    return thresh
  # invert image 
  thresh = cv2.bitwise_not(thresh)
  return thresh

# select the areas that are possible data
def extractROIs(image, origin, minArea = 1800, minHeight = 25, minWidth = 22):
  # find contours
  cnts = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
  cnts = imutils.grab_contours(cnts)
  roisAsRects = []
  # loop trhough 
  for c in cnts:
    rect = cv2.minAreaRect(c)
    (_, _),(rh, rw),_ = rect
    if (rh > 0):
      ratio = float(rw)/rh
      area = rw*rh
      if (area > minArea and rh > minHeight and rw > minWidth and (ratio > 1 or ratio < 0.5)):
        # add to the rois list
        roisAsRects.append(rect)
  return roisAsRects

# adjust and refine the rois (rotation, dumps)
def cropRois(image, rects, multHeight = 0.73, multWidth = 0.97, topHeightCrop = 30):
  crops = []
  data = {}
  # TODO cut off angle outliers here too
  angles = []

  for r in rects:
    box = rect2Box(r)
    W = r[1][0]
    H = r[1][1]

    Xs = [i[0] for i in box]
    Ys = [i[1] for i in box]
    x1 = min(Xs)
    x2 = max(Xs)
    y1 = min(Ys)
    y2 = max(Ys)

    rotated = False
    angle = r[2]

    if angle < -45:
        angle += 90
        rotated = True

    # calc the centroid
    center = (int((x1 + x2) / 2), int((y1 + y2) / 2))
    size = (int((x2-x1)), int((y2 - y1)))
    #cv2.circle(image, center, 2, 255, -1)

    M = cv2.getRotationMatrix2D((size[0] / 2, size[1] / 2), angle, 1.0)

    # prepare the crop
    cropped = cv2.getRectSubPix(image, size, center)
    cropped = cv2.warpAffine(cropped, M, size)
    croppedW = W if not rotated else H 
    croppedH = H if not rotated else W

    ratio = float(croppedW) / (croppedH)
    area = float(croppedW) * croppedH

    # if in the ratio
    if (ratio > 2 and ratio < 16):
      #text = "{0:.2f}-{1:.2f} ".format(ratio, area)
      #cv2.putText(image, text, center, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
      croppedRotated = cv2.getRectSubPix(cropped, (int(croppedW * multWidth), int(croppedH * multHeight if croppedH < topHeightCrop else croppedH * 0.9)), (size[0] / 2, size[1] / 2))
      # save the angles to calc the avg/std
      angles.append(angle)
      # save the crops
      crops.append(croppedRotated)
      # will process from top to bottom, so save it to sort later
      data[y1] = [croppedRotated, area, ratio, angle]
  
  return data, np.mean(np.array(angles)), np.std(np.array(angles))

# fast way to place every string in its place by ratio/aerea/previous detection
# TODO train an AI to do it, (perhaps a decision tree will work for most cases)
def textClassifier(data, text, ratio):
  words = len(re.findall(r"\w+", text))
  textSize = len(text.strip())

  # blank text 
  if textSize == 0: return

  # expect father and mother 
  # TODO use the height for these features
  if (2.5 <= ratio <= 3.2):
    separator = text.find("\n\n")
    if (data["mae"] is None and separator and len(text) > 12 and data['nome'] is not None):
      data["mae"] = text[separator:].replace("\n", " ").strip()
      data["pai"] = text[:separator].replace("\n", " ").strip()
  # expect dates and social number (cpf)
  if (3.3 <= ratio <= 5 and data["nome"] is not None):
    if (textSize > 12 and text.find("-") and text.find(".")):
      if (data["cpf"] is None):
        data["cpf"] = text.replace(",", ".")
    if (textSize == 10 and text.find("/")):
      dateObj = validDateString(text.strip())
      if (isinstance(dateObj, datetime.datetime)):
        now = datetime.datetime.now()
        legalAge = datetime.datetime.now() - datetime.timedelta(days=365*18)
        if (data["dt_nasc"] is None and dateObj < legalAge):
          data["dt_nasc"] = text
        if (data["validade"] is None and dateObj > now):
          data["validade"] = text
        if (data["emissao"] is None and dateObj > legalAge and dateObj < now):
          data["emissao"] = text
  # expect cnh number
  if (5.1 <= ratio <= 7.1 and data['numero'] is None):
    numbers = re.findall(r"(\d{11})", text)
    for i in numbers:
      if (len(i) == 11):
        data['numero'] = i
  # expect rg
  if (7.2 <= ratio <= 10):
    if (data["rg"] is None):
      # cleaning and checking
      if (words >= 1):
        rgData = re.split(r"([\w\/]+)", text)
        for d in rgData:
          size = len(d)
          if (size == 2):
            data["rg_uf"] = d
          elif (2 <= size <= 6):
            data["rg_emissor"] = d
          elif (size > 6):
            data["rg"] = d

  # if (10.1 <= ratio <= 12.4):
  #   if (data["cidade"] is None):
  #     print('RUF', text)

  if (12.5 <= ratio <= 17):
    # ratio of name and no name
    if (data["nome"] is None):
      # cleaning and checking
      if (words < 7 and words > 1):
        data["nome"] = text
    # elif (data["cidade"] is None):
    #   print('RUF', text)

# use tesseract to process the rois read the text 
def readRois(rois, meanAngle, stdAngle):
  data = {
    "nome": None,
    "cpf": None,
    "dt_nasc": None,
    "rg": None,
    "rg_emissor": None,
    "rg_uf": None,
    "numero": None,
    "cidade": None,
    "uf": None,
    "pai": None,
    "mae": None,
    "emissao": None,
    "validade": None,
    "avatar": None
  }
  for i in sorted (rois.keys()):
    r = rois[i][0]
    ratio = rois[i][2]
    #print(r)
    # remove some top pixels 
    (h, w,) = r.shape[:2]
    # ratio = float(w) / h
    r = r[3:h, 0:w]
    # duplicate the image to process against tesseract
    origin = r.copy()
    gray = r.copy()
    gray = cleanImage(gray, 1)
    text_origin = pytesseract.image_to_string(origin)
    text_gray = pytesseract.image_to_string(gray)
    text = text_gray if len(text_gray) > len(text_origin) else text_origin
    text = re.sub(cleanText, "", text)
    text = text.strip()
    textClassifier(data, text, ratio)
    #print("ratio, area, angle: {0:.2f}, {1:.2f}, {2:.2f}".format(ratio, area, angle), " : ", text)
  return data

# detect and return the face photo
def grabFace(image, meanAngle):
  face_cascade = cv2.CascadeClassifier("./models/haarcascade_frontalface_default.xml")
  gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
  for (x, y, w, h) in face_cascade.detectMultiScale(gray, 1.3, 5):
    area = w * h
    radius = int(h * 0.75)
    cx = (x+h/2)
    cy = (y+w/2)
    # TODO: magic numbers everywhere, so sad
    if (area > 5000 and area < 20000):
      #cv2.circle(gray, center, radius, (255, 0, 255))
      crop = image[cy-radius:(cy-radius+2*radius), cx-radius:(cx-radius+2*radius)]
      return crop

# stage 1 clean image
thresh = cleanImage(resize_proc)

# stage 2 detect rois
rrects = extractROIs(thresh, resize_orig)

# stage 3 process rois 
rois, meanAngle, stdAngle = cropRois(resize_orig, rrects)

# if (face is not None):
#   shoWait(face)

# stage 4 read the rois
data = readRois(rois, meanAngle, stdAngle)

# stage 5 detect face
face = grabFace(resize_orig, meanAngle)
if (face is not None):
  retval, imgBuffer = cv2.imencode(".jpg", imutils.resize(face, 60))
  data["avatar"] = base64.b64encode(imgBuffer)

# stage 6 return the json
print(json.dumps(data))
sys.stdout.flush()