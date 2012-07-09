import sublime, sublime_plugin
import time

SCOPES = ['string', 'entity.name.class', 'variable.parameter', 'invalid.deprecated', 'invalid', 'support.function']

class HighlightWordsCommand(sublime_plugin.WindowCommand):
	def run(self):
		view = self.window.active_view()
		self.window.show_input_panel('Words to Highlight:', view.settings().get('highlight_text', ''), None, self.on_change, self.on_cancel)

	def on_change(self, text):
		stamp = time.time()
		self.stamp = stamp
		sublime.set_timeout(lambda: self.highlight(text, stamp), 500)

	def highlight(self, text, stamp):
		if self.stamp != stamp:
			return
		self.window.run_command('unhighlight_words')
		view = self.window.active_view()
		words = text.split()
		regions = []
		size = 0
		word_set = set()
		for word in words:
			if len(word) < 2 or word in word_set:
				continue
			word_set.add(word)
			regions = view.find_all(word, sublime.LITERAL)
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
		size = view.settings().get('highlight_size', 0)
		for i in range(size):
			view.erase_regions('highlight_word_%d' % i)
		view.settings().set('highlight_size', 0)
