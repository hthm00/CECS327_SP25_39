import socket

host = input("Enter server host: ")
port = int(input("Enter server port: "))

myTCPSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
myTCPSocket.connect((host, port))


def toServer(query):
    myTCPSocket.send(query.encode('utf-8'))
    response = myTCPSocket.recv(1024).decode('utf-8')
    print("Server responded:", response)

while True:
    print("""1. What is the average moisture inside my kitchen fridge in the past three hours?
2. What is the average water consumption per cycle in my smart dishwasher?
3. Which device consumed more electricity among my three IoT devices?\n""")
    query = input("Select 1-3 or \'exit\' ")

    match query:
        case "1" | "2" | "3":
            toServer(query)
        case "exit":
            break
        case _:
            print("Sorry, this querry cannot be processed. Please try again\n")
    

myTCPSocket.close()