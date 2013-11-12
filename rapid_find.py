import sublime, sublime_plugin
import os
import re
import fnmatch

from .rapid_output import RapidOutputView

class RapidFindCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		cursor_pos = self.view.sel()[0].begin()
		
		region = self.view.word(cursor_pos)
		pattern = self.view.substr(region)

		region2 = self.view.line(cursor_pos)
		line = self.view.substr(region2)
		words = line.split()

		#for some reason matching '*' is not working by using only 'if pattern in word'
		for word in words:
			if "*" in pattern and "*" in word or pattern in word:		
				pattern = word
				break

		find_class_methods = False
		if "*" in pattern and "." in pattern:
			find_class_methods = True
		
		pattern = pattern.lower()	
		if find_class_methods:
			self.findClass(pattern)
		elif len(pattern) > 0:
			self.find(pattern)

	def find(self, pattern):	
		for folder in sublime.active_window().folders():
			for root, dirs, files in os.walk(folder):
				for name in files:
					if name.endswith("cpp"):
						full_path = os.path.abspath(os.path.join(root, name))
						self.findCpp(full_path, pattern)
					elif name.endswith("lua"):
						full_path = os.path.abspath(os.path.join(root, name))
						self.findLua(full_path, pattern)

	def findCpp(self, filepath, pattern):
		with open(filepath, "r") as f:
			for line in f:
				if re.match(r'///', line) != None:
					lower_line = line.lower()
					#local func = string.match(line, "^///.*=%s*([%.:_%w]+)%(") or string.match(line, "^///%s*([%.:_%w]+)%(")
					match = re.search('.*'+pattern+'.*\(', lower_line)
					if match != None:
						line = line.replace("///", "").strip()
						RapidOutputView.printMessage(line)

	def findLua(self, filepath, pattern):
		with open(filepath, "r") as f:
			for line in f:
				if re.match(r'function', line) != None:
					lower_line = line.lower()
					#local func = string.match(line, "function ([%.:_%w]+)%(")
					match = re.search('.*'+pattern+'.*\(', lower_line)
					if match != None:
						line = line.strip()
						RapidOutputView.printMessage(line)

	def wildcardToRegex(pattern):
		return re.escape()

	def findClass(self, pattern):
		#convert wildcards to regular expressions
		patterns = []
		patterns.append(pattern.replace('.', '[\.:]').replace('*', '.*'))
		
		for folder in sublime.active_window().folders():
			for root, dirs, files in os.walk(folder):
				for name in files:
					if name.endswith("cpp"):
						full_path = os.path.abspath(os.path.join(root, name))
						self.findClassCpp(full_path, patterns)
					elif name.endswith("lua"):
						full_path = os.path.abspath(os.path.join(root, name))
						self.findClassLua(full_path, patterns)

	def findClassCpp(self, filepath, patterns):
		with open(filepath, "r") as f:
			for line in f:
				if re.match(r'///', line) != None: 
					#lower_line = line.lower()
					lower_line = line.lower()
					for pattern in patterns:
						match = re.search('\s' + pattern + '\(', lower_line)
						if match != None:
							line = line.replace("///", "").strip()
							RapidOutputView.printMessage(line)

	def findClassLua(self, filepath, patterns):
		with open(filepath, "r") as f:
			for line in f:
				if re.match(r'function', line) != None:
					#lower_line = line.lower()
					lower_line = line.lower()
					for pattern in patterns:
						match = re.search('\s' + pattern + '\(', lower_line)
						if match != None:
							RapidOutputView.printMessage(line)