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

from .rapid_functionstorage import RapidFunctionStorage
from .rapid_functionstorage import Method
from .rapid_functionstorage import FunctionDefinition

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
				findFunctions = []
				function_lines = self.findLua(file_name)
				for line in function_lines:
					if "function" in line:
						matches = re.search('function\s\w+[:\.](\w+)\((.*)\)', line)
						matches2 = re.search('function\s*(\w+)\s*\((.*)\)', line)
						if matches != None:
							functions.append(Method(matches.group(1), matches.group(2), basename(file_name)))
							findFunctions.append(FunctionDefinition(matches.group(0)))
						elif matches2 != None:
							functions.append(Method(matches2.group(1), matches2.group(2), basename(file_name)))
							findFunctions.append(FunctionDefinition(matches2.group(0)))
				RapidFunctionStorage.addAutoCompleteFunctions(functions, file_name)
				RapidFunctionStorage.addFindFunctions(findFunctions, file_name)
			
			for file_name in cppfiles:
				functions = []
				findFunctions = []
				function_lines = self.findCpp(file_name)
				for line in function_lines:
					line = line.strip()
					func = line.replace("///", "")
					#matches = re.search('(\w+)[:\.](\w+)\((.*)\)', func)
					matches = re.search('(\w+)[:\.](\w+)[\({](.*)[\)}]', func)
					if matches != None:
						functions.append(Method(matches.group(2), matches.group(3), matches.group(1)))
						findFunctions.append(FunctionDefinition(line))
				RapidFunctionStorage.addAutoCompleteFunctions(functions, file_name)
				RapidFunctionStorage.addFindFunctions(findFunctions, file_name)

	def findLua(self, filepath):
		function_list = []
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
								line = str(func, "utf-8").strip()
								function_list.append(line)
								break
							func.append(bytes3[0])
		return function_list

	def findCpp(self, filepath):
		function_list = []
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
								line = str(func, "utf-8").strip()
								function_list.append(line)
								break
							func.append(bytes3[0])
		return function_list

	#Save method signatures from the given file
	def save_method_signature(self, file_name):
		functions = []
		findFunctions = []
		function_lines = self.findLua(file_name)
		RapidFunctionStorage.removeAutoCompleteFunctions(file_name)
		RapidFunctionStorage.removeFindFunctions(file_name) 
		for line in function_lines:
			if "function" in line:
				matches = re.search('function\s\w+[:\.](\w+)\((.*)\)', line)
				matches2 = re.search('function\s*(\w+)\s*\((.*)\)', line)
				if matches != None:
					functions.append(Method(matches.group(1), matches.group(2), basename(file_name)))
					findFunctions.append(FunctionDefinition(matches.group(0)))
				elif matches2 != None:
					functions.append(Method(matches2.group(1), matches2.group(2), basename(file_name)))
					findFunctions.append(FunctionDefinition(matches2.group(0)))
		RapidFunctionStorage.addAutoCompleteFunctions(functions, file_name)
		RapidFunctionStorage.addFindFunctions(findFunctions, file_name)

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
				if name.endswith(".lua"):
					full_path = os.path.abspath(os.path.join(root, name))
					fileList.append(full_path)
					#add lua file path for static analyzer
					RapidFunctionStorage.addLuaFile(full_path) 
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
				if name.endswith(".cpp"):
					full_path = os.path.abspath(os.path.join(root, name))
					fileList.append(full_path)
		return fileList

	def run(self):
		#TODO: change this to use callback instead of polling
		while self.is_running:
			if self.parse_now and self.file_for_parsing:
				self.save_method_signature(self.file_for_parsing)
				self.parse_now = False
			time.sleep(0.1)

	def parseAutoCompleteData(self, view):
		self.file_for_parsing = view.file_name()
		#parse only *.lua files at runtime
		if self.file_for_parsing.endswith(".lua"):
			self.parse_now = True

	def stop(self):
		self.is_running = False

class RapidCollector(sublime_plugin.EventListener):
	applyAutoComplete = False
	parseAutoComplete = False

	def on_post_save(self, view):
		if RapidCollector.parseAutoComplete:
			RapidCollectorThread.instance.parseAutoCompleteData(view)

	def on_query_completions(self, view, prefix, locations):
		if RapidCollector.applyAutoComplete:
			RapidCollector.applyAutoComplete = False
			if view.file_name() != None and '.lua' in view.file_name():
				return RapidFunctionStorage.getAutoCompleteList(prefix)
		completions = []
		return (completions, sublime.INHIBIT_EXPLICIT_COMPLETIONS)
	
class RapidAutoCompleteCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		RapidCollector.applyAutoComplete = True
		self.view.run_command('auto_complete')

class RapidStartCollectorCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		print("Collecting function definitions for autocomplete...")

		settings = RapidSettings().getSettings()		
		if "ParseAutoCompleteOnSave" in settings:
			RapidCollector.parseAutoComplete = settings["ParseAutoCompleteOnSave"]
		
		folders = sublime.active_window().folders()
		if RapidCollectorThread.instance != None:
			RapidCollectorThread.instance.stop()
			RapidCollectorThread.instance.join()
		RapidCollectorThread.instance = RapidCollectorThread(folders, 30)
		RapidCollectorThread.instance.start()