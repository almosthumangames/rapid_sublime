import sublime, sublime_plugin

def fold_region_from_indent(view, r, include_next_line):
	if r.b == view.size():
		return sublime.Region(r.a - 1, r.b)
	elif include_next_line:
	   	(end_row, end_col) = view.rowcol(r.end())
	   	line = view.line(view.text_point(end_row, 0))
	   	end_point = view.text_point(end_row, line.size())
	   	return sublime.Region(r.a - 1, end_point+1)
	else:
		#print("should fold without empty line at the end")
		(end_row, end_col) = view.rowcol(r.end())
		line = view.line(view.text_point(end_row, 0))
		end_point = view.text_point(end_row, line.size())
		return sublime.Region(r.a - 1, end_point)


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
						r = fold_region_from_indent(self.view, s, True)
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

class RapidTestCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		print("RapidFoldUnfold test")
		'''
		cursor_position = self.view.sel()[0].begin()
		cursor_line = self.view.line(cursor_position)


		#check folding cases
		if self.view.indentation_level(cursor_position) == 0:
			if self.view.substr(cursor_line).startswith('function'):
				print("cursor is at the beginning of function")
			elif self.view.substr(cursor_line).startswith('end'):
				print("cursor is at the end of function")
		elif self.view.indentation_level(cursor_position) > 0:
			print("cursor is inside indented block")
		else:
			print("fold/unfold not possible")
			return

		folds = []
		tp = 0
		size = self.view.size()

		while tp < size:
			if self.view.indentation_level(tp) == 1:
				s = self.view.indented_region(tp)
				if not s.empty():
					row = self.view.rowcol(tp)[0]
					previous_line = self.view.full_line(self.view.text_point(row-1, 0))
					if s.contains(cursor_line) and self.view.substr(previous_line).startswith('function'):
						print("zzz")
					else:
						print("yyy")
						
					
					print("----")
					print("Region to be folded: " + self.view.substr(s))

			tp = self.view.full_line(tp).b'''
		

class RapidFoldUnfoldCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		f = FindBlock(self.view)
		region = f.getLines()
		if not region.empty():
			line_str = self.view.substr(region)
			print(line_str)

			is_folding = True

			unfolded = self.view.unfold(region)
			if len(unfolded) == 0:
				'''
				row, col = self.view.rowcol(region.end())
				next_line = self.view.line(self.view.text_point(row+1, 0))
				next_next_line = self.view.line(self.view.text_point(row+2, 0))
				print("Next line is: " + self.view.substr(next_line))
				print("Next next line is: " + self.view.substr(next_next_line))

				if self.view.substr(next_line).startswith("function"):
					
					prev_line = self.view.line(self.view.text_point(row-1, 0))
					r = sublime.Region(region.begin(), self.view.text_point(row-1, prev_line.size()))
					self.view.fold(r)
					'''	
				self.view.fold(region)
			else:
				is_folding = False

			'''
			#check if the lines above contain another function
			row, col = self.view.rowcol(region.begin())
			prev_line = self.view.line(self.view.text_point(row-1, 0))
			prev_prev_line = self.view.line(self.view.text_point(row-2, 0))

			if self.view.substr(prev_line).strip() == "" and self.view.substr(prev_prev_line).strip() == "end":
				#print("prev line: " + self.view.substr(prev_line))
				#print("prev_prev line: " + self.view.substr(prev_prev_line))
				unfold_result = self.view.unfold(prev_prev_line)
				if len(unfold_result) > 0:
					tp = self.view.text_point(row-3, 0)
					#print("prev_prev_prev line: " + self.view.substr(self.view.line(tp)))
					#print("prev_prev_prev line indent level: " + str(self.view.indentation_level(tp)) )
					if self.view.indentation_level(tp) > 0:
						new_fold_region = self.view.indented_region(tp)
						#print(self.view.substr(new_fold_region))
						if is_folding:
							r = fold_region_from_indent(self.view, new_fold_region, True)
						else:
							r = fold_region_from_indent(self.view, new_fold_region, False)
						self.view.fold(r)'''


class FindBlock(sublime_plugin.TextCommand):
	def getLines(self):
		block_region = sublime.Region(0,0)
		for region in self.view.sel():

			current_row  = self.view.rowcol(self.view.sel()[0].begin())[0]

			if region.empty():
				line = self.view.full_line(region)
				line_contents = self.view.substr(line)
	
				if self.view.indentation_level(line.begin()) > 0 or line_contents.startswith('function') or line_contents.startswith('end'):
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
						if self.view.indentation_level(start_line.begin()) == 0 and start_line_contents.strip() != '':
							block_start = True
						else:
							index = index + 1

					index = 1
					if line_contents.startswith('end'): #or self.view.text_point(current_row, line.end()) == self.view.size():
						print("uuu")
						print(line_contents)
						block_end = True
					else:
						block_end = False

					while not block_end:
						end_row = current_row + index
						end_line = self.view.full_line(self.view.text_point(end_row, 0))
						end_line_contents = self.view.substr(end_line)
						if (self.view.indentation_level(end_line.begin()) == 0 and not end_line_contents.strip() != '') or self.view.text_point(end_row, end_line.end()) == self.view.size():
							print("end found, end line contents: " + end_line_contents)
							block_end = True
						else:
							index = index + 1
					
					start_offset = self.view.text_point(start_row, start_line.size()-1)
					end_offset = self.view.text_point(end_row+1, 0)
					block_region = sublime.Region(start_offset, end_offset)
		return block_region



