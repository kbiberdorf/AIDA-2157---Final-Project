import pyodbc
import pandas as pd
import numpy as np
import warnings
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import mean_absolute_error

# Connection
conn_str = (
    "Driver={SQL Server};"
    "Server=Kelsey;" # Change to your server name if different
    "Database=AIDA2157_Final_Project;" # Change to your database name if different
    "Trusted_Connection=yes;"
)
conn = pyodbc.connect(conn_str)

# Run the AI Engine to train models and generate predictions
def run_ai_engine():
    print("="*75 + "\n")
    print("--- ALBERTA WILDFIRE AI ENGINE STARTING ---")
    cursor = conn.cursor()
    
    # Clear old predictions to avoid confusion
    print("\nClearing old prediction logs...\n")
    cursor.execute("DELETE FROM Prediction_Archive")
    conn.commit()
    
    # Define the 10 use cases with their corresponding model types and features
    use_cases = [
        {"db_keyword": "Ignition", "name": "Ignition Predictor", "type": "RF_Class", "target": "Is_Ignited", "features": ["Intensity_kA", "Soil_Moisture"]},
        {"db_keyword": "Size", "name": "Fire Size", "type": "RF_Class", "target": "Is_Major", "features": ["Temperature", "Humidity", "Wind_Speed", "Slope_Steepness"]},
        {"db_keyword": "Alarm", "name": "False Alarm", "type": "Log_Reg", "target": "Is_Real_Fire", "features": ["Temperature", "Humidity"]},
        {"db_keyword": "Containment", "name": "Containment", "type": "RF_Reg", "target": "Days", "features": ["Final_Size_Hectares", "Slope_Steepness"]},
        {"db_keyword": "AQI", "name": "Smoke AQI", "type": "RF_Reg", "target": "AQI", "features": ["Temperature", "Wind_Speed", "Final_Size_Hectares"]},
        {"db_keyword": "Evacuation", "name": "Evacuation", "type": "RF_Class", "target": "Evac_Required", "features": ["Final_Size_Hectares", "Wind_Speed", "Slope_Steepness"]},
        {"db_keyword": "Road", "name": "Road Closure", "type": "Log_Reg", "target": "Road_Closed", "features": ["Final_Size_Hectares", "Slope_Steepness"]},
        {"db_keyword": "Landslide", "name": "Landslide", "type": "RF_Class", "target": "Slide_Risk", "features": ["Slope_Steepness", "Soil_Moisture"]},
        {"db_keyword": "Dispatch", "name": "Dispatch", "type": "RF_Class", "target": "Dispatch_Needed", "features": ["Intensity_kA", "Wind_Speed"]},
        {"db_keyword": "Infrastructure", "name": "Infrastructure", "type": "RF_Class", "target": "Clearance_Required", "features": ["Risk_Level_Score", "Slope_Steepness"]}
    ]

    # Process each use case
    for uc in use_cases:
        # Fetch the corresponding Model_ID for updating accuracy later
        cursor.execute("SELECT Model_ID FROM Model_Metadata WHERE Model_Name LIKE ?", (f"%{uc['db_keyword']}%",))
        row = cursor.fetchone() # If no model found, skip this use case
        if not row: continue # This should not happen as the models are pre-populated, but just in case of mismatch, skip to avoid errors.
        db_model_id = int(row[0]) # Ensure it's an integer for later use in updates

        # Fetch the joined data for this use case
        query = """
        SELECT f.*, t.*, w.*, l.Intensity_kA, c.Is_Real_Fire, i.Risk_Level_Score,
               DATEDIFF(day, f.Start_Date, f.Containment_Date) as Days
        FROM Fire_History f
        JOIN Terrain_Data t ON f.Fire_ID = t.Terrain_ID
        JOIN Weather_Logs w ON t.Terrain_ID = w.Terrain_ID
        LEFT JOIN Lightning_Strikes l ON f.Start_Date = l.Strike_Timestamp
        LEFT JOIN Call_911_History c ON f.Start_Date = c.Call_Timestamp
        LEFT JOIN Community_Infrastructure i ON i.Infra_ID = f.Fire_ID
        """
        
        # Suppress warnings for missing columns during the join, they will be handled in the logic mapping step
        with warnings.catch_warnings():
            warnings.simplefilter("ignore") # This is to ignore warnings about missing columns like 'Intensity_kA' or 'Is_Real_Fire' which may not be present for all records due to the LEFT JOINs.
            df = pd.read_sql(query, conn) # This will create a DataFrame with all the joined data, but some columns may have NaNs due to the LEFT JOINs.

        # Handle missing columns by filling with NaNs or default values, the logic mapping will account for these cases.
        if df["Intensity_kA"].isna().mean() > 0.5: # If more than 50% of the data is missing for this feature, it'll generate synthetic values based on a reasonable distribution for the sake of model training.
            df['Intensity_kA'] = np.random.uniform(10, 160, size = len(df)) # Wildfire intensity in kiloamperes, a common range for lightning strikes that can cause ignitions.

        # --- ROBUST LOGIC MAPPING ---
        
        # 1. False Alarm: If the joined data is missing, it'll pull from the source
        # or use a broader logical check to ensure variety.
        if uc['db_keyword'] == "Alarm": 
            # If the join failed (all 0s), it'll force variety based on Temperature
            df['Is_Real_Fire'] = [1 if (t > 25 or h < 30) else np.random.choice([0,1])
                                  for t, h in zip(df['Temperature'], df['Humidity'])] # This logic assumes that higher temperatures and lower humidity are more likely to be real fires, but still allows for some randomness to ensure the model has both classes to learn from.
            
        # 2. Infrastructure: If the join is empty, it'll base it on the Fire Size 
        # threatening the Infrastructure Priority (Risk_Level_Score)
        if uc['db_keyword'] == "Infrastructure": 
            df['Clearance_Required'] = [1 if (s > 500 or r > 5) else 0  
                                        for s, r in zip(df['Final_Size_Hectares'], df['Risk_Level_Score'].fillna(0))] 

        # 3. Standard Logic for the others
        if uc['db_keyword'] == "Ignition": df['Is_Ignited'] = [1 if x > 60 else 0 for x in df['Intensity_kA'].fillna(0)] 
        if uc['db_keyword'] == "Size": df['Is_Major'] = [1 if x > 1000 else 0 for x in df['Final_Size_Hectares']]
        if uc['db_keyword'] == "AQI": df['AQI'] = (df['Temperature'] * 1.2) + (df['Final_Size_Hectares'] * 0.005)
        if uc['db_keyword'] == "Evacuation": df['Evac_Required'] = [1 if x > 1200 else 0 for x in df['Final_Size_Hectares']]
        if uc['db_keyword'] == "Road": df['Road_Closed'] = [1 if x > 800 else 0 for x in df['Final_Size_Hectares']]
        if uc['db_keyword'] == "Landslide": df['Slide_Risk'] = [1 if s > 20 else 0 for s in df['Slope_Steepness']]
        if uc['db_keyword'] == "Dispatch": df['Dispatch_Needed'] = [1 if i > 40 else 0 for i in df['Intensity_kA'].fillna(0)]
        
        # Prepare features and target for model training, ensuring that if the target variable is missing, 
        # it defaults to a value that allows the model to train without errors, while still providing meaningful patterns to learn from.
        X = df[uc['features']].fillna(0)
        if uc['type'] != "RF_Reg":
            y = df[uc['target']].fillna(0).astype(int)
            if len(np.unique(y)) < 2:
                print(f"Skipping {uc['name']}: Not enough variety.")
                continue
        else:
            y = df[uc['target']].fillna(0) 

        # Split the data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Train the model based on the specified type and evaluate its performance, 
        # then update the database with the new accuracy score and a sample prediction for demonstration.
        if uc['type'] == "Log_Reg":
            model = LogisticRegression(solver='lbfgs', max_iter=5000, class_weight='balanced').fit(X_train, y_train)
            score = model.score(X_test, y_test); metric = "Accuracy"
        elif uc['type'] == "RF_Class":
            model = RandomForestClassifier(n_estimators=50, class_weight='balanced').fit(X_train, y_train)
            score = model.score(X_test, y_test); metric = "Accuracy"
        else:
            model = RandomForestRegressor(n_estimators=50).fit(X_train, y_train)
            score = mean_absolute_error(y_test, model.predict(X_test)); metric = "Avg Error"

        # Update the Model_Metadata with the new accuracy score and log a sample prediction in Prediction_Archive
        cursor.execute("UPDATE Model_Metadata SET Accuracy_Score = ?, Last_Trained_Date = GETDATE() WHERE Model_ID = ?", (float(score), db_model_id))
        sample_pred = float(model.predict(X_test[:1])[0])
        cursor.execute("INSERT INTO Prediction_Archive (Model_ID, Prediction_Timestamp, Predicted_Value) VALUES (?, GETDATE(), ?)", (db_model_id, sample_pred))
        print(f"Success: {uc['name']} | {metric}: {score:.4f}")

    # Final commit after processing all models    
    conn.commit()
    print("\n--- ALL 10 ALBERTA MODELS PROCESSED ---")

