-- STEP 0: CLEANUP 
-- Drops existing objects to allow for a fresh "Clean Run"
IF OBJECT_ID('vw_Final_AI_Predictions', 'V') IS NOT NULL DROP VIEW vw_Final_AI_Predictions;
IF OBJECT_ID('Prediction_Archive', 'U') IS NOT NULL DROP TABLE Prediction_Archive;
IF OBJECT_ID('Model_Metadata', 'U') IS NOT NULL DROP TABLE Model_Metadata;
IF OBJECT_ID('Emergency_Resources', 'U') IS NOT NULL DROP TABLE Emergency_Resources;
IF OBJECT_ID('Community_Infrastructure', 'U') IS NOT NULL DROP TABLE Community_Infrastructure;
IF OBJECT_ID('Call_911_History', 'U') IS NOT NULL DROP TABLE Call_911_History;
IF OBJECT_ID('Fire_History', 'U') IS NOT NULL DROP TABLE Fire_History;
IF OBJECT_ID('Lightning_Strikes', 'U') IS NOT NULL DROP TABLE Lightning_Strikes;
IF OBJECT_ID('Weather_Logs', 'U') IS NOT NULL DROP TABLE Weather_Logs;
IF OBJECT_ID('Weather_Stations', 'U') IS NOT NULL DROP TABLE Weather_Stations;
IF OBJECT_ID('Terrain_Data', 'U') IS NOT NULL DROP TABLE Terrain_Data;
GO

-- 1. Metadata for sensors
CREATE TABLE Weather_Stations (
    Station_ID INT PRIMARY KEY IDENTITY(1,1),
    Station_Name VARCHAR(100),
    Latitude FLOAT,
    Longitude FLOAT,
    Elevation INT
);

-- 2. Static terrain and fuel data
CREATE TABLE Terrain_Data (
    Terrain_ID INT PRIMARY KEY IDENTITY(1,1),
    Latitude FLOAT,
    Longitude FLOAT,
    Fuel_Type VARCHAR(50), 
    Soil_Moisture FLOAT,   -- Critical for Use Case #1
    Slope_Steepness INT    -- Degrees
);

-- 3. Historical and forecast weather metrics (Integrated Terrain_ID)
CREATE TABLE Weather_Logs (
    Log_ID INT PRIMARY KEY IDENTITY(1,1),
    Station_ID INT FOREIGN KEY REFERENCES Weather_Stations(Station_ID),
    Log_Timestamp DATETIME,
    Temperature FLOAT,    -- Celsius
    Humidity FLOAT,       -- Percentage
    Wind_Speed FLOAT,     -- km/h
    Wind_Direction VARCHAR(5),
    Terrain_ID INT FOREIGN KEY REFERENCES Terrain_Data(Terrain_ID)
);

-- 4. Recorded lightning activity
CREATE TABLE Lightning_Strikes (
    Strike_ID INT PRIMARY KEY IDENTITY(1,1),
    Strike_Timestamp DATETIME,
    Latitude FLOAT,
    Longitude FLOAT,
    Intensity_kA FLOAT     -- Kiloamperes (strength of strike)
);

-- 5. Data on past fire incidents
CREATE TABLE Fire_History (
    Fire_ID INT PRIMARY KEY IDENTITY(1,1),
    Start_Date DATETIME,
    Containment_Date DATETIME, -- Used for Regression (Use Case #4)
    Start_Size_Hectares FLOAT,
    Final_Size_Hectares FLOAT,
    Cause VARCHAR(50)          
);

-- 6. Training data for the False Alarm Filter
CREATE TABLE Call_911_History (
    Call_ID INT PRIMARY KEY IDENTITY(1,1),
    Call_Timestamp DATETIME,
    Reported_Location VARCHAR(MAX),
    Is_Real_Fire BIT           -- 1 for True, 0 for False
);

-- 7. Neighborhoods and Power Lines
CREATE TABLE Community_Infrastructure (
    Infra_ID INT PRIMARY KEY IDENTITY(1,1),
    Name VARCHAR(100),
    Infra_Type VARCHAR(50), 
    Risk_Level_Score INT,   -- 1-10
    Latitude FLOAT,
    Longitude FLOAT
);

-- 8. Firefighting assets
CREATE TABLE Emergency_Resources (
    Resource_ID INT PRIMARY KEY IDENTITY(1,1),
    Resource_Type VARCHAR(50), 
    Current_Status VARCHAR(20),
    Home_Base_Location VARCHAR(100)
);

-- 9. Versioning for the 10 Python models
CREATE TABLE Model_Metadata (
    Model_ID INT PRIMARY KEY IDENTITY(1,1),
    Model_Name VARCHAR(100), 
    Model_Type VARCHAR(50), 
    Last_Trained_Date DATETIME,
    Accuracy_Score FLOAT     
);

-- 10. The output log of all AI predictions
CREATE TABLE Prediction_Archive (
    Prediction_ID INT PRIMARY KEY IDENTITY(1,1),
    Model_ID INT FOREIGN KEY REFERENCES Model_Metadata(Model_ID),
    Prediction_Timestamp DATETIME,
    Input_Summary VARCHAR(MAX), 
    Predicted_Value FLOAT,      
    Confidence_Interval FLOAT   
);
GO

PRINT 'Final Project Database Script Execution Complete.';