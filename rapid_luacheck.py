import sublime, sublime_plugin
import os

from .rapid import RapidConnectionThread
from .rapid_functionstorage import RapidFunctionStorage
from .rapid_output import RapidOutputView

class RapidLuaCheck():
	luaCheckLoaded = False

	@staticmethod
	def loadLuaCheck():
		if not RapidLuaCheck.luaCheckLoaded:
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
			RapidConnectionThread.checkConnection()
			line_contents = "@rapid_luacheck.py:1\n analyzeFile(\""+ current_filename +"\")\000"
			RapidConnectionThread.instance.sendString(line_contents)

class RapidLuaCheckAllCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		RapidLuaCheck.loadLuaCheck()
		if RapidFunctionStorage.luaFiles:
			files = ""
			for path in RapidFunctionStorage.luaFiles:
				path = path.replace("\\", "/")
				files += path + "|"

			RapidOutputView.printMessage("Performing static analysis for all lua files in project...")
			RapidConnectionThread.checkConnection()
			line_contents = "@rapid_luacheck.py:1\n analyzeFiles(\""+ files +"\")\000"
			RapidConnectionThread.instance.sendString(line_contents)