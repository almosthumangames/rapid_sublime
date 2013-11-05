import sublime, sublime_plugin
import socket
import time
import threading
import os
import subprocess
import re

from .edit import Edit
from .rapid_output import RapidOutputView

# to run execute from the console:
# view.run_command('rapid_eval')
class RapidConnectionThread(threading.Thread):
	instance = None

	def __init__(self):
	 	self.host = "localhost"
	 	self.port = 4444
	 	self.sock = None
	 	self.running = False

	 	try:
	 		self.sock = socket.create_connection((self.host, self.port))
	 	except OSError as e:
	 		RapidOutputView.printMessage("Failed to connect to rapid server:\n" + str(e))
	 		return False
	 	RapidOutputView.printMessage("Connected to " + self.host + ".")
	 	threading.Thread.__init__(self)
	 	RapidConnectionThread.instance = self

	def run(self):
		self.running = True
		dataQueue = []

		RapidOutputView.printMessage("Thread started")
		try:
			while True:
				data = self.sock.recv(1).decode()
				if not data:
					break

				if data != '\000':
					dataQueue.append(data)

				if data == '\n' or data == '\000':
					datastr = "".join(dataQueue)
					if dataQueue: #sdataQueue is not empty
						RapidOutputView.printMessage(datastr)
					del dataQueue[:]
		except:
			RapidOutputView.printMessage("Error in connection. Connection closed.")

		self.sock.close()
		self.running = False
		RapidOutputView.printMessage("Connection terminated")

	def isRunning(self):
		return self.running 

	def sendString(self, msg):
		self.sock.send(msg.encode())

	@staticmethod
	def checkConnection():
		if RapidConnectionThread.instance == None:
			RapidConnect()
			RapidConnectionThread().start()
		elif not RapidConnectionThread.instance.isRunning():
			RapidConnectionThread.instance.join()
			RapidConnect()
			RapidConnectionThread().start()

class RapidResumeCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		RapidConnectionThread.checkConnection()
		RapidConnectionThread.instance.sendString("\nsys.resume()\000")

class RapidHelpCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		cursor_pos = self.view.sel()[0].begin()
		region = self.view.word(cursor_pos)
		word = self.view.substr(region)

		RapidConnectionThread.checkConnection()
		line = "\nrequire(\"doc\"); doc.find([["+ word +"]])\000"
		RapidConnectionThread.instance.sendString(line)

class RapidEvalCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		RapidConnectionThread.checkConnection()
		line_contents = self.getLines()
		RapidConnectionThread.instance.sendString(line_contents)

	def getLines(self):
		for region in self.view.sel():

			current_row  = self.view.rowcol(self.view.sel()[0].begin())[0]

			if region.empty():
				#check if we are evaluating a block instead of line
				line = self.view.full_line(region)
				line_contents = self.view.substr(line)
				
				#eval block
				if line_contents.find("\t") == 0:
					start_row = current_row
					end_row = current_row
					index = 1

					#find start of the block
					block_start = False
					while not block_start:
						start_row = current_row - index
						start_line = self.view.full_line(self.view.text_point(start_row, 0))
						start_line_contents = self.view.substr(start_line)
						if start_line_contents.find("\t") != 0 and start_line_contents.strip() != '':
							block_start = True
						else:
							index = index + 1

					#find end of the block
					index = 1
					block_end = False
					while not block_end:
						end_row = current_row + index
						end_line = self.view.full_line(self.view.text_point(end_row, 0))
						end_line_contents = self.view.substr(end_line)
						if end_line_contents.find("\t") != 0 and end_line_contents.strip() != '':
							block_end = True
						else:
							index = index + 1
					
					start_offset = self.view.text_point(start_row, 0)
					end_offset = self.view.text_point(end_row+1, 0)
					block_region = sublime.Region(start_offset, end_offset)
					line = self.view.full_line(block_region)

					file_row = start_row
					#print("Sending: " + str(file_row))
					msg = "Updating " + start_line_contents
					RapidOutputView.printMessage(msg)
					file_row_str = str(file_row + 1)
				else:
					line = self.view.line(region) #expand the region for full line if no selection
					file_row_str = str(current_row + 1)
			else:
				line = region #get only the selected area
				file_row_str = str(current_row + 1)

			file_name = ""

			if self.view.file_name() != None:
				file_name = self.view.file_name().split("\\")[-1]
			
			line_str = self.view.substr(line)
			line_contents = "@" + file_name + ":" + file_row_str + "\n" + line_str + "\000"
			#print(line_contents)
			return line_contents

