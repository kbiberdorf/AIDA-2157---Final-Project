import pyodbc
import numpy as np
from datetime import datetime, timedelta

# Connection Settings
conn_str = (
    "Driver={SQL Server};"
    "Server=Kelsey;" # Change to your server name if different
    "Database=AIDA2157_Final_Project;" # Change to your database name if different
    "Trusted_Connection=yes;"
)

def populate_alberta_balanced_data(n=1000):
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    print("Performing a clean wipe for Alberta provincial data...")
    
    tables = ["Prediction_Archive", "Weather_Logs", "Fire_History", "Call_911_History", 
              "Lightning_Strikes", "Terrain_Data", "Weather_Stations", 
              "Emergency_Resources", "Community_Infrastructure", "Model_Metadata"]
    for t in tables: cursor.execute(f"DELETE FROM {t}")
    conn.commit()

    # 1. Infrastructure & Resources
    print("Generating Infrastructure and Resource units...")
    for i in range(n):
        lat, lon = float(np.random.uniform(49.0, 60.0)), float(np.random.uniform(-120.0, -110.0))
        cursor.execute("INSERT INTO Community_Infrastructure (Name, Infra_Type, Risk_Level_Score, Latitude, Longitude) VALUES (?, ?, ?, ?, ?)",
                       (f"AB_Asset_{i}", np.random.choice(['Hospital', 'Oil Rig', 'Power Grid', 'School']), int(np.random.randint(1, 11)), lat, lon))
        cursor.execute("INSERT INTO Emergency_Resources (Resource_Type, Current_Status, Home_Base_Location) VALUES (?, ?, ?)",
                       (np.random.choice(['Air Tanker', 'Helitack', 'Wildland Crew']), 'Available', f"Base_{np.random.randint(1,20)}"))

    # 2. Stations & Models
    stations = []
    for i in range(50):
        cursor.execute("INSERT INTO Weather_Stations (Station_Name, Latitude, Longitude, Elevation) VALUES (?, ?, ?, ?)",
                       (f"AB_Station_{i}", np.random.uniform(49, 60), np.random.uniform(-120, -110), int(np.random.randint(200, 2500))))
        cursor.execute("SELECT @@IDENTITY"); stations.append(int(cursor.fetchone()[0]))

    model_names = ['Ignition Predictor', 'Fire Size', 'False Alarm', 'Containment', 'Smoke AQI', 
                   'Evacuation', 'Road Closure', 'Landslide', 'Dispatch', 'Infrastructure']
    for name in model_names:
        cursor.execute("INSERT INTO Model_Metadata (Model_Name, Model_Type, Accuracy_Score) VALUES (?, ?, ?)", (name, 'Hybrid AI', 0.0))

    # 3. Incident Scenarios
    print("Simulating 1000 Alberta incidents...")
    for i in range(n):
        lat, lon = float(np.random.uniform(49.0, 60.0)), float(np.random.uniform(-120.0, -110.0))
        random_time = datetime.now() - timedelta(days=int(np.random.randint(0, 90)), minutes=int(np.random.randint(0, 1440)))
        temp, hum, wind = float(np.random.uniform(10, 45)), float(np.random.uniform(5, 60)), float(np.random.uniform(0, 95))
        slope = int(np.random.randint(0, 45))
        fuel = str(np.random.choice(['Lodgepole Pine', 'Black Spruce', 'Aspen', 'Boreal Grass']))
        cause = str(np.random.choice(['Lightning', 'Abandoned Campfire', 'Arson', 'Power Line Arch']))

        # Balanced Logic
        is_major = int(1 if (hum < 25 or wind > 40) else np.random.choice([0, 1], p=[0.8, 0.2]))
        is_real = int(np.random.choice([0, 1], p=[0.5, 0.5])) # 50/50 split for False Alarm model
        final_size = float(np.random.uniform(1000, 50000) if is_major else np.random.uniform(0.1, 999))

        cursor.execute("INSERT INTO Terrain_Data (Latitude, Longitude, Fuel_Type, Soil_Moisture, Slope_Steepness) VALUES (?, ?, ?, ?, ?)",
                       (lat, lon, fuel, float(np.random.uniform(2, 40)), slope))
        cursor.execute("SELECT @@IDENTITY"); t_id = int(cursor.fetchone()[0])

        cursor.execute("INSERT INTO Weather_Logs (Log_Timestamp, Temperature, Humidity, Wind_Speed, Wind_Direction, Terrain_ID, Station_ID) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (random_time, temp, hum, wind, np.random.choice(['N','S','E','W','NW','NE','SW','SE']), t_id, int(np.random.choice(stations))))

        cont_days = int(np.random.randint(7, 40) if is_major else np.random.randint(1, 6))
        cursor.execute("INSERT INTO Fire_History (Start_Date, Containment_Date, Start_Size_Hectares, Final_Size_Hectares, Cause) VALUES (?, ?, ?, ?, ?)",
                       (random_time, random_time + timedelta(days=cont_days), float(np.random.uniform(0.1, 5.0)), final_size, cause))

        cursor.execute("INSERT INTO Call_911_History (Call_Timestamp, Is_Real_Fire, Reported_Location) VALUES (?, ?, ?)",
                       (random_time + timedelta(minutes=10), is_real, f"{lat:.4f}, {lon:.4f}"))

        intensity = float(np.random.uniform(10, 160))
        if cause == 'Lightning' or intensity > 100:
            cursor.execute("INSERT INTO Lightning_Strikes (Strike_Timestamp, Latitude, Longitude, Intensity_kA) VALUES (?, ?, ?, ?)",
                           (random_time, lat + np.random.uniform(-0.01, 0.01), lon + np.random.uniform(-0.01, 0.01), intensity))

    conn.commit()
    print("Database Fully Populated and Balanced!")
    conn.close()

populate_alberta_balanced_data(1000)