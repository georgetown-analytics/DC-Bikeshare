from dockless_exploration_graphs import *

if __name__ == '__main__':
    conn = read_only_connect_aws()
    # Geographic Overlap by Operator Over Time
    try:
        os.mkdir('./Load Graphs')
    except FileExistsError:
        pass
    load_path = './Load Graphs/'
    google_drive_location = '1LRJWj6wLBWvyBJbN93jXA2dpgF3BLrN3'
    df = pd.read_sql("""select distinct
                        date,
                        /* % of trips that Start within quarter mile of CaBi Station*/
                        dless_geo_start_jump,
                        dless_geo_start_lime,
                        dless_geo_start_mobike,
                        dless_geo_start_ofo,
                        dless_geo_start_spin,
                        /* % of trips that End within quarter mile of CaBi Station*/
                        dless_geo_end_jump,
                        dless_geo_end_lime,
                        dless_geo_end_mobike,
                        dless_geo_end_ofo,
                        dless_geo_end_spin
                        from final_db
                        where dless_trips_all > 0
                        """, con=conn)
    print(df.tail())

    # Open google drive connection
    dr = open_drive()
    # Reshaping the data to derive operators from the category
    df_2 = pd.melt(
        df, id_vars=['date'], var_name='Category',
        value_name='pct_total_trips')
    df_2['operator'] = df_2['Category'].str.split('_').str.get(3)
    df_2['time'] = df_2['Category'].str.split('_').str.get(2)
    sns.boxplot(
        x='operator', y='pct_total_trips', hue='time', data=df_2,
        showfliers=False)
    plt.title('Geographic Overlap by Operator Over Time')
    all_in_one_save(
            "Geo Overlap", load_path, dr,
            google_drive_location)
    # Delete Graphs from Directory
    shutil.rmtree(load_path)
