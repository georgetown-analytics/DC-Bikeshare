from dockless_exploration_graphs import *

if __name__ == '__main__':
    conn = read_only_connect_aws()
    try:
        os.mkdir('./Load Graphs')
    except FileExistsError:
        pass
    load_path = './Load Graphs/'
    google_drive_location = '1LRJWj6wLBWvyBJbN93jXA2dpgF3BLrN3'
    df = pd.read_sql("""select distinct
                        date,
                        /* Active Users for Individual Dockless Operators*/
                        dless_users_jump,
                        dless_users_lime,
                        dless_users_mobike,
                        dless_users_ofo,
                        dless_users_spin,
                        /* Total Active Users for Dockless Operators*/
                        (dless_users_jump +
                         dless_users_lime +
                         dless_users_mobike +
                         dless_users_ofo +
                         dless_users_spin) as dless_users_total,
                        /* Total Active Users */
                        (cabi_active_members_day_key +
                        cabi_active_members_monthly +
                        cabi_active_members_annual) as cabi_active_members_total
                        from final_db
                        where dless_trips_all > 0
                        """, con=conn)
    print(df.tail())

    dr = open_drive()
    # Utilization by Vendor
    # Reshaping the data to allow for the hue function to work in seaborn
    df = pd.melt(
        df, id_vars=['date'], var_name='Category', value_name='users'
        )
    df.replace(0, np.nan, inplace=True)
    df['date'] = pd.to_datetime(df['date'])
    # Splitting the category column to extract the operator name
    df['operator'] = df['Category'].str.split('_').str.get(2)
    df['operator'].replace('members', 'cabi', inplace=True)
    df['operator'].replace('total', 'dockless', inplace=True)
    df['count'] = df.groupby(['operator']).cumcount()+1
    f, ax = plt.subplots(figsize=(12, 8))
    # Depricated ts plot does a simple line graph that's easier to work with
    # then point plot.
    axis = sns.tsplot(
        time='count', value='users', unit='operator', condition='operator',
        data=df, ax=ax,
        color=['red', 'lime', 'grey', 'yellow', 'orange', 'purple', 'black'])
    axis.set_xlim(0, len(df[df['operator'] == 'cabi']))
    # axis formatting
    axis.xaxis.set_major_locator(ticker.MultipleLocator(10))
    xticks = axis.get_xticks()
    xticks = [
        df['date'].min() + datetime.timedelta(days=int(d)) for d in xticks]
    xticks = [x.strftime("%m/%d/%y") for x in xticks]
    axis.set_xticklabels(xticks, rotation=45)
    axis.set_xlabel('Date')
    axis.set_ylabel('User Count')

    all_in_one_save(
        "Active Users Final", load_path, dr,
        google_drive_location)
    # Delete Graphs from Directory
    shutil.rmtree(load_path)
