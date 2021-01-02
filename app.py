import os
import sys
import configparser as confp
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox

from modules import background_process as bp, UIToolsC, UISettingsCommand


class ToolsAppMain(QtWidgets.QMainWindow, UIToolsC.UiMainWindow):
    def __init__(self):
        # переменные
        self.originVideofilePath = None
        self.settingsWindow = None

        self.ffmpeg_path = "ffmpeg/bin"
        self.keyfile_path = "file.key"
        self.keyinfofile_path = "file.keyinfo"

        self.m3u8key = "mysecurekey"
        self.video_bitrate = 5000

        self.printCommandInTerminal = False
        self.printBanner = False

        # инициализация
        super().__init__()
        self.setupUi(self)
        self.load_config()
        self.command_selector.addItem("Информация о файле")
        self.command_selector.addItem("Конвертирование")
        self.command_selector.addItem("Изменение битрейта")
        self.run_button.setDisabled(True)
        self.toolButton.setDisabled(True)
        self.command_selector.setDisabled(True)
        self.terminal.addItem("Ready...")
        self.terminal.addItem("FFmpeg Path: " + self.ffmpeg_path)
        self.second_process = bp.BackgroundProcess(main_window=self, commands=[])

        # обработчик действий
        self.select_file_button.clicked.connect(self.browse_videofile)
        self.help_info.triggered.connect(self.help_window)
        self.run_button.clicked.connect(self.run_command)
        self.toolButton.clicked.connect(self.commands_settings)

    def load_config(self):
        config = confp.ConfigParser()
        config.read('config.ini')
        self.ffmpeg_path = config["Directories"]["ffmpeg_folder"]
        self.keyfile_path = config["Directories"]["m3u8keyfile"]
        self.keyinfofile_path = config["Directories"]["m3u8keyinfofile"]
        self.m3u8key = str(config["Variables"]["m3u8key"])
        self.video_bitrate = int(config["Variables"]["video_bitrate"])
        self.printCommandInTerminal = bool(config["Options"]["PrintCommandInTerminal"])
        self.printBanner = bool(config["Options"]["PrintBanner"])

    def run_command(self):
        print(self.command_selector.currentIndex())
        print(self.originVideofilePath)
        if self.originVideofilePath is not None:
            if self.command_selector.currentIndex() == 0:
                self.get_info()
            elif self.command_selector.currentIndex() == 2:
                self.change_bitrate()
            else:
                self.terminal.addItem("Command not found")
        else:
            self.terminal.addItem("Video not found")

    def commands_settings(self):
        if not self.settingsWindow:
            self.settingsWindow = Settings(self)
        # Settings.setStyle('Fusion')
        self.settingsWindow.show()

    @staticmethod
    def help_window():  # TODO: Enter info
        help_message = QMessageBox()
        help_message.setIcon(QMessageBox.Information)
        help_message.setText("Как использовать?")
        help_message.setInformativeText("Этот приложение генерирует и запускает команды FFmpeg для различных "
                                        "манипуляций с видео.\n\nВыберите исходное видео, функцию, а затем запустите "
                                        "процесс. Все данные будут выводиться в консоль в основном окне.")
        help_message.setWindowTitle("Справка")
        help_message.setStandardButtons(QMessageBox.Ok)
        help_message.exec_()

    def browse_videofile(self):

        self.run_button.setEnabled(False)
        self.toolButton.setEnabled(False)
        self.command_selector.setEnabled(False)

        path_request = QtWidgets.QFileDialog
        options = QtWidgets.QFileDialog.Options()
        self.originVideofilePath, _ = path_request.getOpenFileName(self, "Укажите путь к видеофайлу...", "",
                                                                   "Video File (*.mp4 *.avi)",
                                                                   options=options)
        if self.originVideofilePath:
            self.terminal.addItem("Selected video: " + self.originVideofilePath)
            self.run_button.setEnabled(True)
            self.toolButton.setEnabled(True)
            self.command_selector.setEnabled(True)

    def browse_ffmpegBin(self):
        path_request = QtWidgets.QFileDialog
        options = QtWidgets.QFileDialog.Options()
        self.ffmpeg_path, _ = path_request.getExistingDirectory(self, "Укажите путь к папке...", options=options)

        if self.ffmpeg_path:
            self.terminal.addItem("FFmpeg Path changed: " + self.ffmpeg_path)

    def get_info(self):
        if self.originVideofilePath is None:
            self.terminal.addItem("ERROR: Videofile path incorrect.")
            self.terminal.addItem("Reselect videofile.")
        else:
            command = self.ffmpeg_path + \
                      "/ffmpeg.exe -i \"" + self.originVideofilePath + "\" -hide_banner"
            self.second_process.commands = [command]
            print(self.second_process.commands)
            self.second_process.start()
            self.terminal.scrollToBottom()

    def change_bitrate(self):
        if self.originVideofilePath is None:
            self.terminal.addItem("ERROR: Videofile path incorrect.")
            self.terminal.addItem("Reselect videofile.")
        else:
            command = self.ffmpeg_path + \
                      "/ffmpeg.exe -i \"" + self.originVideofilePath + "\" -hide_banner -c:v libx264 -b:v 1000K " \
                                                                       "output.mp4 "
            self.second_process.commands = [command]
            print(self.second_process.commands)
            self.second_process.start()
            self.terminal.scrollToBottom()

    def conversion(self):
        if self.originVideofilePath is None:
            self.terminal.addItem("ERROR: Videofile path incorrect.")
            self.terminal.addItem("Reselect videofile.")
        else:
            full_path = self.originVideofilePath  # /path/to/file.mp4
            full_name = os.path.basename(self.originVideofilePath)  # полное имя файла file.mp4
            name = os.path.splitext(full_name)[0]  # имя без расширения file
            # new_folder_name = name.replace(" ", "_")
            # path = full_path.replace(full_name, new_folder_name)
            try:
                # Создание новой output папки
                os.mkdir(self.work_dir + "\\" + name.replace(" ", "_"))

                # Создание файла key
                key_file_path = self.work_dir + "\\" + name.replace(" ", "_") + "\\" + "file.key"
                key_file = open(key_file_path, "w")
                # key_file.truncate()
                key_file.write("KEY")
                key_file.close()

                # Создание файла keyinfo
                keyinfo_file_path = self.work_dir + "\\file.keyinfo"
                keyinfo_file = open(keyinfo_file_path, 'w')
                keyinfo_file.write("file.key\n" + key_file_path)
                keyinfo_file.close()

                # Рабочие комманды для запуска стороннего процесса
                self.cmd_h264 = "ffmpeg/bin/ffmpeg.exe -i \"" + full_path + "\" -c copy -bsf:v h264_mp4toannexb " \
                                                                            "-hls_time 10 " + \
                                "-hls_key_info_file \"" + keyinfo_file_path + "\" " + "-hls_list_size 0 " + \
                                name.replace(" ", "_") + "\\" + name.replace(" ", "_") + ".m3u8"

                self.cmd_hevc = "ffmpeg/bin/ffmpeg.exe -i \"" + full_path + "\" -c copy -bsf:v hevc_mp4toannexb " \
                                                                            "-hls_time 10 " + \
                                "-hls_key_info_file \"" + keyinfo_file_path + "\" " + "-hls_list_size 0 " + \
                                name.replace(" ", "_") + "\\" + name.replace(" ", "_") + ".m3u8"

                self.listWidget.addItem(self.cmd_hevc)
                self.listWidget.addItem(self.cmd_h264)
                self.listWidget.addItem("...")

            except OSError:
                self.listWidget.scrollToBottom()
                self.listWidget.addItem("Command error. Video file not selected.")

            else:
                self.listWidget.addItem(f"Command ready.")
                self.External_command_thread.command_h264 = self.cmd_h264
                self.External_command_thread.command_hevc = self.cmd_hevc
                self.h264Button.setEnabled(False)
                self.FileSelectButton.setEnabled(False)
                self.launch_command()


