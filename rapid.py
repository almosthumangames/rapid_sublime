import sublime, sublime_plugin
import socket
import time
import threading
import os
import subprocess
import re

from .rapid_output import RapidOutputView
from .rapid_parse import RapidSettings

# to run execute from the console:
# view.run_command('rapid_eval')
class RapidConnectionThread(threading.Thread):
	instance = None
	
	def __init__(self):
		self.host = "localhost"
		settings = RapidSettings().getSettings()
		if "Host" in settings:
			self.host = settings["Host"]

		self.port = 4444
		self.sock = None
		self.running = False

		try:
			threading.Thread.__init__(self)
			self.sock = socket.create_connection((self.host, self.port))
			#RapidOutputView.printMessage("Connected to " + self.host + ".")
			RapidConnectionThread.instance = self
		except OSError as e:
			RapidOutputView.printMessage("Failed to connect to rapid server:\n" + str(e))

	def run(self):
		self.running = True
		dataQueue = []

		try:
			while True:
				data = self.sock.recv(1).decode()
				if not data:
					break;

				if data != '\000':
					dataQueue.append(data)

				if data == '\n' or data == '\000':
					datastr = "".join(dataQueue)
					if dataQueue: #dataQueue is not empty
						RapidOutputView.printMessage(datastr)
					del dataQueue[:]
		except socket.error:
			RapidOutputView.printMessage("Socket error")
		except:
			RapidOutputView.printMessage("Error")

		self.sock.close()
		self.running = False
		del self.sock
		RapidOutputView.printMessage("Connection terminated")

	def isRunning(self):
		return self.running 

	def sendString(self, msg):
		self.sock.send(msg.encode())

	@staticmethod
	def checkConnection():
		if RapidConnectionThread.instance == None:
			RapidConnect()
			RapidConnectionThread().start()
		elif not RapidConnectionThread.instance.isRunning():
			RapidConnectionThread.instance.join()
			RapidConnect()
			RapidConnectionThread().start()

class RapidResumeCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		RapidConnectionThread.checkConnection()
		RapidConnectionThread.instance.sendString("\nsys.resume()\000")

class RapidHelpCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		cursor_pos = self.view.sel()[0].begin()
		region = self.view.word(cursor_pos)
		word = self.view.substr(region)
		#print("Sending word: " + word)
		RapidConnectionThread.checkConnection()
		line = "\nrequire(\"doc\"); doc.find([["+ word +"]])\000"
		RapidConnectionThread.instance.sendString(line)

