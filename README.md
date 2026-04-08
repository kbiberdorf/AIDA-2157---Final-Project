# 🔥 Alberta Wildfire AI Engine
### AIDA 2157 — Final Project

A machine learning system that predicts, monitors, and responds to wildfire threats across Alberta, Canada. Built on an MS SQL Server database with 1,000+ synthetic incident records, the engine runs 10 independent AI models and outputs a live **Provincial Emergency Management Briefing** to the console.

---

## 📁 Project Files

| File | Description |
|---|---|
| `Step 1 - Create Tables.sql` | Initializes the full MS SQL database (10 tables, foreign keys) |
| `Step 2 - Row Count.sql` | Validates record counts across key tables |
| `Step 3 - Create View.sql` | Creates the `vw_Final_AI_Predictions` summary view |
| `Step 4 - View.sql` | Query to read the predictions view |
| `data_generator.py` | Generates 1,000 synthetic Alberta wildfire incident records |
| `main_engine.py` | Runs all 10 AI models and prints the Emergency Briefing |
| `AIDA_2157_-_Final_Project_-_Logic.pdf` | Technical summary covering model comparison, ethics, and reliability |

---

## 🗄️ Database Schema (10 Tables)

| Table | Purpose |
|---|---|
| `Weather_Stations` | Metadata and locations for regional sensors |
| `Weather_Logs` | Historical temperature, humidity, and wind data |
| `Terrain_Data` | Fuel types, soil moisture, and slope steepness |
| `Lightning_Strikes` | GPS coordinates and intensity (kA) of recorded strikes |
| `Fire_History` | Past incident data including size and containment duration |
| `Call_911_History` | Training data for the False Alarm Filter |
| `Community_Infrastructure` | Neighborhoods, hospitals, power grids, and roads |
| `Emergency_Resources` | Air tankers, helitack crews, and wildland units |
| `Model_Metadata` | Versioning and accuracy scores for all 10 AI models |
| `Prediction_Archive` | Log of every AI-generated alert and prediction |

---

## 🤖 The 10 AI Models

| # | Use Case | Model Type | Predicts |
|---|---|---|---|
| 1 | Lightning Ignition Predictor | Random Forest Classifier | Will a strike start a fire? |
| 2 | Fire Size Forecast | Random Forest Classifier | Major (>100 ha) or Minor? |
| 3 | False Alarm Filter | Logistic Regression | Real fire or false alarm? |
| 4 | Containment Time Estimator | Random Forest Regressor | Days to full containment |
| 5 | Smoke AQI Forecast | Random Forest Regressor | Air Quality Index score |
| 6 | Evacuation Alert | Random Forest Classifier | Evacuation required? |
| 7 | Road Closure Automation | Logistic Regression | Close roads? Yes/No |
| 8 | Landslide Risk (Post-Fire) | Random Forest Classifier | Collapse risk on burned slopes |
| 9 | Pre-Positioning Dispatch | Random Forest Classifier | Dispatch air tanker now? |
| 10 | Infrastructure Priority | Random Forest Classifier | Flag vegetation clearing zones |

---

## ⚙️ Setup & Usage

### Prerequisites
- Python 3.8+
- MS SQL Server (local instance)
- Required Python packages:

```bash
pip install pyodbc pandas numpy scikit-learn
```

### Step 1 — Initialize the Database
Open MS SQL Server Management Studio and run:
```
AIDA_2157_-_Final_Project_-_SQL_Script.sql
AIDA_2157_-_Final_Project_-_Create_View.sql
```

### Step 2 — Update the Connection String
In both `data_generator.py` and `main_engine.py`, update this line to match your server name:
```python
conn_str = ("Driver={SQL Server};Server=YOUR_SERVER_NAME;Database=AIDA2157_Final_Project;Trusted_Connection=yes;")
```

### Step 3 — Generate Synthetic Data
```bash
python data_generator.py
```
This populates all 10 tables with 1,000 realistic Alberta wildfire incident scenarios.

### Step 4 — Run the AI Engine
```bash
python main_engine.py
```

---

## 🖥️ Sample Console Output

```
--- ALBERTA WILDFIRE AI ENGINE STARTING ---
Success: Ignition Predictor  | Accuracy: 0.9150
Success: Fire Size            | Accuracy: 0.9300
Success: False Alarm          | Accuracy: 0.8750
Success: Containment          | Avg Error: 3.2100
Success: Smoke AQI            | Avg Error: 12.4500
Success: Evacuation           | Accuracy: 0.9200
Success: Road Closure         | Accuracy: 0.9400
Success: Landslide            | Accuracy: 0.8900
Success: Dispatch             | Accuracy: 0.9050
Success: Infrastructure       | Accuracy: 0.8800
--- ALL 10 ALBERTA MODELS PROCESSED ---

==================================================
  PROVINCIAL EMERGENCY MANAGEMENT BRIEFING
  Location: Alberta, Canada | AI Status: Active
==================================================
CRITICAL INCIDENT DETECTED AT: [53.4821, -114.9023]
Current Conditions:   38.2°C | Wind:   72.4 km/h
--------------------------------------------------
 [1] IGNITION PROBABILITY:     HIGH (Model Accuracy: 91.50%)
 [2] FIRE SIZE FORECAST:        MAJOR
 [3] 911 CALL ASSESSMENT:       REAL FIRE
 [4] CONTAINMENT ESTIMATE:      12.5 Days
 [5] SMOKE AQI FORECAST:        187.3 AQI
 [6] EVACUATION STATUS:         REQUIRED
 [7] ROAD CLOSURE STATUS:       CLOSE ROADS
 [8] LANDSLIDE RISK (Post-Fire): HIGH RISK
 [9] AIR TANKER DISPATCH:       DISPATCH NOW
[10] INFRASTRUCTURE PRIORITY:   CLEAR VEGETATION
--------------------------------------------------
ACTION PLAN: DISPATCH AIR TANKER & EVACUATE
Briefing Status: CONFIRMED - Data sent to Alberta Emergency Operations.
==================================================
```

---

## 📄 Technical Summary

See `AIDA_2157_-_Final_Project_-_Logic.pdf` for the full writeup covering:

- **Model Comparison** — Logistic Regression vs. Random Forest for Road Closure prediction
- **Ethics** — Implications of a False Negative in Major Fire classification
- **Reliability** — How soil moisture sensor accuracy affects the Ignition Predictor

---

## 📍 Data Context

All incident scenarios are synthetic and geo-bounded to **Alberta, Canada** (49°N–60°N, 110°W–120°W). Fuel types include Lodgepole Pine, Black Spruce, Aspen, and Boreal Grass. Fire causes include Lightning, Abandoned Campfire, Arson, and Power Line Arc.
