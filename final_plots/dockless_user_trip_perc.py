from dockless_exploration_graphs import *

if __name__ == '__main__':
    conn = read_only_connect_aws()

    '''Stacked Bar Chart showing % of trips taken by users who took 5 trips or less
    vs greater than 5 trips. One bar for each operator for the entire pilot
    (except Mobike)
    '''
    try:
        os.mkdir('./Load Graphs')
    except FileExistsError:
        pass
    load_path = './Load Graphs/'
    google_drive_location = '1LRJWj6wLBWvyBJbN93jXA2dpgF3BLrN3'
    df = pd.read_sql("""select distinct
                        user_freqs.operatorclean,
                        user_freqs.user_trips,
                        count(*) as freq_user_trips
                        from
                        ((select distinct
                        operatorclean,
                        userid,
                        count(*) as user_trips
                        from dockless_trips
                        where operatorclean in ('lime', 'spin', 'jump')
                              AND userid != '0'
                        group by 1, 2
                        order by operatorclean, count(*))
                        union
                        /*ofo users*/
                        (select distinct
                        'ofo' as operatorclean,
                        userid,
                        sum(trips) as user_trips
                        from ofo_users
                        group by 1, 2
                        order by operatorclean, sum(trips))) as user_freqs
                        group by 1, 2
                        order by 1, 2;
                     """, con=conn)
    dr = open_drive()
    df['le_5'] = np.where(df['user_trips'] <= 5, 0, 1)
    le_5_df = df.groupby(
        ['operatorclean', 'le_5'])['freq_user_trips'].sum()
    le_5_df = le_5_df.groupby(level=0).apply(
        lambda x: 100 * x / float(x.sum())).reset_index()
    le_5_df = le_5_df.pivot(
        index='operatorclean', columns='le_5',
        values='freq_user_trips').reset_index()
    f, axes = plt.subplots(1, 1, figsize=(20, 10))
    width = 0.35
    le_5_df.plot.bar(x='operatorclean', y=[0, 1], ax=axes, stacked=True)
    axes.legend(
                ['<= {0} Trips'.format(5), '> {0} Trips'.format(5)],
                bbox_to_anchor=(0., -.13, 1., 0.0), loc=3,
                ncol=5, mode="expand", borderaxespad=0.)
    for pat in axes.patches:
        if pat.get_height() == 0:
            continue
        else:
            h1 = pat.get_height()
            axes.annotate(str(int(np.around(pat.get_height(), 0)))+'%', (
                pat.get_x() + .2, pat.get_y() + pat.get_height()/2),
                fontsize=10)
    axes.set_xlabel('')
    axes.set_xticks(rotate=90)
    all_in_one_save(
        "dless usage by {0} trips".format(5), load_path, dr,
        google_drive_location)
    # Delete Graphs from Directory
    shutil.rmtree(load_path)