class RapidSettings():
	def __init__(self):
		self.path = ""
		self.full_path = ""
		self.project_settings = {}
		
		project_settings_found = False
		#Get path to grimrock folder		
		# Assume that there is only one root folder in the project and the folder is found on sublime.windows[0] 
		# TODO: if there will be more root folders, the project root must be set in settings file?
		for window in sublime.windows():
			for folder in window.folders():
				for root, dirs, files in os.walk(folder):
					for name in files:
						if name.endswith("sublime_proj"):
							self.full_path = os.path.abspath(os.path.join(root, name))
							self.path = os.path.dirname(self.full_path)
							#print("self.path: " + self.path)
							project_settings_found = True
							break
				if project_settings_found:
					break
			if project_settings_found:
				break
		
		if self.path != "":
			with open(self.full_path, "r") as project_settings_file:
				for line in project_settings_file:
					(key, val) = line.split("=")
					self.project_settings[key.strip()] = val.strip()	
		
	def getSettings(self):
		return self.project_settings

	def startupProjectExists(self):
		if "StartupProject" in self.project_settings:
			return True
		RapidOutputView.printMessage(self.project_settings)
		return False

	def getStartupFileName(self):
		if self.startupProjectExists():
			return self.project_settings["StartupProject"]
		return ""

	def getStartupPath(self):
		return self.path

	def getStartupFilePath(self):
		path = ""
		if self.startupProjectExists():
			startup_file_name = self.getStartupFileName()
			path = self.path + "\\" + startup_file_name			
		return path

	def getStartupFileContent(self):
		data = ""
		if self.startupProjectExists():
			path = self.getStartupFilePath()		
			with open(path, "r") as startup_project_file:
				data = startup_project_file.read()
		return data

class RapidCheckServerAndStartupProjectCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		print("Rapid Check Server")

		self.view.run_command('rapid_output_view_clear')


		#Check server and start it if needed
		#RapidConnect()

		#Check if startup project exists and if it has been modified
		startup_exists = False
		is_modified = False

		RapidOutputView.printMessage("Loading project settings...")
		settings = RapidSettings()

		#RapidOutputView.printMessage("Change directory to: " + settings.getStartupPath())
		#os.chdir(settings.getStartupPath())


		startup_path = settings.getStartupFilePath()

		if startup_path:
			startup_exists = True
			new_view = self.view.window().find_open_file(startup_path)
			if new_view != None and new_view.is_dirty():
				is_modified = True
		elif self.view.is_dirty():
			is_modified = True

		#clear output window
		#self.view.run_command('rapid_output_view_clear')

		#Send commands to server accordingly
		RapidConnectionThread.checkConnection()
		if startup_exists:
			#see if the startup project file is currently open and modified
			if is_modified:
				#file is open and modified
				RapidConnectionThread.instance.sendString("\nsys.restart()\000")
				line = "@" + settings.getStartupFileName() + ":1\n" + settings.getStartupFileContent() +"\000"
				RapidConnectionThread.instance.sendString(line)
			else:
				RapidOutputView.printMessage("Startup project: " + settings.getStartupFilePath())
				#file is either not open or open but unmodified
				RapidConnectionThread.instance.sendString("\nsys.loadProject([[" + settings.getStartupFilePath() + "]])\000")
		else:
			#if no startup project, run current page
			if is_modified:
				#file has not been saved - restart runtime engine and send code over
				RapidConnectionThread.instance.sendString("\nsys.restart()\000")
				line = "@" + self.view.file_name() + ":1\n" + self.view.substr(sublime.Region(0, self.view.size())) + "\000"
				RapidConnectionThread.instance.sendString(line)
			else:
				#file is up to date -> reload file - this is faster than sending the code
				RapidConnectionThread.instance.sendString("\nsys.loadProject([[" + self.view.file_name() + "]])\000")

class RapidConnect():
	def __init__(self):
		rapid_running = True

		rapid = subprocess.check_output("tasklist /FI \"IMAGENAME eq rapid.exe\" /FO CSV")
		#print(rapid)
		rapid_search = re.search(r'rapid.exe', rapid.decode("ISO-8859-1"))
		if rapid_search == None:
			rapid_debug = subprocess.check_output("tasklist /FI \"IMAGENAME eq rapid_d.exe\" /FO CSV")
			#print(rapid_debug)
			rapid_debug_search = re.search(r'rapid_d.exe', rapid_debug.decode("ISO-8859-1"))
			if rapid_debug_search == None:
				rapid_running = False

		if rapid_running:
			return

		RapidOutputView.printMessage("Starting rapid.exe")
		subprocess.Popen(r'c:\Work\projects\rapid\rapid.exe', cwd=r'c:\Work\projects\rapid')

# DEBUGGING STUFF, REMOVE AFTER DEVELOPMENT!!!

#For debugging use only, kill rapid exe instantly
class RapidKillCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		subprocess.call("taskkill /F /IM rapid.exe")
		RapidOutputView.printMessage("Server disconnected")