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
				#output.settings().set('server_output', True)
		return RapidOutputView.output


	@staticmethod
	def printMessage(msg):
		output = RapidOutputView.getOutputView()	
		#sublime.active_window().focus_view(output)
		with Edit(output) as edit:
			if not '\n' in msg:
				msg = msg + '\n'
			edit.append(msg)
			region = output.full_line(output.size())
			output.show(region)

class RapidOutputViewClearCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		output = RapidOutputView.getOutputView()
		with Edit(output) as edit:
			edit.erase(sublime.Region(0, output.size()))


class RapidOutputViewListener(sublime_plugin.EventListener):
	def on_close(self, view):
		if view.name() == RapidOutputView.name:
			RapidOutputView.output = None
			#print(view.name() + " was closed")

class RapidDoubleClick(sublime_plugin.WindowCommand):
	def run(self):
		view = self.window.active_view()
		if(view.name() == RapidOutputView.name):
			#RapidOutputView.printMessage("Double clicked " + RapidOutputView.name)
			sel = view.sel()
			r = sel[0]
			s = view.line(r)
			line = view.substr(s)
	
			file_name_and_row = re.search(r'[\w\.-]+.lua:\d{1,16}', line)
			if file_name_and_row:
				#draw line under the clicked filename and row
				underline_region = view.find(file_name_and_row.group(), s.begin())
				view.add_regions("doubleclick", [underline_region], "string","", sublime.DRAW_SOLID_UNDERLINE|sublime.DRAW_NO_FILL|sublime.DRAW_NO_OUTLINE)

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

#STUFF UNDER TESTING, BREAKS EVERYTHING, HANDLE WITH CARE!

class RapidOutputView2():
	name = "Server Output View"
	output = None

	@staticmethod
	def getOutputView():
		if RapidOutputView2.output == None:
			RapidOutputView2.output = sublime.windows()[0].get_output_panel("server_output")
		return RapidOutputView2.output
			
	@staticmethod
	def printMessage(msg):
		print("rapid output view 2 print message")
		output = RapidOutputView2.getOutputView()
		print("rapid output view 2 got view")
		view = sublime.active_window().active_view()
		print("rapid output view 2 show panel")
		view.run_command("show_panel", {"panel": "output.server_output"})
		view.set_read_only(False)
		view.run_command("append", { "characters": msg })
		view.set_read_only(True)

class RapidTest2Command(sublime_plugin.WindowCommand):
	def run(self):
		self.output_view = self.window.get_output_panel("server_output")
		self.window.run_command("show_panel", {"panel": "output.server_output"})

		self.output_view.set_read_only(False)
		self.output_view.run_command("append", { "characters": "Hello World!" })
		self.output_view.set_read_only(True)