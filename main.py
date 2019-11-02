#!/usr/bin/env python3

import functools

from client import GenericClient

COMMAND_HANDLERS = {}

def command_handler(name):
    def _command_handler(func):
        @functools.wraps(func)
        def _func(client, *args):
            try:
                return func(client, *args)
            except TypeError:
                return None
        COMMAND_HANDLERS[name] = _func
        return _func
    return _command_handler

@command_handler("id")
def handle_id(client):
    return client.id

def main():
    client = GenericClient("45.76.128.185", 6112)
    client.login("test999", "12345")
    while True:
        client.update()
        try:
            command = input("> ").split()
        except KeyboardInterrupt:
            print()
            continue
        except EOFError:
            break
        if not command:
            continue
        name, args = command[0], command[1:]
        if name not in COMMAND_HANDLERS:
            print(f"Unknown command: {name}")
            continue
        output = COMMAND_HANDLERS[name](client, *args)
        if output is None:
            print("Error")
            continue
        print(output)

if __name__ == "__main__":
    main()
