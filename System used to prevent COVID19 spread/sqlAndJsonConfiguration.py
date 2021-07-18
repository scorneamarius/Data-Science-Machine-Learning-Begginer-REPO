import mysql.connector
import json
import os
import cv2

db = mysql.connector.connect(
	host="localhost",
	user="placeholder",
	passwd="placeholder",
	database="placeholder"
	)

def createUsersTable():
	mycursor = db.cursor()
	mycursor.execute("CREATE TABLE users(id int AUTO_INCREMENT PRIMARY KEY ,firstname varchar(30),lastname varchar(30),age int,roomID int)")

def createDictionary():
	dict={}
	mycursor = db.cursor()
	mycursor.execute("SELECT id,firstname,lastname FROM users")
	result = mycursor.fetchall()
	for (id , firstname , lastname) in result:
		dict[id] = firstname + " " + lastname
	return dict

def createUserInUsersTable(firstname,lastname,age,roomID):
	with open('configuration.json') as json_file:
		data = json.load(json_file)
	lastEntry = data['allUsers'][-1]
	id = lastEntry['id'] + 1
	mycursor = db.cursor()
	sqlFormula = "INSERT INTO users (id,firstname,lastname,age,roomID) VALUES (%s,%s,%s,%s,%s)"
	nextEntry = (id,firstname,lastname,age,roomID)
	mycursor.execute(sqlFormula,nextEntry)
	db.commit()
	data['allUsers'].append({"id":id,"wear_mask":True})
	data['train_model'] = True
	with open('configuration.json', 'w') as outfile:
		json.dump(data,outfile,indent=2)
	path = (os.getcwd()).replace('\\','/')+"/images/"+str(id)
	os.mkdir(path)
	makePhoto(path)
	
def getFaceFromImage(image):
	grayImage = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
	face_haar_cascade = cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
	coordinatesFace = face_haar_cascade.detectMultiScale(grayImage,scaleFactor=1.3,minNeighbors=4)
	if len(coordinatesFace) == 1 :
		(y1,x1,y2,x2) = coordinatesFace[0]
		face = image[x1:x1+x2,y1:y1+y2]
		return face
	else:
		return None

def makePhoto(path):
	capture = cv2.VideoCapture(0)
	capture.set(3,2000)
	capture.set(4,1300)
	count = 0
	while count < 5:
		succes , img = capture.read()
		cv2.imshow("image",img)
		if cv2.waitKey(1) & 0xFF == ord('q'):
			face = getFaceFromImage(img)
			if face is None:
				continue
			else:
				face = cv2.resize(face,(200,200))
				imagePath = path+"/"+str(count)+".jpg"
				cv2.imwrite(imagePath,face)
				count = count + 1
	cv2.destroyAllWindows()

