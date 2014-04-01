import sublime, sublime_plugin

class Method:
	_name = ""
	_signature = ""
	_filename = ""
	
	def __init__(self, name, signature, filename):
		self._name = name
		self._filename = filename
		self._signature = signature

	#function name
	def name(self):
		return self._name

	#function parameters
	def signature(self):
		return self._signature
  
  	#filename
	def filename(self):
		return self._filename

class FunctionDefinition:
	_function = ""

	def __init__(self, function):
		self._function = function

	def getFunction(self):
		return self._function

class RapidFunctionStorage():
	#autocomplete (ctrl+space)
	funcs = {}

	#find (f1)
	findFuncMap = {}
	findFuncs = []

	#static analyzation (ctrl+f10)
	luaFiles = []

	@staticmethod
	def addAutoCompleteFunctions(functions, filename):
		RapidFunctionStorage.funcs[filename] = functions

	@staticmethod
	def removeAutoCompleteFunctions(filename):
		if filename in RapidFunctionStorage.funcs:
			del RapidFunctionStorage.funcs[filename]

	@staticmethod
	def getAutoCompleteList(word):
		autocomplete_list = []
		for key in RapidFunctionStorage.funcs:
			functions = RapidFunctionStorage.funcs[key]
			for method_obj in functions:
				if word.lower() in method_obj.name().lower():
					
					#parse method variables
					variables = method_obj.signature().split(", ")
					signature = ""
					index = 1
					for variable in variables:
						signature = signature + "${"+str(index)+":"+variable+"}"
						if index < len(variables):
							signature = signature + ", "
						index = index+1

					method_str_to_show = method_obj.name() + '(' + method_obj.signature() +')'
					method_str_to_append = method_obj.name() + '(' + signature + ')'
					method_file_location = method_obj.filename();

					autocomplete_list.append((method_str_to_show + '\t' + method_file_location, method_str_to_append)) 
		return autocomplete_list	

	@staticmethod
	def addLuaFile(full_path):
		if not full_path in RapidFunctionStorage.luaFiles:
			RapidFunctionStorage.luaFiles.append(full_path)
	
	@staticmethod
	def addFindFunctions(functions, filename):
		RapidFunctionStorage.findFuncMap[filename] = functions
		if RapidFunctionStorage.findFuncs:
			# clear findFuncs list in order to parse all new funcs in getFindFunctions()
			del RapidFunctionStorage.findFuncs[:]

	@staticmethod
	def removeFindFunctions(filename):
		if filename in RapidFunctionStorage.findFuncMap:
			del RapidFunctionStorage.findFuncMap[filename]
			del RapidFunctionStorage.findFuncs[:]

	@staticmethod
	def getFindFunctions():
		#parse functions again only if they have been updated, otherwise just return findFuncs list
		if not RapidFunctionStorage.findFuncs:
			for key in RapidFunctionStorage.findFuncMap:
				funcs = RapidFunctionStorage.findFuncMap[key]
				for func in funcs:
					RapidFunctionStorage.findFuncs.append(func.getFunction())
		return RapidFunctionStorage.findFuncs

