import sublime, sublime_plugin
import re
import os
import sublime_api

from .edit import Edit

class RapidOutputView():
	name = "Server Output View"
	output = None
	opening = False

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
		return RapidOutputView.output

	@staticmethod
	def printMessage(msg):
		RapidOutputView.opening = True
		view = RapidOutputView.getOutputView()	
		
		if view.settings().get('syntax') != "Packages/Lua/Lua.tmLanguage":
			view.set_syntax_file("Packages/Lua/Lua.tmLanguage")
			
		with Edit(RapidOutputView.output) as edit:
			if not '\n' in msg:
				msg = msg + '\n'
			edit.append(msg)
			region = RapidOutputView.output.full_line(RapidOutputView.output.size())
			RapidOutputView.output.show(region)
		RapidOutputView.opening = False

	@staticmethod
	def isOpen():
		if RapidOutputView.output == None:
			output_view_found = False
			windows = sublime.windows()
			for window in windows:
				views = window.views()
				for view in views:
					if view.name() == RapidOutputView.name:
						output_view_found = True
						break
				if output_view_found:
					break
			return output_view_found

class RapidOutputViewClearCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		RapidOutputView.opening = True
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
		view = sublime.active_window().active_view()
		#view = self.window.active_view()
		if view.name() == RapidOutputView.name:
			sel = view.sel()
			r = sel[0]
			s = view.line(r)
			line = view.substr(s)
			view.run_command("expand_selection", {"to": "line"})

			file_name_and_row = re.search(r'[\w\.-]+.lua:\d{1,16}', line)
			if file_name_and_row:
				test = file_name_and_row.group().split(':')
				file_name = test[0]
				file_row = test[1]

				#print(file_name)
				#print(file_row)

				path_found = False
				path = None
				file_window = None

				for window in sublime.windows():
					for folder in window.folders():	

						
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
					#todo: check open files that are not in the folders yet!
					#print("path not found")
					return

				view = None
				for window in sublime.windows():
					view = window.find_open_file(path)
					if view != None:
						window.open_file(path+":"+file_row, sublime.ENCODED_POSITION)
						window.focus_view(view)
						break;
				if view == None:
					sublime.windows()[0].focus_group(0)
					view = file_window.open_file(path+":"+file_row, sublime.ENCODED_POSITION)
		# else:
		# 	system_command = args["command"] if "command" in args else None
		# 	if system_command:
		# 		system_args = dict({"event": args["event"]}.items() + args["args"].items())
		# 		self.view.run_command(system_command, system_args)

class RapidCloseOutputViewCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		#print("Rapid Close Output View command")
		if RapidOutputView.output != None:
			self.view.window().focus_view(RapidOutputView.output)
			self.view.window().run_command("close_file")
		else:
			for window in sublime.windows():
				for view in window.views():
					if view.name() == RapidOutputView.name:
						self.view.window().focus_view(view)
						self.view.window().run_command("close_file")
						break
						

class RapidOutputEventListener(sublime_plugin.EventListener):
	def on_query_context(self, view, key, operator, operand, match_all):
		if key == "close_server_output":
			for window in sublime.windows():
				for view in window.views():
					if view.name() == RapidOutputView.name:
						return True
		return False

class RapidFileOpenListener(sublime_plugin.EventListener):

	# empty files (except Server Output View) are always created on the focus_group(0)
	def on_new(self, view):
		print("on_new")
		if RapidOutputView.opening == False:
			window = sublime.active_window()
			window.focus_group(0)
		else:
			RapidOutputView.opening = False


	# loaded files are always brought to focus_group(0)
	def on_load(self, view):
		window = sublime.active_window()
		if window.active_group() != 0:
			active_view = window.active_view_in_group(0)
			active_group, active_view_index = window.get_view_index(active_view)
			#print(active_view_index)
			if active_view_index == -1:
				views = window.views_in_group(0)
				active_view_index = len(views)
			else:
				active_view_index = active_view_index + 1
			window.focus_group(0)
			window.set_view_index(view, 0, active_view_index)

#DEBUG: Double-click testing

# class MySpecialDoubleclickCommand(sublime_plugin.TextCommand):
#  	def run_(self, cmd, args):
#   		if self.view.name() == RapidOutputView.name:
#   			print("yippee-ki-yea!")
#   		else:
#   			system_command = args["command"] if "command" in args else None
#   			if system_command:
#   				system_args = dict({"event" : args["event"].items() | args["args"].items()})
#   				#self.view.run_command(self.view.id, system_command, system_args)
#   				#self.view.run_command(system_command, system_args)
#   				view_id = sublime.active_window().active_view().id()
#   				sublime_api.view_run_command(view_id, cmd, args)

# 	{
# 		"button": "button1", "count": 2,
# 		"press_command": "my_special_doubleclick",
# 		"press_args": {"command": "drag_select", "args": {"by": "words"}}
# 	}