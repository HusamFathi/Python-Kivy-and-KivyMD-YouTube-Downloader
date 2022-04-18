from kivy.config import Config

Config.set('kivy', 'window_icon', 'assets/icon/download.ico')

import datetime
import os
from pathlib import Path

from hurry.filesize import size
from kivy import platform
from kivy.clock import mainthread
from kivy.lang import Builder
from kivy.properties import StringProperty, ListProperty, BooleanProperty, ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from kivymd.app import MDApp
from kivymd.toast import toast
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFloatingActionButton
from kivymd.uix.card import MDCard
from kivymd.uix.screen import MDScreen
import threading

from kivymd.uix.tooltip import MDTooltip
from pytube import YouTube, Playlist


class DownloadCard(MDCard):
    yt = ObjectProperty()
    title = StringProperty('Loading')
    thumbnail = StringProperty()
    resolution = StringProperty('Loading')
    link = StringProperty()
    download_icon = StringProperty('download')
    length = StringProperty('Loading')
    file_size = StringProperty('Loading')
    download = BooleanProperty(False)
    downloading = BooleanProperty(False)
    isNoTDownloadable = BooleanProperty(True)

    def progress_func(self, stream, chunk, bytes_remaining):
        value = round((1 - bytes_remaining / stream.filesize) * 100, 3)
        self.ids.progress_bar.value = value

    def complete_func(self, *args):
        self.download_icon = 'check-circle'

    def remove_from_list(self):
        app = MDApp.get_running_app()
        app.root.ids.scroll_box.remove_widget(self)
        if self.link in app.root.playlist:
            app.root.playlist.remove(self.link)

    def on_link(self, *args):
        app = MDApp.get_running_app()
        app.isLoading = True
        threading.Thread(target=self.start).start()

    def start(self):
        self.ids.progress_bar.value = 0
        self.download_icon = 'download'
        try:
            self.yt = YouTube(
                self.link,
                on_progress_callback=self.progress_func,
                on_complete_callback=self.complete_func,
            )
            self.title = self.yt.title
            self.thumbnail = str(self.yt.thumbnail_url)
            self.resolution = str(self.yt.streams.get_highest_resolution().resolution)
            self.length = str(datetime.timedelta(seconds=self.yt.length))
            self.file_size = size(self.yt.streams.get_highest_resolution().filesize)
            self.isNoTDownloadable = False
        except Exception as e:
            app = MDApp.get_running_app()
            app.isLoading = False
            self.remove_from_list()
            print(e)
            toast(text=f'Some thing wrong {e}')

    def download_video(self, yt, operation):
        self.downloading = True
        app = MDApp.get_running_app()
        try:
            if operation == "Video and Audio":
                yt.streams.get_highest_resolution().download(output_path=app.output_path)
            else:
                user_streams = yt.streams.filte(only_audio=True).first()
                user_streams.download(output_path=app.output_path, filename=yt.title + '.mp3')
        except Exception as e:
            app = MDApp.get_running_app()
            app.isLoading = False
            self.remove_from_list()
            print(e)
            toast(text=f'Some thing wrong {e}')


class YoutubeDownloader(MDScreen):
    link = StringProperty()
    playlist = ListProperty()
    isNotPlayList = BooleanProperty()

    def go(self):
        threading.Thread(target=self.start).start()

    @mainthread
    def start(self):
        self.ids.scroll_box.clear_widgets()
        self.link = self.ids.link_holder.text
        try:
            self.playlist = Playlist(self.link)
            self.isNotPlayList = False
            for play_list_item in self.playlist:
                card = DownloadCard()
                card.link = play_list_item
                self.ids.scroll_box.add_widget(card)
        except:
            self.isNotPlayList = True
            card = DownloadCard()
            card.link = self.link
            self.ids.scroll_box.add_widget(card)

    def download_all(self):
        children = self.ids.scroll_box.children
        for child in children:
            child.download_video(child.yt, child.operation)


class TopBarIconBox(MDBoxLayout):
    pass


class MobileFloatButton(MDFloatingActionButton, MDTooltip):
    pass


class MobileBottomButton(FloatLayout):
    pass


class App(MDApp):
    isLoading = BooleanProperty(False)
    icon = 'assets/icon/download.ico'
    if platform == 'win':
        output_path = f'{str(Path.home() / "Downloads")}/Youtube Downloader/'
    elif platform == 'android':
        from android.storage import primary_external_storage_path
        output_path = f'{str(primary_external_storage_path())}/Youtube Downloader/'

    def build(self):
        root = Builder.load_file('main.kv')
        self.title = 'Youtube Downloader'
        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.primary_palette = 'BlueGray'
        self.theme_cls.accent_palette = 'Amber'

        if platform == 'win':
            root.ids.appbar.add_widget(TopBarIconBox(), 1)
        elif platform == 'android':
            root.add_widget(MobileFloatButton())
            root.add_widget(MobileBottomButton())
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
        return root

    def on_start(self):
        try:
            os.mkdir(self.output_path)
        except:
            pass


App().run()
