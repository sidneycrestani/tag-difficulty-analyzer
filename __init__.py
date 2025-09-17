# __init__.py for Tag Difficulty Analyzer

from aqt import mw
from aqt.qt import QAction
from aqt.utils import qconnect
from .gui.dialogs import MainStatsWindow

def show_main_window():
    """Creates and shows the main dialog window."""
    mw.tag_stats_main_win = MainStatsWindow(parent=None)
    mw.tag_stats_main_win.show()

# Set up web exports to serve files from the gui/web folder
mw.addonManager.setWebExports(__name__, r"gui/web/.*")

# Add the 'Tools' menu item
action = QAction("Tag Difficulty Stats", mw)
qconnect(action.triggered, show_main_window)
mw.form.menuTools.addAction(action)