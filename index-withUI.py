import sys
from pathlib import Path
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QFileDialog

from wallhaven_downloader.core import build_search_url, download_wallpapers


class DownloadWorker(QtCore.QThread):
    progress = QtCore.pyqtSignal(int, int, int)
    finished = QtCore.pyqtSignal(int, int, int)
    failed = QtCore.pyqtSignal(str)

    def __init__(self, url, page_count, output_dir):
        super().__init__()
        self.url = url
        self.page_count = int(page_count)
        self.output_dir = output_dir
        self.downloaded = 0
        self.skipped = 0
        self.errors = 0

    def run(self):
        try:
            download_wallpapers(
                self.url,
                self.page_count,
                self.output_dir,
                progress_callback=self.on_progress,
            )
            self.finished.emit(self.downloaded, self.skipped, self.errors)
        except Exception as exc:
            self.failed.emit(str(exc))

    def on_progress(self, result):
        if result.error is not None:
            self.errors += 1
        elif result.skipped:
            self.skipped += 1
        else:
            self.downloaded += 1
        self.progress.emit(self.downloaded, self.skipped, self.errors)


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(794, 497)
        self.mesb = QMessageBox
        # 类型动漫。。
        self.mark = [1, 1, 1]
        # SFW
        self.mark_2 = [1, 1, 0]
        self.file = ''

        # date_added按时间
        self.sorting = 'toplist'
        self.topRange = '1M'
        self.categories = '111'
        self.purity = '110'
        font = QtGui.QFont()
        font.setPointSize(12)
        self.Button_start = QtWidgets.QPushButton(Form)
        self.Button_start.setGeometry(QtCore.QRect(510, 50, 169, 61))
        self.Button_start.setFont(font)
        self.Button_start.setObjectName("Button_start")
        self.Button_start.clicked.connect(lambda: self.start(Form))
        self.Button_start.setVisible(False)

        self.Button_choose_file = QtWidgets.QPushButton(Form)
        self.Button_choose_file.setGeometry(QtCore.QRect(320, 240, 121, 61))
        self.Button_choose_file.setFont(font)
        self.Button_choose_file.setObjectName("Button_choose_file")
        self.Button_choose_file.clicked.connect(lambda: self.get_filename(Form))

        self.Button_desktop_folder = QtWidgets.QPushButton(Form)
        self.Button_desktop_folder.setGeometry(QtCore.QRect(510, 50, 169, 61))
        self.Button_desktop_folder.setFont(font)
        self.Button_desktop_folder.setObjectName("Button_desktop_folder")
        self.Button_desktop_folder.clicked.connect(lambda: self.use_desktop_folder(Form))

        # 按条件下载
        self.Button_condition_start = QtWidgets.QPushButton(Form)
        self.Button_condition_start.setGeometry(QtCore.QRect(570, 380, 111, 51))
        self.Button_condition_start.setObjectName("Button_condition_start")
        self.Button_condition_start.clicked.connect(lambda: self.condition_down(Form))

        self.Page_input = QtWidgets.QLineEdit(Form)
        self.Page_input.setGeometry(QtCore.QRect(220, 66, 231, 31))
        self.Page_input.setText("")
        self.Page_input.setObjectName("Page_input")
        self.Page_input.setVisible(False)

        # 单张下载url
        self.Label_page = QtWidgets.QLabel(Form)
        self.Label_page.setGeometry(QtCore.QRect(20, 66, 181, 31))
        self.Label_page.setObjectName("Label_page")
        self.Label_page.setVisible(False)

        # 录下载张数
        self.Label_down_nums = QtWidgets.QLabel(Form)
        self.Label_down_nums.setGeometry(QtCore.QRect(500, 240, 260, 61))
        self.Label_down_nums.setObjectName("Label_down_nums")
        font = QtGui.QFont()
        font.setFamily("Adobe Devanagari")
        font.setPointSize(12)
        self.Label_down_nums.setFont(font)

        self.spinBox_nums_common = QtWidgets.QSpinBox(Form)
        self.spinBox_nums_common.setGeometry(QtCore.QRect(220, 130, 61, 31))
        self.spinBox_nums_common.setMinimum(1)
        self.spinBox_nums_common.setMaximum(500)
        self.spinBox_nums_common.setObjectName("spinBox_nums_rmf")
        self.spinBox_nums_common.setVisible(False)

        self.spinBox_start_num = QtWidgets.QSpinBox(Form)
        self.spinBox_start_num.setGeometry(QtCore.QRect(280, 430, 61, 31))
        self.spinBox_start_num.setMinimum(1)
        self.spinBox_start_num.setMaximum(500)
        self.spinBox_start_num.setObjectName("spinBox_start_num")

        self.spinBox_nums_end = QtWidgets.QSpinBox(Form)
        self.spinBox_nums_end.setGeometry(QtCore.QRect(450, 430, 61, 31))
        self.spinBox_nums_end.setMinimum(1)
        self.spinBox_nums_end.setMaximum(500)
        self.spinBox_nums_end.setValue(20)
        self.spinBox_nums_end.setObjectName("spinBox_nums_end")


        self.label_start_num = QtWidgets.QLabel(Form)
        self.label_start_num.setGeometry(QtCore.QRect(200, 440, 72, 15))
        self.label_start_num.setObjectName("label_start_num")
        self.label_end_num = QtWidgets.QLabel(Form)
        self.label_end_num.setGeometry(QtCore.QRect(370, 440, 72, 15))
        self.label_end_num.setObjectName("label_end_num")

        self.Label_nums = QtWidgets.QLabel(Form)
        self.Label_nums.setGeometry(QtCore.QRect(120, 130, 91, 21))
        self.Label_nums.setObjectName("Label_nums")
        self.Label_nums.setVisible(False)

        self.comboBox_time = QtWidgets.QComboBox(Form)
        self.comboBox_time.setGeometry(QtCore.QRect(250, 360, 121, 31))
        self.comboBox_time.setObjectName("comboBox_time")
        self.comboBox_time.addItem("")
        self.comboBox_time.addItem("")
        self.comboBox_time.addItem("")
        self.comboBox_time.addItem("")
        self.comboBox_time.addItem("")

        self.comboBox_condition = QtWidgets.QComboBox(Form)
        self.comboBox_condition.setGeometry(QtCore.QRect(400, 360, 111, 31))
        self.comboBox_condition.setObjectName("comboBox_condition")
        self.comboBox_condition.addItem("")
        self.comboBox_condition.addItem("")
        self.comboBox_condition.addItem("")
        self.comboBox_condition.addItem("")
        self.comboBox_condition.addItem("")

        # General Anime People
        self.checkBox_general = QtWidgets.QCheckBox(Form)
        self.checkBox_general.setGeometry(QtCore.QRect(30, 349, 61, 19))
        self.checkBox_general.setAutoFillBackground(True)
        self.checkBox_general.setChecked(True)
        self.checkBox_general.setObjectName("checkBox_General")
        self.checkBox_general.stateChanged.connect(lambda: self.update_categories(self.checkBox_general))
        self.checkBox_anime = QtWidgets.QCheckBox(Form)
        self.checkBox_anime.setGeometry(QtCore.QRect(100, 349, 61, 19))
        self.checkBox_anime.setAutoFillBackground(True)
        self.checkBox_anime.setChecked(True)
        self.checkBox_anime.setTristate(False)
        self.checkBox_anime.setObjectName("checkBox_Anime")
        self.checkBox_anime.stateChanged.connect(lambda: self.update_categories(self.checkBox_anime))
        self.checkBox_people = QtWidgets.QCheckBox(Form)
        self.checkBox_people.setGeometry(QtCore.QRect(170, 349, 61, 19))
        self.checkBox_people.setAutoFillBackground(True)
        self.checkBox_people.setChecked(True)
        self.checkBox_people.setTristate(False)
        self.checkBox_people.setObjectName("checkBox_People")
        self.checkBox_people.stateChanged.connect(lambda: self.update_categories(self.checkBox_people))

        # ==========SFW  Sketchy   NSFW  ==============

        self.checkBox_SFW = QtWidgets.QCheckBox(Form)
        self.checkBox_SFW.setGeometry(QtCore.QRect(20, 380, 51, 31))
        self.checkBox_SFW.setAutoFillBackground(True)
        self.checkBox_SFW.setChecked(True)
        self.checkBox_SFW.setObjectName("checkBox_SFW")
        self.checkBox_SFW.stateChanged.connect(lambda: self.update_purity(self.checkBox_SFW))
        self.checkBox_Sketchy = QtWidgets.QCheckBox(Form)
        self.checkBox_Sketchy.setGeometry(QtCore.QRect(80, 380, 81, 31))
        self.checkBox_Sketchy.setAutoFillBackground(True)
        self.checkBox_Sketchy.setChecked(True)
        self.checkBox_Sketchy.setTristate(False)
        self.checkBox_Sketchy.setObjectName("checkBox_Sketchy")
        self.checkBox_Sketchy.stateChanged.connect(lambda: self.update_purity(self.checkBox_Sketchy))
        self.checkBox_NSFW = QtWidgets.QCheckBox(Form)
        self.checkBox_NSFW.setGeometry(QtCore.QRect(170, 380, 61, 31))
        self.checkBox_NSFW.setAutoFillBackground(True)
        self.checkBox_NSFW.setTristate(False)
        self.checkBox_NSFW.setObjectName("checkBox_NSFW")
        self.checkBox_NSFW.stateChanged.connect(lambda: self.update_purity(self.checkBox_NSFW))

        self.label = QtWidgets.QLabel(Form)
        self.label.setGeometry(QtCore.QRect(110, 200, 591, 51))
        self.label.setObjectName("label")
        self.line = QtWidgets.QFrame(Form)
        self.line.setGeometry(QtCore.QRect(0, 310, 871, 16))
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")

        self.line = QtWidgets.QFrame(Form)
        self.line.setGeometry(QtCore.QRect(0, 210, 871, 16))
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")

        self.retranslateUi(Form)
        self.comboBox_time.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def set_down_nums(self, text="已经下载张数"):
        _translate = QtCore.QCoreApplication.translate
        self.Label_down_nums.setText(_translate("Form", text))

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Wallhaven-Downloader"))
        self.Button_start.setText(_translate("Form", "开始从此页面下载"))
        self.Button_choose_file.setText(_translate("Form", "选择文件夹"))
        self.Button_desktop_folder.setText(_translate("Form", "桌面Wallhaven"))
        self.Label_page.setText(_translate("Form", "输入wallhaven中的网址"))
        self.Label_nums.setText(_translate("Form", "下载页数"))
        self.set_down_nums()
        self.label_start_num.setText(_translate("Form", "起始页码"))
        self.label_end_num.setText(_translate("Form", "下载页数"))
        self.comboBox_time.setCurrentText(_translate("Form", "近一个月的"))
        self.comboBox_time.setItemText(0, _translate("Form", "最新的"))
        self.comboBox_time.setItemText(1, _translate("Form", "近一个月的"))
        self.comboBox_time.setItemText(2, _translate("Form", "近三个月的"))
        self.comboBox_time.setItemText(3, _translate("Form", "近六个月的"))
        self.comboBox_time.setItemText(4, _translate("Form", "近一年的"))
        self.comboBox_time.currentIndexChanged.connect(lambda: self.update_topRange())

        self.comboBox_condition.setItemText(0, _translate("Form", "Top榜单"))
        self.comboBox_condition.setItemText(1, _translate("Form", "收藏榜单"))
        self.comboBox_condition.setItemText(2, _translate("Form", "评论榜单"))
        self.comboBox_condition.setItemText(3, _translate("Form", "Hot榜单NSFW"))
        self.comboBox_condition.setItemText(4, _translate("Form", "随机下载"))
        self.comboBox_condition.currentIndexChanged.connect(lambda: self.updata_sorting())


        self.checkBox_Sketchy.setText(_translate("Form", "Sketchy"))
        self.checkBox_SFW.setText(_translate("Form", "SFW"))
        self.checkBox_NSFW.setText(_translate("Form", "NSFW"))
        self.Button_condition_start.setText(_translate("Form", "开始下载"))
        self.checkBox_general.setText(_translate("Form", "General"))
        self.checkBox_anime.setText(_translate("Form", "Anime"))
        self.checkBox_people.setText(_translate("Form", "People"))
        # self.label.setText(_translate("Form", "输入指定网站可以从指定页面向后按 ！开始！ 下载，不输入指定网站按 ！开始条件下载 ！ \n\t\t\t 一次下载大约23张 \n\t\t 若长时间不下载，可以重新点击开始尝试"))

    def updateEndSpinBoxNum(self):
        self.spinBox_nums_end.setMaximum(500)

    def get_filename(self, form):
        self.file = QFileDialog.getExistingDirectory(form, "选择文件夹", ".")
        if self.file != '':
            self.mesb.about(form, '对不起！', '选择成功  ' + self.file)
        else:
            self.mesb.about(form, '对不起！', '选择失败  ')

    def use_desktop_folder(self, form):
        desktop = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.DesktopLocation)
        if desktop == '':
            desktop = str(Path.home() / 'Desktop')
        target = Path(desktop) / 'Wallhaven'
        target.mkdir(parents=True, exist_ok=True)
        self.file = str(target)
        self.mesb.about(form, '提示', '下载目录已设置为  ' + self.file)

    def downLoad(self,url,num,file_path,form):
        self.set_download_controls_enabled(False)
        self.set_down_nums('已经下载 0 张，跳过 0 张，失败 0 张')
        self.worker = DownloadWorker(url, num, file_path)
        self.worker.progress.connect(self.on_download_progress)
        self.worker.finished.connect(lambda downloaded, skipped, failed: self.on_download_finished(form, downloaded, skipped, failed))
        self.worker.failed.connect(lambda message: self.on_download_failed(form, message))
        self.worker.start()
        self.mesb.about(form, '提示', '开始下载，稍等片刻')

    def set_download_controls_enabled(self, enabled):
        self.Button_condition_start.setEnabled(enabled)
        self.Button_start.setEnabled(enabled)
        self.Button_choose_file.setEnabled(enabled)
        self.Button_desktop_folder.setEnabled(enabled)

    def on_download_progress(self, downloaded, skipped, failed):
        self.set_down_nums(f'已经下载 {downloaded} 张，跳过 {skipped} 张，失败 {failed} 张')

    def on_download_finished(self, form, downloaded, skipped, failed):
        self.set_download_controls_enabled(True)
        self.set_down_nums(f'下载完成：成功 {downloaded} 张，跳过 {skipped} 张，失败 {failed} 张')
        self.mesb.about(form, '提示', f'下载完成：成功 {downloaded} 张，跳过 {skipped} 张，失败 {failed} 张')

    def on_download_failed(self, form, message):
        self.set_download_controls_enabled(True)
        self.set_down_nums('下载失败')
        self.mesb.about(form, '错误', '下载失败：' + message)



    def start(self, form):
        if self.file != '':
            if self.Page_input.text() != '':
                try:
                    self.downLoad(self.Page_input.text(), self.spinBox_nums_common.text(), self.file, form)
                except Exception as exc:
                    self.mesb.about(form, '错误', '出错：' + str(exc))
            else:
                self.mesb.about(form, '对不起！', '先输入指定页面再开始')
        else:
            self.mesb.about(form, '对不起！', '先选择路径')

    def update_categories(self, check_box):
        name = check_box.objectName()
        if check_box.isChecked():
            if name == 'checkBox_General':
                self.mark[0] = 1
            elif name == 'checkBox_Anime':
                self.mark[1] = 1
            elif name == 'checkBox_People':
                self.mark[2] = 1
        else:
            if name == 'checkBox_General':
                self.mark[0] = 0
            elif name == 'checkBox_Anime':
                self.mark[1] = 0
            elif name == 'checkBox_People':
                self.mark[2] = 0
        self.categories = ''
        for i in self.mark:
            self.categories = self.categories + str(i)

    def update_purity(self, check_box):
        name = check_box.objectName()
        if check_box.isChecked():
            if name == 'checkBox_SFW':
                self.mark_2[0] = 1
            elif name == 'checkBox_Sketchy':
                self.mark_2[1] = 1
            elif name == 'checkBox_NSFW':
                self.mark_2[2] = 1
        else:
            if name == 'checkBox_SFW':
                self.mark_2[0] = 0
            elif name == 'checkBox_Sketchy':
                self.mark_2[1] = 0
            elif name == 'checkBox_NSFW':
                self.mark_2[2] = 0
        self.purity = ''
        for i in self.mark_2:
            self.purity = self.purity + str(i)

    def update_topRange(self):
        choice_time = self.comboBox_time.currentText()
        if choice_time == '近一个月的':
            self.topRange = '1M'
        elif choice_time == '最新的':
            self.topRange = '1d'
        elif choice_time == '近三个月的':
            self.topRange = '3M'
        elif choice_time == '近六个月的':
            self.topRange = '6M'
        else:
            self.topRange = '1y'

    def updata_sorting(self):
        choice_time = self.comboBox_condition.currentText()
        if choice_time == 'Top榜单':
            self.sorting = 'toplist'
        elif choice_time == '收藏榜单':
            self.sorting = 'favorites'
        elif choice_time == '评论榜单':
            self.sorting = 'views'
        elif choice_time == 'Hot榜单NSFW':
            self.sorting = 'hot'
        else:
            self.sorting = 'random'

    def condition_down(self, form):
        if self.file != '':
            try:
                fixed_url = build_search_url(
                    sorting=self.sorting,
                    top_range=self.topRange,
                    purity=self.purity,
                    categories=self.categories,
                    start_page=int(self.spinBox_start_num.text()),
                )
                num = int(self.spinBox_nums_end.text())
                self.downLoad(fixed_url,num,self.file,form)
            except Exception as exc:
                self.mesb.about(form, '错误', '出错：' + str(exc))
        else:
            self.mesb.about(form, '对不起！', '先选择路径')


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_Form()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

