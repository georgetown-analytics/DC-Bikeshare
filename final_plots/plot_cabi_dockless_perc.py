import pandas as pd
import util_functions as uf
import matplotlib.pyplot as plt


if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()

    '''
    Percentage of Total Rides: Dockless vs. CaBi (Total and CaBI)
    [[PLOT]]
    '''
    df = pd.read_sql("""select distinct
                        date,
                        /*Get Daily Percentage by taking daily totals and dividing by pilot totals*/
                        (cabi_trips_wdc_to_wdc/cabi_trips_wdc_to_wdc_pilot)*100 as "Total CaBi DC to DC",
                        (cabi_trips_wdc_to_wdc_casual/cabi_trips_wdc_to_wdc_casual_pilot)*100 as "Total CaBi DC to DC, Casual",
                        (dless_trips_all/dless_trips_all_pilot)*100 as "Total Dockless Trips"
                        from final_db as db
                        left join
                        /*Aggregate Trips for the entire Pilot for CaBi and Dockless Totals*/
                        (select
                        sum(cabi_trips_wdc_to_wdc) as cabi_trips_wdc_to_wdc_pilot,
                        sum(cabi_trips_wdc_to_wdc_casual) as cabi_trips_wdc_to_wdc_casual_pilot,
                        sum(cabi_trips_wdc_to_wdc_member) as cabi_trips_wdc_to_wdc_member_pilot,
                        sum(dless_trips_all) as dless_trips_all_pilot
                        from final_db
                        where dless_trips_all > 0 and date > '2017-09-10') as tot
                        on db.date = db.date
                        where dless_trips_all > 0 and date > '2017-09-10';
                     """, con=conn)

    total_df = df[['date', "Total CaBi DC to DC", "Total Dockless Trips"]]
    casual_df = df[['date', "Total CaBi DC to DC, Casual", "Total Dockless Trips"]]

    for df in [total_df, casual_df]:
        # Plot Style
        plt.style.use('seaborn-darkgrid')
        plt.figure(figsize=(20, 10))
        # multiple line plot
        for column in df[[col for col in df if col != "Total Dockless Trips"]].drop('date', axis=1):
            plt.plot(df['date'], df[column], marker='', linewidth=1, alpha=0.4)

        # Now re do the interesting curve, but biger with distinct color
        plt.plot(df['date'], df['Total Dockless Trips'], marker='', linewidth=2, alpha=0.4)

        # Add titles
        '''plt.title("Daily Percentage of Total Trips over the Dockless Pilot Period (September 10, 2017 - April 30, 2018) \
                  \n{} (Orange) vs {}".format(df.columns[-1], df.columns[1]), loc='left', fontsize=12, fontweight=0)'''
        plt.xlabel("Dockless Pilot Period (September 10, 2017 - April 30, 2018)")
        plt.ylabel("Daily Percentage of Total Trips")
        plt.legend()

        plt.savefig("Daily Percentage_{}_vs_{}.png".format(df.columns[-1], df.columns[1]))
