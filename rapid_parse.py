import sublime, sublime_plugin
import json
import os

from .rapid_output import RapidOutputView

class RapidSettings():
	def __init__(self):
		self.project_settings = {}
		self.project_filename = ""
		self.path = ""
		self.full_path = ""

		project_settings_found = False
		for window in sublime.windows():
			for folder in window.folders():
				for root, dirs, files in os.walk(folder):
					for name in files:
						if name.endswith("rapid_sublime"):
							self.full_path = os.path.abspath(os.path.join(root, name))
							self.path = os.path.dirname(self.full_path)
							self.project_filename = name
							project_settings_found = True
							break
				if project_settings_found:
					break
			if project_settings_found:
				break

		if self.path != "":
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
		return self.path

	def getStartupFilePath(self):
		if self.startupProjectExists():
			return self.project_settings["StartupProject"]
		return ""

	def getStartupFileContent(self):
		data = ""
		if self.startupProjectExists():	
			with open(self.getStartupFilePath(), "r") as startup_project_file:
				data = startup_project_file.read()
		return data