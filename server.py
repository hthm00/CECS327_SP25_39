"""
Server implementation for handling IoT device data processing and analysis.
This server connects to a MongoDB database and processes data from various household devices
including moisture sensors, water flow meters, and electricity consumption meters.
"""

import socket
import psycopg2
import json
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
    hours = 1
    voltage = 240
    if key == "09h-o4h-6ec-q99":
        amperes = float(data["payload"].get("Ammeter", 0))
    elif key == "0a4-g7y-3jy-4w0":
        amperes = float(data["payload"].get("Ammeter2", 0))
    else:
        amperes = float(data["payload"].get("Ammeter1", 0))
    power_watts = amperes * voltage
    kilowatts = (power_watts * hours) / 1000
    return kilowatts

def get_data_from_neon(cursor, cutoff):
    query = """
        SELECT payload, time
        FROM "Table_virtual"
        WHERE time > %s
    """
    cursor.execute(query, (cutoff,))
    rows = cursor.fetchall()

    data = defaultdict(list)
    for payload, time in rows:
        record = {
            "payload": payload,
            "time": time
        }
        uid = payload.get("parent_asset_uid")
        if uid:
            data[uid].append(record)
    return data

def start_server():
    try:
        # Get server configuration from user
        server_ip = input("Enter server IP address: ")
        server_port = int(input("Enter the port number: "))
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((server_ip, server_port))
        server_socket.listen(1)

        print(f"Listening on {server_ip}:{server_port}")

        while True:
            # Accept client connection
            conn, addr = server_socket.accept()
            print("Connected")

            while True:
                data = conn.recv(1024)
                if not data:
                    break

                request = data.decode()
                print(f"Received: {request}")

                try:
                    # Connect to NeonDB (PostgreSQL)
                    conn_str = "postgresql://neondb_owner:npg_PDG5yHtwd9ig@ep-dark-glade-a4y5rfkw-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require"
                    with psycopg2.connect(conn_str) as db_conn:
                        with db_conn.cursor() as cursor:
                            cutoff = datetime.now() - timedelta(hours=3)
                            data = get_data_from_neon(cursor, cutoff)

                            match request:
                                case "1":
                                    key = "09h-o4h-6ec-q99"
                                    records = data.get(key, [])
                                    moisture_values = [
                                        relative_moisture_process(r) for r in records
                                    ]
                                    if moisture_values:
                                        avg = sum(moisture_values) / len(moisture_values)
                                        conn.sendall(f"The average moisture is: {avg}".encode())

                                case "2":
                                    key = "0a4-g7y-3jy-4w0"
                                    records = data.get(key, [])
                                    water_values = [
                                        water_flow_gallons_process(r) for r in records
                                    ]
                                    if water_values:
                                        avg = sum(water_values) / len(water_values)
                                        conn.sendall(f"The average water flow is: {avg}".encode())

                                case "3":
                                    keys = ["09h-o4h-6ec-q99", "0a4-g7y-3jy-4w0", "178ca7ee-1e25-4941-aec8-f144a04b95a2"]
                                    electricity = {}
                                    for key in keys:
                                        records = data.get(key, [])
                                        values = [amperes_to_kilowatts_process(r, key) for r in records]
                                        if values:
                                            electricity[key] = sum(values) / len(values)

                                    if electricity:
                                        max_key = max(electricity, key=electricity.get)
                                        max_val = electricity[max_key]
                                        labels = {
                                            "09h-o4h-6ec-q99": "the first fridge",
                                            "0a4-g7y-3jy-4w0": "the dishwasher",
                                            "178ca7ee-1e25-4941-aec8-f144a04b95a2": "the second fridge"
                                        }
                                        conn.sendall(
                                            f"The maximum electricity consumption is: {labels[max_key]} with {max_val} kilowatts.".encode()
                                        )

                except Exception as e:
                    print(f"Error: {e}")

            conn.close()
            print("Connection closed.")

    except ValueError:
        print("Invalid port number.")
    except socket.error as e:
        print(f"Socket error: {e}")

if __name__ == "__main__":
    start_server()
