import sublime, sublime_plugin

def fold_region_from_indent(view, r):
	if r.b == view.size():
		return sublime.Region(r.a - 1, r.b)
	else:
	   	(end_row, end_col) = view.rowcol(r.end())
	   	line = view.line(view.text_point(end_row, 0))
	   	end_point = view.text_point(end_row, line.size())
	   	return sublime.Region(r.a - 1, end_point+1)


class RapidTestCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		current_row  = self.view.rowcol(self.view.sel()[0].begin())[0]
		print("Current row: " + str(current_row))		

class RapidFoldAllCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		folds = []
		tp = 0
		size = self.view.size()

		while tp < size:
			if self.view.indentation_level(tp) == 1:
				s = self.view.indented_region(tp)
				if not s.empty():
					row = self.view.rowcol(tp)[0]
					previous_line = self.view.full_line(self.view.text_point(row-1, 0))
					if self.view.substr(previous_line).startswith('function'):
						r = fold_region_from_indent(self.view, s)
						folds.append(r)
						tp = s.b
						continue;
			tp = self.view.full_line(tp).b

		self.view.fold(folds)
		sublime.status_message("Folded " + str(len(folds)) + " regions")

class RapidUnfoldAllCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.view.unfold(sublime.Region(0, self.view.size()))
		self.view.show(self.view.sel())

class RapidFoldUnfoldCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		f = FindBlock(self.view)
		region = f.getLines()
		if not region.empty():
			#line_str = self.view.substr(region)
			#print(line_str)
			unfolded = self.view.unfold(region)
			if len(unfolded) == 0:
				self.view.fold(region)
			else:
				print("TODO")
				#find previous block region, check if it is folded
				#if it is, just unfold and fold it without empty line at the bottom 

class FindBlock(sublime_plugin.TextCommand):
	def getLines(self):
		block_region = sublime.Region(0,0)
		for region in self.view.sel():

			current_row  = self.view.rowcol(self.view.sel()[0].begin())[0]

			if region.empty():
				line = self.view.full_line(region)
				line_contents = self.view.substr(line)

				print("Indentation level: " + self.view.indentation_level(line.begin()))
				
				if line_contents.find("\t") == 0 or line_contents.startswith('function') or line_contents.startswith('end'):
					start_row = current_row
					end_row = current_row
					index = 1

					#find start of the block
					if line_contents.startswith('function'):
						block_start = True
						start_line = self.view.full_line(self.view.text_point(start_row, 0))
					else:
						block_start = False

					while not block_start:
						start_row = current_row - index
						start_line = self.view.full_line(self.view.text_point(start_row, 0))
						start_line_contents = self.view.substr(start_line)
						if start_line_contents.find("\t") != 0 and start_line_contents.strip() != '':
							block_start = True
						else:
							index = index + 1

					index = 1
					if line_contents.startswith('end') or self.view.text_point(current_row, line.end()) == self.view.size():
						block_end = True
					else:
						block_end = False
					while not block_end:
						end_row = current_row + index
						end_line = self.view.full_line(self.view.text_point(end_row, 0))
						end_line_contents = self.view.substr(end_line)
						if (end_line_contents.find("\t") != 0 and end_line_contents.strip() != '') or self.view.text_point(end_row, end_line.end()) == self.view.size():
							block_end = True
						else:
							index = index + 1
					
					start_offset = self.view.text_point(start_row, start_line.size()-1)
					end_offset = self.view.text_point(end_row+1, 0)
					block_region = sublime.Region(start_offset, end_offset)
		return block_region



