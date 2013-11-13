import sublime, sublime_plugin
import re
import os

from .edit import Edit

class RapidOutputView():
	name = "Server Output View"
	output = None

	@staticmethod
	def getOutputView():
		if RapidOutputView.output == None:
			output_view_found = False
			windows = sublime.windows()
			for window in windows:
				views = window.views()
				for view in views:
					if view.name() == RapidOutputView.name:
						RapidOutputView.output = view
						output_view_found = True
						break
				if output_view_found:
					break

			if RapidOutputView.output == None:
				groups = sublime.windows()[0].num_groups()
				if groups < 2:
					sublime.windows()[0].set_layout( {"cols": [0.0, 1.0], "rows": [0.0, 0.8, 1.0], "cells": [[0,0,1,1], [0,1,1,2]]} )
				sublime.windows()[0].focus_group(1)
				RapidOutputView.output = sublime.windows()[0].new_file()
				RapidOutputView.output.set_read_only(True)
				RapidOutputView.output.set_scratch(True)
				RapidOutputView.output.set_name(RapidOutputView.name)
				sublime.windows()[0].focus_group(0)
				#output.settings().set('server_output', True)
		return RapidOutputView.output


	@staticmethod
	def printMessage(msg):
		view = RapidOutputView.getOutputView()		
		#view.set_syntax_file("Rapid.tmLanguage")
			
		with Edit(RapidOutputView.output) as edit:
			if not '\n' in msg:
				msg = msg + '\n'
			edit.append(msg)
			region = RapidOutputView.output.full_line(RapidOutputView.output.size())
			RapidOutputView.output.show(region)

class RapidOutputViewClearCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		view = RapidOutputView.getOutputView()
		with Edit(view) as edit:
			edit.erase(sublime.Region(0, RapidOutputView.output.size()))

class RapidOutputViewListener(sublime_plugin.EventListener):
	def on_close(self, view):
		if view.name() == RapidOutputView.name:
			RapidOutputView.output = None
			sublime.windows()[0].set_layout( {"cols": [0.0, 1.0], "rows": [0.0, 1.0], "cells": [[0,0,1,1]] } )

class RapidDoubleClick(sublime_plugin.WindowCommand):
	def run(self):
		view = self.window.active_view()
		if view.name() == RapidOutputView.name:
			#RapidOutputView.printMessage("Double clicked " + RapidOutputView.name)
			sel = view.sel()
			r = sel[0]
			s = view.line(r)
			line = view.substr(s)
			view.run_command("expand_selection", {"to": "line"})

			file_name_and_row = re.search(r'[\w\.-]+.lua:\d{1,16}', line)
			if file_name_and_row:
				#parse file name and row to separate variables
				test = file_name_and_row.group().split(':')
				file_name = test[0]
				file_row = test[1]

				path_found = False
				path = None
				file_window = None

				for window in sublime.windows():
					for folder in window.folders():	
						#print(folder)
						
						for root, dirs, files in os.walk(folder):
							if path_found:
								break
							for name in files:
								if name == file_name:
									path = os.path.abspath(os.path.join(root, name))
									#print(path)
									path_found = True
									file_window = window
									break

				if not path_found:
					return

				view = None
				for window in sublime.windows():
					view = window.find_open_file(path)
					if view != None:
						#focus on open file
						window.open_file(path+":"+file_row, sublime.ENCODED_POSITION)
						#print("File name: " + view.file_name())
						window.focus_view(view)
						break;
				if view == None:
					#print("file is not open in window")
					sublime.windows()[0].focus_group(0)
					view = file_window.open_file(path+":"+file_row, sublime.ENCODED_POSITION)
					#print("File name: " + view.file_name())
		# else:
			# system_command = args["command"] if "command" in args else None
			# if system_command:
			# 	system_args = dict({"event": args["event"]}.items() + args["args"].items())
			# 	self.view.run_command(system_command, system_args)

class RapidCloseOutputViewCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		if RapidOutputView.output != None:
			self.view.window().focus_view(RapidOutputView.output)
			self.view.window().run_command("close_file")

class RapidOutputEventListener(sublime_plugin.EventListener):
	def on_query_context(self, view, key, operator, operand, match_all):
		if key == "close_server_output":
			for window in sublime.windows():
				for view in window.views():
					if view.name() == RapidOutputView.name:
						return True
		return False