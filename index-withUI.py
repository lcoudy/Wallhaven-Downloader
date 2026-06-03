import sys
from pathlib import Path

from PyQt5 import QtCore, QtWidgets

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
        Form.resize(720, 430)
        Form.setMinimumSize(640, 390)
        Form.setWindowTitle("Wallhaven-Downloader")
        Form.setStyleSheet(
            """
            QWidget {
                color: #202124;
                font-size: 10pt;
            }
            QGroupBox {
                font-weight: 600;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
            QPushButton {
                min-height: 30px;
                padding: 4px 10px;
            }
            QLineEdit, QComboBox, QSpinBox {
                min-height: 28px;
            }
            """
        )
        self.form = Form
        self.file = ""
        self.worker = None

        self._setup_widgets(Form)
        self._setup_layout(Form)
        self._connect_signals()

    def _setup_widgets(self, Form):
        self.path_input = QtWidgets.QLineEdit(Form)
        self.path_input.setReadOnly(True)
        self.path_input.setPlaceholderText("尚未选择下载目录")

        self.folder_name_input = QtWidgets.QLineEdit("Wallhaven", Form)
        self.folder_name_input.setMinimumWidth(160)

        self.desktop_button = QtWidgets.QPushButton("使用桌面文件夹", Form)
        self.choose_button = QtWidgets.QPushButton("选择文件夹", Form)

        self.general_checkbox = QtWidgets.QCheckBox("General", Form)
        self.anime_checkbox = QtWidgets.QCheckBox("Anime", Form)
        self.people_checkbox = QtWidgets.QCheckBox("People", Form)
        for checkbox in (self.general_checkbox, self.anime_checkbox, self.people_checkbox):
            checkbox.setChecked(True)

        self.sfw_checkbox = QtWidgets.QCheckBox("SFW", Form)
        self.sketchy_checkbox = QtWidgets.QCheckBox("Sketchy", Form)
        self.nsfw_checkbox = QtWidgets.QCheckBox("NSFW", Form)
        self.sfw_checkbox.setChecked(True)

        self.sorting_combo = QtWidgets.QComboBox(Form)
        self.sorting_combo.addItem("Top榜单", "toplist")
        self.sorting_combo.addItem("收藏榜单", "favorites")
        self.sorting_combo.addItem("浏览榜单", "views")
        self.sorting_combo.addItem("Hot", "hot")
        self.sorting_combo.addItem("随机", "random")
        self.sorting_combo.addItem("最新", "date_added")

        self.time_combo = QtWidgets.QComboBox(Form)
        self.time_combo.addItem("最新", "1d")
        self.time_combo.addItem("近一周", "1w")
        self.time_combo.addItem("近一个月", "1M")
        self.time_combo.addItem("近三个月", "3M")
        self.time_combo.addItem("近六个月", "6M")
        self.time_combo.addItem("近一年", "1y")
        self.time_combo.setCurrentIndex(2)

        self.start_page_spin = QtWidgets.QSpinBox(Form)
        self.start_page_spin.setRange(1, 9999)
        self.start_page_spin.setValue(1)

        self.page_count_spin = QtWidgets.QSpinBox(Form)
        self.page_count_spin.setRange(1, 9999)
        self.page_count_spin.setValue(20)

        self.progress_label = QtWidgets.QLabel("等待开始", Form)
        self.progress_label.setMinimumHeight(28)

        self.start_button = QtWidgets.QPushButton("开始下载", Form)
        self.start_button.setMinimumHeight(38)

    def _setup_layout(self, Form):
        root_layout = QtWidgets.QVBoxLayout(Form)
        root_layout.setContentsMargins(24, 20, 24, 20)
        root_layout.setSpacing(16)

        destination_group = QtWidgets.QGroupBox("保存位置", Form)
        destination_layout = QtWidgets.QGridLayout(destination_group)
        destination_layout.setColumnStretch(1, 1)
        destination_layout.addWidget(QtWidgets.QLabel("当前目录"), 0, 0)
        destination_layout.addWidget(self.path_input, 0, 1, 1, 3)
        destination_layout.addWidget(QtWidgets.QLabel("桌面文件夹名"), 1, 0)
        destination_layout.addWidget(self.folder_name_input, 1, 1)
        destination_layout.addWidget(self.desktop_button, 1, 2)
        destination_layout.addWidget(self.choose_button, 1, 3)
        root_layout.addWidget(destination_group)

        filter_group = QtWidgets.QGroupBox("筛选条件", Form)
        filter_layout = QtWidgets.QGridLayout(filter_group)
        filter_layout.setHorizontalSpacing(18)
        filter_layout.setVerticalSpacing(12)
        filter_layout.addWidget(QtWidgets.QLabel("分类"), 0, 0)
        filter_layout.addWidget(self.general_checkbox, 0, 1)
        filter_layout.addWidget(self.anime_checkbox, 0, 2)
        filter_layout.addWidget(self.people_checkbox, 0, 3)
        filter_layout.addWidget(QtWidgets.QLabel("分级"), 1, 0)
        filter_layout.addWidget(self.sfw_checkbox, 1, 1)
        filter_layout.addWidget(self.sketchy_checkbox, 1, 2)
        filter_layout.addWidget(self.nsfw_checkbox, 1, 3)
        filter_layout.addWidget(QtWidgets.QLabel("排序"), 2, 0)
        filter_layout.addWidget(self.sorting_combo, 2, 1)
        filter_layout.addWidget(QtWidgets.QLabel("时间"), 2, 2)
        filter_layout.addWidget(self.time_combo, 2, 3)
        filter_layout.addWidget(QtWidgets.QLabel("起始页"), 3, 0)
        filter_layout.addWidget(self.start_page_spin, 3, 1)
        filter_layout.addWidget(QtWidgets.QLabel("下载页数"), 3, 2)
        filter_layout.addWidget(self.page_count_spin, 3, 3)
        root_layout.addWidget(filter_group)

        footer_layout = QtWidgets.QHBoxLayout()
        footer_layout.addWidget(self.progress_label, 1)
        footer_layout.addWidget(self.start_button)
        root_layout.addLayout(footer_layout)

    def _connect_signals(self):
        self.desktop_button.clicked.connect(self.use_desktop_folder)
        self.choose_button.clicked.connect(self.choose_folder)
        self.start_button.clicked.connect(self.start_download)

    def choose_folder(self):
        selected = QtWidgets.QFileDialog.getExistingDirectory(self.form, "选择文件夹", ".")
        if selected:
            self.set_download_dir(selected)

    def use_desktop_folder(self):
        desktop = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.DesktopLocation)
        if desktop == "":
            desktop = str(Path.home() / "Desktop")

        folder_name = self.folder_name_input.text().strip() or "Wallhaven"
        target = Path(desktop) / folder_name
        target.mkdir(parents=True, exist_ok=True)
        self.set_download_dir(str(target))

    def set_download_dir(self, path):
        self.file = path
        self.path_input.setText(path)

    def start_download(self):
        if self.file == "":
            QtWidgets.QMessageBox.warning(self.form, "提示", "请先选择下载目录")
            return

        categories = self._bit_string(
            self.general_checkbox,
            self.anime_checkbox,
            self.people_checkbox,
        )
        purity = self._bit_string(
            self.sfw_checkbox,
            self.sketchy_checkbox,
            self.nsfw_checkbox,
        )
        if categories == "000":
            QtWidgets.QMessageBox.warning(self.form, "提示", "请至少选择一个分类")
            return
        if purity == "000":
            QtWidgets.QMessageBox.warning(self.form, "提示", "请至少选择一个分级")
            return

        url = build_search_url(
            sorting=self.sorting_combo.currentData(),
            top_range=self.time_combo.currentData(),
            purity=purity,
            categories=categories,
            start_page=self.start_page_spin.value(),
        )
        self.set_download_controls_enabled(False)
        self.progress_label.setText("已经下载 0 张，跳过 0 张，失败 0 张")
        self.worker = DownloadWorker(url, self.page_count_spin.value(), self.file)
        self.worker.progress.connect(self.on_download_progress)
        self.worker.finished.connect(self.on_download_finished)
        self.worker.failed.connect(self.on_download_failed)
        self.worker.start()

    def set_download_controls_enabled(self, enabled):
        self.desktop_button.setEnabled(enabled)
        self.choose_button.setEnabled(enabled)
        self.start_button.setEnabled(enabled)
        self.folder_name_input.setEnabled(enabled)

    def on_download_progress(self, downloaded, skipped, failed):
        self.progress_label.setText(f"已经下载 {downloaded} 张，跳过 {skipped} 张，失败 {failed} 张")

    def on_download_finished(self, downloaded, skipped, failed):
        self.set_download_controls_enabled(True)
        self.progress_label.setText(f"下载完成：成功 {downloaded} 张，跳过 {skipped} 张，失败 {failed} 张")

    def on_download_failed(self, message):
        self.set_download_controls_enabled(True)
        self.progress_label.setText("下载失败")
        QtWidgets.QMessageBox.critical(self.form, "错误", "下载失败：" + message)

    @staticmethod
    def _bit_string(*checkboxes):
        return "".join("1" if checkbox.isChecked() else "0" for checkbox in checkboxes)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main_window = QtWidgets.QWidget()
    ui = Ui_Form()
    ui.setupUi(main_window)
    main_window.show()
    sys.exit(app.exec_())
