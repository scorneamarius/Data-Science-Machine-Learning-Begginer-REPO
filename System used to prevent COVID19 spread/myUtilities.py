import os
import tensorflow as tf
from tensorflow import keras
import cv2
import numpy as np
from tensorflow.keras.models import load_model
import json
import distance


def putText(image , text , x , y):
    cv2.putText(image,text,(x,y),cv2.FONT_HERSHEY_DUPLEX,1,(0,0,255),1)


def getTheCoordinatesOfTheFace(image):
	grayImage = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
	face_haar_cascade = cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
	coordinatesFace = face_haar_cascade.detectMultiScale(grayImage,scaleFactor=1.3,minNeighbors=4)
	return coordinatesFace

def getROIfromImage(image):
	face_haar_cascade = cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
	grayImage = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
	faceCoordinates = face_haar_cascade.detectMultiScale(grayImage,scaleFactor=1.3,minNeighbors=4)
	if len(faceCoordinates) == 1 :
		(y1,x1,y2,x2) = faceCoordinates[0]
		ROI_image = grayImage[int(x1+x2/2):x1+x2,y1:y1+y2]
		ROI_image_resized = cv2.resize(ROI_image,(30,30))
		ROI_image_scaled = ROI_image_resized/(255.0)
		return ROI_image_scaled
	else:
		return None


def predict_mask_and_person(image,model,faceRecognizer,dictionaryWithNames):
	threshold = 750
	faceCoordinates = getTheCoordinatesOfTheFace(image)
	ROI_images = []
	faces = []
	result = [] # image,[(nume,wear/no wear mask)]
	if len(faceCoordinates) == 0:
		return None
	else:
		grayImage = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
		for (y1,x1,y2,x2) in faceCoordinates:
			face = grayImage[x1:x1+x2,y1:y1+y2]
			face = cv2.resize(face,(200,200))
			faces.append(face)
			ROI_image = grayImage[int(x1+x2/2):x1+x2,y1:y1+y2]
			ROI_image_resized = cv2.resize(ROI_image,(50,50))
			ROI_image_scaled = ROI_image_resized/(255.0)
			ROI_image_finally = tf.expand_dims(ROI_image_scaled, axis=-1)
			ROI_images.append(ROI_image_finally)
		ROI_images = np.array(ROI_images)
		predicts = model.predict(ROI_images)
		mask=""
		for iterator in range(len(faceCoordinates)):
			if(predicts[iterator][0]>predicts[iterator][1]):
				mask = 'with_mask'
				putText(image,"with_mask",faceCoordinates[iterator][0],faceCoordinates[iterator][1])
			else:
				mask = 'without_mask'
				putText(image,"without_mask",faceCoordinates[iterator][0],faceCoordinates[iterator][1])
			label,confidence = faceRecognizer.predict(faces[iterator])
			if confidence < threshold:
				putText(image,dictionaryWithNames[label],faceCoordinates[iterator][0],faceCoordinates[iterator][1]+faceCoordinates[iterator][3])
				cv2.rectangle(image,(faceCoordinates[iterator][0],faceCoordinates[iterator][1]),(faceCoordinates[iterator][0]+faceCoordinates[iterator][2],faceCoordinates[iterator][1]+faceCoordinates[iterator][3]),(255,0,0),1)
				topLeft = (faceCoordinates[iterator][0], faceCoordinates[iterator][1])
				bottomRight = (faceCoordinates[iterator][0]+faceCoordinates[iterator][2],faceCoordinates[iterator][1]+faceCoordinates[iterator][3])
				result.append((dictionaryWithNames[label],mask,(topLeft,bottomRight)))
			else:
				putText(image,"Uncertain",faceCoordinates[iterator][0],faceCoordinates[iterator][1]+faceCoordinates[iterator][3])
				cv2.rectangle(image,(faceCoordinates[iterator][0],faceCoordinates[iterator][1]),(faceCoordinates[iterator][0]+faceCoordinates[iterator][2],faceCoordinates[iterator][1]+faceCoordinates[iterator][3]),(255,0,0),1)
				topLeft = (faceCoordinates[iterator][0], faceCoordinates[iterator][1])
				bottomRight = (faceCoordinates[iterator][0]+faceCoordinates[iterator][2],faceCoordinates[iterator][1]+faceCoordinates[iterator][3])
				result.append((dictionaryWithNames[label],mask,(topLeft,bottomRight)))
			print (str(confidence)+" "+dictionaryWithNames[label])
	result = [image,result]
	return result

