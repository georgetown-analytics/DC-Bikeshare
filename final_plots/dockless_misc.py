import sys
import numpy as np
from read_aws import *
from google_drive_push import *
import seaborn as sns
from seaborn import *
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import re
import datetime
import os
import shutil


google_drive_location = '1LRJWj6wLBWvyBJbN93jXA2dpgF3BLrN3'

# Lists for graphing metrics
distance = [
    'cabi_trip_dist_avg_wdc_to_wdc', 'dless_tripdist_avg_jump',
    'dless_tripdist_avg_lime', 'dless_tripdist_avg_mobike',
    'dless_tripdist_avg_ofo', 'dless_tripdist_avg_spin']

trips_agg = [
    'cabi_trips_wdc_to_wdc', 'cabi_trips_wdc_to_wdc_member',
    'cabi_trips_wdc_to_wdc_casual', 'dless_trips_all']

trips_gran = [
    'cabi_trips_wdc_to_wdc', 'dless_trips_jump', 'dless_trips_lime',
    'dless_trips_mobike', 'dless_trips_ofo', 'dless_trips_spin']

user_all = [
    'cabi_active_members_total', 'dless_users_total',
    'dless_users_jump', 'dless_users_lime', 'dless_users_mobike',
    'dless_users_ofo', 'dless_users_spin']

month_lst = {
    1: 'January', 2: 'Feburary', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
    7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November',
    12: 'December'}


def month_prep(mon):
    # convert float month digit to integer to string month name
    mon = mon.astype(int)
    mon = mon.map(month_lst)
    return mon


def day_locations(ax, date_col):
    years = mdates.YearLocator()   # every year
    months = mdates.MonthLocator()  # every month
    yearsFmt = mdates.DateFormatter('%Y')
    ax.xaxis.set_major_locator(years)
    ax.xaxis.set_major_formatter(yearsFmt)
    ax.xaxis.set_minor_locator(months)
    datemin = datetime.date(date_col.min().year, 1, 1)
    datemax = datetime.date(date_col.max().year + 1, 1, 1)
    ax.set_xlim(datemin, datemax)
    ax.format_xdata = mdates.DateFormatter('%Y-%m-%d')
    ax.format_ydata = price


# format the coords message box
def price(x):
    return '$%1.2f' % x


class Data_Graph:
    # Class to draw different seaborn graphs. First step is init the dataframe
    def __init__(self, DATA):
        self.DATA = DATA

    def settings(self, columns, time):
        # list of columns to graph (y axis)
        self.columns = columns
        # Metric to graph by (x axis)
        self.time = time

    def utilization(self):
        # create utilization rates for cabi trip vars or dockless trip vars
        for x in self.columns:
            if re.match('cabi', x):
                self.DATA['{0}'.format(x.replace('trips', 'util'))] = (
                    self.DATA[x]/self.DATA['cabi_bikes_avail'])
                continue
            else:
                self.DATA['{0}'.format(x.replace('trips', 'util'))] = (
                    self.DATA[x]/self.DATA[x.replace('trips', 'bikes')])
        return self.DATA

    def grapher(self, axis, func):
        # pass in a list of matplotlib axis and a graphing module to plot ontop
        # of matplotlib figure. Little bit of sytle guides at the bottom for
        # graphs that use months on the x-axis.
        self.func = func
        self.axis = axis
        test = zip(self.columns, self.axis.flatten())
        for one, two in test:
            if self.time == 'date':
                day_locations(two, self.DATA[self.time])
            self.func(
                x=self.DATA[self.time], y=self.DATA[one], data=self.DATA,
                ax=two, showfliers=False, showmeans=True)
            if self.time == 'month':
                two.set_xticklabels(two.get_xticklabels(), rotation=45)


