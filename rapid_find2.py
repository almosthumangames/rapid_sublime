import sublime, sublime_plugin
import os
import re
import io

import time

from .rapid_output import RapidOutputView
from .rapid_parse import RapidSettings
from .rapid_functionstorage import RapidFunctionStorage

class RapidFind2Command(sublime_plugin.TextCommand):
	folders_fetched = False
	exclude_folders = False
	excluded_folders = []

	def getExcludedFolders(self):
		if not self.folders_fetched:
			settings = RapidSettings().getSettings()
			sublime_project_path = RapidSettings().getStartupProjectPath()
			if "ExcludeFoldersInFind" in settings:
				#true/false if folders are excluded
				self.exclude_folders = settings["ExcludeFoldersInFind"]
			if "ExcludedFolders" in settings:
				#list of excluded folders
				excluded = settings["ExcludedFolders"]
				for excluded_folder in excluded:
					self.excluded_folders.append(os.path.abspath(os.path.join(sublime_project_path, excluded_folder)))
			# for excluded_folder in self.excluded_folders:
			# 	print("Excluded folder change check: " + excluded_folder)
			self.folders_fetched = True

	def run(self, edit):
		self.getExcludedFolders()
		cursor_pos = self.view.sel()[0].begin()
		
		region = self.view.word(cursor_pos)
		pattern = self.view.substr(region)
		#RapidOutputView.printMessage("Pattern is: " + pattern)

		region2 = self.view.line(cursor_pos)
		line = self.view.substr(region2)
		words = line.split()
		#RapidOutputView.printMessage("Words are: " + str(words))

		for word in words:
			if "*" in word:
				#Handle edge cases for class find
				if (pattern in word or 
					"*\n" in pattern or "* " in pattern or 
					"\n*" in pattern or " *" in pattern):
					pattern = word
					break

		find_class_methods = False
		if "*" in pattern and "." in pattern:
			find_class_methods = True
		
		pattern = pattern.lower().strip()

		if find_class_methods:
			self.findClass(pattern)
		elif len(pattern) > 0:
			self.find(pattern)

	##########################################
	# Find word(s) from function definitions #
	##########################################

	def find(self, pattern):	
		pattern = '.*'+pattern+'.*[\({].*[\)}]'
		#print("find word(s), pattern: " + pattern)

		functions = RapidFunctionStorage.getFindFunctions()
		for func in functions:
			match = re.search(pattern, func.lower())
			if match != None:
				func = func.strip()
				RapidOutputView.printMessage(func)


	############################################
	# Find class(es) from function definitions #
	############################################

	def findClass(self, pattern):
		#convert wildcards to regular expression
		pattern = pattern.replace('.', '[\.:]').replace('*', '.*')
		search_pattern = pattern + '[\({].*[\)}]'		
		#print("find class, pattern: " + pattern)
		#print("find class, search pattern: " + search_pattern)

		functions = RapidFunctionStorage.getFindFunctions()
		for func in functions:
			match = re.search(search_pattern, func.lower())
			if match != None:
				func = func.strip()
				RapidOutputView.printMessage(func)