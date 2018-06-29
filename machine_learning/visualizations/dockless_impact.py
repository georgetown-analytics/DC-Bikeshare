import pandas as pd
import util_functions as uf
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates


if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()
    '''
    Dockless Impact Derived from Machine Learning Model
    [[PLOT]]
    '''
    models = ['rf_total', 'rf_casual', 'lasso_casual', 'lasso_total']
    for model in models:
        df = pd.read_sql("""select
                            *
                            from """ + model + """;
                         """, con=conn)
        # Scatter Plot with Reg Line
        fig, ax = plt.subplots(figsize=(20, 10))
        df['plot_date'] = mdates.date2num(df['date'])
        sns.regplot(x='plot_date', y='dless_impact', data=df, ax=ax, scatter_kws={'alpha': 0.3})
        # Assign locator and formatter for the xaxis ticks.
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y.%m.%d'))
        # Uncomment if we want to zoom in on reg line
        # plt.ylim(-1.5, 2)
        plt.xlim(min(df['plot_date']) - 10, max(df['plot_date']) + 10)
        # Add titles
        ax.set(xlabel='Dockless Pilot', ylabel='Impact = (Predicted-Actual) / Dockless Trips')
        fig.autofmt_xdate()
        plt.savefig("{}_impact.png".format(model))
