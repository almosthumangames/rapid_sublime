import sublime, sublime_plugin
import os
import re
import threading

from .rapid_output import RapidOutputView
from os.path import basename

class RapidAutoComplete(sublime_plugin.TextCommand):
	def run(self, edit):
		self.var_list = []

		cursor_pos = self.view.sel()[0].begin()
		region = self.view.word(cursor_pos)
		word = self.view.substr(region)
		print("AutoComplete word: " + word)

		valid = re.match('^[\w-]+$', word) is not None
		#match = re.match(r'[a-zA-Z0-9]*', word)

		if valid and len(word) > 0:
			word = word.lower()
			self.findLua(word)

			RapidOutputView.printMessage("----")
			self.var_list = self.removeDuplicates(self.var_list)
			for variable in self.var_list:
				RapidOutputView.printMessage(variable)

		else:
			print("Not valid word for AutoComplete")

		#finally insert the bracket into document
		for region in self.view.sel():
			self.view.insert(edit, region.begin(), "(")


	def findLua(self, pattern):
		for folder in sublime.active_window().folders():
			for root, dirs, files in os.walk(folder):
				for name in files:
					if name.endswith("lua"):
						full_path = os.path.abspath(os.path.join(root, name))
						self.findFunction(full_path, pattern)

	def findFunction(self, filepath, pattern):
		with open(filepath, "r") as f:
			for line in f:
				if re.match(r'function', line) != None:
					lower_line = line.lower()
					
					#'\w*'+
					match = re.search(pattern+'\(', lower_line)
					if match != None:
						#p = re.search('(?<=\().*?(?=\))', c)
						test = re.search('(?<=\().*?(?=\))', line)
						#test = file_name_and_row.group().split(':')
						self.var_list.append(test.group())
						
						#text = ""
						#variables = test.group().split(',')
						# for variable in variables:
						# 	text = text + variable + " "
						# RapidOutputView.printMessage(text)

	def removeDuplicates(self, seq):
   		# Not order preserving
   		keys = {}
   		for e in seq:
   			keys[e] = 1
   		return keys.keys()