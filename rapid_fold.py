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

						#Hack to handle strings spanning multiple lines and breaking indentation 
						next_line = self.view.full_line(s.end()+1)
						next_row = self.view.rowcol(next_line.begin())[0]
						if not self.view.substr(next_line).startswith("end"):
							end_found = False
							while not end_found:
								next_line = self.view.full_line(next_line.end()+1)
								next_row = self.view.rowcol(next_line.begin())[0]
								if self.view.substr(next_line).startswith("end") or next_line.end() == self.view.size():
									s = sublime.Region(s.begin(), next_line.end())
									end_found = True

						should_include_newline = self.checkFunctionBelow(s)
						r = fold_region_from_indent(self.view, s, should_include_newline)
						folds.append(r)
						tp = s.b
						continue;
			tp = self.view.full_line(tp).b

		self.view.fold(folds)
		sublime.status_message("Folded " + str(len(folds)) + " regions")

	def checkFunctionBelow(self, region):
		row, col = self.view.rowcol(region.end())
		next_line = self.view.line(self.view.text_point(row+1, 0))
		next_next_line = self.view.line(self.view.text_point(row+2, 0))

		if self.view.substr(next_next_line).startswith("function"):
			return True
		else:
			return False

class RapidUnfoldAllCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.view.unfold(sublime.Region(0, self.view.size()))
		self.view.show(self.view.sel())

class RapidFoldUnfoldCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		cursor_position = self.view.sel()[0].begin()
		cursor_line = self.view.line(cursor_position)

		#check folding cases
		cursor_at_beginning = False
		cursor_at_end = False
		cursor_at_indent = False

		if self.view.indentation_level(cursor_position) == 0:
			if self.view.substr(cursor_line).startswith('function'):
				cursor_at_beginning = True
				#print("cursor is at the beginning of function")
			elif self.view.substr(cursor_line).startswith('end'):
				cursor_at_end = True
				#print("cursor is at the end of function")
			elif self.view.substr(cursor_line).strip() == "":
				#check here if the cursor is inside a function block
				row = self.view.rowcol(cursor_position)[0]
				
				check_finished = False
				index = 1
				while not check_finished:
					previous_line = self.view.full_line(self.view.text_point(row-index, 0))
					if self.view.substr(previous_line).startswith("function"):
						cursor_position = previous_line.begin()
						cursor_at_beginning = True
						#print("cursor is inside function block")
						break
					elif self.view.substr(previous_line).startswith("end") or previous_line.begin() == 0:
						#print("cursor is not inside a function block")
						return
					index = index + 1
			else:
				return
		elif self.view.indentation_level(cursor_position) > 0:
			cursor_at_indent = True
			#print("cursor is inside indented block")


		folds = []
		tp = 0
		size = self.view.size()

		while tp < size:
			if self.view.indentation_level(tp) == 1:
				s = self.view.indented_region(tp)
				if not s.empty():		

					#Hack to handle strings spanning multiple lines and breaking indentation 
					next_line = self.view.full_line(s.end()+1)
					next_row = self.view.rowcol(next_line.begin())[0]
					if not self.view.substr(next_line).startswith("end"):
						end_found = False
						while not end_found:
							next_line = self.view.full_line(next_line.end()+1)
							next_row = self.view.rowcol(next_line.begin())[0]
							if self.view.substr(next_line).startswith("end") or next_line.end() == self.view.size():
								s = sublime.Region(s.begin(), next_line.end())
								end_found = True

					row = self.view.rowcol(tp)[0]
					previous_line = self.view.full_line(self.view.text_point(row-1, 0))

					#TODO: fold/unfold at the end of the block

					region_found = False
					if ( s.contains(cursor_line) and self.view.substr(previous_line).startswith('function') or
						 cursor_at_beginning and previous_line.contains(cursor_line) ): 
						 #cursor_at_end and next_line.contains(cursor_line) ):
						region_found = True

					if region_found:
						unfolded = self.view.unfold(s)
						if len(unfolded) == 0:
							#folding
							self.checkPrevBlock(s, True)
							should_include_newline = self.checkNextBlockWhenFolding(s)
							r = fold_region_from_indent(self.view, s, should_include_newline)
							self.view.fold(r)
						else:
							#unfolding
							self.checkPrevBlock(s, False)
						break

			tp = self.view.full_line(tp).b

	def checkNextBlockWhenFolding(self, region):
		#check if the lines below contain another function
		row, col = self.view.rowcol(region.end())
		next_line = self.view.line(self.view.text_point(row+1, 0))
		next_next_line = self.view.line(self.view.text_point(row+2, 0))

		#print("next line: " + self.view.substr(next_line))
		#print("next next line: " + self.view.substr(next_next_line))

		if self.view.substr(next_line).strip() == "" and self.view.substr(next_next_line).startswith("function"):
			unfold_result = self.view.unfold(self.view.line(self.view.text_point(row+3, 0)))
			if len(unfold_result) > 0: 
				#next block is folded, should be folded back
				self.view.fold(unfold_result)
				return True
			else:
				#next block is not folded
				return False
		return False

	def checkPrevBlock(self, region, folding):
		#check if the lines above contain another function
		row, col = self.view.rowcol(region.begin())
		prev_line = self.view.line(self.view.text_point(row-2, 0))
		prev_prev_line = self.view.line(self.view.text_point(row-3, 0))

		#print("prev line: " + self.view.substr(prev_line))
		#print("prev prev line: " + self.view.substr(prev_prev_line))

		if self.view.substr(prev_line).strip() == "" and self.view.substr(prev_prev_line).strip() == "end":
			unfold_result = self.view.unfold(self.view.line(self.view.text_point(row-4, 0)))
			if len(unfold_result) > 0:
				#print("prev block is folded, it should include newline to its region")
				tp = self.view.text_point(row-4, 0)
				if self.view.indentation_level(tp) > 0:
					new_fold_region = self.view.indented_region(tp)
					if folding:
						r = fold_region_from_indent(self.view, new_fold_region, True)
					else:
						r = fold_region_from_indent(self.view, new_fold_region, False)
					self.view.fold(r)	
