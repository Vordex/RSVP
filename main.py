from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.core.window import Window
from kivy.lang.builder import Builder
from kivy.lang import Observable
from kivy.properties import BooleanProperty, ObjectProperty, StringProperty
from kivy.uix.progressbar import ProgressBar
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.modalview import ModalView
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.textinput import TextInput
from kivy.utils import platform

from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog, MDInputDialog
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.label import Label

import database
from functools import partial
import gettext
import rsvp

settings = database.Settings()

if settings.language == "en":
    _ = gettext.gettext
else:
    locales = gettext.translation(settings.language, "locales", languages=[settings.language])
    _ = locales.gettext


class Words(Observable):
    def __init__(self, **kwargs):
        super(Words, self).__init__(**kwargs)

        self.start = _("Start")
        self.open = _("Open")
        self.image_duration = _("Image Duration")
        self.size = _("Size")
        self.speed = _("Speed")


kv_translate = Words()


class RSVP(MDApp):
    lang = StringProperty(settings.language)

    def __init__(self, **kwargs):
        super(RSVP, self).__init__(**kwargs)

        self.title = "VReader"
        self.theme_cls.primary_palette = "Blue"

        Builder.load_string(open("interface.kv", encoding="utf-8").read(), rulesonly=True)

    def build(self):
        return ScreenManager()


class FileManager(Screen):
    manager_open = BooleanProperty()
    _manager = ObjectProperty()
    file_manager = ObjectProperty()

    def __init__(self, **kwargs):
        super(FileManager, self).__init__(**kwargs)

        Window.bind(on_keyboard=self.events)

        self.screen = ""
        self.dir_select = False
        self.name = ""

    def open(self, screen, dir_select=False):
        self.screen = screen
        self.dir_select = dir_select

        if dir_select:
            dialog = MDDialog(
                title="",
                size_hint=(0.8, 0.4),
                text_button_ok=_("Ok"),
                text_button_cancel=_("Cancel"),
                events_callback=partial(self._open, (screen, dir_select))
            )
            dialog.open()
        else:
            self.manager.current = "file_manager"

            if not self._manager:
                self._manager = ModalView(size_hint=(1, 1), auto_dismiss=False)
                self.file_manager = MDFileManager(
                    exit_manager=lambda x: self.exit_manager(),
                    select_path=self.select_path
                )
                self._manager.add_widget(self.file_manager)

            if platform == "win":
                self.file_manager.show("C:/")
            else:
                self.file_manager.show("/")

            self.manager_open = True
            self._manager.open()

    def _open(self, screen, *args):
        self.manager.current = "file_manager"

        if not self._manager:
            self._manager = ModalView(size_hint=(1, 1), auto_dismiss=False)
            self.file_manager = MDFileManager(
                exit_manager=lambda x: self.exit_manager(),
                select_path=self.select_path
            )
            self._manager.add_widget(self.file_manager)

        if platform == "win":
            self.file_manager.show("C:/")
        else:
            self.file_manager.show("/")

        self.manager_open = True
        self._manager.open()

    def select_path(self, path):
        if not self.dir_select:
            self.exit_manager()
            self.manager.get_screen(self.screen).load(path)
        else:
            if len(path.split("\\")[-1].split(".")) == 1:
                dialog = MDInputDialog(
                    title=_("Choose a name for the file"),
                    hint_text="Teste",
                    size_hint=(0.8, 0.4),
                    text_button_ok=_("Convert"),
                )
                self.name = dialog.hint_text
                dialog.events_callback = partial(self.select_name, (path,))
                dialog.open()

    def select_name(self, path, *args):
        self.exit_manager()
        self.manager.get_screen(self.screen).save(path, self.name)

    def exit_manager(self):
        self._manager.dismiss()
        self.manager_open = False
        self.manager.current = self.screen

    def events(self, instance, keyboard, keycode, text, modifiers):
        if keyboard in (1001, 27):
            if self.manager_open:
                self.file_manager.back()
        return True