class Settings(QtWidgets.QWidget, UISettingsCommand.Ui_SettingsWindow):
    def __init__(self, parent=None):
        super().__init__(parent, QtCore.Qt.Window)
        self.setupUi(self)
        self.config = confp.ConfigParser()
        self.config.read('config.ini')
        self.ffmpeg_path = self.config["Directories"]["ffmpeg_folder"]
        self.keyfile_path = self.config["Directories"]["m3u8keyfile"]
        self.keyinfofile_path = self.config["Directories"]["m3u8keyinfofile"]

        self.m3u8key = str(self.config["Variables"]["m3u8key"])
        self.KeyEdit.setText(self.m3u8key)

        self.video_bitrate = int(self.config["Variables"]["video_bitrate"])
        self.bitrate_settings.setValue(self.video_bitrate)

        # self.printCommandInTerminal = bool(self.config["Options"]["printcommandinterminal"])
        # self.terminal_output.setEnabled(self.printCommandInTerminal)
        #
        # self.printBanner = bool(self.config["Options"]["printbanner"])
        # self.banner_settings.setEnabled(self.printBanner)

        self.OkButton.clicked.connect(self.WriteChanges)

    def WriteChanges(self):
        if self.KeyEdit.text() is not None:
            self.m3u8key = self.KeyEdit.text()
            self.config["Variables"]["m3u8key"] = self.KeyEdit.text()
        else:
            self.config["Variables"]["m3u8key"] = "defaultkey"
        self.video_bitrate = str(self.bitrate_settings.value)

        with open('config.ini', 'w') as configfile:
            self.config.write(configfile)

        self.destroy()


def main():
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    # app.setStyle('Fusion')
    app.setWindowIcon(QIcon('assets/logo.png'))
    window = ToolsAppMain()  # Создаём объект
    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение


if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    main()  # то запускаем функцию main()
