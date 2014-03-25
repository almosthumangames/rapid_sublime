# This file is based on the MySignature Sublime Text Plugin
# Modified to work with Lua files and automatically load function signatures at startup  

#Original header comments:

#-----------------------------------------------------------------------------------
# MySignature Sublime Text Plugin
# Author: Elad Yarkoni
# Version: 1.0
# Description: Sublime text autocomplete improvements: 
#       - showing javascript methods with parameters
#-----------------------------------------------------------------------------------

import sublime, sublime_plugin
import os, re, threading
import time

from os.path import basename
from .rapid_output import RapidOutputView
from .rapid_parse import RapidSettings

class Method:
	_name = ""
	_signature = ""
	_filename = ""
	
	def __init__(self, name, signature, filename):
		self._name = name
		self._filename = filename;
		self._signature = signature

	def name(self):
		return self._name

	def signature(self):
		return self._signature
  
	def filename(self):
		return self._filename

class RapidCollectorThread(threading.Thread):
	instance = None

	def getExcludedFolders(self):
		settings = RapidSettings().getSettings()	
		sublime_project_path = RapidSettings().getStartupProjectPath()	
		if "ExcludeFoldersInFind" in settings:
			self.exclude_folders = settings["ExcludeFoldersInFind"]
		if "ExcludedFolders" in settings:
			#list of excluded folders
			excluded = settings["ExcludedFolders"]
			for excluded_folder in excluded:
				self.excluded_folders.append(os.path.abspath(os.path.join(sublime_project_path, excluded_folder)))		
		# for excluded_folder in self.excluded_folders:
		# 	print("Methodcomplete excluded folder change check: " + excluded_folder)
			
	def __init__(self, folders, timeout):
		threading.Thread.__init__(self)
		self.folders = folders
		self.timeout = timeout

		self.exclude_folders = False
		self.excluded_folders = []
		self.getExcludedFolders()

		self.save_method_signatures()
		self.parse_now = False
		self.file_for_parsing = ""
		self.is_running = True

		
		RapidCollectorThread.instance = self

	#Save all method signatures from all project folders
	def save_method_signatures(self):
		for folder in self.folders:
			luafiles = self.get_lua_files(folder)
			cppfiles = self.get_cpp_files(folder)
			
			for file_name in luafiles:
				functions = []
				file_lines = open(file_name, encoding='utf-8').read()
				#file_lines = open(file_name, 'r')
				for line in file_lines:
					if "function" in line:
						matches = re.search('function\s\w+[:\.](\w+)\((.*)\)', line)
						matches2 = re.search('function\s*(\w+)\s*\((.*)\)', line)
						if matches != None:
							functions.append(Method(matches.group(1), matches.group(2), basename(file_name)))
						elif matches2 != None:
							functions.append(Method(matches2.group(1), matches2.group(2), basename(file_name)))
				RapidFunctionStorage.addFunctions(functions, file_name)
			
			for file_name in cppfiles:
				functions = []
				file_lines = open(file_name, "r").read()
				function_list = re.findall('///.*\(.*\).*\n', file_lines)
				for func in function_list:
					func = func.replace("///", "").strip()
					matches = re.search('(\w+)[:\.](\w+)\((.*)\)', func)
					if matches != None:
						functions.append(Method(matches.group(2), matches.group(3), matches.group(1)))
				RapidFunctionStorage.addFunctions(functions, file_name)

	#Save method signatures from the given file
	def save_method_signature(self, file_name):
		functions = []
		file_lines = open(file_name, 'r')
		for line in file_lines:
			if "function" in line:
				matches = re.search('function\s\w+[:\.](\w+)\((.*)\)', line)
				matches2 = re.search('function\s*(\w+)\s*\((.*)\)', line)
				if matches != None:
					functions.append(Method(matches.group(1), matches.group(2), basename(file_name)))
				elif matches2 != None:
					functions.append(Method(matches2.group(1), matches2.group(2), basename(file_name)))
		RapidFunctionStorage.addFunctions(functions, file_name)

	def get_lua_files(self, folder, *args):
		fileList = []
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
				if name.endswith("lua"):
					full_path = os.path.abspath(os.path.join(root, name))
					fileList.append(full_path)
		return fileList

	def get_cpp_files(self, folder, *args):
		fileList = []
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
					fileList.append(full_path)
		return fileList

	def run(self):
		while self.is_running:
			if self.parse_now and self.file_for_parsing:
				self.save_method_signature(self.file_for_parsing)
				self.parse_now = False
			time.sleep(0.1)

	def parseAutoCompleteData(self, view):
		self.file_for_parsing = view.file_name()
		#parse only *.lua files at runtime
		if self.file_for_parsing.endswith("lua"):
			self.parse_now = True

	def stop(self):
		self.is_running = False

class RapidFunctionStorage():
	funcs = {}

	@staticmethod
	def addFunctions(functions, filename):
		RapidFunctionStorage.funcs[filename] = functions

	@staticmethod
	def removeFunctions(filename):
		del RapidFunctionStorage.funcs[filename]

	@staticmethod
	def getAutoCompleteList(word):
		autocomplete_list = []
		for key in RapidFunctionStorage.funcs:
			functions = RapidFunctionStorage.funcs[key]
			for method_obj in functions:
				if word.lower() in method_obj.name().lower():
					
					#parse method variables
					variables = method_obj.signature().split(", ")
					signature = ""
					index = 1
					for variable in variables:
						signature = signature + "${"+str(index)+":"+variable+"}"
						if index < len(variables):
							signature = signature + ", "
						index = index+1

					method_str_to_show = method_obj.name() + '(' + method_obj.signature() +')'
					method_str_to_append = method_obj.name() + '(' + signature + ')'
					method_file_location = method_obj.filename();

					autocomplete_list.append((method_str_to_show + '\t' + method_file_location, method_str_to_append)) 
		return autocomplete_list	

class RapidCollector(sublime_plugin.EventListener):
	applyAutoComplete = False
	parseAutoComplete = False

	# def on_post_save(self, view):
	# 	if RapidCollector.parseAutoComplete:
	# 		RapidCollectorThread.instance.parseAutoCompleteData(view)

	# def on_query_completions(self, view, prefix, locations):
	# 	if RapidCollector.applyAutoComplete:
	# 		RapidCollector.applyAutoComplete = False
	# 		if view.file_name() != None and '.lua' in view.file_name():
	# 			return RapidFunctionStorage.getAutoCompleteList(prefix)
	# 	completions = []
	# 	return (completions, sublime.INHIBIT_EXPLICIT_COMPLETIONS)
	
class RapidAutoCompleteCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		RapidCollector.applyAutoComplete = True
		self.view.run_command('auto_complete')

class RapidStartCollectorCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		print("huu")
		# print("Collecting function definitions for autocomplete...")

		# settings = RapidSettings().getSettings()		
		# if "ParseAutoCompleteOnSave" in settings:
		# 	RapidCollector.parseAutoComplete = settings["ParseAutoCompleteOnSave"]
		
		# folders = self.view.window().folders()
		# if RapidCollectorThread.instance != None:
		# 	RapidCollectorThread.instance.stop()
		# 	RapidCollectorThread.instance.join()
		# RapidCollectorThread.instance = RapidCollectorThread(folders, 30)
		# RapidCollectorThread.instance.start()