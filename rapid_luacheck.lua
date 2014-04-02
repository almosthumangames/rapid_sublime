-- Helper function for doing static analyzation from Sublime Text
luacheck = require "luacheck"

-- analyze single file
function analyzeFile(files)

	-- do not print "redefined warnings"
	local options = {}
	options.check_redefined = false

	report = luacheck(files, options)
	printReport(report)
end 

-- analyze multiple files
-- files are in one string, separated with |
function analyzeFiles(files)

	--parse filenames from files string
	local f = {}
	local index = 1
	for line in files:gmatch("[^|]+") do 
	 	--print(line)
	 	f[index] = line
	 	index = index + 1
	end
	
	-- do not print "redefined warnings"
	local options = {}
	options.check_redefined = false

	report = luacheck(f, options)
	printReport(report)
end

function printReport(report)
	for _,v in pairs(report) do	
		if type(v) == "table" then
			local line, name, wtype
			local filename = string.match(v["file"], "([^\\/]-%.?[^%.\\/]*)$")

			for _, v2 in pairs(v) do
				if type(v2) == "table" then
					for key, value in pairs(v2) do
						if key == "line" then line = value end
						if key == "name" then name = value end
						if key == "type" then wtype = value end	
					end

					local warningLine = filename..":"..line..": "..wtype..": "..name
					print(warningLine)
				end
			end			
		end
	end
end