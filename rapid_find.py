import sublime, sublime_plugin
import os
import re

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
		
		pattern = pattern.lower()

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

	def findCpp(self, filepath, pattern):
		f = open(filepath, encoding='utf-8').read()
		function_list = re.findall('///.*\n', f)
		for func in function_list:
			lower_line = func.lower()
			match = re.search(pattern, lower_line)
			if match != None:
				func = func.replace("///", "").strip()
				RapidOutputView.printMessage(func)

	def findLua(self, filepath, pattern):
		f = open(filepath, encoding='utf-8').read()
		function_list = re.findall('function.*\n', f)
		for func in function_list:
			lower_line = func.lower()
			match = re.search(pattern, lower_line)
			if match != None:
				line = func.strip()
				RapidOutputView.printMessage(func)

	############################################
	# Find class(es) from function definitions #
	############################################

	def findClass(self, pattern):
		#full_time1 = time.clock()

		#convert wildcards to regular expression
		pattern = pattern.replace('.', '[\.:]').replace('*', '.*')
		search_pattern = '\s' + pattern + '\(.*\)'
		
		for folder in sublime.active_window().folders():
			for root, dirs, files in os.walk(folder):

				if self.exclude_folders:
					for excluded_folder in self.excluded_folders:
						if root.startswith(excluded_folder):
							continue

				for name in files:
					if name.endswith("cpp"):
						full_path = os.path.abspath(os.path.join(root, name))
						self.findClassCpp(full_path, search_pattern)
					elif name.endswith("lua"):
						full_path = os.path.abspath(os.path.join(root, name))
						self.findClassLua(full_path, search_pattern)

		#full_time2 = time.clock()
		#print("Whole op took: " + str(full_time2-full_time1))

	def findClassCpp(self, filepath, pattern):
		f = open(filepath, "r").read()
		function_list = re.findall('///.*\n', f)
		for func in function_list:
			lower_line = func.lower()
			match = re.search(pattern, lower_line)
			if match != None:
				func = func.replace("///", "").strip()
				RapidOutputView.printMessage(func)

	def findClassLua(self, filepath, pattern):
		f = open(filepath, "r").read()
		function_list = re.findall('function.*\n', f)
		for func in function_list:
			lower_line = func.lower()
			match = re.search(pattern, lower_line)
			if match != None:
				RapidOutputView.printMessage(func)