class RapidEvalCommand(sublime_plugin.TextCommand):
	def run(self, edit):

		#do not evaluate python files
		if self.view.file_name() != None and self.view.file_name().endswith("py"):
			print("cannot evaluate python files")
			return

		RapidConnectionThread.checkConnection()
		line_contents = self.getLines()
		RapidConnectionThread.instance.sendString(line_contents)

	# Checks if the cursor is inside lua function() block
	def checkBlock(self, view, current_row, line_contents, cursor_pos):
		#added special case check for comments inside a block which might have no indentation
		if self.view.indentation_level(cursor_pos) > 0 \
		or ( self.view.indentation_level(cursor_pos) == 0 \
		and line_contents.startswith("--") ):
			return True
		elif line_contents.strip() == '':
			# cursor might be on an empty unintended row inside block
			start_row = current_row
			end_row = current_row
			index = 1

			# find first previous non-empty row
			block_start = False
			while not block_start:
				start_row = current_row - index
				start_pos = self.view.text_point(start_row, 0)
				start_line = self.view.full_line(start_pos)
				start_line_contents = self.view.substr(start_line)
				if start_line_contents.strip() != '':
					block_start = True
				else:
					index = index + 1

			#find first next non-empty row
			index = 1
			block_end = False
			while not block_end:
				end_row = current_row + index
				end_pos = self.view.text_point(end_row, 0)
				end_line = self.view.full_line(end_pos)
				end_line_contents = self.view.substr(end_line)
				if end_line_contents.strip() != '':
					block_end = True
				else:
					index = index + 1

			# Assume that the cursor is inside a function block if:
			# 1) start_row and end_row have indentation level > 0 OR
			# 2) start_row has indentation level > 0 and end_row starts with "end" OR
			# 3) start_row starts with "function" or "local function" and end_row indentation level > 0
			if (self.view.indentation_level(start_pos) > 0 and self.view.indentation_level(end_pos) > 0):
				return True
			elif (self.view.indentation_level(start_pos) > 0 \
				and self.view.indentation_level(end_pos) == 0 and end_line_contents.startswith("end")):
				return True
			elif (self.view.indentation_level(start_pos) == 0 and self.view.indentation_level(end_pos) > 0) \
				and (start_line_contents.startswith("function") or start_line_contents.startswith("local function")):
				return True
			else:
				return False
		else:
			return False

	def getLines(self):
		for region in self.view.sel():
			cursor_pos = self.view.sel()[0].begin()
			current_row = self.view.rowcol(cursor_pos)[0]

			if region.empty():
				#check if we are evaluating a block instead of line
				line = self.view.full_line(region)
				line_contents = self.view.substr(line)
				
				# if self.view.indentation_level(cursor_pos) > 0 \
				# or ( self.view.indentation_level(cursor_pos) == 0 \
				# and line_contents.startswith("--") ):

				#eval block
				if self.checkBlock(self.view, current_row, line_contents, cursor_pos) == True:
					start_row = current_row
					end_row = current_row
					index = 1

					#find start of the block
					block_start = False
					while not block_start:
						start_row = current_row - index
						start_pos = self.view.text_point(start_row, 0)
						start_line = self.view.full_line(start_pos)
						start_line_contents = self.view.substr(start_line)
						if self.view.indentation_level(start_pos) == 0 \
						and	start_line_contents.strip() != '' \
						and	not start_line_contents.startswith("--"):
							block_start = True
						else:
							index = index + 1

					#find end of the block
					index = 1
					block_end = False
					while not block_end:
						end_row = current_row + index
						end_pos = self.view.text_point(end_row, 0)
						end_line = self.view.full_line(end_pos)
						end_line_contents = self.view.substr(end_line)
						if self.view.indentation_level(end_pos) == 0 \
						and end_line_contents.strip() != '' \
						and not end_line_contents.startswith("--"):
							block_end = True
						else:
							index = index + 1
					
					start_offset = self.view.text_point(start_row, 0)
					end_offset = self.view.text_point(end_row+1, 0)
					block_region = sublime.Region(start_offset, end_offset)
					line = self.view.full_line(block_region)

					file_row = start_row
					#print("Sending: " + str(file_row))
					msg = "Updating " + start_line_contents
					RapidOutputView.printMessage(msg)
					file_row_str = str(file_row + 1)
				else:
					line = self.view.line(region) #expand the region for full line if no selection
					file_row_str = str(current_row + 1)
			else:
				line = region #get only the selected area
				file_row_str = str(current_row + 1)

			file_name = ""

			if self.view.file_name() != None:
				file_name = self.view.file_name().split("\\")[-1]
			
			line_str = self.view.substr(line)
			line_contents = "@" + file_name + ":" + file_row_str + "\n" + line_str + "\000"
			
			#print("------")
			#print("sending contents:")
			#print(line_contents)
			return line_contents


