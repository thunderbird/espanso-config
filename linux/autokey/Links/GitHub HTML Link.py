# AutoKey script. Shift+Ctrl+Super+G: see linux/autokey/links.py.
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
import links
import github_link

# Reload, so that changes to the repo files work without an AutoKey restart.
importlib.reload(github_link)
importlib.reload(links)
links.link_hotkey(github_link.github_links, "html", keyboard)
