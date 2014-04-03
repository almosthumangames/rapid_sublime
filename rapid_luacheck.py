import sublime, sublime_plugin
import os, re


from .rapid import RapidConnectionThread
from .rapid_functionstorage import RapidFunctionStorage
from .rapid_output import RapidOutputView
from .rapid_parse import RapidSettings

class RapidLuaCheck():
	luaCheckLoaded = False

	@staticmethod
	def loadLuaCheck():
		rapid_sublime_dir = os.path.dirname(os.path.realpath(__file__))
		luacheck_path = os.path.abspath(os.path.join(rapid_sublime_dir, "rapid_luacheck.lua"))
		luacheck_path = luacheck_path.replace('\\', '/')
		luafile = open(luacheck_path, 'r').read()
		RapidConnectionThread.checkConnection()
		line_contents = "@rapid_luacheck.lua:1\n" + luafile + "\000"
		RapidConnectionThread.instance.sendString(line_contents)
		RapidLuaCheck.luaCheckLoaded = True

class RapidLuaCheckCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		if self.view.file_name():
			RapidLuaCheck.loadLuaCheck()
			current_filename = self.view.file_name().replace("\\", "/")
			if current_filename.endswith(".lua"):
				RapidConnectionThread.checkConnection()
				line_contents = "@rapid_luacheck.py:1\n analyzeFile(\""+ current_filename +"\")\000"
				RapidConnectionThread.instance.sendString(line_contents)

				#open analyze_result.lua in new window
				result_file = os.path.abspath(os.path.join(RapidSettings().getStartupProjectPath(), "analyze_result.lua"))
				sublime.active_window().open_file(result_file)
			else:
				RapidOutputView.printMessage("Static analysis is only possible for lua files!")

class RapidLuaCheckAllCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		RapidLuaCheck.loadLuaCheck()

		settings = RapidSettings().getSettings()
		excluded = settings["ExcludedStaticAnalysisFolders"]
		
		if RapidFunctionStorage.luaFiles:
			files = ""
			for path in RapidFunctionStorage.luaFiles:
				path = path.replace("\\", "/")
				addToPath = True
				
				for excluded_path in excluded:
					match = re.search(excluded_path, path)
					if match != None:
						addToPath = False
						break

				if addToPath == True:
					files += path + "|"

			RapidOutputView.printMessage("Performing static analysis for all lua files in project...")
			RapidConnectionThread.checkConnection()
			line_contents = "@rapid_luacheck.py:1\n analyzeFiles(\""+ files +"\")\000"
			RapidConnectionThread.instance.sendString(line_contents)

			#open analyze_result.lua in new window
			result_file = os.path.abspath(os.path.join(RapidSettings().getStartupProjectPath(), "analyze_result.lua"))
			sublime.active_window().open_file(result_file)