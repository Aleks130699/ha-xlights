[![](https://img.shields.io/github/release/Aleks130699/ha-xlights/all.svg?style=for-the-badge)](https://github.com/Aleks130699/ha-xlights/releases)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
[![](https://img.shields.io/github/license/Aleks130699/ha-xlights?style=for-the-badge)](LICENSE)

# HomeAssistant - xLights Schedule Component

This is a custom component to allow control of the [xLights](https://xlights.org) Schedule in [Home Assistant](https://home-assistant.io).

# Features:

- View current playing sequence and playlist
- List all available playlist and sequences as sources
- Start a playlist or sequence
- Stop a playlist or sequence
- Set or step the player volume
- Next a sequence
- Prev a sequence
- Pause a sequence
- Resume a sequence
- Seek a sequence

# Installation

### 1. Easy Mode

Install via HACS.

### 2. Manual

Install it as any custom homeassistant component:

1. Download `custom_components` folder.
2. Copy the `xlights_schedule` directory to the `custom_components` directory of your homeassistant installation. Your `custom_components` directory resides within your homeassistant configuration directory.

**Note**: If the `custom_components` directory does not exist, you need to create it.

After a correct installation, your configuration directory should look like the following:

    └── ...
    └── configuration.yaml
    └── custom_components
        └── xlights_schedule
            └── __init__.py
            └── media_player.py
            └── manifest.json

# Configuration

1. Enable the component by editing your configuration.yaml file (within the config directory as well). Edit it by adding the following lines:

   ```
   # Example configuration.yaml entry
   media_player:
     - platform: xlights_schedule
       name: NAME
       host: IP_ADDRESS:PORT (or hostname:port)

   ```

2. Reboot Home Assistant
3. You're good to go!

# Images

### Overview

![Overview](./images/overview.PNG)

### Playing

![Playing](./images/playing.PNG)

### Playlists

![Playlist](./images/playlists.PNG)

### Song Selection

![Song Selection](./images/song_selection.PNG)
