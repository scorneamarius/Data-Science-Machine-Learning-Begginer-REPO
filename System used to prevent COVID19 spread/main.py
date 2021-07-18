import cv2
import sqlAndJsonConfiguration
import myUtilities
import tkinter
import PIL.Image
import PIL.ImageTk
import json
import mysql.connector
import os
import tkinter.messagebox
from detecto.utils import read_image
from detecto.core import Dataset
from detecto.core import DataLoader, Model
import datetime
from tkcalendar import Calendar

class MainApp:
	def __init__(self,rootWindow):
		self.rootWindow = rootWindow
		self.videoCapture = MyVideoCapture(900,700)
		self.canvas = tkinter.Canvas(self.rootWindow,width = self.videoCapture.getWidthStreamVideo(), height = self.videoCapture.getHeightStreamVideo())
		self.canvas.grid(row = 0 , column = 0, columnspan = 4)

		self.db = mysql.connector.connect(
			host="localhost",
			user="root",
			passwd="root",
			database="trackingpeople"
		)
		self.mycursor = self.db.cursor()

		self.labels=['door']
		self.model = Model.load("Models/doorModel.pth",self.labels)

		
		_,self.firstImage,_ = self.videoCapture.getImage()
		self.labels, self.boxes, self.scores = self.model.predict(self.firstImage)
		self.predictions = self.model.predict_top(self.firstImage)
		self.boxesList = []
		for box in self.boxes: 
			topleft = (int(box[0].item()),int(box[1].item()))
			botright= (int(box[2].item()),int(box[3].item()))
			self.boxesList.append((topleft,botright))
		self.boxSelected = None

		self.optionMenuValue = tkinter.StringVar()
		self.optionMenuValue.set('Region of interest')
		self.options = list(range(len(self.boxesList)))
		self.drop = tkinter.OptionMenu(rootWindow,self.optionMenuValue,*self.options)
		self.drop.grid(row = 1, column = 0)

		self.showROI = tkinter.Button(self.rootWindow,command = self.showROIMethod, text = "Show the region")
		self.showROI.grid(row = 2, column = 0)

		self.selectROI = tkinter.Button(self.rootWindow,command = self.selectROIMethod, text = "Select the region")
		self.selectROI.grid(row = 3, column = 0)

		self.infoLabel = tkinter.Label(self.rootWindow, text="Info: no info")
		self.infoLabel.grid(row = 5, column = 2)

		self.listPacientValue = tkinter.StringVar()
		self.listPacientOptions = []
		self.pacient = []
		self.resultPacients = self.mycursor.execute("SELECT * FROM users")
		self.resultPacients = self.mycursor.fetchall()
		for i,(id,firstname,lastname,age,roomID) in enumerate(self.resultPacients):
			self.listPacientOptions.append(firstname + " " + lastname)
			self.pacient.append([id, firstname, lastname, age, roomID])
		self.listPacientValue.set("Select person")
		self.listPacient = tkinter.OptionMenu(self.rootWindow, self.listPacientValue, *self.listPacientOptions)
		self.listPacient.grid(row = 1, column = 1)

		self.putWhiteListButton = tkinter.Button(self.rootWindow,command = self.putWhiteListMethod, text = "Put in white list")
		self.putWhiteListButton.grid(row = 2, column = 1)

		self.whiteList = []	
		self.listbox = tkinter.Listbox(self.rootWindow, height = 7, 
                  width = 15, 
                  activestyle = 'dotbox',
                  yscrollcommand = True)
		self.listbox.grid(row = 3, column = 1)
		self.idPacientsWhitelist = self.mycursor.execute("SELECT PersonID from whitelist")
		self.idPacientsWhitelist = self.mycursor.fetchall()
		for elem in self.idPacientsWhitelist:
			id = elem[0]
			resultPacientById = self.mycursor.execute(f"SELECT CONCAT(firstname, ' ', lastname) as fullName FROM users WHERE id = {id}")
			resultPacientById = self.mycursor.fetchall()
			self.whiteList.append(resultPacientById[0][0])
			self.listbox.insert(0,resultPacientById[0][0])

		self.deleteItem = tkinter.Button(self.rootWindow,command = self.deleteItemMethod, text = "Remove person")
		self.deleteItem.grid(row = 4, column = 1)

		self.pacientHistoryOptionMenuValue = tkinter.StringVar()
		self.pacientHistoryOptionMenuValue.set("Select person")
		self.pacientHistoryOptionMenuOptions = self.listPacientOptions
		self.pacientHistoryOptionMenu = tkinter.OptionMenu(rootWindow,self.pacientHistoryOptionMenuValue,*self.pacientHistoryOptionMenuOptions)
		self.pacientHistoryOptionMenu.grid(row = 1, column = 2)

		self.getHistoryBtn = tkinter.Button(self.rootWindow,command = self.historyBtnMethod, text = "Get history")
		self.getHistoryBtn.grid(row = 2, column = 2)

		self.historyListbox = tkinter.Listbox(self.rootWindow, height = 7, 
                  width = 45, 
                  activestyle = 'dotbox',
                  yscrollcommand = True)
		self.historyListbox.grid(row = 3, column = 2)

		self.cal = Calendar(self.rootWindow, selectmode = 'day',
               year = 2020, month = 5,
               day = 22,
               date_pattern = "y-mm-dd")
		self.cal.grid(row = 3, column = 3)

		self.delayForUpdate = 10
		self.rootWindow.mainloop()

	def historyBtnMethod(self):
		historyList = []
		pacient = self.pacientHistoryOptionMenuValue.get()
		if pacient != "Select person":
			self.historyPacient = self.mycursor.execute(f"SELECT * FROM restriction WHERE name = '{pacient}'")
			self.historyPacient = self.mycursor.fetchall()
			for i,(id,name,wearmask,caughtroidenied,currentdate) in enumerate(self.historyPacient):
				currentdate = str(currentdate)
				if currentdate.find(self.cal.get_date()) != -1:
					if caughtroidenied == 1:
						if wearmask == 1: 
							historyList.append((currentdate,"with mask","inside region"))
						else:
							historyList.append((currentdate,"without mask","inside region"))
					else:
						if wearmask == 1: 
							historyList.append((currentdate,"with mask","outside region"))
						else:
							historyList.append((currentdate,"without mask","outside region"))

			historyList = [t for t in (set(tuple(i) for i in historyList))] # remove duplicate
			self.historyListbox.delete(0,'end')
			for i,(currentdate,mask,region) in enumerate(historyList):
				self.historyListbox.insert(0,str(i) + " " + str(currentdate) + "-" + mask + "-" + region)
		else:
			self.infoLabel['text'] = "Please select the person"


	def deleteItemMethod(self):
			value = self.listbox.get(self.listbox.curselection())
			if value is not(None):
				self.listbox.delete(self.listbox.curselection())
				self.whiteList.remove(value)
				query = (f'select id from users where concat(firstname," ",lastname) = "{value}"')
				personID = self.mycursor.execute(query)
				personID = self.mycursor.fetchall()
				personID = personID[0][0]
				query = (f'DELETE FROM whitelist where PersonID = {personID}')
				self.mycursor.execute(query)
				self.db.commit()




	def putWhiteListMethod(self):
		pacient = self.listPacientValue.get()
		if pacient != "Select person":
			fullNameList = pacient.split()
			lastname = fullNameList[-1]
			firstname = ""
			for i,elem in enumerate(fullNameList[0:-1]):
				if i == 0:
					firstname = elem
				else:
					firstname = firstname + " " + elem
			fullName = firstname + " "+lastname

			if fullName in self.whiteList:
				self.infoLabel['text'] = "White list already contais selected person"
			else:
				query = (f'SELECT id FROM users WHERE (firstname = "{firstname}" and lastname = "{lastname}")')
				personID = self.mycursor.execute(query)
				personID = self.mycursor.fetchall()
				personID = personID[0][0]
				result = self.mycursor.execute(f'INSERT INTO whitelist (PersonID) VALUES ({personID})')
				result = self.db.commit()
				self.infoLabel['text'] = "Info: no info"
				self.listbox.insert(0,fullName)
				self.whiteList.append(fullName)
		else:
			self.infoLabel['text'] = "Select person before add in the white list"

	def selectROIMethod(self):
		value = self.optionMenuValue.get()
		if value == 'Region of interest':
			self.infoLabel['text'] = "select ROI label"
		else:
			self.infoLabel['text'] = "Info: no info"
			value = int(self.optionMenuValue.get())
			self.boxSelected = self.boxesList[value]
			self.selectROI['state'] = "disabled"
			self.showROI['state'] = "disabled"
			self.drop['state'] = "disabled"
			self.rootWindow.after(self.delayForUpdate,self.update)

	
	def showROIMethod(self):
		value = self.optionMenuValue.get()
		if value == 'Region of interest':
			self.infoLabel['text'] = "select ROI label"
		else:
			self.infoLabel['text'] = "Info: no info"
			value = int(self.optionMenuValue.get())
			image = self.firstImage.copy()
			image = cv2.rectangle(image,self.boxesList[value][0],self.boxesList[value][1],(255,0,0),2)
			self.canvasImage = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(image))
			self.canvas.create_image(0, 0, image=self.canvasImage,anchor = tkinter.NW)

	def update(self):
		succes,image,infoList = self.videoCapture.getImage()
		if succes == True:
			image = cv2.rectangle(image,self.boxSelected[0],self.boxSelected[1],(255,0,0),2)
			self.canvasImage = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(image))
			self.canvas.create_image(0, 0, image=self.canvasImage,anchor = tkinter.NW)
			sqlFormula = "INSERT INTO restriction (name,wearmask,caughtroidenied,currentdate) VALUES (%s,%s,%s,%s)"
			now = datetime.datetime.now()
			if infoList is not(None):
				for (name,wear,point) in infoList:
					if name !="Uncertain":
						(topLeft,bottomRight) = point
						if myUtilities.rectangleOverlap(topLeft,bottomRight,self.boxSelected[0],self.boxSelected[1]) == True: # se afla in roi
							if name in self.whiteList: # in lista alba
								if wear == "without_mask": # nu poarta masca
									nextEntry = (name,0,1,now.strftime('%Y-%m-%d %H:%M:%S'))
									# print(0,1)
									self.mycursor.execute(sqlFormula,nextEntry)
									self.db.commit()
							else: #nu se afla pe lista alba
								if wear == 'with_mask': # poarta masca
									nextEntry = (name,1,1,now.strftime('%Y-%m-%d %H:%M:%S'))
									# print(1,1)
									self.mycursor.execute(sqlFormula,nextEntry)
									self.db.commit()
								else:  # nu poarta masca
									nextEntry = (name,0,1,now.strftime('%Y-%m-%d %H:%M:%S'))
									self.mycursor.execute(sqlFormula,nextEntry)
									self.db.commit()
									# print(0,1)
						else: # nu se afla in roi
							if wear == 'without_mask': # fara masca
									nextEntry = (name,0,0,now.strftime('%Y-%m-%d %H:%M:%S'))
									self.mycursor.execute(sqlFormula,nextEntry)
									self.db.commit()
									# print(0,0)
							else: # cu masca
								nextEntry = (name,1,0,now.strftime('%Y-%m-%d %H:%M:%S'))
								self.mycursor.execute(sqlFormula,nextEntry)
								self.db.commit()
								# print(1,0)
					
		self.rootWindow.after(self.delayForUpdate,self.update)

