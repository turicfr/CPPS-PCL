from client import GenericClient

def main():
    client = GenericClient("45.76.128.185", 6112)
    client.login("test999", "12345")
    while True:
        client.update()
        try:
            command = input("> ")
        except KeyboardInterrupt:
            print()
            continue
        except EOFError:
            break
        print(command)

if __name__ == "__main__":
    main()
