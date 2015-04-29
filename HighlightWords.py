import sublime, sublime_plugin
import time
import sys
import re
import functools

SCOPES = ['string', 'entity.name.class', 'variable.parameter', 'invalid.deprecated', 'invalid', 'support.function']

ST3 = False if sys.version_info < (3, 0) else True
USE_REGEX = False
IGNORE_CASE = False
WHOLE_WORD = False # only effective when USE_REGEX is True
KEYWORD_MAP = []

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
			region = region.empty() and view.word(region) or region
			cursor_word = view.substr(region).strip()
			if USE_REGEX:
				# ST uses perl regular expression syntax, espcae all special characters
				cursor_word = re.sub(r'([ \\.\[{}()\*+?|^$])', r'\\\1', cursor_word).replace('\t', '\\t').replace('\n', '\\n')
				if WHOLE_WORD:
					cursor_word = "\\b" + cursor_word + "\\b"
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
		v = self.window.show_input_panel(prompt, display_list, None, self.on_change, self.on_cancel)
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
			'Turn [Case Sensitive] ' + ('ON' if IGNORE_CASE else 'OFF'),
			'Turn [Whole Word] ' + ('OFF' if WHOLE_WORD else 'ON')
		]
		self.window.show_quick_panel(names, self.on_done)

	def on_done(self, selected):
		if selected == -1:
			return
		settings = sublime.load_settings('HighlightWords.sublime-settings')
		if selected == 0:
			settings.set('use_regex', not USE_REGEX)
		elif selected == 1:
			settings.set('ignore_case', not IGNORE_CASE)
		else:
			settings.set('whole_word', not WHOLE_WORD)
		settings.set('colors_by_scope', SCOPES)
		sublime.save_settings('HighlightWords.sublime-settings')

class HighlightKeywordsCommand(sublime_plugin.EventListener):

	def handleTimeout(self, view, stamp):
		if self.stamp != stamp:
			return
		self.highlightKws(view)

	def on_modified(self, view):
		stamp = time.time()
		self.stamp = stamp
		sublime.set_timeout(functools.partial(self.handleTimeout, view, stamp), 500)

	def on_activated(self, view):
		stamp = time.time()
		self.stamp = stamp
		sublime.set_timeout(functools.partial(self.handleTimeout, view, stamp), 500)

	def highlightKws(self, view):
		size = 0
		word_set = set()
		for pair in KEYWORD_MAP:
			word = pair['keyword']
			color = pair['color']
			flag = pair.get('flag', sublime.LITERAL)
			if (word and color):
				if word in word_set:
					continue
				word_set.add(word)
				regions = view.find_all(word, flag)
				view.add_regions('highlight_keyword_%d' % size, regions, color, '', sublime.HIDE_ON_MINIMAP)
				size += 1

def get_settings():
	global USE_REGEX, IGNORE_CASE, WHOLE_WORD, SCOPES, KEYWORD_MAP
	setting = sublime.load_settings('HighlightWords.sublime-settings')
	USE_REGEX = setting.get('use_regex', False)
	IGNORE_CASE = setting.get('ignore_case', False)
	WHOLE_WORD = setting.get('whole_word', False)
	SCOPES = setting.get('colors_by_scope', SCOPES)
	KEYWORD_MAP = setting.get('permanent_highlight_keyword_color_mappings', [])
	return setting

def plugin_loaded():
	get_settings().add_on_change('get_settings', get_settings)

if not ST3:
	plugin_loaded()
