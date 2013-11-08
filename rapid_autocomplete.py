import sublime, sublime_plugin
import os
import re

from .rapid_output import RapidOutputView

class RapidAutoComplete(sublime_plugin.TextCommand):
	def run(self, edit):
		
		cursor_pos = self.view.sel()[0].begin()
		region = self.view.word(cursor_pos)
		word = self.view.substr(region)
		print("AutoComplete word: " + word)

		if len(word) > 0:
			self.findLua(word)

		#finally insert the bracket into document
		for region in self.view.sel():
			self.view.insert(edit, region.begin(), "(")


	def findLua(self, pattern):
		lua_files = []
		for folder in sublime.active_window().folders():
			for root, dirs, files in os.walk(folder):
				for name in files:
					if name.endswith("lua"):
						full_path = os.path.abspath(os.path.join(root, name))
						lua_files.append(full_path)

		RapidOutputView.printMessage("findLua: " + pattern)
		pattern = pattern.lower()
		for filepath in lua_files:
			with open(filepath, "r") as f:
				for line in f:
					if re.match(r'function', line) != None:
						lower_line = line.lower()
						
						match = re.search('.*'+pattern+'\(', lower_line)
						if match != None:
							test = re.search('\(.*\)', line)
							#line = line.strip()
							RapidOutputView.printMessage(str(test.group()))

# class AutocompleteAll(sublime_plugin.EventListener):
#     def on_query_completions(self, view, prefix, locations):
#     	window = sublime.active_window()
#     	for folder in window.folders():
#     		for root, dirs, files in os.walk(folder):
#     			for name in files:
#     				if name.endswith("lua"):



#     					full_path = os.path.abspath(os.path.join(root, name))
#     					print(full_path)
#     					break
# 						#self.path = os.path.dirname(self.full_path)
# 						#self.project_filename = name
# 						#project_settings_found = True

    	
#     	# get results from each tab
#     	results = [v.extract_completions(prefix) for v in window.views() if v.buffer_id() != view.buffer_id()]
#     	results = [(item,item) for sublist in results for item in sublist] #flatten
#     	results = list(set(results)) # make unique
#     	results.sort() # sort
#     	return results

# class AutocompleteAll(sublime_plugin.EventListener):
# 	def on_query_completions(self, view, prefix, locations):
# 		tags_path = view.window().folders()[0]+"\.tags"
# 		results=[]
		
# 		if (not view.window().folders() or not os.path.exists(tags_path)): #check if a project is open and the .tags file exists
# 			return results

# 		print("Prefix: " + prefix)
# 		print("Tags_path: " + tags_path)

# 		f=os.popen("grep -i '^"+prefix+"' '"+tags_path+"' | awk '{ print $1 }'") # grep tags from project directory .tags file
# 		for i in f.readlines():
# 			print(i.strip())
# 			results.append([i.strip()])
# 			results = [(item,item) for sublist in results for item in sublist] #flatten
# 			results = list(set(results)) # make unique
# 			results.sort() # sort
# 			return results