import sublime, sublime_plugin
import os, re


from .rapid import RapidConnectionThread
from .rapid_functionstorage import RapidFunctionStorage
from .rapid_output import RapidOutputView
from .rapid_parse import RapidSettings

class RapidLuaCheck():
	luaCheckLoaded = False

class RapidLuaCheckCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		if self.view.file_name():
			current_filename = self.view.file_name().replace("\\", "/")
			if current_filename.endswith(".lua"):
				RapidConnectionThread.checkConnection()
				line_contents = "@rapid_luacheck.py:1\n require(\"luacheck\")(\""+ current_filename +"\")\000"
				RapidConnectionThread.instance.sendString(line_contents)

				#open analyze_result.lua in new window
				result_file = os.path.abspath(os.path.join(RapidSettings().getStartupProjectPath(), "analyze_result.lua"))
				sublime.active_window().open_file(result_file)
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

			files = files[:-1]
			files += "}"

			print(files)

			RapidOutputView.printMessage("Performing static analysis for all lua files in project...")
			RapidConnectionThread.checkConnection()
			line_contents = "@rapid_luacheck.py:1\n require(\"luacheck\")"+ files +"\000"
		
			RapidConnectionThread.instance.sendString(line_contents)

			#open analyze_result.lua in new window
			result_file = os.path.abspath(os.path.join(RapidSettings().getStartupProjectPath(), "analyze_result.lua"))
			sublime.active_window().open_file(result_file)