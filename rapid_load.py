import sublime

from .rapid_output import RapidOutputView

def plugin_loaded():
	# Start shortly after Sublime starts 
	view = sublime.windows()[0].active_view()	
	sublime.set_timeout(lambda: view.run_command('rapid_start_collector'), 2000)