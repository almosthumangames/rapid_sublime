import sublime, sublime_plugin
import re
import os
import sublime_api

class RapidOutputView():
	
	name = "Server Output View"
	analyze_view_name = "Analyze Result"
	analyze_file_name = "analyze_result.lua"

	messageQueue = []
	outputViews = []

	@classmethod
	def getOutputView(self, window):
		for view in window.views():
			if view.name() == RapidOutputView.name:
				return view
		return None

	@classmethod
	def hasOutputView(self, window):
		
		openView = None
		for view in sublime.active_window().views():
			if view.name() == RapidOutputView.name:
				openView = view
				break

		for view in RapidOutputView.outputViews:
			if view.window() == sublime.active_window():
				return True

		if openView != None:
			RapidOutputView.outputViews.append(openView)
			return True	
		return False

	@classmethod
	def getOutputViews(self):
		if self.hasOutputView(sublime.active_window()):
			#print("has output view, returns it")
			return RapidOutputView.outputViews
		else:
			hasView = False
			for view in sublime.active_window().views():
				if view.name() == RapidOutputView.name:
					hasView = True
					break

			if not hasView:
				# no existing output views are available, create a new one
				activeView = sublime.active_window().active_view()
				groups = sublime.active_window().num_groups()
				if groups < 2:
					sublime.active_window().set_layout( {"cols": [0.0, 1.0], "rows": [0.0, 0.8, 1.0], "cells": [[0,0,1,1], [0,1,1,2]]} )
				sublime.active_window().focus_group(1)
				outputView = sublime.active_window().new_file()
				outputView.set_read_only(True)
				outputView.set_scratch(True)
				outputView.set_name(RapidOutputView.name)
				sublime.active_window().set_view_index(outputView, 1, 0)
				sublime.active_window().focus_view(activeView)
				RapidOutputView.outputViews.append(outputView)
			
		return RapidOutputView.outputViews
		
	@classmethod
	def printMessage(self, msg):
		RapidOutputView.messageQueue.append(msg)
		sublime.set_timeout(RapidOutputView.callback, 100)

	@classmethod
	def getQueueLen(self):
		return len(RapidOutputView.messageQueue)
			
	@classmethod
	def callback(self):
		while len(RapidOutputView.messageQueue) > 0:
			msg = RapidOutputView.messageQueue.pop(0)
			views = RapidOutputView.getOutputViews()
			if len(views) > 0:
				for view in views:	
					if view != None and view.window() != None and RapidOutputView.hasOutputView(view.window()):
						view.window().run_command("rapid_output_view_insert", {"msg": msg } )
			
class RapidOutputViewInsertCommand(sublime_plugin.TextCommand):
	def run(self, edit, msg):

		views = RapidOutputView.getOutputViews()
		for view in views:
			if self.view.window() == view.window():
				if view.settings().get('syntax') != "Packages/Lua/Lua.tmLanguage":
					view.set_syntax_file("Packages/Lua/Lua.tmLanguage")		
				if not '\n' in msg:
					msg = msg + '\n'
				if re.search("Static analysis done", msg):
					self.view.window().run_command("rapid_luacheck_load_static_analysis")
					return

				view.set_read_only(False)
				view.insert(edit, view.size(), msg)
				view.set_read_only(True)

				region = view.full_line(view.size())
				view.show(region)

class RapidOutputViewClearCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		views = RapidOutputView.getOutputViews()
		if len(views) > 0:
			for view in views:
				view.set_read_only(False)
				view.erase(edit, sublime.Region(0, view.size()))
				view.set_read_only(True)

class RapidOutputViewListener(sublime_plugin.EventListener):
	def on_close(self, view):
		if view.name() == RapidOutputView.name:
			RapidOutputView.output = None
			sublime.active_window().set_layout( {"cols": [0.0, 1.0], "rows": [0.0, 1.0], "cells": [[0,0,1,1]] } )

class RapidDoubleClick(sublime_plugin.WindowCommand):
	def run(self):
		view = sublime.active_window().active_view()
		if view.name() == RapidOutputView.name or view.name() == RapidOutputView.analyze_view_name or \
						  (view.file_name() != None and view.file_name().endswith(RapidOutputView.analyze_file_name)):
			sel = view.sel()
			r = sel[0]
			s = view.line(r)
			line = view.substr(s)
			
			file_name_and_row = re.search(r'[\w\.-]+.lua:\d{1,16}', line)
			if file_name_and_row:
				view.run_command("expand_selection", {"to": "line"})
				test = file_name_and_row.group().split(':')
				file_name = test[0]
				file_row = test[1]

				# print("Double click result: " + file_name + ":" + file_row)

				path_found = False
				path = None
				file_window = None
		
				# check if file is already open in the window
				open_views = sublime.active_window().views()
				for open_view in open_views:
					if open_view.file_name() != None and open_view.file_name().endswith(file_name):
						path = open_view.file_name()
						view = sublime.active_window().open_file(path+":"+file_row, sublime.ENCODED_POSITION)
						sublime.active_window().focus_view(view)
						return

				# scan all the folders if view not found on window
				for window in sublime.windows():
					for folder in window.folders():			
						for root, dirs, files in os.walk(folder):
							if path_found:
								break
							for name in files:
								if name.endswith(".lua"):
									if name == file_name:
										path = os.path.abspath(os.path.join(root, name))
										path_found = True
										file_window = window
										break
				if not path_found:
					RapidOutputView.printMessage(file_name + " not found in the project folders!")
					return
				
				view = None
				for window in sublime.windows():
					view = window.find_open_file(path)
					if view != None:
						window.open_file(path+":"+file_row, sublime.ENCODED_POSITION)
						window.focus_view(view)
						break

				if view == None:
					sublime.active_window().focus_group(0)
					view = file_window.open_file(path+":"+file_row, sublime.ENCODED_POSITION)
			# else:
			# 	print("File name and row not found from line: " + line)
		# else:
		#  	print("no output view or analyze_result!")
		#  	print("View name: " + view.name())
		#  	print("View filename: " + view.file_name())
		#  	print(os.path.basename(view.file_name()))

class RapidCloseOutputViewCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		#print("Rapid Close Output View command")
		window = sublime.active_window()
		if RapidOutputView.hasOutputView(window):
			view = RapidOutputView.getOutputView(window)
			if view != None:
				RapidOutputView.outputViews.remove(view)
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

class RapidFileOpenListener(sublime_plugin.EventListener):

	# empty files (except Server Output View) are always created on the focus_group(0)
	def on_new(self, view):
		window = sublime.active_window()
		window.focus_group(0)

	# loaded files are always brought to focus_group(0)
	def on_load(self, view):
		window = sublime.active_window()
		if window.active_group() != 0:
			active_view = window.active_view_in_group(0)
			active_group, active_view_index = window.get_view_index(active_view)
			if active_view_index == -1:
				views = window.views_in_group(0)
				active_view_index = len(views)
			else:
				active_view_index = active_view_index + 1
			window.focus_group(0)
			window.set_view_index(view, 0, active_view_index)