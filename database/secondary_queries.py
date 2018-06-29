import pandas as pd


def dark_sky(conn):
    # All weather data from Dark Sky
    df = pd.read_sql("""SELECT weather_date as date,
                        EXTRACT('year' FROM weather_date) as year,
                        EXTRACT('quarter' FROM weather_date) as quarter,
                        EXTRACT('month' FROM weather_date) as month,
                        EXTRACT('dow' FROM weather_date) as day_of_week,
                        EXTRACT('hour' FROM to_timestamp(apparenttemperaturehightime) at time zone 'america/new_york') as apparenttemperaturehightime,
                        EXTRACT('hour' FROM to_timestamp(apparenttemperaturelowtime) at time zone 'america/new_york') as apparenttemperaturelowtime,
                        EXTRACT('hour' FROM to_timestamp(temperaturehightime) at time zone 'america/new_york') as temperaturehightime,
                        EXTRACT('hour' FROM to_timestamp(temperaturelowtime) at time zone 'america/new_york') as temperaturelowtime,
                        EXTRACT('hour' FROM to_timestamp(precipintensitymaxtime) at time zone 'america/new_york') as precipintensitymaxtime,
                        EXTRACT('hour' FROM to_timestamp(sunrisetime) at time zone 'america/new_york') as sunrisetime,
                        EXTRACT('hour' FROM to_timestamp(sunsettime) at time zone 'america/new_york') as sunsettime,
                        EXTRACT('hour' FROM to_timestamp(day_time) at time zone 'america/new_york') as day_time,
                        EXTRACT('hour' FROM to_timestamp(sunsettime) at time zone 'america/new_york') - EXTRACT('hour' FROM to_timestamp(sunrisetime) at time zone 'america/new_york') as daylight_hours,
                        apparenttemperaturehigh,
                        apparenttemperaturelow,
                        temperaturehigh,
                        temperaturelow,
                        cloudcover,
                        dewpoint,
                        humidity,
                        moonphase,
                        precipaccumulation,
                        precipintensity,
                        precipintensitymax,
                        precipprobability,
                        pressure,
                        CASE WHEN preciptype = 'rain' THEN 1 ELSE 0 END as rain,
                        CASE WHEN preciptype = 'snow' THEN 1 ELSE 0 END as snow,
                        CASE WHEN preciptype = 'sleet' THEN 1 ELSE 0 END as sleet,
                        visibility,
                        windbearing,
                        windspeed
                        FROM dark_sky_raw
                        """, con=conn)
    return df


def nats_games(conn):
    # Count of National Games per day 2010-2018 (attendance data to be added later)
    df = pd.read_sql("""SELECT
                        date,
                        case when count(*) = 1 then 1 else 0 end as nats_single,
                        case when count(*) = 2 then 1 else 0 end as nats_double,
                        sum(attendance) as nats_attendance
                        from nats_attendance
                        where Home_Away != '@'
                        group by 1
                        order by 1
                        ;
                        """, con=conn)
    return df


def dc_pop(conn):
    # DC Monthly Population Estimates
    df = pd.read_sql("""SELECT
                        EXTRACT(year FROM pop_date) as year,
                        EXTRACT(month from pop_date) as month,
                        citypop as dc_pop
                        FROM dc_pop
                        WHERE pop_date::date >= '2010-09-01'
                        ORDER BY EXTRACT(year FROM pop_date), EXTRACT(month from pop_date)
                        """, con=conn)
    return df


def dc_bike_events(conn):
    # DC Bike Events 2014-2018
    df = pd.read_sql("""SELECT
                        final_date AS date,
                        1 AS dc_bike_event
                        FROM bike_events
                        ORDER BY final_date;
                        """, con=conn)
    return df


