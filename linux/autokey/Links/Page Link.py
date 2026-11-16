# AutoKey script. Ctrl+Super+L: see page_hotkey in linux/autokey/links.py.
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
import links
import page_link

# Reload, so that changes to the repo files work without an AutoKey restart.
importlib.reload(page_link)
importlib.reload(links)
links.page_hotkey("markdown", window)
