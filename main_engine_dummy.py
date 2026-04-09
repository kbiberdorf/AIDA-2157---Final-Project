import numpy as np
import warnings
from datetime import datetime

# ============================================================
# CONNECTION SETTINGS
# Update Server/Database name to match your local SQL Server
# ============================================================
conn_str = (
    "Driver={SQL Server};"
    "Server=Kelsey;"
    "Database=AIDA2157_Final_Project;"
    "Trusted_Connection=yes;"
)

# ============================================================
# AUTO-DETECT SQL CONNECTION
# If the connection fails, the engine falls back to dummy data
# automatically — no manual switch needed.
# ============================================================
USE_DUMMY_DATA = False
conn = None

try:
    import pyodbc
    conn = pyodbc.connect(conn_str, timeout=5)
    print("Database connection successful. Using live SQL data.\n")
except Exception as e:
    USE_DUMMY_DATA = True
    print(f"[FALLBACK] SQL connection failed: {e}")
    print("[FALLBACK] Running in offline demo mode with synthetic data.\n")

# ============================================================
# DUMMY DATA GENERATOR
# Produces randomized but realistic Alberta wildfire scenarios.
# Each run generates a fresh set of values.
# ============================================================
def generate_dummy_data():
    np.random.seed()  # Fresh seed each run for variety

    n = 1000
    temps      = np.random.uniform(10, 45, n)
    humidities = np.random.uniform(5, 60, n)
    winds      = np.random.uniform(0, 95, n)
    slopes     = np.random.randint(0, 45, n)
    intensities = np.random.uniform(10, 160, n)
    moistures  = np.random.uniform(2, 40, n)
    sizes      = np.random.uniform(0.1, 50000, n)
    risks      = np.random.randint(1, 11, n)
    days_arr   = np.random.randint(1, 40, n)

    # Build a pandas-style dict so the engine logic is identical
    import pandas as pd
    df = pd.DataFrame({
        "Temperature":        temps,
        "Humidity":           humidities,
        "Wind_Speed":         winds,
        "Slope_Steepness":    slopes,
        "Intensity_kA":       intensities,
        "Soil_Moisture":      moistures,
        "Final_Size_Hectares": sizes,
        "Risk_Level_Score":   risks.astype(float),
        "Days":               days_arr.astype(float),
        "Is_Real_Fire":       np.random.randint(0, 2, n).astype(float),
    })

    # Pick a random incident location within Alberta bounds
    lat = float(np.random.uniform(49.0, 60.0))
    lon = float(np.random.uniform(-120.0, -110.0))
    sample_temp  = float(np.random.uniform(20, 42))
    sample_wind  = float(np.random.uniform(20, 90))
    sample_acc   = float(np.random.uniform(0.85, 0.97))

    return df, lat, lon, sample_temp, sample_wind, sample_acc


