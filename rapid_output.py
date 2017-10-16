import sublime, sublime_plugin
import re
import os
import sublime_api

class RapidOutputView():
	
	name = "Rapid Output"
	analyze_view_name = "Analyze Result"
	analyze_file_name = "analyze_result.lua"

	messageQueue = []

	@classmethod
	def getOutputView(self, create):
		for window in sublime.windows():
			for view in window.views():
				if view.name() == RapidOutputView.name:
					return view

		# create new view
		if create:
			window = sublime.active_window()
			activeView = window.active_view()
			groups = window.num_groups()
			if groups < 2:
				window.set_layout( {"cols": [0.0, 1.0], "rows": [0.0, 0.8, 1.0], "cells": [[0,0,1,1], [0,1,1,2]]} )
			window.focus_group(1)
			outputView = window.new_file()
			outputView.set_read_only(True)
			outputView.set_scratch(True)
			outputView.set_name(RapidOutputView.name)
			window.set_view_index(outputView, 1, 0)
			window.focus_view(activeView)
			#if outputView.settings().get('syntax') != "Packages/Lua/Lua.tmLanguage":
			outputView.set_syntax_file("Packages/Lua/Lua.tmLanguage")		
			return outputView
			
		return None
		
	@classmethod
	def printMessage(self, msg):
		RapidOutputView.messageQueue.append(msg)
		if len(RapidOutputView.messageQueue) == 1:
			sublime.set_timeout(RapidOutputView.callback, 100)
			
	@classmethod
	def callback(self):
		view = RapidOutputView.getOutputView(True)
		while len(RapidOutputView.messageQueue) > 0:
			msg = RapidOutputView.messageQueue.pop(0)
			view.run_command("rapid_output_view_insert", {"msg": msg } )
			
class RapidOutputViewInsertCommand(sublime_plugin.TextCommand):
	def run(self, edit, msg):
		view = self.view

		if not '\n' in msg:
			msg = msg + '\n'
		
		#if re.search("Static analysis done", msg):
		#	self.view.window().run_command("rapid_luacheck_load_static_analysis")
		#	return

		view.set_read_only(False)
		view.insert(edit, view.size(), msg)
		view.set_read_only(True)

		region = view.full_line(view.size())
		view.show(region)

class RapidOutputViewClearCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		view = RapidOutputView.getOutputView(True)
		if view != None:
			view.set_read_only(False)
			view.erase(edit, sublime.Region(0, view.size()))
			view.set_read_only(True)

# class RapidOutputViewListener(sublime_plugin.EventListener):
# 	def on_close(self, view):
# 		if view.name() == RapidOutputView.name:
# 			sublime.active_window().set_layout( {"cols": [0.0, 1.0], "rows": [0.0, 1.0], "cells": [[0,0,1,1]] } )

class RapidDoubleClick(sublime_plugin.WindowCommand):
	def run(self):
		view = sublime.active_window().active_view()
		if view.name() == RapidOutputView.name or view.name() == RapidOutputView.analyze_view_name or \
						  (view.file_name() != None and view.file_name().endswith(RapidOutputView.analyze_file_name)):
			sel = view.sel()
			r = sel[0]
			s = view.line(r)
			line = view.substr(s).replace('\\', '/')
			
			#file_name_and_row = re.search(r'[\w\.-]+.lua:\d{1,16}', line) #old implementation
			file_name_and_row = re.search(r'[^ ]+lua[^ ]+', line)

			# try to find hlsl file
			if file_name_and_row == None:
				file_name_and_row = re.search(r'[^ ]+hlsl[^ ]+', line)

			if file_name_and_row:
				file_path_name_row = file_name_and_row.group(0)
				if file_path_name_row.endswith(":"):
					file_path_name_row = file_path_name_row[:-1]
				
				view.run_command("expand_selection", {"to": "line"})

				#split on the last occurence of ':' 
				test = file_path_name_row.rsplit(':', 1)
				file_name = test[0].strip()
				file_row = test[1]

				#RapidOutputView.printMessage("file_name: " + file_name)
				#RapidOutputView.printMessage("file_row: " + file_row)
	
				path_found = False
				window_found = self.window
				path = None
		
				# scan all opened folders of *all* windows
				# we need scan other windows, because the rapid output view
				# can be detached from the window, where the project is loaded
				for window in sublime.windows():
					for folder in window.folders():
						candidate = os.path.join(folder, file_name)
						if os.path.isfile(candidate):
							path_found = True
							window_found = window
							path = candidate
							break

				if path_found:
					view = window_found.find_open_file(path)
					if view != None:
						window_found.open_file(path+":"+file_row, sublime.ENCODED_POSITION)
						window_found.focus_view(view)
					else:
						window_found.focus_group(0)
						view = window_found.open_file(path+":"+file_row, sublime.ENCODED_POSITION)
				else:
					RapidOutputView.printMessage(file_name + " not found in the project folders!")

class RapidCloseOutputViewCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		#print("Rapid Close Output View command")
		view = RapidOutputView.getOutputView(False)
		if view != None:
			self.view.window().focus_view(view)
			self.view.window().run_command("close_file")

class RapidOutputEventListener(sublime_plugin.EventListener):
	def on_query_context(self, view, key, operator, operand, match_all):
		if key == "close_server_output":
			for window in sublime.windows():
				for view in window.views():
					if view.name() == RapidOutputView.name:
						return True
		return False

# class RapidFileOpenListener(sublime_plugin.EventListener):
#
# 	# empty files (except Server Output View) are always created on the focus_group(0)
# 	def on_new(self, view):
# 		window = sublime.active_window()
# 		window.focus_group(0)
#
# 	# loaded files are always brought to focus_group(0)
# 	def on_load(self, view):
# 		window = sublime.active_window()
# 		if window.active_group() != 0:
# 			active_view = window.active_view_in_group(0)
# 			active_group, active_view_index = window.get_view_index(active_view)
# 			if active_view_index == -1:
# 				views = window.views_in_group(0)
# 				active_view_index = len(views)
# 			else:
# 				active_view_index = active_view_index + 1
# 			window.focus_group(0)
# 			window.set_view_index(view, 0, active_view_index)