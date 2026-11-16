# AutoKey script. Ctrl+Super+Z: see linux/autokey/links.py.
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
import links
import zendesk_link

# Reload, so that changes to the repo files work without an AutoKey restart.
importlib.reload(zendesk_link)
importlib.reload(links)
links.link_hotkey(zendesk_link.zendesk_links, "markdown", keyboard)