if __name__ == '__main__':
    # Loading the final database using a custom class to connect with AWS
    sys.path.append("..")
    conn = read_only_connect_aws()
    Full_Data = QueryTool(conn, 'final_db')
    df = Full_Data.basic()
    # Creating a temporary directory to stage the graphs for google drives
    os.mkdir('./Load Graphs')
    load_path = './Load Graphs/'
    # Only looking at days with at least one dockless trip
    df = df[df['dless_trips_all'] != 0]
    # Month Converter
    df['month'] = month_prep(df['month'])
    df['date'] = pd.to_datetime(df['date'])
    # Open google drive connection
    dr = open_drive()
    # Duration of Trips
    f, axes = plt.subplots(2, 3, sharex='col', sharey='row',  figsize=(20, 10))
    first = Data_Graph(df)
    first.settings(distance, 'month')
    first.grapher(axes, sns.boxplot)
    all_in_one_save(
        "Trip Duration", load_path, dr,
        google_drive_location)
    f, axes = plt.subplots(2, 2, sharex='col', sharey='row', figsize=(20, 10))
    first.settings(trips_agg, 'date')
    first.grapher(axes, sns.pointplot)
    f.autofmt_xdate()
    all_in_one_save(
        "Daily Trips", load_path, dr,
        google_drive_location)
    # Pct Cabi versus Dockless. Casual and total dc to dc trips
    pct_df = df.groupby(['month'])[
        'dless_trips_all', 'cabi_trips_wdc_to_wdc_casual',
        'cabi_trips_wdc_to_wdc'].sum().reset_index()
    pct_df['dless_tot'] = (
        pct_df['dless_trips_all']/(
            pct_df['dless_trips_all']+pct_df['cabi_trips_wdc_to_wdc'])*100)
    pct_df['cabi_tot'] = (
        pct_df['cabi_trips_wdc_to_wdc']/(
            pct_df['dless_trips_all'] + pct_df['cabi_trips_wdc_to_wdc'])*100)
    pct_df['dless_casual'] = (
        pct_df['dless_trips_all']/(
            pct_df['dless_trips_all'] + pct_df[
                'cabi_trips_wdc_to_wdc_casual'])*100)
    pct_df['cabi_casual'] = (
        pct_df['cabi_trips_wdc_to_wdc_casual']/(
            pct_df['dless_trips_all'] + pct_df[
                'cabi_trips_wdc_to_wdc_casual'])*100)
    # Creating subplots
    f, axes = plt.subplots(1, 2, sharex='col', sharey='row',  figsize=(20, 10))
    width = 0.35
    # Custom sorting on months
    pct_df['month'] = pd.Categorical(
        pct_df['month'], [
            'September', 'October', 'November', 'December',
            'January', 'Feburary', 'March', 'April'])
    pct_df.sort_values('month', inplace=True)
    pct_df = pct_df.reset_index()
    pct_df['index'] = pct_df.index.values
    # Stacked bar chart and making pretty plots
    l1 = axes[0].bar(pct_df['index'], pct_df['cabi_tot'], width)
    l2 = axes[0].bar(
        pct_df['index'], pct_df['dless_tot'], width, bottom=pct_df['cabi_tot'])
    axes[0].set_xticklabels(
        ('September', 'October', 'November', 'December', 'January',
         'Feburary', 'March', 'April'))
    axes[0].set_xticklabels(
        ('', 'September', 'October', 'November', 'December', 'January',
         'Feburary', 'March', 'April'))
    axes[0].set_title("Total Cabi Rides vs Dockless", fontsize=12)
    r1 = axes[1].bar(pct_df['index'], pct_df['cabi_casual'], width)
    r2 = axes[1].bar(
        pct_df['index'], pct_df['dless_casual'], width,
        bottom=pct_df['cabi_casual'])
    axes[1].set_xticklabels(
        ('', 'September', 'October', 'November', 'December', 'January',
         'Feburary', 'March', 'April'))
    axes[1].set_title("Cabi Casual Rides vs Dockless", fontsize=12)
    f.legend(
        (r1[0], r2[0]), ('Capital Bikeshare', 'Dockless'), loc='upper left')
    # Annotating the graph
    for grp in axes:
        for pat in grp.patches:
            h1 = pat.get_height()
            grp.annotate(str(int(np.around(pat.get_height(), 0)))+'%', (
                pat.get_x(), pat.get_y() + pat.get_height()/2),
                fontsize=10)
    all_in_one_save(
        "Market Share", load_path, dr,
        google_drive_location)
    # Dockless operator over total dockles trips
    pct_df = df.groupby(['month'])[
        'dless_trips_jump', 'dless_trips_lime', 'dless_trips_mobike',
        'dless_trips_ofo', 'dless_trips_spin', 'dless_trips_all'
        ].sum().reset_index()
    dless = [
            'dless_trips_jump', 'dless_trips_lime', 'dless_trips_mobike',
            'dless_trips_ofo', 'dless_trips_spin']
    for x in dless:
        pct_df['pct_{0}'.format(x)] = (
            pct_df[x] / pct_df['dless_trips_all'] * 100)
    dless_pct = [
            'pct_dless_trips_jump', 'pct_dless_trips_lime',
            'pct_dless_trips_mobike', 'pct_dless_trips_ofo',
            'pct_dless_trips_spin']
    pct_df['month'] = pd.Categorical(
        pct_df['month'], [
            'September', 'October', 'November', 'December', 'January',
            'Feburary', 'March', 'April'])
    pct_df.sort_values('month', inplace=True)
    pct_df = pct_df.reset_index()
    pct_df['index'] = pct_df.index.values
    f, axes = plt.subplots(1, 1, figsize=(20, 10))
    width = 0.35
    pct_df.plot.bar(
        x='index', y=dless_pct, ax=axes, stacked=True,
        color=['red', 'lime', 'gray', 'yellow', 'orange'])
    axes.set_xticklabels((
        'September', 'October', 'November', 'December', 'January', 'Feburary',
        'March', 'April'), rotation=0)
    axes.set_xlabel('Month')
    axes.legend(
        ['Jump', 'Lime', 'Mobike', 'Ofo', 'Spin'],
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

    all_in_one_save(
            "Market Share Dockless", load_path, dr,
            google_drive_location)
    # Delete Graphs from Directory
    shutil.rmtree(load_path)