class Files(Screen):
    def __init__(self, **kwargs):
        super(Files, self).__init__(**kwargs)

        self.file = ""
        self.arq = None

        self.box = BoxLayout(orientation="vertical")
        self.input = TextInput(size_hint_y=None, height=30, multiline=False)
        self.dialog = None

        self.loop = None

    def load(self, _file):
        self.file = _file

        if self.file.split(".")[-1] == "rsvp":
            self.arq = rsvp.File(self.file)
            self.manager.current = "reader"

            try:
                self.manager.get_screen("reader").pre_read(self.arq)
            except KeyError:
                dialog = Popup(
                    title=_("Error"),
                    size_hint=[None, None],
                    size=[400, 200],
                    content=Label(text=_("Sorry, it was not possible to open this file"))
                )
                dialog.open()

                self.manager.current = "files"

        elif self.file.split(".")[-1] == "pdf" or self.file.split(".")[-1] == "epub":
            self.dialog = MDDialog(
                title=_("Error"),
                text=_("This file is not compatible"),
                text_button_ok=_("Convert"),
                text_button_cancel=_("Cancel"),
                size_hint=(0.8, 0.3),
                events_callback=self.convert
            )
            self.dialog.open()

        else:
            if len(self.file.split(".")[-1].split(".")) > 1:
                dialog = MDDialog(
                    title=_("Error"),
                    text=_("This file is not compatible"),
                    text_button_ok=_("Back"),
                    size_hint=(0.8, 0.3),
                )
                dialog.open()
            else:
                dialog = MDDialog(
                    title=_("Error"),
                    text=_("Please select some file"),
                    text_button_ok=_("Back"),
                    size_hint=(0.8, 0.3),
                )
                dialog.open()

    def convert(self, *args):
        self.dialog.dismiss()
        self.manager.get_screen("file_manager").open("files", True)

    def save(self, directory, name, *args):
        directory = directory[0]

        dialog = Popup(title=_("Converting file"), size_hint=[0.5, 0.5])
        box = BoxLayout(orientation="vertical")
        progress_bar = ProgressBar(max=100)
        progress_label = Label()
        box.add_widget(progress_label)
        box.add_widget(progress_bar)
        dialog.add_widget(box)
        dialog.open()
        self.arq = rsvp.File(self.file, directory, name, existing=False)

        while True:
            progress_label.text = _("{}% completed").format(rsvp.progress)
            progress_bar.value = rsvp.progress

            if rsvp.progress == 100:
                dialog.dismiss()
                self.manager.current = "reader"
                self.manager.get_screen("reader").pre_read(self.arq)

                break


class Reader(Screen):
    def __init__(self, **kwargs):
        super(Reader, self).__init__(**kwargs)

        self.file = None
        self.words = None
        self.len_words = None
        self.info = None
        self.position = None

        self.text = Label(color=[0, 0, 0, 1], bold=True)
        self.image = None

        self.reading = False

    def pre_read(self, file):
        self.file = file
        self.info = file.get_info()
        self.position = self.info["starting point"]
        self.words = file.read_lines()
        self.len_words = len(self.words)

        self.image = Image64(self.file.get_image("cover.png"))

        self.ids.slider_speed.value = settings.speed
        self.ids.slider_size.value = settings.size
        self.ids.slider_time.value = settings.time

        Clock.schedule_interval(lambda x: self.update_size(), 0.05)

        self.update()

    def update(self):
        if self.position == 0 or self.reading:
            self.ids.image_left.disabled = True

        else:
            self.ids.image_left.disabled = False

        if self.position + 1 == self.len_words or self.reading:
            self.ids.image_left.disabled = True

        else:
            self.ids.image_left.disabled = False

        if len(self.words[self.position].split()) > 1:
            self.ids.box.remove_widget(self.text)
            self.ids.box.remove_widget(self.image)
            self.ids.box.add_widget(self.image)
            self.image.update(self.file.get_image(self.words[self.position].split()[1]))

        else:
            self.ids.box.remove_widget(self.text)
            self.ids.box.remove_widget(self.image)
            self.ids.box.add_widget(self.text)
            self.text.text = self.words[self.position]

    def update_size(self):
        self.text.font_size = self.ids.slider_size.value
        settings.update(self.ids.slider_speed.value, self.ids.slider_size.value, self.ids.slider_time.value)

    def back(self):
        if not self.ids.image_left.disabled:
            self.position -= 1
            self.update()

    def next(self):
        if not self.ids.image_right.disabled:
            self.position += 1
            self.update()

    def read(self):
        if not self.reading:
            self.ids.on_off.text = _("Pause")
            self.reading = True
            self.loop1()
        else:
            self.ids.on_off.text = _("Start")
            self.ids.image_left.disabled = False
            self.ids.image_right.disabled = False
            self.reading = False

        if self.position == 0 or self.reading:
            self.ids.image_left.disabled = True

        else:
            self.ids.image_left.disabled = False

        if self.position + 1 == self.len_words or self.reading:
            self.ids.image_right.disabled = True

        else:
            self.ids.image_right.disabled = False

    def loop1(self):
        if self.position == self.len_words:
            self.read()
        if self.reading:
            if len(self.words[self.position].split()) > 1:
                Clock.schedule_once(lambda x: self.loop2(), self.ids.slider_time.value)
            else:
                Clock.schedule_once(lambda x: self.loop2(), 60 / self.ids.slider_speed.value)

    def loop2(self):
        self.update()
        self.loop1()
        self.position += 1

    def close(self):
        self.manager.current = "files"


class ImageButton(ButtonBehavior, Image):
    def __init__(self, **kwargs):
        super(ImageButton, self).__init__(**kwargs)


class Image64(Image):
    def __init__(self, image, **kwargs):
        super(Image64, self).__init__(**kwargs)

        self.source = "images/transparent.png"
        self._data = image
        self.core_image = CoreImage(self._data, ext="png")
        self.texture = self.core_image.texture
        self.pos_hint = {"center_x": .5, "center_y": .5}

    def update(self, image):
        self._data = image
        self.core_image = CoreImage(self._data, ext="png")
        self.texture = self.core_image.texture


class Tabe(TabbedPanel):
    pass


if __name__ == "__main__":
    RSVP().run()

    database.close()
