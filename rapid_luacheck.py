import sublime, sublime_plugin
import os, re, time
import tempfile

from .rapid import RapidConnectionThread
from .rapid_functionstorage import RapidFunctionStorage
from .rapid_output import RapidOutputView
from .rapid_parse import RapidSettings

g_tempName = ""

class RapidLuaCheckCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		global g_tempName
		if self.view.file_name():
			current_filename = self.view.file_name().replace("\\", "/")
			if current_filename.endswith(".lua"):

				RapidConnectionThread.checkConnection()
				line_contents = "@rapid_luacheck.py:1\n require(\"luacheck\")(\""+ current_filename +"\")\000"
				RapidConnectionThread.instance.sendString(line_contents)

				#open analyze_result.lua in new window
				result_file = os.path.abspath(os.path.join(RapidSettings().getStartupProjectPath(), "analyze_result.lua"))
				sublime.active_window().open_file(result_file)

				#TODO: open in temporary file
				
				# with tempfile.NamedTemporaryFile() as temp:
				# 	print("Temp name: " + temp.name)
				# 	g_tempName = temp.name
				# 	print("Global Temp name: " + g_tempName)

				# 	tfile = temp.name.replace("\\", "/")
				# 	RapidConnectionThread.checkConnection()
				# 	line_contents = "@rapid_luacheck.py:1\n require(\"luacheck\")(\""+ current_filename +"\",\"" + tfile + "\")\000"
				# 	RapidConnectionThread.instance.sendString(line_contents)
				# 	result_view = sublime.active_window().open_file(temp.name)
			else:
				RapidOutputView.printMessage("Static analysis is only possible for lua files!")

# class RapidLuaCheckModifiedListener(sublime_plugin.EventListener):
	# def on_load(self, view):
	# 	if view != None and view.file_name() != None:
	# 		if view.file_name() == 	g_tempName:
	# 			view.set_name(RapidOutputView.analyze_view_name)
	# 			print("huu")


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

			RapidOutputView.printMessage("Performing static analysis for all lua files in project...")
			RapidConnectionThread.checkConnection()
			line_contents = "@rapid_luacheck.py:1\n require(\"luacheck\")"+ files +"\000"
		
			RapidConnectionThread.instance.sendString(line_contents)

			#open analyze_result.lua in new window
			result_file = os.path.abspath(os.path.join(RapidSettings().getStartupProjectPath(), "analyze_result.lua"))
			sublime.active_window().open_file(result_file)