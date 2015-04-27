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
			self.excluded_folders = settings["ExcludedFolders"]
			
	def __init__(self, folders, timeout):
		threading.Thread.__init__(self)
		self.folders = folders
		self.timeout = timeout

		self.luaFuncPattern = re.compile('\s*function\s*')
		self.cppFuncPattern = re.compile("///\s")

		self.exclude_folders = False
		self.excluded_folders = []
		self.getExcludedFolders()

		self.save_method_signatures()
		#self.parse_now = False
		self.file_for_parsing = ""
		self.is_running = True

		RapidCollectorThread.instance = self

	#Save all method signatures from all project folders
	def save_method_signatures(self):
		for folder in self.folders:
			luafiles = []
			cppfiles = []
			fileLists = self.get_files_in_project(folder, luafiles, cppfiles)

			methodPattern = re.compile('function\s\w+[:\.](\w+)\((.*)\)')
			funcPattern = re.compile('function\s*(\w+)\s*\((.*)\)')

			for file_name in luafiles:
				functions = []
				findFunctions = []
				function_lines = self.findLua(file_name)
				for line in function_lines:
					matches = methodPattern.match(line)
					if matches:
						functions.append(Method(matches.group(1), matches.group(2), basename(file_name)))
						findFunctions.append(FunctionDefinition(matches.group(0)))
					else:
						matches = funcPattern.match(line)
						if matches:
							functions.append(Method(matches.group(1), matches.group(2), basename(file_name)))
							findFunctions.append(FunctionDefinition(matches.group(0)))
				RapidFunctionStorage.addAutoCompleteFunctions(functions, file_name)
				RapidFunctionStorage.addFindFunctions(findFunctions, file_name)
			
			for file_name in cppfiles:
				functions = []
				findFunctions = []
				function_lines = self.findCpp(file_name)
				for line in function_lines:
					# match global functions without return values, e.g. "/// foobar(x, y)"
					matches = re.match('///\s*(\w+)[\({](.*)[\)}]', line)
					if matches != None:
						functions.append(Method(matches.group(1), matches.group(2), ""))
						findFunctions.append(FunctionDefinition(line))
					else:
						# match global functions with return values, e.g. "/// baz = foobar(x, y)"
						matches = re.match('///\s*\w+\s*=\s*(\w+)[\({](.*)[\)}]', line)
						if matches != None:
							functions.append(Method(matches.group(1), matches.group(2), ""))
							findFunctions.append(FunctionDefinition(line))
						else:
							# match functions without return values, e.g. "/// Foo.bar(x, y)"
							matches = re.match('///\s*(\w+)[:\.](\w+)[\({](.*)[\)}]', line)
							if matches != None:
								functions.append(Method(matches.group(2), matches.group(3), matches.group(1)))
								findFunctions.append(FunctionDefinition(line))
							else:
								# match functions with return values, e.g. "/// baz = Foo.bar(x, y)"
								matches = re.match('///\s*\w+\s*=\s*(\w+)[:\.](\w+)[\({](.*)[\)}]', line)
								if matches != None:
									functions.append(Method(matches.group(2), matches.group(3), matches.group(1)))
									findFunctions.append(FunctionDefinition(line))
				RapidFunctionStorage.addAutoCompleteFunctions(functions, file_name)
				RapidFunctionStorage.addFindFunctions(findFunctions, file_name)

	def findLua(self, filepath):
		function_list = []
		#print(filepath)
		with open(filepath, 'r', encoding="ascii", errors="surrogateescape") as f:
			for line in f:
				matches = self.luaFuncPattern.match(line)
				if matches != None:
					function_list.append(line.strip())
		return function_list

	def findCpp(self, filepath):
		function_list = []
		#print(filepath)
		with open(filepath, 'r', encoding="ascii", errors="surrogateescape") as f:
			for line in f:
				matches = self.cppFuncPattern.match(line)
				if matches != None:
					function_list.append(line.strip())
		return function_list

	#Save method signatures from the given file
	def save_method_signature(self, file_name):
		functions = []
		findFunctions = []
		function_lines = self.findLua(file_name)
		methodPattern = re.compile('function\s\w+[:\.](\w+)\((.*)\)')
		funcPattern = re.compile('function\s*(\w+)\s*\((.*)\)')
		RapidFunctionStorage.removeAutoCompleteFunctions(file_name)
		RapidFunctionStorage.removeFindFunctions(file_name) 
		for line in function_lines:
			matches = methodPattern.match(line)
			if matches:
				functions.append(Method(matches.group(1), matches.group(2), basename(file_name)))
				findFunctions.append(FunctionDefinition(matches.group(0)))
			else:
				matches = funcPattern.match(line)
				if matches:
					functions.append(Method(matches.group(1), matches.group(2), basename(file_name)))
					findFunctions.append(FunctionDefinition(matches.group(0)))
		RapidFunctionStorage.addAutoCompleteFunctions(functions, file_name)
		RapidFunctionStorage.addFindFunctions(findFunctions, file_name)

	def get_files_in_project(self, folder, luaFileList, cppFileList):
		for root, dirs, files in os.walk(folder, True):

			# prune excluded folders from search
			if self.exclude_folders:
				if self.excluded_folders:
					for excluded_folder in self.excluded_folders:
						if excluded_folder in dirs:
							#print("Pruning excluded folder " + excluded_folder)
							dirs.remove(excluded_folder)
						
			for name in files:
				if name.endswith(".lua"):
					full_path = os.path.abspath(os.path.join(root, name))
					luaFileList.append(full_path)
					#add lua file path for static analyzer
					RapidFunctionStorage.addLuaFile(full_path) 
				if name.endswith(".cpp"):
					full_path = os.path.abspath(os.path.join(root, name))
					cppFileList.append(full_path)

	#def run(self):
		# #TODO: change this to use callback instead of polling
		# while self.is_running:
		# 	if self.parse_now and self.file_for_parsing:
		# 		self.save_method_signature(self.file_for_parsing)
		# 		self.parse_now = False
		# 	time.sleep(0.1)

	def callback(self):
		#print("Rapid MethodComplete: saving method signature")
		self.save_method_signature(self.file_for_parsing)

	def parseAutoCompleteData(self, view):
		self.file_for_parsing = view.file_name()
		#parse only *.lua files at runtime
		if self.file_for_parsing.endswith(".lua"):
			#print("calling methodcomplete callback")
			sublime.set_timeout(self.callback, 100)
			#self.parse_now = True

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
		startTime = time.time()

		settings = RapidSettings().getSettings()		
		if "ParseAutoCompleteOnSave" in settings:
			RapidCollector.parseAutoComplete = settings["ParseAutoCompleteOnSave"]
		
		folders = sublime.active_window().folders()
		if RapidCollectorThread.instance != None:
			RapidCollectorThread.instance.stop()
			RapidCollectorThread.instance.join()
		RapidCollectorThread.instance = RapidCollectorThread(folders, 30)

		RapidCollectorThread.instance.start()
		print("Took " + str(time.time() - startTime) + " seconds.")