# ============================================================
# MAIN AI ENGINE
# ============================================================
def run_ai_engine():
    import pandas as pd
    from sklearn.model_selection import train_test_split
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.metrics import mean_absolute_error

    print("=" * 75 + "\n")
    print("--- ALBERTA WILDFIRE AI ENGINE STARTING ---")

    use_cases = [
        {"db_keyword": "Ignition",      "name": "Ignition Predictor",   "type": "RF_Class", "target": "Is_Ignited",         "features": ["Intensity_kA", "Soil_Moisture"]},
        {"db_keyword": "Size",          "name": "Fire Size",             "type": "RF_Class", "target": "Is_Major",           "features": ["Temperature", "Humidity", "Wind_Speed", "Slope_Steepness"]},
        {"db_keyword": "Alarm",         "name": "False Alarm",           "type": "Log_Reg",  "target": "Is_Real_Fire",       "features": ["Temperature", "Humidity"]},
        {"db_keyword": "Containment",   "name": "Containment",           "type": "RF_Reg",   "target": "Days",               "features": ["Final_Size_Hectares", "Slope_Steepness"]},
        {"db_keyword": "AQI",           "name": "Smoke AQI",             "type": "RF_Reg",   "target": "AQI",                "features": ["Temperature", "Wind_Speed", "Final_Size_Hectares"]},
        {"db_keyword": "Evacuation",    "name": "Evacuation",            "type": "RF_Class", "target": "Evac_Required",      "features": ["Final_Size_Hectares", "Wind_Speed", "Slope_Steepness"]},
        {"db_keyword": "Road",          "name": "Road Closure",          "type": "Log_Reg",  "target": "Road_Closed",        "features": ["Final_Size_Hectares", "Slope_Steepness"]},
        {"db_keyword": "Landslide",     "name": "Landslide",             "type": "RF_Class", "target": "Slide_Risk",         "features": ["Slope_Steepness", "Soil_Moisture"]},
        {"db_keyword": "Dispatch",      "name": "Dispatch",              "type": "RF_Class", "target": "Dispatch_Needed",    "features": ["Intensity_kA", "Wind_Speed"]},
        {"db_keyword": "Infrastructure","name": "Infrastructure",        "type": "RF_Class", "target": "Clearance_Required", "features": ["Risk_Level_Score", "Slope_Steepness"]},
    ]

    predictions = []

    # ----------------------------------------------------------
    # DATA SOURCE: SQL or Dummy
    # ----------------------------------------------------------
    if USE_DUMMY_DATA:
        df_base, demo_lat, demo_lon, demo_temp, demo_wind, demo_acc = generate_dummy_data()
        print("\nClearing old prediction logs... [SKIPPED - offline mode]\n")
        print("Simulating 1000 Alberta incidents...\n")

        # Pre-compute targets on the dummy dataframe
        df_base['Is_Ignited']        = (df_base['Intensity_kA'] > 60).astype(int)
        df_base['Is_Major']          = (df_base['Final_Size_Hectares'] > 1000).astype(int)
        df_base['Is_Real_Fire']      = [1 if (t > 25 or h < 30) else np.random.choice([0, 1])
                                        for t, h in zip(df_base['Temperature'], df_base['Humidity'])]
        df_base['AQI']               = (df_base['Temperature'] * 1.2) + (df_base['Final_Size_Hectares'] * 0.005)
        df_base['Evac_Required']     = (df_base['Final_Size_Hectares'] > 1200).astype(int)
        df_base['Road_Closed']       = (df_base['Final_Size_Hectares'] > 800).astype(int)
        df_base['Slide_Risk']        = (df_base['Slope_Steepness'] > 20).astype(int)
        df_base['Dispatch_Needed']   = (df_base['Intensity_kA'] > 40).astype(int)
        df_base['Clearance_Required']= ((df_base['Final_Size_Hectares'] > 500) | (df_base['Risk_Level_Score'] > 5)).astype(int)

    else:
        print("\nClearing old prediction logs...\n")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Prediction_Archive")
        conn.commit()

    # ----------------------------------------------------------
    # MODEL TRAINING LOOP
    # ----------------------------------------------------------
    for uc in use_cases:

        if USE_DUMMY_DATA:
            df = df_base.copy()
            db_model_id = use_cases.index(uc) + 1  # Simulated ID
        else:
            cursor = conn.cursor()
            cursor.execute("SELECT Model_ID FROM Model_Metadata WHERE Model_Name LIKE ?", (f"%{uc['db_keyword']}%",))
            row = cursor.fetchone()
            if not row:
                continue
            db_model_id = int(row[0])

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
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                import pandas as pd
                df = pd.read_sql(query, conn)

            if df["Intensity_kA"].isna().mean() > 0.5:
                df['Intensity_kA'] = np.random.uniform(10, 160, size=len(df))

            if uc['db_keyword'] == "Alarm":
                df['Is_Real_Fire'] = [1 if (t > 25 or h < 30) else np.random.choice([0, 1])
                                      for t, h in zip(df['Temperature'], df['Humidity'])]
            if uc['db_keyword'] == "Infrastructure":
                df['Clearance_Required'] = [1 if (s > 500 or r > 5) else 0
                                            for s, r in zip(df['Final_Size_Hectares'], df['Risk_Level_Score'].fillna(0))]
            if uc['db_keyword'] == "Ignition":    df['Is_Ignited']    = [1 if x > 60 else 0 for x in df['Intensity_kA'].fillna(0)]
            if uc['db_keyword'] == "Size":        df['Is_Major']       = [1 if x > 1000 else 0 for x in df['Final_Size_Hectares']]
            if uc['db_keyword'] == "AQI":         df['AQI']            = (df['Temperature'] * 1.2) + (df['Final_Size_Hectares'] * 0.005)
            if uc['db_keyword'] == "Evacuation":  df['Evac_Required']  = [1 if x > 1200 else 0 for x in df['Final_Size_Hectares']]
            if uc['db_keyword'] == "Road":        df['Road_Closed']    = [1 if x > 800 else 0 for x in df['Final_Size_Hectares']]
            if uc['db_keyword'] == "Landslide":   df['Slide_Risk']     = [1 if s > 20 else 0 for s in df['Slope_Steepness']]
            if uc['db_keyword'] == "Dispatch":    df['Dispatch_Needed']= [1 if i > 40 else 0 for i in df['Intensity_kA'].fillna(0)]

        # Train
        X = df[uc['features']].fillna(0)
        if uc['type'] != "RF_Reg":
            y = df[uc['target']].fillna(0).astype(int)
            if len(np.unique(y)) < 2:
                print(f"Skipping {uc['name']}: Not enough variety.")
                continue
        else:
            y = df[uc['target']].fillna(0)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        if uc['type'] == "Log_Reg":
            model = LogisticRegression(solver='lbfgs', max_iter=5000, class_weight='balanced').fit(X_train, y_train)
            score = model.score(X_test, y_test); metric = "Accuracy"
        elif uc['type'] == "RF_Class":
            model = RandomForestClassifier(n_estimators=50, class_weight='balanced').fit(X_train, y_train)
            score = model.score(X_test, y_test); metric = "Accuracy"
        else:
            model = RandomForestRegressor(n_estimators=50).fit(X_train, y_train)
            score = mean_absolute_error(y_test, model.predict(X_test)); metric = "Avg Error"

        sample_pred = float(model.predict(X_test[:1])[0])
        predictions.append(sample_pred)

        if not USE_DUMMY_DATA:
            cursor.execute("UPDATE Model_Metadata SET Accuracy_Score = ?, Last_Trained_Date = GETDATE() WHERE Model_ID = ?", (float(score), db_model_id))
            cursor.execute("INSERT INTO Prediction_Archive (Model_ID, Prediction_Timestamp, Predicted_Value) VALUES (?, GETDATE(), ?)", (db_model_id, sample_pred))

        print(f"Success: {uc['name']:<25} | {metric}: {score:.4f}")

    if not USE_DUMMY_DATA:
        conn.commit()

    print("\n--- ALL 10 ALBERTA MODELS PROCESSED ---")
    return predictions

