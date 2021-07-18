import myUtilities
import cv2 
import sqlAndJsonConfiguration
cap = cv2.VideoCapture(0)
cap.set(3,1280)
cap.set(4,720)

# myUtilities.train_model_and_saveMD()
# myUtilities.train_model_and_saveFR()

maskDetectorModel = myUtilities.loadModelMD()
faceRecognizer = cv2.face.LBPHFaceRecognizer_create()

# faceRecognizer = cv2.face.createLBPHFaceRecognizer()
faceRecognizer.read("Models/faceRecognizerModel.xml")
dictionaryWithNames = sqlAndJsonConfiguration.createDictionary()

while True:
	succes , img = cap.read()
	copyImg = img
	img = myUtilities.predict_mask_and_person(img,maskDetectorModel,faceRecognizer,dictionaryWithNames)
	if img is None:
		cv2.imshow("image",copyImg)
	else:
		cv2.imshow("image",img)
	if cv2.waitKey(1) & 0xFF == ord('q'):
		break



