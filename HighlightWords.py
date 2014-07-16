import sublime, sublime_plugin
import time
import sys
import re

SCOPES = ['string', 'entity.name.class', 'variable.parameter', 'invalid.deprecated', 'invalid', 'support.function']

ST3 = False if sys.version_info < (3, 0) else True
USE_REGEX = False
IGNORE_CASE = False

class HighlightWordsCommand(sublime_plugin.WindowCommand):
	def get_words(self, text):
		if USE_REGEX:
			return list(filter(lambda x: x and x != ' ', re.split(r'((?:\\ |[^ ])+)', text)))
		else:
			return text.split()

	def run(self):
		view = self.window.active_view()
		if not view:
			return
		word_list = self.get_words(view.settings().get('highlight_text', ''))
		for region in view.sel():
			if not region.empty():
				cursor_word = view.substr(region)
				if USE_REGEX:
					# ST uses perl regular expression syntax, espcae all special characters
					cursor_word = re.sub(r'([ \\.\[{}()\*+?|^$])', r'\\\1', cursor_word).replace('\t', '\\t').replace('\n', '\\n')
				if cursor_word in word_list:
					word_list.remove(cursor_word)
				else:
					word_list.append(cursor_word)
				break
		display_list = ' '.join(word_list)
		prompt = 'Highlight words '
		if USE_REGEX:
			prompt += '(RegEx, '
		else:
			prompt += '(Literal, '
		if IGNORE_CASE:
			prompt += 'Ignore Case'
		else:
			prompt += 'Case Sensitive'
		prompt += '):'
		v = self.window.show_input_panel(prompt, display_list, None, self.on_change, None)
		sel = v.sel()
		sel.clear()
		sel.add(sublime.Region(0, v.size()))

	def on_change(self, text):
		stamp = time.time()
		self.stamp = stamp
		sublime.set_timeout(lambda: self.highlight(text, stamp), 500)

	def highlight(self, text, stamp):
		if self.stamp != stamp:
			return
		self.window.run_command('unhighlight_words')
		view = self.window.active_view()
		words = self.get_words(text)
		regions = []
		size = 0
		flag = 0
		if not USE_REGEX:
			flag |= sublime.LITERAL
		if IGNORE_CASE:
			flag |= sublime.IGNORECASE
		word_set = set()
		for word in words:
			if len(word) < 2 or word in word_set:
				continue
			word_set.add(word)
			regions = view.find_all(word, flag)
			view.add_regions('highlight_word_%d' % size, regions,  SCOPES[size % len(SCOPES)] , '', sublime.HIDE_ON_MINIMAP)
			size += 1
		view.settings().set('highlight_size', size)
		view.settings().set('highlight_text', text)

	def on_cancel(self):
		self.window.run_command('unhighlight_words')
		view = self.window.active_view()
		view.settings().erase('highlight_text')

class UnhighlightWordsCommand(sublime_plugin.WindowCommand):
	def run(self):
		view = self.window.active_view()
		if not view:
			return
		size = view.settings().get('highlight_size', 0)
		for i in range(size):
			view.erase_regions('highlight_word_%d' % i)
		view.settings().set('highlight_size', 0)

class HighlightSettingsCommand(sublime_plugin.WindowCommand):
	def run(self):
		names = [
			'Turn [Regular Expression] ' + ('OFF' if USE_REGEX else 'ON'),
			'Turn [Case Sensitive] ' + ('ON' if IGNORE_CASE else 'OFF')
		]
		self.window.show_quick_panel(names, self.on_done)

	def on_done(self, selected):
		if selected == -1:
			return
		settings = sublime.load_settings('HighlightWords.sublime-settings')
		if selected == 0:
			settings.set('use_regex', not USE_REGEX)
		else:
			settings.set('ignore_case', not IGNORE_CASE)
		sublime.save_settings('HighlightWords.sublime-settings')

def get_settings():
	global USE_REGEX, IGNORE_CASE
	setting = sublime.load_settings('HighlightWords.sublime-settings')
	USE_REGEX = setting.get('use_regex', False)
	IGNORE_CASE = setting.get('ignore_case', False)
	return setting

def plugin_loaded():
	get_settings().add_on_change('get_settings', get_settings)

if not ST3:
	plugin_loaded()
