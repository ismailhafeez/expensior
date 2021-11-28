import string
import random
import requests
import json
from pyairtable import Table
from datetime import datetime
import os
import cv2
import pytesseract
import numpy as np
from flask import *
import cloudinary as cloud
import urllib
import sys

total = ""

cloud.config( 
  cloud_name = "cloud_name", 
  api_key = "api_key", 
  api_secret = "api_secret" 
)

table = Table("api_key", 'name', 'tablename')

app = Flask('')

@app.route('/')
def home():
	return 'Im in!'

#Just a gateway program
@app.route('/imageurl', methods = ['POST'])
def gettheurl():
  if request.method == 'POST':
    return get_image(request.data.decode('ASCII'))

#For signing in
@app.route('/signin', methods = ['POST'])
def signin():
  if request.method == 'POST':
    username, password = request.data.decode('ASCII').split(":")
    with open("credentials.txt", 'r') as file:
      creds = file.readlines()
      for i in creds:
        user, pas = i.split(":")
        try:
          pas = pas.strip("\n")
        except Exception as e:
          pass
        if user == username and password == pas:
          return "Signed In"
    return "Invalid credentials"

#For signing up
@app.route('/signup', methods = ['POST'])
def signup():
  if request.method == 'POST':
    username, password = request.data.decode('ASCII').split(":")
    with open("credentials.txt", 'r') as file:
      creds = file.readlines()
      for i in creds:
        user, _ = i.split(":")
        if user == username:
          return "Username already exists"
    with open("credentials.txt", 'a') as file:
      file.append(username + ":" + password + "\n")
    return "Signed up"

#Save receipt data
@app.route('/save', methods=['POST'])
def save_receiept():
  global total
  print(request.data)
  try:
    user, reciept = request.data.decode('ASCII').split("|_|")
  except Exception as e:
    user, reciept = request.data.split("|_|")
  print(user, reciept, file = sys.stdout)
  a = user + "^" + datetime.today().strftime(r'%d_%m_%y_%H_%M_%S')
  f = open("I:/RecieptSaves/" + a + ".txt", 'x')
  f.close()
  with open("I:/RecieptSaves/" + a + ".txt", 'w') as file:
    file.write(reciept)
  return total

#Same as read_receipts but returns important data
def get_receipt_details(img):
  receiptOcrEndpoint = 'https://ocr.asprise.com/api/v1/receipt' # Receipt OCR API endpoint
  imageFile = img
  r = requests.post(receiptOcrEndpoint, data = { \
    'client_id': 'TEST', 
    'recognizer': 'auto',
    'ref_no': 'ocr_python_123',
    }, \
    files = {"file": open(imageFile, "rb")})
  data = json.loads(r.text)
  print(data, file = sys.stdout)
  maindata = data["receipts"]
  maindata = maindata[0]
  data = {}
  user, _ = img.split("^")
  data["Username"] = user
  data["Store"] = maindata.get("merchant_name")
  data["Address"] = maindata.get("merchant_address")
  data["Number"] = maindata.get("merchant_phone")
  data["Date"] = maindata.get("date")
  items = []
  for i in maindata.get("items"):
    items.append(str(i.get("description")) + ": " + str(i.get("amount")))
  items = str(items).strip("[").strip("]")
  data["Items"] = items
  data["Total"] = str(maindata.get("total")) + " " + maindata.get("currency")
  table.create(data)
  return data

#Gets the saved reciepts
def get_receiepts(user):
  foundfiles = []
  files = os.listdir("I:/RecieptSaves")
  for i in files:
    if user in i:
      i = i.strip(".txt")
      _, date = i.split("^")
      with open(i, 'r') as file:
        foundfiles.append(date + "|_|" + file.read())
  return foundfiles

#Reads the reciepts
def read_receiept(filename):
  global total
  #Earlier attempt to OCR, but wasn't as accurate
  #pytesseract.pytesseract.tesseract_cmd = r"C:\Users\Lenovo\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
  #img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
  #if img.shape[0] < 300 and img.shape[1] < 300:
    #img = cv2.resize(img, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)
  #cv2.threshold(cv2.bilateralFilter(img, 5, 75, 75), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
  #out_below = pytesseract.image_to_string(img)
  #return out_below

  receiptOcrEndpoint = 'https://ocr.asprise.com/api/v1/receipt' # Receipt OCR API endpoint
  imageFile = filename + ".png"
  r = requests.post(receiptOcrEndpoint, data = { \
    'client_id': 'TEST', 
    'recognizer': 'auto',
    'ref_no': 'ocr_python_123',
    }, \
    files = {"file": open(imageFile, "rb")})

  data = json.loads(r.text)
  print(data, file = sys.stdout)
  maindata = data["receipts"][0]
  total = maindata.get("Total")
  total = str(total)
  return maindata.get("ocr_text")

#Get images from cloudinary via links from the app.
def get_image(url):
  r = urllib.request.urlopen(url)
  image = np.asarray(bytearray(r.read()), dtype = np.uint8)
  image = cv2.imdecode(image, -1)
  filename = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
  cv2.imwrite(filename + ".png", image)
  return read_receiept(filename)

app.run(host = 'localhost', port = 500)