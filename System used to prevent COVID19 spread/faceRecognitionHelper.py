import numpy as np
import cv2
import os

def generateLabelsFaceRecognition():
	faces = []
	facesID = []
	pathToWalk = "images"
	for root,subdirnames,filenames in os.walk(pathToWalk):
		for filename in filenames:
			folderID = int(os.path.basename(root))
			imagePath = root + '/' + filename
			image = cv2.imread(imagePath)
			grayImage = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
			faceCoordinates = getTheCoordinatesOfTheFace(image)
			if len(faceCoordinates) == 1:
				(y1,x1,y2,x2) = faceCoordinates[0]
				faceImage = grayImage[x1:x1+x2,y1:y1+y2]
				faces.append(faceImage)
				facesID.append(folderID)
	return np.array(facesID),faces

def getTheCoordinatesOfTheFace(image):
	grayImage = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
	face_haar_cascade = cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
	coordinatesFace = face_haar_cascade.detectMultiScale(grayImage,scaleFactor=1.3,minNeighbors=4)
	return coordinatesFace

def train_model_and_save():
	(faces , labels) = generateLabelsFaceRecognition()
	faceRecognizer = cv2.face.LBPHFaceRecognizer_create()
	faceRecognizer.train(labels,faces)
	faceRecognizer.save("Models/faceRecognizerModel.xml")