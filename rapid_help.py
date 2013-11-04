import sublime, sublime_plugin

from .rapid_output import RapidOutputView
from .rapid import RapidConnectionThread

class RapidHelpCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		cursor_pos = self.view.sel()[0].begin()
		region = self.view.word(cursor_pos)
		word = self.view.substr(region)

		RapidConnectionThread.checkConnection()
		line = "\nrequire(\"doc\"); doc.find([["+ word +"]])\000"
		RapidConnectionThread.instance.sendString(line)