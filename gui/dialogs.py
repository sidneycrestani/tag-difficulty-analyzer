# gui/dialogs.py

import os
import json
from aqt import mw
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QPushButton, QLabel, QUrl,
    QWebEngineView
)
from aqt.webview import AnkiWebView
from aqt.utils import qconnect, showInfo
from aqt.theme import theme_manager

from aqt import dialogs

from ..logic import calculate_tag_difficulties, get_parent_tags

parent_dir = os.path.dirname(__file__)
package_name = __name__.split('.')[0]

def open_browser_for_tag(tag_name: str):
    """Opens the Anki browser with a search for the given tag, excluding suspended cards."""
    search_query = f'tag:"{tag_name}" -is:suspended -is:new'
    dialogs.open("Browser", mw, search=(search_query,))

class GraphWebView(AnkiWebView):
    """A custom webview to handle loading and rendering the graph."""
    def __init__(self, mw, parent=None):
        super().__init__(parent)
        self._mw = mw
        self.parent = parent
        self.setEnabled(False)
        self._page_loaded = False
        self._pending_data = None
        
        self.set_bridge_command(self._on_bridge_cmd, self)
        
        self.loadFinished.connect(self._on_page_load)
        self._load_html()

    def _on_bridge_cmd(self, cmd: str):
        if cmd.startswith("browseTag:"):
            tag_name = cmd.replace("browseTag:", "", 1)
            open_browser_for_tag(tag_name)

    def _load_html(self):
        html_path = os.path.join(parent_dir, "web", "graph.html")
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()
        
        base_url = QUrl(f"http://localhost:{self._mw.mediaServer.getPort()}/_addons/{package_name}/gui/web/")
        QWebEngineView.setHtml(self, html, baseUrl=base_url)

    def _on_page_load(self, success: bool):
        if not success:
            return
        self._page_loaded = True

        # --- Reverted to the correct pattern: Set initial theme on load ---
        is_night_mode = theme_manager.night_mode
        js_script = f"setInitialTheme({json.dumps(is_night_mode)});"
        self._run_javascript(js_script)

        if self._pending_data:
            self._render_now(self._pending_data)
            self._pending_data = None

    def _run_javascript(self, script: str):
        self.setEnabled(False)
        self.evalWithCallback(script, self._on_javascript_evaluated)

    def _on_javascript_evaluated(self, result):
        self.setEnabled(True)

    def _render_now(self, data: list):
        plot_data = data[:25]
        graph_data = [
            {
                "label": item['tag'].split('::')[-1],
                "value": item['difficulty'],
                "fullTag": item['tag']
            }
            for item in plot_data
        ]
        
        # --- Reverted to the correct pattern: Pass the boolean flag ---
        is_night_mode = theme_manager.night_mode

        json_data = json.dumps(graph_data)
        js_script = f"renderGraph({json_data}, {json.dumps(is_night_mode)});"
        self._run_javascript(js_script)

    def render(self, data: list):
        if self._page_loaded:
            self._render_now(data)
        else:
            self._pending_data = data

class MainStatsWindow(QDialog):
    _PLACEHOLDER_TEXT = "Please select a parent tag..."

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowIcon(mw.windowIcon())
        self.current_data = []
        self.setWindowTitle("Tag Difficulty Analyzer")
        self.setMinimumSize(850, 800)

        # Controls
        controls_hbox = QHBoxLayout()
        label = QLabel("Analyze difficulty of sub-tags for:")
        self.tag_combo = QComboBox()
        
        self.tag_combo.addItem(self._PLACEHOLDER_TEXT)
        self.tag_combo.addItems(get_parent_tags())
        qconnect(self.tag_combo.currentTextChanged, self.on_analyze)

        controls_hbox.addWidget(label)
        controls_hbox.addWidget(self.tag_combo, 1)

        self.webview = GraphWebView(mw, self)
        self.webview.setFixedHeight(450)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Sub-Tag Group", "Median Difficulty", "Card Count", "Metric"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        vbox = QVBoxLayout()
        vbox.addLayout(controls_hbox)
        vbox.addWidget(self.webview)
        vbox.addWidget(self.table)
        self.setLayout(vbox)

    def on_tag_link_clicked(self, tag_name: str):
        """Handles clicks on the generated tag links in the table."""
        open_browser_for_tag(tag_name)

    def on_analyze(self, parent_tag: str):
        if not parent_tag or parent_tag == self._PLACEHOLDER_TEXT:
            # If placeholder is selected, clear the results
            self.current_data = []
            self.webview.render([]) # Send empty data to clear graph
            self.populate_table()
            return
        
        mw.progress.start(immediate=True, label="Aggregating tag difficulties...")
        try:
            stats_data = calculate_tag_difficulties(parent_tag)
        finally:
            mw.progress.finish()
        
        self.current_data = stats_data
        
        self.webview.render(self.current_data)
        
        self.populate_table()

    def populate_table(self):
        self.table.clearContents()
        if not self.current_data:
            self.table.setRowCount(0)
            # Only show the "no cards" message if it wasn't the placeholder
            if self.tag_combo.currentText() != self._PLACEHOLDER_TEXT:
                showInfo("No reviewed, non-suspended cards found for this tag.")
            return

        self.table.setRowCount(len(self.current_data))
        for row, item in enumerate(self.current_data):
            tag_name = item["tag"]
            
            label = QLabel(f'<a href="{tag_name}">{tag_name}</a>')
            label.setOpenExternalLinks(False)
            label.linkActivated.connect(self.on_tag_link_clicked)
            self.table.setCellWidget(row, 0, label)
            
            difficulty_str = f"{item['difficulty']:.1f}%"
            self.table.setItem(row, 1, QTableWidgetItem(difficulty_str))
            self.table.setItem(row, 2, QTableWidgetItem(str(item["card_count"])))
            self.table.setItem(row, 3, QTableWidgetItem(item["metric_used"]))