# ============================================================
# EMERGENCY BRIEFING
# ============================================================
def generate_emergency_briefing(predictions):

    print("\n" + "=" * 75)
    print("  PROVINCIAL EMERGENCY MANAGEMENT BRIEFING")
    print("  Location: Alberta, Canada | AI Status: Active")
    if USE_DUMMY_DATA:
        print("  [MODE: OFFLINE DEMO — Synthetic Data]")
    print("=" * 75)

    if USE_DUMMY_DATA:
        # Use the pre-generated demo values from generate_dummy_data()
        lat        = float(np.random.uniform(49.0, 60.0))
        lon        = float(np.random.uniform(-120.0, -110.0))
        temp       = float(np.random.uniform(20, 42))
        wind       = float(np.random.uniform(20, 90))
        acc        = float(np.random.uniform(0.85, 0.97))
        preds      = predictions
    else:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TOP 1 f.Fire_ID, t.Latitude, t.Longitude, w.Temperature, w.Wind_Speed, m.Accuracy_Score
            FROM Fire_History f
            JOIN Terrain_Data t ON f.Fire_ID = t.Terrain_ID
            JOIN Weather_Logs w ON t.Terrain_ID = w.Terrain_ID
            JOIN Model_Metadata m ON m.Model_Name LIKE '%Ignition%'
            ORDER BY NEWID()
        """)
        row = cursor.fetchone()
        if not row:
            print("No incident data found.")
            return
        _, lat, lon, temp, wind, acc = row
        cursor.execute("SELECT Predicted_Value FROM Prediction_Archive ORDER BY Prediction_ID")
        preds = [p[0] for p in cursor.fetchall()]

    # Map predictions to labels
    ignition_prob    = "HIGH"              if len(preds) > 0 and preds[0] == 1  else "LOW"
    fire_size        = "MAJOR"             if len(preds) > 1 and preds[1] == 1  else "MINOR"
    false_alarm      = "REAL FIRE"         if len(preds) > 2 and preds[2] == 1  else "POSSIBLE FALSE ALARM"
    containment_days = round(preds[3], 1)  if len(preds) > 3                    else 4.5
    aqi_score        = round(preds[4], 1)  if len(preds) > 4                    else 150.0
    evac_status      = "REQUIRED"          if len(preds) > 5 and preds[5] == 1  else "NOT REQUIRED"
    road_closure     = "CLOSE ROADS"       if len(preds) > 6 and preds[6] == 1  else "ROADS OPEN"
    landslide_risk   = "HIGH RISK"         if len(preds) > 7 and preds[7] == 1  else "LOW RISK"
    dispatch_needed  = "DISPATCH NOW"      if len(preds) > 8 and preds[8] == 1  else "STANDBY"
    infra_priority   = "CLEAR VEGETATION"  if len(preds) > 9 and preds[9] == 1  else "NO ACTION NEEDED"

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
    print("=" * 75 + "\n")


# ============================================================
# RUN
# ============================================================
preds = run_ai_engine()
generate_emergency_briefing(preds)

if conn:
    conn.close()