-- Helper function for doing static analyzation from Sublime Text
inspect = require "luacheck/inspect"
luacheck = require "luacheck"

-- analyze single file
function analyzeFile(files, options)
	report = luacheck(files, options)
	print(inspect(report))
end 

-- analyze multiple files
-- files are in one string, separated with newline
function analyzeFiles(files, options)
	f = {}
	index = 1
	for line in files:gmatch("[^|]+") do 
	 	--print(line)
	 	f[index] = line
	 	index = index + 1
	end
	
	report = luacheck(f, options)
	parsedReport = inspect(report)
	print(parsedReport)
end