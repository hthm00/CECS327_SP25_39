import socket

host = input("Enter server host (e.g., localhost): ")
port = int(input("Enter server port (e.g., 8081): "))

myTCPSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
myTCPSocket.connect((host, port))

while True:
    message = input("Enter message to send to server (type 'exit' to quit): ")
    if message.lower() == 'exit':
        break
    myTCPSocket.send(message.encode('utf-8'))
    response = myTCPSocket.recv(1024).decode('utf-8')
    print("Server responded:", response)

myTCPSocket.close()
