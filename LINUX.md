# Linux setup

This page tells you how to install the link hotkeys on Linux. The espanso macros are not set up for Linux yet. Issue #49 tracks the Linux work.

The hotkeys use [AutoKey for Wayland](https://daveking.com/autokey-wayland-ppa/), a fork of AutoKey. Upstream AutoKey works only on X11. We tested on Ubuntu 26.04 with GNOME 50 on Wayland.

## Zendesk hotkeys

| Hotkey | Result |
| --- | --- |
| Ctrl+Super+Z | Replaces the selection with the Markdown link, for example `[Zendesk ticket #12345: blah blah](https://tbpro.zendesk.com/agent/tickets/12345)` |
| Shift+Ctrl+Super+Z | Copies the link as rich text, with the Markdown link as plain text. Then press Ctrl+V. Use this in Gmail. |

The hotkeys use the first number in the selection and ignore the text before it. Text after the number goes in the link text, so a selected `12345 blah blah` or a ticket URL followed by `blah blah` gives the link text `Zendesk ticket #12345: blah blah`. If nothing is selected, the hotkeys use the text on the clipboard and only copy the link. If the text has no number, a notification shows the error and nothing changes.

## Page link hotkeys

| Hotkey | Result |
| --- | --- |
| Ctrl+Super+L | Copies a Markdown link to the web page in the active Firefox or Chrome window, for example `[Santiago! (film) - Wikipedia](https://en.wikipedia.org/wiki/Santiago!_%28film%29)`. Then press Ctrl+V. |
| Shift+Ctrl+Super+L | Copies the link as rich text, with the Markdown link as plain text. Then press Ctrl+V. Use this in Gmail. |

The page title is the link text. The hotkeys do not press keys and do not use the selection. AutoKey gives only the window title, so the hotkeys find the URL of the most recent visit with this title in the browser history. If two pages have the same title, you can get the URL of the other page. A private window has no history, so it gives an error.

The hotkeys look in the open Firefox profiles in `~/snap/firefox/common/.mozilla/firefox` (the snap), `~/.config/mozilla/firefox`, and `~/.mozilla/firefox`, and in all Chrome and Chromium profiles in `~/.config/google-chrome`, `~/.config/chromium`, and `~/snap/chromium/common/chromium`. Chrome writes its history late, so a page that you opened a few seconds ago can be missing.

For a Mozilla Support knowledge base article, the link text starts with `SUMO KB Article: `, ` Help` goes away from the end, `Thunderbird` in the product name becomes `TB`, and the URL loses the locale.

## Install

### 1. Install AutoKey for Wayland and the tools

Run these commands:

```sh
curl -s --compressed https://daveking.com/autokey-wayland-ppa/autokey-wayland-ppa.gpg \
  | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/autokey-wayland-ppa.gpg > /dev/null
sudo curl -s --compressed -o /etc/apt/sources.list.d/autokey-wayland-ppa.list \
  https://daveking.com/autokey-wayland-ppa/autokey-wayland-ppa.list
sudo apt update
sudo apt install autokey-gtk wl-clipboard libnotify-bin gir1.2-gtk-4.0
```

`wl-clipboard` reads and writes the clipboard, `libnotify-bin` shows the notifications, and `gir1.2-gtk-4.0` copies the rich text link.

### 2. Let AutoKey read and press keys

On Wayland, AutoKey reads the keyboard and presses keys through `/dev/uinput`. Run these commands:

```sh
sudo cp /usr/share/autokey/uinput-udev-rule/10-autokey.rules /etc/udev/rules.d/
sudo usermod -aG input "$USER"
gnome-extensions install /usr/share/autokey/gnome-shell-extension/autokey-gnome-extension@autokey.shell-extension.zip
```

The `input` group lets every program that you run read and press keys, not only AutoKey. To undo it later, run `sudo gpasswd -d "$USER" input`.

The GNOME extension tells AutoKey the title of the active window.

### 3. Restart the computer

After the restart, make sure that the steps worked:

```sh
id -nG | tr ' ' '\n' | grep -x input
ls -l /dev/uinput
```

The first command must print `input`. The second must show the group `input` and `crw-rw----`.

Then turn on the extension:

```sh
gnome-extensions enable autokey-gnome-extension@autokey
gnome-extensions info autokey-gnome-extension@autokey
```

The state must be `ACTIVE`.

### 4. Link the hotkeys

Start AutoKey one time from the app menu, so that it makes its config folder. Then quit it from its icon in the top bar. In the root of this repository, run these commands:

```sh
ln -s "$PWD/linux/autokey/Links" ~/.config/autokey/data/Links
autokey-gtk &
```

The link points to the repository, so the hotkeys stay current when you pull. After a change to a `.json` file in `linux/autokey/Links/`, quit AutoKey and start it again. A change to a `.py` file works at once.

To start AutoKey at each login, open AutoKey, click **Edit > Preferences**, and select **Automatically start AutoKey at login**.

## Troubleshooting

If a hotkey does nothing, start AutoKey from a terminal with the debug log:

```sh
autokey-gtk -v > /tmp/autokey.log 2>&1 &
```

Press the hotkey, and look for `Script runner executing` and `Script error` in `/tmp/autokey.log`. The log contains every key that you press, also passwords. Quit AutoKey and delete the log after the test, then start AutoKey again without `-v`.

AutoKey calls the Super key `<meta>`. A hotkey with `<super>` in its `.json` file does nothing, and the key goes to the app.

If AutoKey cannot press keys, make sure that `id -nG` includes `input`. A new group works only after you log in again.

## Test

```sh
uv run --with pytest --with pyperclip pytest tests
```

`tests/test_zendesk_link_linux.py` and `tests/test_page_link_linux.py` test the link text and the history lookup. The hotkeys need a person to test them, because a terminal cannot select text in another app or focus a browser window.
