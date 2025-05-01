"""
Server implementation for handling IoT device data processing and analysis.
This server connects to a MongoDB database and processes data from various household devices
including moisture sensors, water flow meters, and electricity consumption meters.
"""

import socket
from pymongo import MongoClient
from datetime import datetime, timedelta
from collections import defaultdict
from config import (
    MONGODB_CONNECTION_STRING,
    MONGODB_DATABASE,
    MONGODB_COLLECTION,
    DEVICE_IDS,
    SENSOR_CONFIG
)

def relative_moisture_process(data):
    """
    Process raw moisture data to calculate relative moisture percentage.
    
    Args:
        data (dict): Dictionary containing raw moisture sensor data
        
    Returns:
        float: Relative moisture percentage (0-100)
    """
    max_val = SENSOR_CONFIG["MOISTURE"]["MAX_VALUE"]
    raw_moisture = float(data["payload"][SENSOR_CONFIG["MOISTURE"]["SENSOR_KEY"]])
    relative_moisture = (raw_moisture / max_val) * 100
    return relative_moisture

def water_flow_gallons_process(data):
    """
    Process raw water flow data to calculate gallons per hour.
    
    Args:
        data (dict): Dictionary containing raw water flow sensor data
        
    Returns:
        float: Water flow in gallons per hour
    """
    max_flow_rate_lpm = SENSOR_CONFIG["WATER_FLOW"]["MAX_FLOW_RATE_LPM"]
    raw_water_flow = float(data["payload"].get(SENSOR_CONFIG["WATER_FLOW"]["SENSOR_KEY"], 0))
    flow_rate_lpm = (raw_water_flow / 100) * max_flow_rate_lpm
    flow_rate_gpm = flow_rate_lpm * SENSOR_CONFIG["WATER_FLOW"]["CONVERSION_FACTOR"]
    gallons = flow_rate_gpm * 60
    return gallons

def amperes_to_kilowatts_process(data, key):
    """
    Convert amperes to kilowatts for electricity consumption calculation.
    
    Args:
        data (dict): Dictionary containing raw ammeter data
        key (str): Device identifier to determine which ammeter to use
        
    Returns:
        float: Power consumption in kilowatts
    """
    hours = SENSOR_CONFIG["ELECTRICITY"]["HOURS"]
    voltage = SENSOR_CONFIG["ELECTRICITY"]["VOLTAGE"]
    
    # Determine which ammeter to use based on device ID
    device_type = next((k for k, v in DEVICE_IDS.items() if v == key), None)
    if not device_type:
        return 0
        
    amperes = float(data.get("payload", {}).get(SENSOR_CONFIG["ELECTRICITY"]["SENSOR_KEYS"][device_type], 0))
    power_watts = amperes * voltage
    kilowatts = (power_watts * hours) / 1000
    return kilowatts

def start_server():
    """
    Start the server and handle client connections.
    Processes requests for moisture, water flow, and electricity consumption data.
    """
    try:
        # Get server configuration from user
        server_ip = input("Enter server IP address: ")
        server_port = int(input("Enter the port number (has to be the same number for the client): "))
        
        # Initialize server socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((server_ip, server_port))
        server_socket.listen(1)
        
        print(f"Listening in server IP: {server_ip} and port: {server_port}")

        while True:
            # Accept client connection
            conn, addr = server_socket.accept()
            print("Connected")

            while True:
                data = conn.recv(1024)
                if not data:
                    break

                try:
                    # MongoDB connection
                    client = MongoClient(MONGODB_CONNECTION_STRING)
                    db = client[MONGODB_DATABASE]
                    collection = db[MONGODB_COLLECTION]

                    current_time = datetime.now()
                    cutoff = current_time - timedelta(hours=3)
                    print(f"Received data from client: {data.decode()}")
                    
                    request = data.decode()
                    data = defaultdict(list)

                    # Group records by device ID
                    for rec in collection.find():
                        data[rec["payload"]["parent_asset_uid"]].append(rec)
                    
                    match request:
                        case "1":
                            # Process moisture data for Fridge1
                            key = DEVICE_IDS["FRIDGE1"]
                            records = data.get(key, [])
                            moisture_values = []

                            for r in records:
                                if r["time"] > cutoff:
                                    moisture_values.append(relative_moisture_process(r))

                            if moisture_values:
                                average_moisture = sum(moisture_values) / len(moisture_values)
                                print(f"Average moisture: {average_moisture}")
                                conn.sendall(f"The average moisture is: {average_moisture}".encode('utf-8'))
                            else:
                                conn.sendall("No moisture data available for the specified time period.".encode('utf-8'))

                        case "2":
                            # Process water flow data for DishWasher
                            key = DEVICE_IDS["DISHWASHER"]
                            records = data.get(key, [])
                            water_flow_values = []

                            for r in records:
                                water_flow_values.append(water_flow_gallons_process(r))

                            if water_flow_values:
                                average_water_flow = sum(water_flow_values) / len(water_flow_values)
                                print(f"Average water flow: {average_water_flow}")
                                conn.sendall(f"The average water flow is: {average_water_flow}".encode('utf-8'))
                            else:
                                conn.sendall("No water flow data available.".encode('utf-8'))
                        
                        case "3":
                            # Process electricity consumption data for all devices
                            electricity_records = {}

                            for device_name, device_id in DEVICE_IDS.items():
                                records = data.get(device_id, [])
                                electricity_values = [amperes_to_kilowatts_process(r, device_id) for r in records]

                                if electricity_values:
                                    average_electricity = sum(electricity_values) / len(electricity_values)
                                    electricity_records[device_name] = average_electricity

                            if electricity_records:
                                max_device = max(electricity_records, key=electricity_records.get)
                                max_value = electricity_records[max_device]
                                conn.sendall(f"The maximum electricity consumption is: the {max_device.lower()} with {max_value} kilowatts.".encode('utf-8'))
                            else:
                                conn.sendall("No electricity consumption data available for any device.".encode('utf-8'))

                except Exception as e:
                    print(f"Error processing request: {e}")
                    conn.sendall(f"Error processing request: {str(e)}".encode('utf-8'))

            conn.close()
            print("Connection closed.")
            
    except ValueError:
        print("Error: Invalid port number. Please enter an integer.")

    except socket.error as e:
        print(f"Socket error: {e}")


if __name__ == "__main__":
    start_server()