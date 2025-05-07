import socket
import psycopg2
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
        server_ip = input("Enter server IP address: ")
        server_port = int(input("Enter the port number: "))
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((server_ip, server_port))
        server_socket.listen(1)

        print(f"Listening on {server_ip}:{server_port}")

        while True:
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
