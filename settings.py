import curses

def settings(stdscr, interface):
    popup_height = 10
    popup_width = 30
    y_start = (curses.LINES - popup_height) // 2
    x_start = (curses.COLS - popup_width) // 2

    popup_win = curses.newwin(popup_height, popup_width, y_start, x_start)
    popup_win.border()
    popup_win.addstr(1, 1, "Select an option:")
    options = ["Reboot", "Reset NodeDB", "Shutdown", "Factory Reset"]
    for i, option in enumerate(options, start=1):
        popup_win.addstr(i + 1, 2, f"{i}. {option}")   
    popup_win.addstr(i + 2, 2, f"ESC: Exit Menu")

    popup_win.refresh()
    
    while True:
        char = popup_win.getch()
        if char == 27:
            break

        # Handle the selected option
        elif char in [ord('1'), ord('2'), ord('3'), ord('4')]:
            selected_option = chr(char)
            if selected_option == '1':
                settings_reboot(interface)
            elif selected_option == '2':
                settings_reset_nodedb(interface)
            elif selected_option == '3':
                settings_shutdown(interface)
            elif selected_option == '4':
                settings_factory_reset(interface)
            break

    # Close the popup window
    popup_win.clear()
    popup_win.refresh()
    del popup_win  # Delete the window object to free up memory

def settings_reboot(interface):
    interface.getNode('^local').reboot()

def settings_reset_nodedb(interface):
    interface.getNode('^local').resetNodeDb()

def settings_shutdown(interface):
    interface.getNode('^local').shutdown()

def settings_factory_reset(interface):
    interface.getNode('^local').factory_reset()
    

    # ourNode = interface.getNode('^local')
    # ourNode.localConfig.lora.modem_preset = 'LONG_FAST'
    # ourNode.writeConfig("lora")