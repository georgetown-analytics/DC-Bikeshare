import pandas as pd
import numpy as np
import util_functions as uf


def Growing(x, y):
    growth = (x - y) / y
    growth = growth / 12
    return growth


def building_month():
    df_dc_month['temp'] = df_dc_month['citypop'] * df_dc_month['grow_rate']
    df_dc_month['temp'] = df_dc_month['temp'].shift(1)
    df_dc_month.loc[df_dc_month['citypop'].isnull(), 'citypop'] = df_dc_month['temp'] + df_dc_month['citypop'].shift(1)
    del df_dc_month['temp']


def apply_rate():
    if df_dc_month.loc[[x], 'citypop'].item() == 0:
        df_dc_month['temp'] = df_dc_month['citypop'] * df_dc_month['grow_rate']
        df_dc_month['temp'] = df_dc_month['temp'].shift(1)
        df_dc_month.loc[[x], 'citypop'] = df_dc_month['temp'] + df_dc_month['citypop'].shift(1)
        del df_dc_month['temp']


def pct_bike():
    # GENERATING Biking as a percentage of overall transportation methods, Statecip = 98 is DC and TRANWORK = 40 is BIKING
    df_dc_trans = pd.read_sql("""SELECT year,
                                 CASE
                                    WHEN (tranwork = 40) THEN 1
                                    ELSE 0
                                 END as biking
                                 FROM acs
                                 WHERE stateicp = 98""", con=conn)

    df_dc_dummies = df_dc_trans.groupby(['year'])['biking'].agg(['sum', 'count'])
    df_dc_dummies['pct_bike'] = df_dc_dummies['sum'] / df_dc_dummies['count']
    df_dc_dummies.reset_index(inplace=True)
    return df_dc_dummies


def dc_pop():
    '''Creating Monthly Population data. for 17/18, start at 1/16 and pull the number forwarder growing'''
    df_dc_pop = pd.read_sql("""SELECT DISTINCT year, citypop *100 as citypop
                               FROM acs
                               WHERE stateicp = 98
                               ORDER BY year""", con=conn)
    df_dc_pop['prior_pop'] = df_dc_pop['citypop'].shift(1)
    df_dc_pop['grow_rate'] = Growing(df_dc_pop['citypop'], df_dc_pop['prior_pop'])
    df_dc_pop['month'] = 1
    return df_dc_pop


def create_dc_pop(cur):
    # This script creates the CaBi System AWS table
    cur.execute("""
    DROP TABLE dc_pop;
    CREATE TABLE dc_pop (
        pop_date timestamp PRIMARY KEY,
        citypop numeric,
        grow_rate numeric,
        pct_bike numeric
            """)


if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()

    # Merge percent bike onto DC growth rate
    df_dc_pop = dc_pop().merge(pct_bike(), on=['year'], how='left')
    df_dc_pop = df_dc_pop[['year', 'citypop', 'prior_pop', 'grow_rate', 'month', 'pct_bike']]

    # Define Dataframe of years and all month and merge to dc pop dataframe
    month = np.arange(1, 13, 1)
    df_dc_month = pd.DataFrame([(d, tup.year) for tup in df_dc_pop.itertuples() for d in month], columns=['month', 'year'])
    df_dc_month = pd.merge(df_dc_month, df_dc_pop, on=['year', 'month'], how='left')

    # add 2017 and 2018 year/month by repurposing 2015 and 2016
    year_month_1718 = df_dc_month[['year', 'month']][df_dc_month['year'] >= 2015]
    year_month_1718['year'] = year_month_1718['year'] + 2
    df_dc_month = df_dc_month.append(year_month_1718)

    # Fill down growth rates for population and bike
    df_dc_month['grow_rate'] = df_dc_month['grow_rate'].fillna(method='ffill')
    df_dc_month['pct_bike'] = df_dc_month['pct_bike'].fillna(method='ffill')
    df_dc_month = df_dc_month.reset_index()

    # Apply growth rate to population figures
    for x in range(11):
        building_month()
    df_dc_month['citypop'] = df_dc_month['citypop'].fillna(value=0)
    for x in df_dc_month.index:
        apply_rate()

    # Keep final fields and drop any additional records
    df_dc_month['day'] = 1
    df_dc_month['pop_date'] = pd.to_datetime(df_dc_month[['year', 'month', 'day']])
    df_dc_month = df_dc_month[['pop_date', 'citypop', 'grow_rate', 'pct_bike']]
    df_dc_month = df_dc_month.dropna(how='any')

    # Output dataframe as CSV
    outname = "dc_pop"
    df_dc_month.to_csv(outname + ".csv", index=False, sep='|')
    # Create Table
    create_dc_pop(cur)
    # Load to Database
    uf.aws_load(outname, "dc_pop", cur)
    # Commit changes to database
    conn.commit()

