-- Helper function for doing static analyzation from Sublime Text
luacheck = require "luacheck"
require "Set"

function getOptions()
	local options = {}
	options.check_redefined = false
	options.check_unused = false
	local globals = dofile("Globals.lua")
	globals = Set(globals)
	options.globals = globals
	return options
end

-- analyze single file
function analyzeFile(file)

	local options = getOptions()
	report = luacheck(file, options)

	writeReport(report, true)
end 

-- analyze multiple files
-- files are in one string, separated with |
function analyzeFiles(files)
	-- parse filenames from files string (one string with | as a separator)
	local f = {}
	local index = 1
	for line in files:gmatch("[^|]+") do 
	 	f[index] = line
	 	index = index + 1
	end
	
	local options = getOptions()
	report = luacheck(f, options)

	writeReport(report, false)
end


function writeReport(report, singleFile)

	local resultFile = "analyze_result.lua"	
	local file = io.open(resultFile, "w+")

	for _,v in pairs(report) do	
		if type(v) == "table" then
			local line, name, wtype
			local filename = string.match(v["file"], "([^\\/]-%.?[^%.\\/]*)$")
			local warningFound = false

			for _, v2 in pairs(v) do
				if type(v2) == "table" then
					for key, value in pairs(v2) do
						if key == "line" then line = value end
						if key == "name" then name = value end
						if key == "type" then wtype = value end	
					end

					if name ~= "self" then 
						if wtype == "unused" then wtype = "unused local variable" end
						if wtype == "global" then wtype = "use of non-standard global" end
						local warningLine = filename..":"..line..": "..wtype..": "..name.."\n"
						file:write(warningLine)
						if not warningFound then warningFound = true end
					end
					line = ""
					name = ""
					wtype = ""
				end
			end	

			if not warningFound and singleFile then
				file:write("No warnings found from given file: "..filename)
			end	
		end
	end
	file:close()
	print("Results written to file "..tostring(resultFile))
end

-- function printReport(report)
-- 	for _,v in pairs(report) do	
-- 		if type(v) == "table" then
-- 			local line, name, wtype
-- 			local filename = string.match(v["file"], "([^\\/]-%.?[^%.\\/]*)$")

-- 			for _, v2 in pairs(v) do
-- 				if type(v2) == "table" then
-- 					for key, value in pairs(v2) do
-- 						if key == "line" then line = value end
-- 						if key == "name" then name = value end
-- 						if key == "type" then wtype = value end	
-- 					end

-- 					local warningLine = filename..":"..line..": "..wtype..": "..name
-- 					print(warningLine)
-- 				end
-- 			end			
-- 		end
-- 	end
-- end