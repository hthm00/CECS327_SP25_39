import socket
from datetime import datetime, timedelta
import psycopg2
from collections import defaultdict
from config import NEONDB_CONNECTION_STRING, SENSOR_CONFIG, DEVICE_IDS


def relative_moisture(record):
    """
    Calculates relative moisture percentage from sensor reading.
    
    Args:
        record (dict): A single record from the database, containing 'payload' with sensor values.

    Returns:
        float: Moisture percentage (0–100).
    """
    sensor_key = SENSOR_CONFIG["MOISTURE"]["SENSOR_KEY"]
    max_val = SENSOR_CONFIG["MOISTURE"]["MAX_VALUE"]
    value = float(record["payload"].get(sensor_key, 0))
    return (value / max_val) * 100


def water_flow_gallons(record):
    """
    Converts raw water flow sensor reading into gallons per hour.

    Args:
        record (dict): A single record from the database, containing 'payload' with sensor values.

    Returns:
        float: Estimated gallons used in an hour.
    """
    cfg = SENSOR_CONFIG["WATER_FLOW"]
    raw = float(record["payload"].get(cfg["SENSOR_KEY"], 0))
    flow_lpm = (raw / 100) * cfg["MAX_FLOW_RATE_LPM"]
    return flow_lpm * cfg["CONVERSION_FACTOR"] * 60  # gallons per hour


def amperes_to_kilowatts(record, device_key):
    """
    Calculates energy consumption in kilowatts for a given device from amperes.

    Args:
        record (dict): A single record from the database.
        device_key (str): One of 'FRIDGE1', 'DISHWASHER', 'FRIDGE2'.

    Returns:
        float: Energy consumption in kilowatts.
    """
    cfg = SENSOR_CONFIG["ELECTRICITY"]
    sensor_key = cfg["SENSOR_KEYS"][device_key]
    amps = float(record["payload"].get(sensor_key, 0))
    return (amps * cfg["VOLTAGE"] * cfg["HOURS"]) / 1000


def handle_request(request, data):
    """
    Handles client requests by computing the appropriate sensor data summary.

    Args:
        request (str): The client request type ("1", "2", or "3").
        data (dict): Dictionary mapping device IDs to lists of sensor records.

    Returns:
        str: A human-readable summary of the computed data.
    """
    if request == "1":  # Moisture
        key = DEVICE_IDS["FRIDGE1"]
        values = [relative_moisture(r) for r in data.get(key, [])]
        if values:
            avg = sum(values) / len(values)
            return f"The average moisture is: {avg:.2f} percent"

    elif request == "2":  # Water Flow
        key = DEVICE_IDS["DISHWASHER"]
        values = [water_flow_gallons(r) for r in data.get(key, [])]
        if values:
            avg = sum(values) / len(values)
            return f"The average water flow is: {avg:.2f} gallons per hour"

    elif request == "3":  # Electricity
        consumption = {}
        labels = {
            "FRIDGE1": "the first fridge",
            "DISHWASHER": "the dishwasher",
            "FRIDGE2": "the second fridge"
        }
        for label, key in DEVICE_IDS.items():
            records = data.get(key, [])
            values = [amperes_to_kilowatts(r, label) for r in records]
            if values:
                consumption[label] = sum(values) / len(values)

        if consumption:
            max_device = max(consumption, key=consumption.get)
            return f"The maximum electricity consumption is: {labels[max_device]} with {consumption[max_device]:.2f} kilowatts."

    return "Invalid request or no data available."


def get_recent_sensor_data(hours=None):
    """
    Queries the database for recent sensor data from the past `hours`.

    Args:
        hours (int): Time window in hours to retrieve recent sensor readings.

    Returns:
        dict: Mapping of device UIDs to lists of records (dicts with payload and timestamp).
    """
    query = """"""
    if hours: 
        query = """
            SELECT payload, time
            FROM "Table_virtual"
            WHERE time > %s
        """
    else:
        query = """
            SELECT payload, time
            FROM "Table_virtual"
        """
    with psycopg2.connect(NEONDB_CONNECTION_STRING) as conn:
        with conn.cursor() as cursor:
            if hours:   
                cutoff = datetime.now() - timedelta(hours=hours)
                cursor.execute(query, (cutoff,))
            else:
                cursor.execute(query)
            rows = cursor.fetchall()

    data = defaultdict(list)
    for payload, timestamp in rows:
        uid = payload.get("parent_asset_uid")
        if uid:
            data[uid].append({"payload": payload, "time": timestamp})
    return data


def start_server():
    """
    Starts the TCP server to handle client connections and respond to sensor data queries.
    """
    server_ip = input("Enter server IP address: ")
    server_port = int(input("Enter the port number: "))

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((server_ip, server_port))
        server_socket.listen(1)
        print(f"Listening on {server_ip}:{server_port}")

        while True:
            conn, addr = server_socket.accept()
            print(f"Connected from {addr}")

            with conn:
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    request = data.decode().strip()
                    print(f"Received: {request}")

                    try:
                        sensor_data = None
                        if request == "1":
                            sensor_data = get_recent_sensor_data(hours=3)
                        else:
                            sensor_data = get_recent_sensor_data()
                        if sensor_data:
                            response = handle_request(request, sensor_data)
                            conn.sendall(response.encode('utf-8'))
                        else:
                            error_msg = "No data available."
                            print(error_msg)
                            conn.sendall(error_msg.encode('utf-8'))
                    except Exception as e:
                        error_msg = f"Error: {e}"
                        print(error_msg)
                        conn.sendall(error_msg.encode('utf-8'))

            print("Connection closed.")


if __name__ == "__main__":
    start_server()