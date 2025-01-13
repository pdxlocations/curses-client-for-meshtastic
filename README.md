Python based command line client using the curses library, powered by Meshtastic.org

<img width="846" alt="Screenshot_2024-03-29_at_4 00 29_PM" src="https://github.com/pdxlocations/meshtastic-curses-client/assets/117498748/e99533b7-5c0c-463d-8d5f-6e3cccaeced7">


<br><br>
Settings can be accessed within the client or can be run standalone

<img width="509" alt="Screenshot 2024-04-15 at 3 39 12 PM" src="https://github.com/pdxlocations/meshtastic-curses-client/assets/117498748/37bc57db-fe2d-4ba4-adc8-679b4cb642f9">

## Arguments

You can pass the following arguments to the client:

### Connection Arguments

Optional arguments to specify a device to connect to and how.

- `--port`, `--serial`, `-s`: The port to connect to via serial, e.g. `/dev/ttyUSB0`.
- `--host`, `--tcp`, `-t`: The hostname or IP address to connect to using TCP.
- `--ble`, `-b`: The BLE device MAC address or name to connect to.

If no connection arguments are specified, the client will attempt a serial connection and then a TCP connection to localhost.

### Example Usage

```sh
python main.py --port /dev/ttyUSB0
python main.py --host 192.168.1.1
python main.py --ble BlAddressOfDevice