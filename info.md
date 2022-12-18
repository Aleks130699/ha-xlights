[![](https://img.shields.io/github/release/koolsb/ha-fpp/all.svg?style=for-the-badge)](https://github.com/koolsb/ha-fpp/releases)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
[![](https://img.shields.io/github/license/koolsb/ha-fpp?style=for-the-badge)](LICENSE)

# HomeAssistant - Falcon Pi Player (FPP) Component

This is a custom component to allow control of the Falcon Pi Player in [Home Assistant](https://home-assistant.io). 

# Features:

* View current playing sequence and playlist
* List all available playlist and sequences as sources
* Start a playlist or sequence
* Stop a playlist or sequence
* Set or step the player volume

# Installation

### 1. Easy Mode

Install via HACS.

### 2. Manual

Install it as any custom homeassistant component:

1. Download `custom_components` folder.
2. Copy the `falcon_pi_player` directory to the `custom_components` directory of your homeassistant installation. Your `custom_components` directory resides within your homeassistant configuration directory.

**Note**: If the `custom_components` directory does not exist, you need to create it.

After a correct installation, your configuration directory should look like the following:

    
    └── ...
    └── configuration.yaml
    └── custom_components
        └── falcon_pi_player.py
            └── __init__.py
            └── media_player.py
            └── manifest.json
    

# Configuration

1. Enable the component by editing your configuration.yaml file (within the config directory as well). Edit it by adding the following lines:
    ```
    # Example configuration.yaml entry
    media_player:
      - platform: falcon_pi_player
        name: FPP_NAME
        host: IP_ADDRESS (or hostname)

2. Reboot Home Assistant
3. You're good to go!
