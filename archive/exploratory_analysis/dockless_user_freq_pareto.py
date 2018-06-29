import pandas as pd
import util_functions as uf
from plotly.offline import plot
from plotly.graph_objs import *
from plotly import tools


if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()

    # Trip Frequency Count for entire pilot by Operator
    full_df = pd.read_sql("""select distinct
                        user_freqs.operatorclean,
                        user_freqs.user_trips,
                        count(*) as freq_user_trips
                        from
                        ((select distinct
                        operatorclean,
                        userid,
                        count(*) as user_trips
                        from dockless_trips
                        where operatorclean in ('lime', 'spin')
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
                        order by operatorclean, sum(trips))
                        union
                        /*jump users*/
                        (select distinct
                        'jump' as operatorclean,
                        userid,
                        sum(trips) as user_trips
                        from jump_users
                        group by 1, 2
                        order by operatorclean, sum(trips))) as user_freqs
                        group by 1, 2
                        order by 1, 2;
                     """, con=conn)

    # Initialize Excel Instance
    # operator = 'jump'
    for operator in full_df['operatorclean'].drop_duplicates().tolist():
        df = full_df[full_df['operatorclean'] == operator].copy()
        df = df[df['user_trips'] < 50]
        # Calculate Cumulative Sum and Perc
        df['cumulative_sum'] = df['freq_user_trips'].cumsum()
        df['cumulative_perc'] = (df['cumulative_sum'] / df['freq_user_trips'].sum()) * 100
        df['demarcation'] = 80

        # Set up Plotly Traces
        trace1 = Bar(x=df.user_trips, y=df.freq_user_trips, name='Users by Frequency of Trips', marker=dict(color='rgb(34,163,192)'))
        trace2 = Scatter(x=df.user_trips, y=df.cumulative_perc, name='Cumulative Percentage', yaxis='y2',
                         line=dict(color='rgb(243,158,115)', width=2.4))
        trace3 = Scatter(x=df.user_trips, y=df.demarcation, name='80%', yaxis='y2',
                         line=dict(color='rgba(128,128,128,.45)', dash='dash', width=1.5))
        data = [trace1, trace2, trace3]
        # Set up Plotly Layout
        layout = Layout(title='{}'.format(operator.title()), titlefont=dict(color='', family='', size=0),
                        font=Font(color='rgb(128,128,128)', family='Balto, sans-serif', size=12),
                        width=1500, height=623, paper_bgcolor='rgb(240, 240, 240)', plot_bgcolor='rgb(240, 240, 240)',
                        hovermode='compare', margin=dict(b=120, l=60, r=60, t=65), showlegend=True,
                        legend=dict(x=.83, y=1.3, font=dict(family='Balto, sans-serif', size=12, color='rgba(128,128,128,.75)'),),
                        annotations=[dict(text="", showarrow=False, xref="paper", yref="paper", textangle=90, x=1.029, y=.75,
                                     font=dict(family='Balto, sans-serif', size=14, color='rgba(243,158,115,.9)'),)],
                        xaxis=dict(),
                        yaxis=dict(title='Users by Frequency of Trips', range=[0, max(df['freq_user_trips'])],
                                   tickfont=dict(color='rgba(34,163,192,.75)'),
                                   titlefont=dict(family='Balto, sans-serif', size=14, color='rgba(34,163,192,.75)')),
                        yaxis2=dict(range=[0, 101], tickfont=dict(color='rgba(243,158,115,.9)'), tickvals=[0, 20, 40, 60, 80, 100],
                                    overlaying='y', side='right'))
        # Save Figure
        '''fig = tools.make_subplots(rows=1, cols=1)
        fig.append_trace(trace1, 1, 1)
        fig.append_trace(trace2, 1, 1)
        fig.append_trace(trace3, 1, 1)
        fig['layout'].update(layout)'''
        fig = dict(data=data, layout=layout)
        plot(fig, auto_open=False, image='png', image_filename='plot_image',
             output_type='file', image_width=800, image_height=600,
             filename='{}_test.html'.format(operator), validate=False)
