import sublime, sublime_plugin
import json
import os

from .rapid_output import RapidOutputView

class RapidSettings():

	#TODO: settings are parsed once per window?  

	def __init__(self):
		self.project_settings = {}
		self.project_filename = ""
		self.full_path = ""
		self.sublime_project_path = ""
		self.rapid_path_win = ""
		self.rapid_path_osx = ""

		#parse project path
		sublime_full_project_path = sublime.active_window().project_file_name()
		if sublime_full_project_path == None:
			# try to find sublime project file from folders
			folders = sublime.active_window().folders()
			for folder in folders:
				for root, dirs, files in os.walk(folder):		
					for name in files:
						if name.endswith("sublime-project"):
							sublime_full_project_path = os.path.abspath(os.path.join(root, name))
							break
					if sublime_full_project_path != None:
						break
				if sublime_full_project_path != None:
						break
		if sublime_full_project_path == None:			
			print("No Sublime Text project file (.sublime-project) found!")
			return

		#split project path and filename
		self.sublime_project_path, sublime_project_filename = os.path.split(sublime_full_project_path)
		
		#parse rapid settings full path
		rapid_sublime_found = False
		for root, dirs, files in os.walk(self.sublime_project_path):
			for name in files:
				if name.endswith("rapid_sublime"):
					self.full_path = os.path.abspath(os.path.join(self.sublime_project_path, name))
					#RapidOutputView.printMessage("Rapid_Sublime full path: " + self.full_path)
					rapid_sublime_found = True
					break
			if rapid_sublime_found:
				break

		if self.full_path != "":
			json_data = open(self.full_path).read()
			self.project_settings = json.loads(json_data)
			#print(json_data)

	def getSettings(self):
		return self.project_settings

	def startupProjectExists(self):
		if "StartupProject" in self.project_settings:
			return True
		return False

	def getStartupProjectPath(self):
		return self.sublime_project_path

	def getStartupFilePath(self):
		if self.startupProjectExists():
			return os.path.abspath(os.path.join(self.sublime_project_path, self.project_settings["StartupProject"]))
		return ""

	def getStartupFileContent(self):
		data = ""
		if self.startupProjectExists():	
			with open(self.getStartupFilePath(), "r") as startup_project_file:
				data = startup_project_file.read()
		return data
