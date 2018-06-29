# Bikeshare-DC: Data Loads

This folder will serve as a library of data loads to AWS.  

## Primary Data (CaBi and Dockless).

1. cabi_out_hist - Capital Bikeshare station outage history from May 2011 to March 22, 2018.

1. cabi_trips - Capital Bikeshare trip history from October 2010 to December 2017.

1. cabi_system - System informatiom from the CaBi API pulled on 3/24/2018.  Used primarily for appending region_code to station information 

1. cabi_stations_temp - Capital Bikeshare station information pulled from CaBi API 3/25/2018.

1. cabi_stations_geo_temp - Capital Bikeshare station information pulled from CaBi API 3/25/2018 + geopolitical identifiers from open data DC
    # Neighborhood Cluster Name - "cluster_name", ex. "Cluster 6"
    # Neighborhod Cluster Description = "ngh_names", ex. "Dupont Circle, Connecticut Avenue/K Street"
    # Advisory Neighborhood Commissioner District - "anc", ex. "2B"
    # Ward - "ward", ex. "2"

1. cabi_pricing_model - Capital Bikeshare overage pricing data for up to 24 hours of usage for both member and day pass users as of 3/25/2018.

1. cabi_trips_membertype - CaBi trips data from 2015-July 2017 with enhanced member type added to trip.  Will not be integrated into final database

1. cabi_membership - Monthly membership and trip counts

1. dockless_pricing_model - Pricing data all dockless except for Jump bike for up to 24 hours of usage.

1. jump_pricing_model - Pricing data for Jump Bikes, need to incorporate hub docking discount when using in Python scripts.

1. dockless_trips - Dockles trip data through February 2018 (no Spin Jan data and no Mobike Feb data)

1. dockless_trips_geo - Calculates trip distance, distance to closest start and end cabi station and keeps vital fields from dockless_trips.  Jump data not currently included due to rounding issues with lat and lon that will hopefully be resolved in the future.  As of 4/29: Now includes start and end ANC and Neighborhood Cluster.

1. ofo_users - Ofo operator data, users trips by user id and month, as of April have data from October through Febrary

1. jump_users - Jump operator data, users trips by user id and month, as of April have data from September through Febrary

1. dockless_bikes_api - Jump operator data, users trips by user id and month, as of April have data from September through Febrary

1. dockless_summary - Summary provided by DDOT with monthly bike available counts and trips taken


## Secondary Data (Weather, DC Population, Etc).

1. dark_sky_raw - Dark Sky API data from October 2010 to March 22, 2018.  Will be updated for rest of pilot period  at some point.

1. nats_games - List of all Nationals Home games from 2010 to 2018.  Datetime of game start, game number(for double header), and game attendance (to be added)

1. acs - American Community Survey data used to generate dc_pop

1. dc_pop - DC population estimates by year and month

1. bike_events - All significant bike events based on the WABA calendar as of 3/25/2018.


