import tkinter
import cv2
import PIL.Image
import PIL.ImageTk
import json
import mysql.connector
import os
import tkinter.messagebox
import shutil 
from myUtilities import train_model_and_saveFR


class MainApp:
	def __init__(self,rootWindow):

		self.db = mysql.connector.connect(
			host="localhost",
			user="root",
			passwd="root",
			database="trackingpeople"
		)
		self.stop = False

		self.mycursor = self.db.cursor()

		self.mycursor.execute('SET FOREIGN_KEY_CHECKS=0')

		self.rootWindow = rootWindow
		self.rootWindow.title("Tracking people in hospital")
		self.videoCapture = MyVideoCapture(1000,700)

		self.statusInfoUserOk = False

		self.canvas = tkinter.Canvas(self.rootWindow,width = self.videoCapture.getWidthStreamVideo(), height = self.videoCapture.getHeightStreamVideo())
		self.canvas.grid(row = 0 , column = 0, columnspan = 4)


		self.firstnameLabel = tkinter.Label(rootWindow, text = "First name: ")
		self.firstnameLabel.grid(row = 1 , column = 0)
		self.firstname = tkinter.Entry(self.rootWindow)
		self.firstname.grid(row = 1 , column = 1)

		self.lastnameLabel = tkinter.Label(rootWindow, text = "Last name: ")
		self.lastnameLabel.grid(row = 2 , column = 0)
		self.lastname = tkinter.Entry(self.rootWindow)
		self.lastname.grid(row = 2 , column = 1)

		self.ageLabel = tkinter.Label(rootWindow, text = "Age: ")
		self.ageLabel.grid(row = 3 , column = 0)
		self.age = tkinter.Entry(self.rootWindow)
		self.age.grid(row = 3 , column = 1)



		self.roomLabel = tkinter.Label(rootWindow, text = 'Select room')
		self.roomLabel.grid(row = 4, column = 0)
		self.options = []
		self.optionsInfo = []
		self.result = self.mycursor.execute("SELECT * FROM hospitalrooms")
		self.result = self.mycursor.fetchall()
		for i,(idRoom , nrPerson , capacity) in enumerate(self.result):
			self.options.append(str(i)+" Room ID: "+str(idRoom)+"| capacitate: "+str(nrPerson)+"/"+str(capacity))
			self.optionsInfo.append([idRoom,nrPerson,capacity])
		self.optionMenuValue = tkinter.StringVar()
		self.optionMenuValue.set('No option')
		self.drop = tkinter.OptionMenu(rootWindow,self.optionMenuValue,*self.options)
		self.drop.grid(row = 4, column = 1)

		self.buttonAddRooms = tkinter.Button(self.rootWindow,command = self.addRoom, text = "Add room")
		self.buttonAddRooms.grid(row = 3, column = 2)
		self.capacityRoom = tkinter.Entry(self.rootWindow)
		self.capacityRoom.grid(row = 2, column = 2)
		self.labelCapacity = tkinter.Label(rootWindow, text = "Persons per room")
		self.labelCapacity.grid(row = 1, column = 2)

		self.labelDelete = tkinter.Label(self.rootWindow, text = "Remove a person")
		self.labelDelete.grid(row = 5, column = 0)
		self.listPacientValue = tkinter.StringVar()
		self.listPacientOptions = []
		self.pacient = []
		self.resultPacients = self.mycursor.execute("SELECT * FROM users")
		self.resultPacients = self.mycursor.fetchall()
		for i,(id,firstname,lastname,age,roomID) in enumerate(self.resultPacients):
			self.listPacientOptions.append(str(id) + " " + firstname + " " + lastname)
			self.pacient.append([id, firstname, lastname, age, roomID])

		self.listPacientValue.set("No option")
		self.listPacient = tkinter.OptionMenu(self.rootWindow, self.listPacientValue, *self.listPacientOptions)
		self.listPacient.grid(row = 5, column = 1)
		self.externPacientButton = tkinter.Button(self.rootWindow, command = self.externPacientCommand, text = "Remove a person")
		self.externPacientButton.grid(row = 5, column = 2)

		self.buttonAddUser = tkinter.Button(self.rootWindow,command = self.createUser , text="Add person in system",state = "disabled")
		self.buttonAddUser.grid(row = 6 , column = 0)

		self.buttonMakePhoto = tkinter.Button(self.rootWindow,command = self.makePhoto , text="Make photo",state = "disabled")
		self.buttonMakePhoto.grid(row = 6 , column = 1)

		self.photoRemained = 150

		self.photoInfo = tkinter.Label(rootWindow, text = "Photo remained: "+str(self.photoRemained))
		self.photoInfo.grid(row = 6 , column = 2)

		self.infoLabel = tkinter.Label(rootWindow, text="Info: no info")
		self.infoLabel.grid(row = 6, column = 3)

		self.updateBtn = tkinter.Button(self.rootWindow,command = self.updateMethod , text="Update system")
		self.updateBtn.grid(row = 7 , column = 0)


		self.currentUser = {
			"firstname" : "",
			"lastname" : "",
			"age" : "",
			"id":None,
			"idRoom":0,
			"indexImage":0
		}

		self.delayForUpdate = 10
		self.rootWindow.after(self.delayForUpdate,self.update)
		self.rootWindow.mainloop()

	def updateMethod(self):
		train_model_and_saveFR()
		popupUpdate = tkinter.messagebox.showinfo("Update","The system was updated succesfully!")


	def makePhoto(self):
		succes , image = self.videoCapture.getImage()
		image = cv2.cvtColor(image,cv2.COLOR_RGB2BGR)
		if succes == True:
			face = self.getFaceFromImage(image)
			if face is None:
				print("Couldn't detect face")
			else:
				self.photoRemained = self.photoRemained - 1
				self.photoInfo['text'] = "Photo remained : " + str(self.photoRemained)
				face = cv2.resize(face,(200,200))
				path = (os.getcwd()).replace('\\','/')+"/images/"+str(self.currentUser['id'])
				imagePath = path+"/"+str(self.currentUser['indexImage'])+".jpg"
				cv2.imwrite(imagePath,face)
				self.currentUser['indexImage'] = self.currentUser['indexImage'] + 1
				if self.photoRemained == 0:
					self.buttonMakePhoto['state']='disabled'
					self.popup = tkinter.messagebox.askquestion("Continue","Do you want to continue?")
					if self.popup == 'yes':
						self.popup = None
						self.currentUser = {
							"firstname" : "",
							"lastname" : "",
							"age" : "",
							"id":None,
							"idRoom":0,
							"indexImage":0
						}
						self.canvas.delete('all')
						self.stop = True
						self.firstname['state']='normal'
						self.lastname['state']='normal'
						self.age['state']='normal'
						self.firstname.delete(0, 'end')
						self.lastname.delete(0, 'end')
						self.age.delete(0, 'end')
						self.statusInfoUserOk = False
						self.options = []
						self.optionsInfo = []
						self.result = self.mycursor.execute("SELECT * FROM hospitalrooms")
						self.result = self.mycursor.fetchall()
						self.drop.grid_remove()
						for i,(idRoom , nrPerson , capacity) in enumerate(self.result):
							self.options.append(str(i)+" Room ID: "+str(idRoom)+"| capacitate: "+str(nrPerson)+"/"+str(capacity))
							self.optionsInfo.append([idRoom,nrPerson,capacity])
						self.optionMenuValue = tkinter.StringVar()
						self.optionMenuValue.set('No option')
						self.drop = tkinter.OptionMenu(self.rootWindow,self.optionMenuValue,*self.options)
						self.drop.grid(row = 4, column = 1)
					else:
						self.rootWindow.destroy()



	def getFaceFromImage(self,image):
		grayImage = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
		face_haar_cascade = cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
		coordinatesFace = face_haar_cascade.detectMultiScale(grayImage,scaleFactor=1.3,minNeighbors=4)
		if len(coordinatesFace) == 1 :
			(y1,x1,y2,x2) = coordinatesFace[0]
			face = image[x1:x1+x2,y1:y1+y2]
			return face
		else:
			return None

	def addRoom(self):
		capacity = self.capacityRoom.get()
		ok = 0
		for i in capacity:
			if not(i >= '0' and i <= '9'):
				ok = 1
		if ok == 0 and len(capacity) != 0:
			self.infoLabel['text'] = 'Info : no info'
			newId = self.optionsInfo[-1][0] + 1
			sqlFormula = (f'INSERT INTO hospitalrooms (idRoom,nrPerson,capacity) VALUES({newId}, {0}, {capacity})')
			self.mycursor.execute(sqlFormula)
			self.db.commit()
			self.options = []
			self.optionsInfo = []
			self.result = self.mycursor.execute("SELECT * FROM hospitalrooms")
			self.result = self.mycursor.fetchall()
			self.drop.grid_remove()
			for i,(idRoom , nrPerson , capacity) in enumerate(self.result):
				self.options.append(str(i)+" Room ID: "+str(idRoom)+"| capacitate: "+str(nrPerson)+"/"+str(capacity))
				self.optionsInfo.append([idRoom,nrPerson,capacity])
			self.optionMenuValue = tkinter.StringVar()
			self.optionMenuValue.set('No option')
			self.drop = tkinter.OptionMenu(self.rootWindow,self.optionMenuValue,*self.options)
			self.drop.grid(row = 4, column = 1)
			self.capacityRoom.delete(0,'end')

		else:
			self.infoLabel['text'] = 'Invalid capacity'

	def externPacientCommand(self):
		if self.listPacientValue.get() !='No option' :
			number = ""
			for i in self.listPacientValue.get():
				if i >= '0' and i <= '9':
					number = number + i
				else:
					break
			id = int(number)
			sqlFormula = (f"DELETE FROM users WHERE id = {id}")
			self.mycursor.execute(sqlFormula)
			self.db.commit()
			sqlFormula = (f"DELETE FROM whitelist WHERE PersonID = {id}")
			self.mycursor.execute(sqlFormula)
			self.db.commit()
			for i_id,_,_,_,idRoom in self.pacient:
				if i_id == id:
					sqlFormula = (f"SELECT nrPerson FROM hospitalrooms WHERE idRoom = {idRoom}")
					self.mycursor.execute(sqlFormula)
					result = self.mycursor.fetchall()
					newresult = result[0][0] - 1
					sqlFormula = (f"UPDATE hospitalrooms SET nrPerson = {newresult} WHERE idRoom = {idRoom}")
					self.mycursor.execute(sqlFormula)
					self.db.commit()
					path = "C:/Users/scorn/OneDrive/Desktop/Licenta/MaskDetector/images" +  "/" + str(id)
					shutil.rmtree(path)
					with open('configuration.json') as json_file:
						data = json.load(json_file)

					for entry in data['allUsers']:
						if entry['id'] == id:
							data['allUsers'].remove(entry)
							break
					with open('configuration.json', 'w') as outfile:
						json.dump(data,outfile,indent=2)
					self.options = []
					self.optionsInfo = []
					self.result = self.mycursor.execute("SELECT * FROM hospitalrooms")
					self.result = self.mycursor.fetchall()
					self.drop.grid_remove()
					for i,(idRoom , nrPerson , capacity) in enumerate(self.result):
						self.options.append(str(i)+" Room ID: "+str(idRoom)+"| capacitate: "+str(nrPerson)+"/"+str(capacity))
						self.optionsInfo.append([idRoom,nrPerson,capacity])
					self.optionMenuValue = tkinter.StringVar()
					self.optionMenuValue.set('No option')
					self.drop = tkinter.OptionMenu(self.rootWindow,self.optionMenuValue,*self.options)
					self.drop.grid(row = 4, column = 1)
					self.capacityRoom.delete(0,'end')

					self.listPacient.grid_remove()
					self.listPacientOptions = []
					self.pacient = []
					self.resultPacients = self.mycursor.execute("SELECT * FROM users")
					self.resultPacients = self.mycursor.fetchall()
					for i,(id,firstname,lastname,age,roomID) in enumerate(self.resultPacients):
						self.listPacientOptions.append(str(id) + " " + firstname + " " + lastname)
						self.pacient.append([id, firstname, lastname, age, roomID])
					self.listPacientValue.set("No option")
					self.listPacient = tkinter.OptionMenu(self.rootWindow, self.listPacientValue, *self.listPacientOptions)
					self.listPacient.grid(row = 5, column = 1)
					break

	def createUser(self):
		if self.optionMenuValue.get() !='No option' :
			number = ""
			for i in self.optionMenuValue.get():
				if i >='0' and i <= '9':
					number = number + i
				else:
					break
			if self.optionsInfo[int(number)][1] >= self.optionsInfo[int(number)][2]:
				self.infoLabel['text'] = "Info: exceeded capacity"
			else:
				self.photoInfo.destroy()
				self.photoInfo = tkinter.Label(self.rootWindow, text = "Photo remained: "+str(self.photoRemained))
				self.photoInfo.grid(row = 6 , column = 2)
				self.photoRemained = 150
				self.photoInfo['text'] = "Photo remained : " + str(self.photoRemained)
				self.stop = False
				idRoom = self.optionsInfo[int(number)][0]
				self.infoLabel['text'] = "Info: no info"
				self.statusInfoUserOk = True
				self.firstname['state']='disabled'
				self.lastname['state']='disabled'
				self.age['state']='disabled'
				self.buttonAddUser['state']="disabled"
				self.currentUser['firstname'] = self.firstname.get()
				self.currentUser['lastname'] = self.lastname.get()
				self.currentUser['idRoom'] = idRoom
				self.currentUser['age'] = self.age.get()
				self.buttonMakePhoto['state'] = 'active'
				with open('configuration.json') as json_file:
					data = json.load(json_file)
				lastEntry = data['allUsers'][-1]
				id = lastEntry['id'] + 1
				self.currentUser['id'] = id
				sqlFormula = "INSERT INTO users (id,firstname,lastname,age,roomID) VALUES (%s,%s,%s,%s,%s)"
				nextEntry = (id,self.currentUser['firstname'],self.currentUser['lastname'],self.currentUser['age'],self.currentUser['idRoom'])
				self.mycursor.execute(sqlFormula,nextEntry)
				self.db.commit()

				sqlFormula = (f'SELECT nrPerson FROM hospitalrooms WHERE idRoom ={idRoom}')
				nextEntry = (idRoom)
				self.mycursor.execute(sqlFormula)
				results = self.mycursor.fetchall()
				result = results[0][0]

				sqlFormula = (f'UPDATE hospitalrooms SET nrPerson ={result + 1} WHERE idRoom = {idRoom}')
				self.mycursor.execute(sqlFormula)
				self.db.commit()
				data['allUsers'].append({"id":id,"wear_mask":True})
				data['train_model'] = True
				with open('configuration.json', 'w') as outfile:
					json.dump(data,outfile,indent=2)
				path = (os.getcwd()).replace('\\','/')+"/images/"+str(id)
				os.mkdir(path)

				#aici
				self.listPacient.grid_remove()
				self.listPacientOptions = []
				self.pacient = []
				self.resultPacients = self.mycursor.execute("SELECT * FROM users")
				self.resultPacients = self.mycursor.fetchall()
				for i,(id,firstname,lastname,age,roomID) in enumerate(self.resultPacients):
					self.listPacientOptions.append(str(id) + " " + firstname + " " + lastname)
					self.pacient.append([id, firstname, lastname, age, roomID])
				self.listPacientValue.set("No option")
				self.listPacient = tkinter.OptionMenu(self.rootWindow, self.listPacientValue, *self.listPacientOptions)
				self.listPacient.grid(row = 5, column = 1)
		else:
			self.infoLabel['text'] = "Info: select room"


		
	def update(self):
		if self.statusInfoUserOk == False :
			firstnameInput = self.firstname.get()
			lastnameInput = self.lastname.get()
			ageInput = self.age.get()
			if(firstnameInput!=''and lastnameInput!='' and ageInput!=''):
				self.buttonAddUser['state']="active"
			else:
				self.buttonAddUser['state']="disabled"
		else:
			succes , image = self.videoCapture.getImage()
			if succes == True:
				self.canvasImage = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(image))
				if self.stop == False:
					self.canvas.create_image(0, 0, image=self.canvasImage,anchor = tkinter.NW)
		self.rootWindow.after(self.delayForUpdate,self.update)


class MyVideoCapture:
	def __init__(self,width,height):
		self.streamVideo = cv2.VideoCapture(0)
		self.streamVideo.set(cv2.CAP_PROP_FRAME_WIDTH,width)
		self.streamVideo.set(cv2.CAP_PROP_FRAME_HEIGHT,height)

	def getWidthStreamVideo(self):
		return self.streamVideo.get(cv2.CAP_PROP_FRAME_WIDTH)

	def getHeightStreamVideo(self):
		return self.streamVideo.get(cv2.CAP_PROP_FRAME_HEIGHT)

	def getImage(self):
		if self.streamVideo.isOpened():
			succes, currentImage = self.streamVideo.read()
			if succes == True:
				RGBimage = cv2.cvtColor(currentImage,cv2.COLOR_BGR2RGB)
				return succes , RGBimage
			else:
				return False, None
		else:
			return False, None


MainApp(tkinter.Tk())




