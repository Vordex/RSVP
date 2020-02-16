import gettext
from kivy.lang import Observable


class Lang(Observable):
    observers = []
    lang = None

    def __init__(self, default_lang):
        super(Lang, self).__init__()
        self.ugettext = None
        self.lang = default_lang
        self.switch_lang(self.lang)

    def gettext(self):
        return self.ugettext

    def _(self, text):
        return self.ugettext(text)

    def fbind(self, name, func, *largs, **kwargs):
        if name == "_":
            self.observers.append((func, largs, kwargs))
        else:
            return super(Lang, self).fbind(name, func, largs, kwargs)

    def funbind(self, name, func, *largs, **kwargs):
        if name == "_":
            key = (func, largs, kwargs)
            if key in self.observers:
                self.observers.remove(key)
        else:
            return super(Lang, self).funbind(name, func, largs, kwargs)

    def switch_lang(self, lang):
        locales = gettext.translation(lang, "locales", languages=[lang])
        self.ugettext = locales.gettext

        for func, largs, kwargs in self.observers:
            func(largs, None, None)
