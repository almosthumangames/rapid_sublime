import sublime, sublime_plugin
import os, re, time
import tempfile

from .rapid import RapidConnectionThread
from .rapid_functionstorage import RapidFunctionStorage
from .rapid_output import RapidOutputView
from .rapid_parse import RapidSettings

class RapidLuaCheckCommand(sublime_plugin.TextCommand):
	tempFileName = ""

	def run(self, edit):
		if self.view.file_name():
			current_filename = self.view.file_name().replace("\\", "/")
			if current_filename.endswith(".lua"):

				#TODO: set buffer name for temp file				
				with tempfile.NamedTemporaryFile() as temp:
					RapidLuaCheckCommand.tempFileName = temp.name
					tfile = temp.name.replace("\\", "/")
					RapidConnectionThread.checkConnection()
					line_contents = "@rapid_luacheck.py:1\n require(\"luacheck\")(\""+ current_filename +"\",\"" + tfile + "\")\000"
					RapidConnectionThread.instance.sendString(line_contents)
			else:
				RapidOutputView.printMessage("Static analysis is only possible for lua files!")

class RapidLuaCheckAllCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		settings = RapidSettings().getSettings()
		excluded = settings["ExcludedStaticAnalysisFolders"]
		
		if RapidFunctionStorage.luaFiles:
			files = "{"
			for path in RapidFunctionStorage.luaFiles:
				path = path.replace("\\", "/")
				addToPath = True
				
				for excluded_path in excluded:
					match = re.search(excluded_path, path)
					if match != None:
						addToPath = False
						break

				if addToPath == True:
					files += "\"" + path + "\","

			files = files[:-1] #remove last ","
			files += "}"

			#TODO: set buffer name for temp file				
			with tempfile.NamedTemporaryFile() as temp:
				RapidLuaCheckCommand.tempFileName = temp.name				
				tfile = temp.name.replace("\\", "/")
				RapidConnectionThread.checkConnection()
				line_contents = "@rapid_luacheck.py:1\n require(\"luacheck\")("+ files +",\"" + tfile + "\")\000"
				RapidConnectionThread.instance.sendString(line_contents)
				RapidOutputView.printMessage("Performing static analysis for all lua files in project...")

class RapidLuacheckLoadStaticAnalysisCommand(sublime_plugin.TextCommand):
	def run(self, edit):		
		with open(RapidLuaCheckCommand.tempFileName, 'r') as f:
			data = f.read()
			result_view = sublime.active_window().new_file()
			result_view.set_scratch(True)
			result_view.set_name(RapidOutputView.analyze_view_name)
			result_view.insert(edit, 0, data)