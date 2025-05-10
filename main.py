from PySide6 import QtCore, QtWidgets, QtGui, QtMultimedia, QtMultimediaWidgets
from version_check import VersionCheck
from pathlib import Path
import sys
import subprocess
import os
import tempfile

sys.argv += ['-platform', 'windows:darkmode=2']

# Icon Path for pyinstaller
if getattr(sys, 'frozen', False):
    resource_path = Path(sys._MEIPASS)
else:
    resource_path = Path(__file__).parent

class AppWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        icon = QtGui.QIcon(f"{resource_path}\\icon.ico")
        self.setWindowTitle("Song Pitcher")
        self.setWindowIcon(icon)
        self.setAcceptDrops(True)
        self.file_path = None
        self.temp_file = None

        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(10)

        self.label = QtWidgets.QLabel("Drag and Drop or select MP3")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.label)

        btn_layout = QtWidgets.QHBoxLayout()
        self.select_button = QtWidgets.QPushButton("Select File")
        self.select_button.setFixedWidth(150)
        self.select_button.clicked.connect(self.selectFile)
        btn_layout.addWidget(self.select_button)

        self.pitch_button = QtWidgets.QPushButton("Apply Pitch")
        self.pitch_button.setFixedWidth(150)
        self.pitch_button.clicked.connect(self.pitchFile)
        btn_layout.addWidget(self.pitch_button)

        self.preview_button = QtWidgets.QPushButton("▶ Preview")
        self.preview_button.setFixedWidth(120)
        self.preview_button.setEnabled(False)
        self.preview_button.clicked.connect(self.previewAudio)
        btn_layout.addWidget(self.preview_button)

        self.save_button = QtWidgets.QPushButton("💾 Save")
        self.save_button.setFixedWidth(150)
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.saveFile)
        btn_layout.addWidget(self.save_button)

        layout.addLayout(btn_layout)

        # Slider
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(0, 200)
        self.slider.setValue(100)
        self.slider.setTickInterval(10)
        self.slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.slider.valueChanged.connect(self.updateSliderLabel)
        layout.addWidget(self.slider)

        self.slider_label = QtWidgets.QLabel("Pitch-Factor: 1")
        self.slider_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.slider_label)

        self.status = QtWidgets.QLabel("")
        self.status.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.status)

        self.setLayout(layout)

        # Player
        self.audio_output = QtMultimedia.QAudioOutput()
        self.player = QtMultimedia.QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(1.0)

        bottom_layout = QtWidgets.QHBoxLayout()
        self.github_button = QtWidgets.QPushButton("GitHub")
        self.github_button.setFixedWidth(80)
        self.github_button.clicked.connect(self.openGitHub)
        bottom_layout.addWidget(self.github_button, alignment=QtCore.Qt.AlignLeft)
        layout.addLayout(bottom_layout)

    def openGitHub(self):
        subprocess.run("start https://github.com/snytex/", shell=True)

    def updateSliderLabel(self, value):
        factor = value / 100.0
        self.slider_label.setText(f"Pitch-Factor: {factor:.2f}×")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.toLocalFile().endswith(".mp3"):
                self.file_path = url.toLocalFile()
                self.label.setText(f"Datei: {os.path.basename(self.file_path)}")
                break

    def selectFile(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select MP3 File", "", "Audio (*.mp3)")
        if path:
            self.file_path = path
            self.label.setText(f"Datei: {os.path.basename(self.file_path)}")
            self.preview_button.setEnabled(False)
            self.preview_button.setText("▶ Preview")
            self.status.setText("")
            self.player.stop()
            self.save_button.setEnabled(False)

    def saveFile(self):
        if self.temp_file and os.path.exists(self.temp_file):
            save_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save", "", "MP3-Datei (*.mp3)")
            if save_path:
                try:
                    with open(self.temp_file, 'rb') as src, open(save_path, 'wb') as dst:
                        dst.write(src.read())
                    self.status.setText(f"Saved under: {os.path.basename(save_path)}")
                except Exception as e:
                    self.status.setText(f"Error whilst saving: {str(e)}")

    def pitchFile(self):
        if not self.file_path:
            self.status.setText("Please select an MP3 file first.")
            return

        if self.player.isPlaying():
            self.player.stop()
            self.preview_button.setText("▶ Preview")

        pitch_factor = self.slider.value() / 100.0

        if abs(pitch_factor - 1.0) < 0.001:
            self.status.setText("Pitch-Factor = 1.00 → No change.")
            return

        fd, temp_path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        self.temp_file = temp_path

        cmd = [
            "ffmpeg", "-y",
            "-i", self.file_path,
            "-filter:a", f"rubberband=pitch={pitch_factor}",
            self.temp_file
        ]

        try:
            self.status.setText("Pitching...")
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            self.status.setText("Pitching completed.")
            self.preview_button.setEnabled(True)
            self.save_button.setEnabled(True)
        except subprocess.CalledProcessError:
            self.status.setText("Pitching failed.")
            self.preview_button.setEnabled(False)

    def previewAudio(self):
        if self.temp_file and os.path.exists(self.temp_file) and self.preview_button.text() == "▶ Preview":
            url = QtCore.QUrl.fromLocalFile(self.temp_file)
            self.player.setSource(url)
            self.player.play()
            self.status.setText("Playing pitched preview ...")

            self.preview_button.setText("Stop")
        
        elif self.preview_button.text() == "Stop":
            self.player.stop()
            self.preview_button.setText("▶ Preview")
            self.status.setText("")


if __name__ == "__main__":
    versioncheck = VersionCheck()
    versioncheck.checkForUpdates()

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")

    widget = AppWidget()
    widget.resize(600, 400)
    widget.show()

    sys.exit(app.exec())