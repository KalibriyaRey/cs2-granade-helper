import sys
import math
import os
import keyboard
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QPoint, QRectF, QTimer, QUrl, QRect
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget

class CS2GrennadeHelper(QWidget):
    def __init__(self):
        super().__init__()
        
        self.base_dir = "assets"
        self.fav_file = "favorites.txt"
        self.max_per_page = 12
        self.map_list = ["⭐ FAVORITES", "Mirage", "Dust2", "Inferno", "Nuke", "Ancient", "Anubis", "Vertigo"]
        self.type_list = ["Smoke", "Molotov", "Flash"]

        self.check_and_create_structure()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        
        self.screen_geo = QApplication.primaryScreen().geometry()
        self.setGeometry(self.screen_geo)

        self.is_active = False
        self.current_step = "MAP"
        self.selected_map = ""
        self.selected_type = ""
        self.click_lock = False
        self.scroll_lock = False 
        
        self.all_items = self.map_list
        self.current_page = 0
        self.options = self.get_current_page_items()
        self.selected_index = -1
        self.last_hovered_index = -1

        # Видео-контейнер
        self.video_container = QWidget(self)
        v_w, v_h = 640, 360
        self.video_container.setGeometry(
            self.screen_geo.width() - v_w - 50,
            (self.screen_geo.height() - v_h) // 2,
            v_w, v_h
        )
        self.video_container.setStyleSheet("background-color: black; border: 3px solid #ff8c00; border-radius: 10px;")
        self.video_container.hide()

        v_layout = QVBoxLayout(self.video_container)
        v_layout.setContentsMargins(2, 2, 2, 2)
        self.video_widget = QVideoWidget()
        v_layout.addWidget(self.video_widget)

        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setLoops(QMediaPlayer.Loops.Infinite)

        self.timer = QTimer()
        self.timer.timeout.connect(self.main_loop)
        self.timer.start(16)

    def check_and_create_structure(self):
        if not os.path.exists(self.base_dir): os.makedirs(self.base_dir)
        for m in self.map_list[1:]:
            map_path = os.path.join(self.base_dir, m.lower())
            for t in self.type_list:
                p = os.path.join(map_path, t.lower())
                if not os.path.exists(p): os.makedirs(p)

    def get_current_page_items(self):
        start = self.current_page * self.max_per_page
        return self.all_items[start : start + self.max_per_page]

    def paintEvent(self, event):
        if not self.is_active: return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.fillRect(self.rect(), QColor(0, 0, 0, 180))

        cols = 3
        item_w, item_h = 240, 80
        gap = 15
        start_x = 100
        start_y = 150

        mouse_pos = self.mapFromGlobal(self.cursor().pos())
        self.selected_index = -1

        for i, item in enumerate(self.options):
            r = i // cols
            c = i % cols
            x = start_x + c * (item_w + gap)
            y = start_y + r * (item_h + gap)
            rect = QRect(x, y, item_w, item_h)

            is_hovered = rect.contains(mouse_pos)
            if is_hovered: 
                self.selected_index = i
                if self.current_step == "POINT" and i != self.last_hovered_index:
                    self.last_hovered_index = i
                    self.handle_preview(item)

            color = QColor(255, 140, 0, 240) if is_hovered else QColor(30, 30, 30, 200)
            painter.setBrush(color)
            painter.setPen(QPen(Qt.GlobalColor.white, 2))
            painter.drawRoundedRect(QRectF(rect), 8, 8)

            painter.setPen(Qt.GlobalColor.white)
            painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            painter.drawText(rect.adjusted(10,0,-10,0), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, item)

        painter.setFont(QFont("Arial", 20, QFont.Weight.Black))
        painter.setPen(QColor(255, 140, 0))
        painter.drawText(100, 80, 500, 50, Qt.AlignmentFlag.AlignLeft, f"MENU: {self.current_step}")

    def handle_preview(self, name):
        if name in ["No Videos", "Empty"]: return
        
        path = self.get_fav_path(name) if self.selected_map == "favorites" else \
               os.path.join(self.base_dir, self.selected_map, self.selected_type, f"{name}.mp4")
        
        if os.path.exists(path):
            self.media_player.setSource(QUrl.fromLocalFile(os.path.abspath(path)))
            self.media_player.play()
            self.video_container.show()

    def main_loop(self):
        if keyboard.is_pressed('alt'):
            if not self.is_active: self.activate_menu()
            
            total_pages = math.ceil(len(self.all_items) / self.max_per_page)
            if keyboard.is_pressed('d') and not self.scroll_lock:
                if (self.current_page + 1) < total_pages:
                    self.current_page += 1
                    self.refresh_ui()
                self.scroll_lock = True
            elif keyboard.is_pressed('a') and not self.scroll_lock:
                if self.current_page > 0:
                    self.current_page -= 1
                    self.refresh_ui()
                self.scroll_lock = True
            
            if not keyboard.is_pressed('a') and not keyboard.is_pressed('d'):
                self.scroll_lock = False

            is_lmb = QApplication.mouseButtons() == Qt.MouseButton.LeftButton
            if is_lmb and not self.click_lock:
                if self.selected_index != -1: self.handle_click()
                self.click_lock = True
            if not is_lmb: self.click_lock = False
            self.update()
        else:
            if self.is_active: self.deactivate_menu()

    def refresh_ui(self):
        self.options = self.get_current_page_items()
        self.last_hovered_index = -1
        self.update()

    def handle_click(self):
        choice = self.options[self.selected_index]
        if choice in ["No Videos", "Empty"]: return

        if self.current_step == "MAP":
            if choice == "⭐ FAVORITES":
                self.selected_map = "favorites"
                self.all_items = self.load_favs()
                if not self.all_items: self.all_items = ["Empty"]
                self.current_step = "POINT"
            else:
                self.selected_map = choice.lower()
                self.all_items = self.type_list
                self.current_step = "TYPE"
            self.current_page = 0 

        elif self.current_step == "TYPE":
            self.selected_type = choice.lower()
            path = os.path.join(self.base_dir, self.selected_map, self.selected_type)
            if os.path.exists(path):
                files = [f.replace(".mp4", "") for f in os.listdir(path) if f.endswith(".mp4")]
                self.all_items = files
            self.all_items = self.all_items if self.all_items else ["No Videos"]
            self.current_step = "POINT"
            self.current_page = 0

        elif self.current_step == "POINT":
            if keyboard.is_pressed('shift'):
                if self.selected_map == "favorites":
                    self.remove_fav(choice)
                    self.all_items = self.load_favs()
                else:
                    self.add_fav(choice)

        self.options = self.get_current_page_items()

    def add_fav(self, name):
        path = os.path.join(self.base_dir, self.selected_map, self.selected_type, f"{name}.mp4")
        if name not in self.load_favs():
            with open(self.fav_file, "a", encoding="utf-8") as f:
                f.write(f"{name}|{path}\n")

    def remove_fav(self, name):
        if not os.path.exists(self.fav_file): return
        with open(self.fav_file, "r", encoding="utf-8") as f:
            lines = [l for l in f.readlines() if not l.startswith(f"{name}|")]
        with open(self.fav_file, "w", encoding="utf-8") as f:
            f.writelines(lines)

    def load_favs(self):
        if not os.path.exists(self.fav_file): return []
        with open(self.fav_file, "r", encoding="utf-8") as f:
            return [line.strip().split("|")[0] for line in f if "|" in line]

    def get_fav_path(self, name):
        with open(self.fav_file, "r", encoding="utf-8") as f:
            for line in f:
                p = line.strip().split("|")
                if p[0] == name: return p[1]
        return ""

    def activate_menu(self):
        self.is_active = True
        self.current_step, self.all_items, self.current_page = "MAP", self.map_list, 0
        self.options = self.get_current_page_items()
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowTransparentForInput)
        self.show()

    def deactivate_menu(self):
        self.is_active = False
        self.video_container.hide()
        self.media_player.stop()
        self.last_hovered_index = -1
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowTransparentForInput)
        self.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = CS2GrennadeHelper()
    w.show()
    sys.exit(app.exec())
