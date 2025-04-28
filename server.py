import socket
from pymongo import MongoClient
from datetime import datetime, timedelta
from collections import defaultdict

def relative_moisture_process(data):
    max_val = 999
    raw_moisture = float(data["payload"]["Moisture Meter - MoistureMeter"])
    relative_moisture = (raw_moisture / max_val) * 100
    return relative_moisture

def water_flow_gallons_process(data):
    max_flow_rate_lpm = 10
    raw_water_flow = float(data["payload"].get("WaterConsumptionSensor", 0))
    flow_rate_lpm = (raw_water_flow / 100) * max_flow_rate_lpm
    flow_rate_gpm = flow_rate_lpm * 0.264172
    gallons = flow_rate_gpm * 60
    return gallons

def amperes_to_kilowatts_process(data, key):

    hours = 1
    voltage = 240
    amperes = 0
    if key == "09h-o4h-6ec-q99":
        amperes = float(data.get("payload", {}).get("Ammeter", 0)) #Fridge1
    elif key == "0a4-g7y-3jy-4w0":
        amperes = float(data.get("payload", {}).get("Ammeter2", 0)) #DishWasher
    else:
        amperes = float(data.get("payload", {}).get("Ammeter1", 0)) #Fridge2
    power_watts = amperes * voltage
    kilowatts = (power_watts * hours) / 1000

    return kilowatts


def start_server():

    try:
        server_ip = input("Enter server IP address: ")
        server_port = int(input("Enter the port number (has to be the same number for the client): "))
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((server_ip, server_port))
        server_socket.listen(1)
        
        print(f"Listening in server IP: {server_ip} and port: {server_port}")

        while True:
            conn, addr = server_socket.accept()
            print("Connected")

            while True:
                data = conn.recv(1024)
                if not data:
                    break

               
                connection_string = "mongodb+srv://asangaspar012:NVhc3zW3E3myNZNR@cluster0.1yr0d.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
                client = MongoClient(connection_string)

                current_time = datetime.now()
                cutoff = current_time - timedelta(hours=3)
                print(f"Received data from client: {data.decode()}")
                
                request = data.decode()
                try :
                    db = client["test"]
                    collection = db["House_virtual"]

                    data = defaultdict(list)

                    for rec in collection.find():
                        data[rec["payload"]["parent_asset_uid"]].append(rec)
                    
                    match request:
                        case "1":

                            key = "09h-o4h-6ec-q99" #Fridge1
                            # records = tree.search(key)
                            records = data.get(key, [])
                            moisture_values = []

                            current_time = datetime.now()
                            cutoff = current_time - timedelta(hours=3)  
                            for r in records:
                                print(r)
                                if r["time"] > cutoff:
                                    relative_moisture_process(r)
                                    moisture_values.append(relative_moisture_process(r))

                            if moisture_values:
                                average_moisture = sum(moisture_values) / len(moisture_values)
                                print(f"Average moisture: {average_moisture}")
                                conn.sendall(f"The average moisture is: {average_moisture}".encode('utf-8'))
                                

                        case "2":
                            key = "0a4-g7y-3jy-4w0" # DishWasher
                            records = data.get(key, [])
                            water_flow_values = []

                            for r in records:
                                print(r)
                                water_flow_values.append(water_flow_gallons_process(r))

                            if water_flow_values:
                                average_water_flow = sum(water_flow_values) / len(water_flow_values)
                                print(f"Average water flow: {average_water_flow}")
                                conn.sendall(f"The average water flow is: {average_water_flow}".encode('utf-8'))
                        
                        case "3":
                            
                            keys = ["09h-o4h-6ec-q99", "0a4-g7y-3jy-4w0", "178ca7ee-1e25-4941-aec8-f144a04b95a2"] # Fridge1, DishWasher, Fridge2
                            electricity_records = {}

                            for key in keys:

                                records = data.get(key, [])

                                electricity_values = [amperes_to_kilowatts_process(r, key) for r in records]

                                if electricity_values:
                                    average_electricity = sum(electricity_values) / len(electricity_values)
                                    electricity_records[key] = average_electricity

                            if electricity_records:
                                max_electricity = max(electricity_records, key=electricity_records.get)
                                max_electricity_value = electricity_records[max_electricity]

                                if max_electricity == "09h-o4h-6ec-q99":
                                    conn.sendall(f"The maximum electricity consumption is: the dishwaher with {max_electricity_value} kilowatts.".encode('utf-8'))
                                elif max_electricity == "0a4-g7y-3jy-4w0":
                                    conn.sendall(f"The maximum electricity consumption is: the second fridge with {max_electricity_value} kilowatts.".encode('utf-8'))
                                elif max_electricity == "178ca7ee-1e25-4941-aec8-f144a04b95a2":
                                    conn.sendall(f"The maximum electricity consumption is: the first fridge with {max_electricity_value} kilowatts.".encode('utf-8'))

                except Exception as e:
                    print(e)

            conn.close()
            print("Connection closed.")
            
    except ValueError:
        print(("Error: Invalid port number. Please enter an integer."))

    except socket.error as e:
        print(f"Socket error: {e}")


if __name__ == "__main__":
    start_server()