def rectangleOverlap(r1TopLeft,r1BottomRight,r2TopLeft,r2BottomRight):
	# Point(y,x)
	if (r1BottomRight[1] < r2TopLeft[1]) or (r1BottomRight[1] < r1TopLeft[1]):
		return False
	if (r2BottomRight[0] < r1TopLeft[0]) or (r1BottomRight[0] < r2TopLeft[0]):
		return False
	return True


def generateLabelsMaskDetection():
	train_images=[]
	train_labels=[]
	pathMaskDirectory='mask'
	pathNoMaskDirectory='no_mask'
	for root,subdir,images in os.walk(pathMaskDirectory):
		for image in images:
			path = 'mask/' + image
			image = cv2.imread(path)
			image = getROIfromImage(image)
			if image is None:
				continue
			else:
				train_images.append(image)
				train_labels.append(0) # mask 0
	for root,subdir,images in os.walk(pathNoMaskDirectory):
		for image in images:
			path = "no_mask/"+ image
			image = cv2.imread(path)
			image = getROIfromImage(image)
			if image is None:
				continue
			else:
				train_images.append(image)
				train_labels.append(1) # no mask 1
	return np.array(train_images),np.array(train_labels)

def train_model_and_saveMD():
	train_images,train_labels = generateLabelsMaskDetection()
	train_images = tf.expand_dims(train_images,axis=-1)
	# model = keras.Sequential([
	# 	tf.keras.layers.Conv2D(64,kernel_size=(3,3),activation=tf.nn.relu,input_shape=(30,30,1)),
	# 	tf.keras.layers.MaxPooling2D(2,2),
	# 	tf.keras.layers.Conv2D(64,kernel_size=(3,3),activation=tf.nn.relu),
	# 	tf.keras.layers.MaxPooling2D(2,2),tf.keras.layers.Flatten(),
	# 	tf.keras.layers.Dense(128,activation=tf.nn.relu),
	# 	tf.keras.layers.Dense(2,activation=tf.nn.softmax)])
	model =keras.Sequential([
		tf.keras.layers.Conv2D(64,kernel_size=(5,5),activation=tf.nn.relu,input_shape=(50,50,1)), 
		tf.keras.layers.MaxPooling2D(2,2), tf.keras.layers.Conv2D(64,kernel_size=(3,3),activation=tf.nn.relu), 
		tf.keras.layers.MaxPooling2D(2,2), tf.keras.layers.Flatten(), tf.keras.layers.Dense(30,activation=tf.nn.relu), 
		tf.keras.layers.Dense(2,activation=tf.nn.softmax) ])
	model.compile(optimizer = tf.optimizers.Adam(),loss='sparse_categorical_crossentropy',metrics='accuracy')	
	model.fit(train_images,train_labels,epochs=50)
	model.save('Models/maskDetectorModel.h5')
	print("The model was trained OK")

def loadModelMD():
	model=load_model('Models/maskDetectorModel.h5')
	return model

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
			# faceCoordinates = getTheCoordinatesOfTheFace(image)
			# if len(faceCoordinates) == 1:
				# (y1,x1,y2,x2) = faceCoordinates[0]
				# faceImage = grayImage[x1:x1+x2,y1:y1+y2]
			faces.append(grayImage)
			facesID.append(folderID)
	return np.array(facesID),faces


def train_model_and_saveFR():
	(faces , labels) = generateLabelsFaceRecognition()
	faceRecognizer = cv2.face.LBPHFaceRecognizer_create(radius=1,neighbors=8,grid_x=20,grid_y=20)
	faceRecognizer.train(labels,faces)
	faceRecognizer.save("Models/faceRecognizerModel.xml")
	with open('configuration.json') as json_file:
		data = json.load(json_file)
	data['train_model'] = False
	with open('configuration.json', 'w') as outfile:
		json.dump(data,outfile,indent=2)
	print("model FR was trained succesfully")


