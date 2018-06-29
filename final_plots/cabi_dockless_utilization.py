from dockless_exploration_graphs import *

if __name__ == '__main__':
    conn = read_only_connect_aws()
    try:
        os.mkdir('./Load Graphs')
    except FileExistsError:
        pass
    load_path = './Load Graphs/'
    google_drive_location = '1LRJWj6wLBWvyBJbN93jXA2dpgF3BLrN3'

    ''' Daily Utilization using only API data for Jump, Spin and Lime vs CaBi
        System Wide
        [[PLOT]]
    '''
    df = pd.read_sql("""SELECT
                        api.*,
                        cabi_bikes_avail,
                        cabi_trips,
                        dless_trips_jump,
                        dless_trips_lime,
                        dless_trips_spin,
                        (dless_trips_jump / dless_bikes_jump) as jump_util_rate,
                        (dless_trips_lime / dless_bikes_lime) as lime_util_rate,
                        (dless_trips_spin / dless_bikes_spin) as spin_util_rate,
                        cabi_util_rate
                        FROM
                        (SELECT * FROM crosstab($$
                         /* Join dockless trip date to bikes available */
                        SELECT DISTINCT
                        date,
                        operator,
                        bikes_available
                        FROM dockless_bikes_api
                        WHERE date <= '04-30-2018'
                        ORDER BY 1, 2;
                         $$
                           ,$$SELECT unnest('{jump,lime,spin}'::text[])$$)
                        AS ct ("date" date, "dless_bikes_jump" int, "dless_bikes_lime" int, "dless_bikes_spin" int)) as api
                        LEFT JOIN
                        (select
                        date,
                        cabi_trips,
                        cabi_bikes_avail,
                        cabi_util_rate,
                        dless_trips_jump,
                        dless_trips_lime,
                        dless_trips_spin
                        from final_db) as db
                        on api.date = db.date
                     """, con=conn)

    dr = open_drive()
    # Utilization by Vendor
    df_utl = df[[
        'jump_util_rate', 'lime_util_rate', 'spin_util_rate', 'cabi_util_rate',
        'date']]
    df_utl = pd.melt(
        df_utl, id_vars=['date'], var_name='Category', value_name='utilization'
        )
    df_utl.replace(0, np.nan, inplace=True)
    df_utl['date'] = pd.to_datetime(df_utl['date'])
    df_utl['operator'] = df_utl['Category'].str.split('_').str.get(0)
    f, ax = plt.subplots(figsize=(20, 10))
    axis = sns.pointplot(
        x='date', y='utilization', hue='operator', data=df_utl, ax=ax,
        palette=['red', 'lime', 'orange', 'black'])
    axis.set_xlim(0, len(df_utl[df_utl['operator'] == 'cabi']))
    axis.xaxis.set_major_locator(ticker.MultipleLocator(10))
    xticks = axis.get_xticks()
    xticks = [
        df_utl['date'].min() + datetime.timedelta(days=int(d)) for d in xticks]
    xticks = [x.strftime("%m/%d/%y") for x in xticks]
    axis.set_xticklabels(xticks)
    axis.axvline(linewidth=4, color='blue', x=21)
    axis.annotate(
        'Lime Scooters Deployed!',
        xy=(21, 6),  # theta, radius
        xytext=(28, 6.5),    # fraction, fraction
        arrowprops=dict(facecolor='black', shrink=0.05)
        )
    all_in_one_save(
        "Utilization Operators Final", load_path, dr,
        google_drive_location)
    # Delete Graphs from Directory
    shutil.rmtree(load_path)
