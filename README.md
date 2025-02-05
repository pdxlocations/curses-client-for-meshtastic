## Contact - A Console UI for Meshtastic
### (Formerly Curses Client for Meshtastic)

#### Powered by Meshtastic.org

This Python curses client for Meshtastic is a terminal-based client designed to manage device settings, enable mesh chat communication, and handle configuration backups and restores.


<img width="846" alt="Screenshot_2024-03-29_at_4 00 29_PM" src="https://github.com/pdxlocations/meshtastic-curses-client/assets/117498748/e99533b7-5c0c-463d-8d5f-6e3cccaeced7">

<br><br>
The settings dialogue can be accessed within the client or may be run standalone to configure your node by launching `settings.py`

<img width="509" alt="Screenshot 2024-04-15 at 3 39 12 PM" src="https://github.com/pdxlocations/meshtastic-curses-client/assets/117498748/37bc57db-fe2d-4ba4-adc8-679b4cb642f9">

## Message Persistence 

All messages will saved in a SQLite DB and restored upon relaunch of the app.  You may delete `client.db` if you wish to erase all stored messages and node data.  If multiple nodes are used, each will independently store data in the database, but the data will not be shared or viewable between nodes.

## Client Configuration

By navigating to Settings -> App Settings, you may customize your UI's icons, colors, and more!

## Commands

- `↑→↓←` = Navigate around the UI.
- `ENTER` = Send a message typed in the Input Window, or with the Node List highlighted, select a node to DM
-  `` ` `` = Open the Settings dialogue
- `CTRL` + `p` = Hide/show a log of raw received packets.
- `CTRL` + `t` = With the Node List highlighted, send a traceroute to the selected node 
- `CTRL` + `d` = With the Channel List hightlighted, archive a chat to reduce UI clutter. Messages will be saved in the db and repopulate if you send or receive a DM from this user.
- `ESC` = Exit out of the Settings Dialogue, or Quit the application if settings are not displayed.

### Search
- Press `CTRL` + `/` while the nodes or channels window is highlighted to start search
- Type text to search as you type, first matching item will be selected, starting at current selected index
- Press Tab to find next match starting from the current index - search wraps around if necessary
- Press Esc or Enter to exit search mode

## Arguments

You can pass the following arguments to the client:

### Connection Arguments

Optional arguments to specify a device to connect to and how.

- `--port`, `--serial`, `-s`: The port to connect to via serial, e.g. `/dev/ttyUSB0`.
- `--host`, `--tcp`, `-t`: The hostname or IP address to connect to using TCP, will default to localhost if no host is passed.
- `--ble`, `-b`: The BLE device MAC address or name to connect to.

If no connection arguments are specified, the client will attempt a serial connection and then a TCP connection to localhost.

### Example Usage

```sh
python main.py --port /dev/ttyUSB0
python main.py --host 192.168.1.1
python main.py --ble BlAddressOfDevice
```
To quickly connect to localhost, use:
```sh
python main.py -t
```
