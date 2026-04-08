SELECT 
   (SELECT COUNT(*) FROM Terrain_Data) AS Total_Incidents,
   (SELECT COUNT(*) FROM Community_Infrastructure) AS Total_Assets,
   (SELECT COUNT(*) FROM Emergency_Resources) AS Total_Resources;