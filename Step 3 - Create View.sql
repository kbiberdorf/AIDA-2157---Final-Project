-- STEP 2: VIEWS
-- Provides a human-readable summary of AI performance
CREATE VIEW vw_Final_AI_Predictions AS
SELECT 
    p.Prediction_ID, 
    m.Model_Name, 
    p.Prediction_Timestamp, 
    p.Predicted_Value
FROM Prediction_Archive p
INNER JOIN Model_Metadata m ON p.Model_ID = m.Model_ID;
GO