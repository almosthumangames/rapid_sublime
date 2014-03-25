import sublime, sublime_plugin
import os
import re
import io

import time

from .rapid_output import RapidOutputView
from .rapid_parse import RapidSettings

class RapidFindCommand(sublime_plugin.TextCommand):
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
		#full_time1 = time.clock()
		pattern = '.*'+pattern+'.*\(.*\)'

		#print("find word(s), pattern: " + pattern)

		for folder in sublime.active_window().folders():		
			for root, dirs, files in os.walk(folder):
				checkFolder = True
				if self.exclude_folders:
					for excluded_folder in self.excluded_folders:
						if root.lower().startswith(excluded_folder.lower()):			
							checkFolder = False 
							break
					if not checkFolder:
					 	continue

				for name in files:
					if name.endswith("cpp"):
						full_path = os.path.abspath(os.path.join(root, name))
						self.findCpp(full_path, pattern)
					elif name.endswith("lua"):
						full_path = os.path.abspath(os.path.join(root, name))
						self.findLua(full_path, pattern)
		#full_time2 = time.clock()
		#print("Whole op took: " + str(full_time2-full_time1))

	############################################
	# Find class(es) from function definitions #
	############################################

	def findClass(self, pattern):
		#full_time1 = time.clock()
		#convert wildcards to regular expression
		pattern = pattern.replace('.', '[\.:]').replace('*', '.*')
		search_pattern = '\s' + pattern + '\(.*\)'
		
		#print("find class, search pattern: " + search_pattern)

		for folder in sublime.active_window().folders():
			for root, dirs, files in os.walk(folder):

				if self.exclude_folders:
					for excluded_folder in self.excluded_folders:
						if root.startswith(excluded_folder):
							continue

				for name in files:
					if name.endswith("cpp"):
						full_path = os.path.abspath(os.path.join(root, name))
						self.findCpp(full_path, search_pattern)
						#self.findClassCpp(full_path, search_pattern)
					elif name.endswith("lua"):
						full_path = os.path.abspath(os.path.join(root, name))
						self.findLua(full_path, search_pattern)
						#self.findClassLua(full_path, search_pattern)
		#full_time2 = time.clock()
		#print("Whole op took: " + str(full_time2-full_time1))

	#######################
	# Actual find methods #
	#######################

	def findCpp(self, filepath, pattern):
		with open(filepath, 'rb') as f:
			while 1:
				bytes = f.read(1)
				if not bytes:
					break
				if bytes == b'/':
					bytes2 = f.read(2)
					if bytes2 == b'//':
						func = bytearray()
						func.append(bytes[0])
						func.append(bytes2[0])
						func.append(bytes2[1])
						while 1:
							bytes3 = f.read(1)
							if not bytes3:
								break
							if bytes3 == b'\r' or bytes3 == b'\n':
								self.findPatternCpp(func, pattern)
								break
							func.append(bytes3[0])

	def findPatternCpp(self, func, pattern):
		line = str(func, "utf-8").strip()
		match = re.search(pattern, line.lower())
		if match != None:
			line = line.replace("///", "").strip()
			RapidOutputView.printMessage(line)

	def findLua(self, filepath, pattern):
		with open(filepath, 'rb') as f:
			while 1:
				bytes = f.read(1)
				if not bytes:
					break
				if bytes == b'f':
					bytes2 = f.read(7)
					if bytes2 == b'unction':
						func = bytearray()
						func.append(bytes[0])
						func.append(bytes2[0])
						func.append(bytes2[1])
						func.append(bytes2[2])
						func.append(bytes2[3])
						func.append(bytes2[4])
						func.append(bytes2[5])
						func.append(bytes2[6])
						while 1:
							bytes3 = f.read(1)
							if not bytes3:
								break
							if bytes3 == b'\r' or bytes3 == b'\n':
								self.findPatternLua(func, pattern)
								break
							func.append(bytes3[0])

	def findPatternLua(self, func, pattern):
		line = str(func, "utf-8").strip()
		match = re.search(pattern, line.lower())
		if match != None:
			line = line.strip()
			RapidOutputView.printMessage(line)
