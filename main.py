from kivy.app import App
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.lang.builder import Builder
from kivy.uix.progressbar import ProgressBar
from kivy.properties import StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.textinput import TextInput

import database
import language
import rsvp

settings = database.Settings()

tr = language.Lang("pt_BR")
_ = tr.gettext()


class VReader(App):
    lang = StringProperty("pt_BR")

    def build(self):
        Builder.load_string(open("interface.kv", encoding="utf-8").read(), rulesonly=True)
        return ScreenManager()

    # noinspection PyMethodMayBeStatic
    def on_lang(self, lang):
        tr.switch_lang(lang)


class Files(Screen):
    def __init__(self, **kwargs):
        super(Files, self).__init__(**kwargs)

        self.path = ""
        self.file = ""
        self.arq = None

        self.box = BoxLayout(orientation="vertical")
        self.popup = Popup(title=_("Error"), size_hint=(None, None), size=(400, 200), auto_dismiss=False)
        self.file_chooser = FileChooserListView(dirselect=True)
        self.input = TextInput(size_hint_y=None, height=30, multiline=False)

        self.loop = None

    def load(self, _file):
        if len(_file) == 1:
            self.file = _file[0].split("\\")[-1]
            path = _file[0].split("\\")[0:-1]

            for _dir in path:
                self.path = f"{self.path}\\{_dir}"

            if self.file.split(".")[-1] == "rsvp":
                self.arq = rsvp.File(path, self.file)
                self.manager.current = "reader"
                self.manager.get_screen("reader").pre_read(self.arq)

            elif self.file.split(".")[-1] == "pdf" or self.file.split(".")[-1] == "epub":
                box = BoxLayout(size_hint_y=None, height=40)
                box.add_widget(Button(
                    text=_("Convert"),
                    size_hint_y=None,
                    height=40,
                    on_press=lambda x: self.convert()
                ))
                button_cancel = Button(text=_("Cancel"), size_hint_y=None, height=40)
                box.add_widget(button_cancel)
                self.box.add_widget(Label(text=_("You must convert this file to open it"), font_size=15))
                self.box.add_widget(box)
                button_cancel.bind(on_press=self.popup.dismiss)
                self.popup.add_widget(self.box)
                self.popup.open()

            else:
                self.box.add_widget(Label(text=_("This file is not compatible"), font_size=15))
                button_back = Button(text=_("Back"), size_hint_y=None, height=40)
                self.box.add_widget(button_back)
                popup = Popup(
                    title=_("Error"),
                    content=self.box,
                    size_hint=(None, None), size=(400, 200)
                )
                button_back.bind(on_press=popup.dismiss)
                popup.open()

    def convert(self):
        self.popup.dismiss()
        popup = Popup(title="Save", size_hint=[None, None], size=[500, 500], auto_dismiss=False)
        box = BoxLayout(orientation="vertical")
        box.add_widget(self.file_chooser)
        box.add_widget(self.input)
        box2 = BoxLayout(size_hint_y=None, height=50)
        box2.add_widget(Button(text="Cancel", on_press=popup.dismiss))
        box2.add_widget(Button(text="Save", on_press=lambda x: self.save(popup)))
        box.add_widget(box2)
        popup.add_widget(box)
        popup.open()

    def save(self, _popup):
        popup = Popup(title=_("Converting file"))
        box = BoxLayout(orientation="vertical")
        progress_bar = ProgressBar(max=100)
        progress_label = Label()
        box.add_widget(progress_label)
        box.add_widget(progress_bar)
        popup.add_widget(box)
        arq = rsvp.File(self.path[1:], self.file, self.file_chooser.path, self.input.text, False)
        popup.open()

        while True:
            progress_label.text = _("{}% completed").format(rsvp.progress)
            progress_bar.value = rsvp.progress

            if rsvp.progress == 100:
                popup.dismiss()
                _popup.dismiss()
                self.manager.current = "reader"
                self.manager.get_screen("reader").pre_read(arq)

                break


class Reader(Screen):
    def __init__(self, **kwargs):
        super(Reader, self).__init__(**kwargs)

        self.file = None
        self.words = None
        self.len_words = None
        self.info = None
        self.position = None

        self.text = Label(
            color=[0, 0, 0, 1],
            bold=True
        )
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
            self.ids.image_left.source = "images/left_arrow_disabled.png"

        else:
            self.ids.image_left.source = "images/left_arrow.png"

        if self.position == self.len_words or self.reading:
            self.ids.image_right.source = "images/right_arrow_disabled.png"

        else:
            self.ids.image_right.source = "images/right_arrow.png"

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
        if self.ids.image_left.source != "images/left_arrow_disabled.png":
            self.position -= 1
            self.update()

    def next(self):
        if self.ids.image_right.source != "images/right_arrow_disabled.png":
            self.position += 1
            self.update()

    def read(self):
        if not self.reading:
            self.ids.on_off.text = _("Pause")
            self.reading = True
            self.loop1()
        else:
            self.ids.on_off.text = _("Start")
            self.ids.image_left.source = "images/left_arrow.png"
            self.ids.image_right.source = "images/right_arrow.png"
            self.reading = False

        if self.position == 0 or self.reading:
            self.ids.image_left.source = "images/left_arrow_disabled.png"

        else:
            self.ids.image_left.source = "images/left_arrow.png"

        if self.position == self.len_words or self.reading:
            self.ids.image_right.source = "images/right_arrow_disabled.png"

        else:
            self.ids.image_right.source = "images/right_arrow.png"

    def loop1(self):
        if self.reading:
            if len(self.words[self.position].split()) > 1:
                Clock.schedule_once(lambda x: self.loop2(), self.ids.slider_time.value)
            else:
                Clock.schedule_once(lambda x: self.loop2(), 60 / self.ids.slider_speed.value)

    def loop2(self):
        self.position += 1
        self.update()
        self.loop1()


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
    VReader().run()

    database.close()
