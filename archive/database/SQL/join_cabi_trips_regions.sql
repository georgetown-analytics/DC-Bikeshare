SELECT cabi_trips.*, 
       start_st.region_code AS start_region_code,
       start_st.ngh_names AS start_ngh_names,
       start_st.anc AS start_anc,
       start_st.ward AS start_ward,
       end_st.region_code AS end_region_code,
       end_st.ngh_names AS end_ngh_names,
       end_st.anc AS end_anc,
       end_st.ward AS end_ward
FROM cabi_trips
LEFT JOIN(SELECT cabi_stations_geo_temp.*, cabi_system.code AS region_code
	  FROM cabi_stations_geo_temp
	  LEFT JOIN cabi_system
	  ON cabi_stations_geo_temp.region_id = cabi_system.region_id) AS start_st
ON cabi_trips.start_station = start_st.short_name
LEFT JOIN(SELECT cabi_stations_geo_temp.*, cabi_system.code AS region_code
	  FROM cabi_stations_geo_temp
	  LEFT JOIN cabi_system
	  ON cabi_stations_geo_temp.region_id = cabi_system.region_id) AS end_st
ON cabi_trips.end_station = end_st.short_name
LIMIT 10000;