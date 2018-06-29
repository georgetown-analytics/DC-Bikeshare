from dockless_exploration_graphs import *


def plot_reg_lines(df_s, axis):
    # Function to create a regression plot and change the x axis to be dates
    df = df_s
    df['index'] = df.reset_index().index.values
    sns.regplot(
        x='index', y='dless_total_perc', data=df, ax=axis,
        label='Dockless', color='b')
    sns.regplot(
        x='index', y='cabi_total_perc', data=df, ax=axis,
        label='Cabi Total', color='r')
    sns.regplot(
        x='index', y='cabi_casual_perc', data=df, ax=axis,
        label='Cabi Casual', color='g')
    axis.set_xlim(0, len(df))
    xticks = axis.get_xticks()
    # the value of the x axis is the day difference from the starting minimum
    # start day of the main dataframe.
    xticks = [df['date'].min() + datetime.timedelta(days=d) for d in xticks]
    # custom list of xticks are now set as tick labels
    axis.set_xticklabels(xticks)
    axis.xaxis.label.set_visible(False)
    axis.yaxis.label.set_visible(False)


if __name__ == '__main__':

    conn = read_only_connect_aws()
    try:
        os.mkdir('./Load Graphs')
    except FileExistsError:
        pass
    load_path = './Load Graphs/'
    google_drive_location = '1LRJWj6wLBWvyBJbN93jXA2dpgF3BLrN3'
    main = pd.read_sql(
        """select distinct
        date,
        /*Get Daily Percentage by taking daily totals and dividing by pilot totals*/
        (cabi_trips_wdc_to_wdc/cabi_trips_wdc_to_wdc_pilot)*100 as cabi_total_perc,
        (cabi_trips_wdc_to_wdc_casual/cabi_trips_wdc_to_wdc_casual_pilot)*100 as cabi_casual_perc,
        (dless_trips_all/dless_trips_all_pilot)*100 as dless_total_perc
        from final_db as db
        left join
        /*Aggregate Trips for the entire Pilot for CaBi and Dockless Totals*/
        (select
        sum(cabi_trips_wdc_to_wdc) as cabi_trips_wdc_to_wdc_pilot,
        sum(cabi_trips_wdc_to_wdc_casual) as cabi_trips_wdc_to_wdc_casual_pilot,
        sum(dless_trips_all) as dless_trips_all_pilot
        from final_db
        where dless_trips_all > 0) as tot
        on db.date = db.date
        where dless_trips_all > 0;
             """, con=conn)
    print(main.head())

    dr = open_drive()
    f, axes = plt.subplots(1, 2, sharey='row', figsize=(20, 10))

    axes[0].set_title(
        "First Four Trial Months (September 10, 2017 - December 31, 2017)")
    axes[1].set_title(
        "Second Four Trial Months (January 1, 2018 - April 30, 2018)")
    # Adding regression line plots to the subplots
    plot_reg_lines(
        main[main['date'] <= datetime.date(
            year=2017, month=12, day=31)], axes[0])
    plot_reg_lines(
        main[main['date'] > datetime.date(
            year=2017, month=12, day=31)], axes[1])
    axes[0].yaxis.label.set_visible(True)
    axes[0].set_ylabel("Daily Percentage of Total Trips")
    handles, labels = axes[0].get_legend_handles_labels()
    f.legend(handles, labels, loc='best')
    all_in_one_save(
        "Dockless Pilot", load_path, dr,
        google_drive_location)
    # Delete Graphs from Directory
    shutil.rmtree(load_path)
