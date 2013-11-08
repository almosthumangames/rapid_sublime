import sublime, sublime_plugin
import os
import re

from .rapid_output import RapidOutputView

class RapidFindCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.cpp_files = []
		self.lua_files = []

		cursor_pos = self.view.sel()[0].begin()
		region = self.view.word(cursor_pos)
		pattern = self.view.substr(region)
		
		#RapidOutputView.printMessage("Pattern is: " + pattern)
		find_class_methods = False
		if pattern == ".*":
			cursor_pos = cursor_pos-2
			region = self.view.word(cursor_pos)
			pattern = self.view.substr(region)
			find_class_methods = True
		else:
			r = sublime.Region(region.end(), region.end()+2)
			if self.view.substr(r) == ".*":
				find_class_methods = True
		
		#find all cpp and lua files from folders
		self.find()

		if find_class_methods:
			print(pattern)
			self.findClassCpp(self.cpp_files, pattern)
			self.findClassLua(self.lua_files, pattern)
		elif len(pattern) > 0:
			self.findCpp(self.cpp_files, pattern)
			self.findLua(self.lua_files, pattern)

	def find(self):		
		for folder in sublime.active_window().folders():
			for root, dirs, files in os.walk(folder):
				for name in files:
					if name.endswith("cpp"):
						full_path = os.path.abspath(os.path.join(root, name))
						self.cpp_files.append(full_path)
					elif name.endswith("lua"):
						full_path = os.path.abspath(os.path.join(root, name))
						self.lua_files.append(full_path)

	def findCpp(self, files, pattern):
		pattern = pattern.lower()
		for filepath in files:			
			with open(filepath, "r") as f:
				for line in f:
					if re.match(r'///', line) != None:
						lower_line = line.lower()
						#local func = string.match(line, "^///.*=%s*([%.:_%w]+)%(") or string.match(line, "^///%s*([%.:_%w]+)%(")
						match = re.search('.*'+pattern+'.*\(', lower_line)
						if match != None:
							line = line.replace("///", "").strip()
							RapidOutputView.printMessage(line)
							
	def findLua(self, files, pattern):
		pattern = pattern.lower()
		for filepath in files:
			with open(filepath, "r") as f:
				for line in f:
					if re.match(r'function', line) != None:
						lower_line = line.lower()
						#local func = string.match(line, "function ([%.:_%w]+)%(")
						match = re.search('.*'+pattern+'.*\(', lower_line)
						if match != None:
							line = line.strip()
							RapidOutputView.printMessage(line)

	def findClassCpp(self, files, pattern):
		pattern = pattern.lower()
		for filepath in files:
			with open(filepath, "r") as f:
				for line in f:
					if re.match(r'///', line) != None:
						lower_line = line.lower()
						match = re.search('.*'+pattern+':.*\(', lower_line)
						match2 = re.search('.*'+pattern+'\..*\(', lower_line)
						if match != None or match2 != None:
							line = line.replace("///", "").strip()
							RapidOutputView.printMessage(line)	

	def findClassLua(self, files, pattern):
		pattern = pattern.lower()
		for filepath in files:
			with open(filepath, "r") as f:
				for line in f:
					if re.match(r'function', line) != None:
						lower_line = line.lower()
						match = re.search('.*'+pattern+':.*\(', lower_line)
						match2 = re.search('.*'+pattern+'\..*\(', lower_line)
						if match != None or match2 != None:
						 	RapidOutputView.printMessage(line)	



						