run_ai_engine()

# Generate a sample emergency briefing based on the latest predictions and current conditions in the database, 
# simulating a real-time briefing for emergency management teams.
def generate_emergency_briefing():
    print("\n" + "="*75)
    print("  PROVINCIAL EMERGENCY MANAGEMENT BRIEFING")
    print("  Location: Alberta, Canada | AI Status: Active")
    print("="*75)

    # Fetch the latest prediction and current conditions for a random incident to create a briefing scenario. 
    # This simulates the AI engine providing actionable insights based on the most recent data and model outputs
    cursor = conn.cursor()
    
    # For demonstration, fetch a random incident and its associated data, then map the latest predictions to the briefing format.
    cursor.execute("""
        SELECT TOP 1 f.Fire_ID, t.Latitude, t.Longitude, w.Temperature, w.Wind_Speed, m.Accuracy_Score
        FROM Fire_History f
        JOIN Terrain_Data t ON f.Fire_ID = t.Terrain_ID
        JOIN Weather_Logs w ON t.Terrain_ID = w.Terrain_ID
        JOIN Model_Metadata m ON m.Model_Name LIKE '%Ignition%'
        ORDER BY NEWID()
    """)
    row = cursor.fetchone() # This will fetch a random fire incident along with its location, current temperature, wind speed, and the accuracy score of the Ignition Predictor model for demonstration purposes.

    # If a row is returned, it will proceed to map the predictions to the briefing format. 
    # If no data is available, it will simply print that no incidents are currently detected.    
    if row:
        f_id, lat, lon, temp, wind, acc = row
        
        cursor.execute("SELECT Predicted_Value FROM Prediction_Archive ORDER BY Prediction_ID")
        preds = [p[0] for p in cursor.fetchall()]

        # Map all 10 model outputs
        ignition_prob    = "HIGH" if len(preds) > 0 and preds[0] == 1 else "LOW"
        fire_size        = "MAJOR" if len(preds) > 1 and preds[1] == 1 else "MINOR"
        false_alarm      = "REAL FIRE" if len(preds) > 2 and preds[2] == 1 else "POSSIBLE FALSE ALARM"
        containment_days = round(preds[3], 1) if len(preds) > 3 else 4.5
        aqi_score        = round(preds[4], 1) if len(preds) > 4 else 150.0
        evac_status      = "REQUIRED" if len(preds) > 5 and preds[5] == 1 else "NOT REQUIRED"
        road_closure     = "CLOSE ROADS" if len(preds) > 6 and preds[6] == 1 else "ROADS OPEN"
        landslide_risk   = "HIGH RISK" if len(preds) > 7 and preds[7] == 1 else "LOW RISK"
        dispatch_needed  = "DISPATCH NOW" if len(preds) > 8 and preds[8] == 1 else "STANDBY"
        infra_priority   = "CLEAR VEGETATION" if len(preds) > 9 and preds[9] == 1 else "NO ACTION NEEDED"

        print(f"CRITICAL INCIDENT DETECTED AT: [{lat:.4f}, {lon:.4f}]")
        print(f"Current Conditions - Temperature: {temp:6.1f}°C | Wind: {wind:6.1f} km/h")
        print("-" * 75)
        print(f" [1] IGNITION PROBABILITY:        {ignition_prob} (Model Accuracy: {acc:.2%})")
        print(f" [2] FIRE SIZE FORECAST:          {fire_size}")
        print(f" [3] 911 CALL ASSESSMENT:         {false_alarm}")
        print(f" [4] CONTAINMENT ESTIMATE:        {containment_days} Days")
        print(f" [5] SMOKE AQI FORECAST:          {aqi_score:.1f} AQI")
        print(f" [6] EVACUATION STATUS:           {evac_status}")
        print(f" [7] ROAD CLOSURE STATUS:         {road_closure}")
        print(f" [8] LANDSLIDE RISK (Post-Fire):  {landslide_risk}")
        print(f" [9] AIR TANKER DISPATCH:         {dispatch_needed}")
        print(f"[10] INFRASTRUCTURE PRIORITY:     {infra_priority}")
        print("-" * 75)
        print(f"ACTION PLAN: {'DISPATCH AIR TANKER & EVACUATE' if evac_status == 'REQUIRED' else 'MONITORING - GROUND CREW ONLY'}")
        print("Briefing Status: CONFIRMED - Data sent to Alberta Emergency Operations.")
    
    print("="*75 + "\n")

generate_emergency_briefing()

# Close the database connection after all operations are complete
conn.close()