class RapidCheckServerAndStartupProjectCommand(sublime_plugin.WindowCommand):
	def run(self):
		self.view = self.window.active_view()
		self.view.run_command('rapid_output_view_clear')

		#Check if startup project exists and if it has been modified
		startup_exists = False
		is_modified = False

		RapidOutputView.printMessage("Loading project settings...")
		startup_path = RapidSettings().getStartupFilePath()
		RapidOutputView.printMessage("Startup path: " + startup_path)

		if startup_path:
			startup_exists = True
			new_view = sublime.active_window().find_open_file(startup_path)
			if new_view != None and new_view.is_dirty():
				is_modified = True
		elif self.view.is_dirty():
			is_modified = True

		#Send commands to server accordingly
		RapidConnectionThread.checkConnection()
		if startup_exists:
			#always load project, even if it is open and modified (modifications are loaded only after saving)
			RapidOutputView.printMessage("Startup project: " + startup_path)
			line = "\nsys.loadProject([[" + startup_path + "]])\000"
			RapidConnectionThread.instance.sendString(line)
		else:
			#if no startup project, run current page
			if is_modified:
				#file has not been saved - restart runtime engine and send code over
				RapidConnectionThread.instance.sendString("\nsys.restart()\000")
				line = "@" + self.view.file_name() + ":1\n" + self.view.substr(sublime.Region(0, self.view.size())) + "\000"
				RapidConnectionThread.instance.sendString(line)
			else:
				#file is up to date -> reload file - this is faster than sending the code
				RapidConnectionThread.instance.sendString("\nsys.loadProject([[" + self.view.file_name() + "]])\000")

class RapidConnect():
	def __init__(self):
	
		print("rapidconnect")

		if os.name == "nt":
			# check if rapid is already running	
			rapid_running = True
			rapid = subprocess.check_output("tasklist /FI \"IMAGENAME eq rapid.exe\" /FO CSV")
			rapid_search = re.search(r'rapid.exe', rapid.decode("ISO-8859-1"))
			if rapid_search == None:
				rapid_debug = subprocess.check_output("tasklist /FI \"IMAGENAME eq rapid_d.exe\" /FO CSV")
				rapid_debug_search = re.search(r'rapid_d.exe', rapid_debug.decode("ISO-8859-1"))
				if rapid_debug_search == None:
					rapid_running = False
			if rapid_running:
				return	
		elif os.name == "posix":
			data = subprocess.Popen(['ps','aux'], stdout=subprocess.PIPE).stdout.readlines() 
			rapid_running = False
			for line in data:
				lineStr = line.decode("utf-8")
				if lineStr.find("rapid") > -1 and lineStr.find(os.getlogin()) > -1:
					print("Rapid executable is already running for user: " + os.getlogin())
					print(lineStr)
					rapid_running = True
					break
			if rapid_running:
				return

		settings = RapidSettings().getSettings()
		if "Host" in settings and settings["Host"] != "localhost":
			return

		if os.name == "nt":
			rapid_path = settings["RapidPathWin"]
		elif os.name == "posix":
			os.chdir(RapidSettings().getStartupProjectPath()) 
			rapid_path = os.path.realpath(settings["RapidPathOSX"])
		else:
			RapidOutputView.printMessage("Could not find \"RapidPath<OS>\" variable from projects' rapid_sublime -file!")
			return

		#rapid_exe = sublime.active_window().active_view().settings().get("RapidExe")
		rapid_exe = settings["RapidExe"]

		if rapid_path != None and rapid_exe != None:
			RapidOutputView.printMessage("Starting " + rapid_exe)
			full_path = os.path.abspath(os.path.join(rapid_path, rapid_exe))
			subprocess.Popen(full_path, cwd=rapid_path)
			if os.name == "posix":
				time.sleep(0.5) #small delay to get server running on OSX
		else:
			RapidOutputView.printMessage("Could not start server executable!")
			RapidOutputView.printMessage("\"RapidPath<OS>\" and/or \"RapidExe\" variables not found from \"Preferences.sublime_settings\" file!")

class RapidTestCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		data = subprocess.Popen(['ps','aux'], stdout=subprocess.PIPE).stdout.readlines() 
		#print(data)
		rapid_running = False
		for line in data:
			lineStr = line.decode("utf-8")
			if lineStr.find("rapid") > -1:
				rapid_running = True
				break
		if rapid_running:
			print("rapid is already running!")
		else:
			print("rapid is not running!")