class MyVideoCapture:
	def __init__(self,width,height):
		self.streamVideo = cv2.VideoCapture(0)
		self.streamVideo.set(cv2.CAP_PROP_FRAME_WIDTH,width)
		self.streamVideo.set(cv2.CAP_PROP_FRAME_HEIGHT,height)
		#myUtilities.train_model_and_saveMD()
		#myUtilities.train_model_and_saveFR()
		self.maskDetectorModel = myUtilities.loadModelMD()
		self.faceRecognizer = cv2.face.LBPHFaceRecognizer_create(radius=1,neighbors=8,grid_x=20,grid_y=20)
		self.faceRecognizer.read("Models/faceRecognizerModel.xml")
		self.dictionaryWithNames = sqlAndJsonConfiguration.createDictionary()

	def getWidthStreamVideo(self):
		return self.streamVideo.get(cv2.CAP_PROP_FRAME_WIDTH)

	def getHeightStreamVideo(self):
		return self.streamVideo.get(cv2.CAP_PROP_FRAME_HEIGHT)


	def getImage(self):
		if self.streamVideo.isOpened():
			succes, currentImage = self.streamVideo.read()
			if succes == True:
				copyImage = currentImage
				result = myUtilities.predict_mask_and_person(currentImage,self.maskDetectorModel,self.faceRecognizer,self.dictionaryWithNames)
				if result is None:
					RGBimage = cv2.cvtColor(copyImage,cv2.COLOR_BGR2RGB)
					return succes, RGBimage, None
				else:
					image,infoList = result
					RGBimage = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
					return succes,RGBimage,infoList
			else:
				return False, None, None
		else:
			return False, None, None


MainApp(tkinter.Tk())


