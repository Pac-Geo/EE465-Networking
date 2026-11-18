#!/usr/bin/env python3

from gpiozero import LED, Button
from queue import Queue, Empty
from threading import Event, Thread
import requests

my_talkback_key = "YOUR_TALKBACK_API_KEY"
baseurl = "https://api.thingspeak.com/talkbacks/58484/commands"

commands = Queue()
stop = Event()


def send_button_commands():
    while not stop.is_set():
        try:
            command = commands.get(timeout=0.5)
        except Empty:
            continue

        try:
            # Exactly one request per event. No automatic retries.
            response = requests.post(
                baseurl + ".json",
                data={"api_key": my_talkback_key,
                      "command_string": command},
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            if not isinstance(result, dict) or not result.get("id"):
                raise ValueError("TalkBack did not confirm the queued command")
            print(f"Button {int(command == 'ON')}: {command} queued once.",
                  flush=True)
        except (requests.RequestException, ValueError) as error:
            print(f"Button send failed; no retry: {error}", flush=True)
        finally:
            commands.task_done()


with LED(17) as led, Button(23, pull_up=True, bounce_time=0.05) as button:
    # Callbacks only queue events, so network delays cannot block release detection.
    button.when_pressed = lambda: commands.put("ON")
    button.when_released = lambda: commands.put("OFF")

    sender = Thread(target=send_button_commands, daemon=True)
    sender.start()

    try:
        print("Button GPIO23: press=1/ON, release=0/OFF.", flush=True)
        print("LED GPIO17. Checking TalkBack every 30 seconds.", flush=True)

        while not stop.is_set():
            try:
                response = requests.post(
                    baseurl + "/execute",
                    data={"api_key": my_talkback_key},
                    timeout=10
                )
                response.raise_for_status()
                state = response.text.strip().upper()

                if state == "ON":
                    led.on()
                    print("LED1 ON", flush=True)
                elif state == "OFF":
                    led.off()
                    print("LED1 OFF", flush=True)
                elif not state:
                    print("No command. LED unchanged.", flush=True)
                else:
                    print(f"Unrecognized response: {state}", flush=True)

            except requests.RequestException as error:
                print(f"TalkBack check failed: {error}", flush=True)

            stop.wait(30)

    except KeyboardInterrupt:
        print("\nStopped.", flush=True)
    finally:
        button.when_pressed = None
        button.when_released = None
        stop.set()
        sender.join(timeout=11)
        led.off()
