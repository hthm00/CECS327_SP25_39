import socket

host = input("Enter host (e.g., localhost): ")
port = int(input("Enter port (e.g., 8081): "))

numberOfBytes = 1024
myTCPSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
myTCPSocket.bind((host, port))
myTCPSocket.listen(5)

print(f"Server listening on {host}:{port}...")

incomingSocket, incomingAddress = myTCPSocket.accept()
print(f"Connection from {incomingAddress}")

while True:
    myData = incomingSocket.recv(numberOfBytes).decode('utf-8')
    if not myData:
        break
    print("Data from client:", myData)
    response = input("Enter response to client: ")
    incomingSocket.send(response.encode('utf-8'))

incomingSocket.close()
myTCPSocket.close()
