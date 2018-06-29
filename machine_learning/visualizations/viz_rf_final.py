"""
This script generates visualizations for our final presentation.
Our dependent variable is total DC to DC CaBi trips taken,
and the model used here is Random Forest.

Output = 4 graphs in png format.
"""

from util_functions import *
import numpy as np
import pandas as pd
from pprint import pprint
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.externals import joblib
from yellowbrick.regressor import ResidualsPlot
from yellowbrick.features import Rank2D
from yellowbrick.features.importances import FeatureImportances

set_env_path()
conn, cur = aws_connect()

query = """
SELECT
EXTRACT(DOY FROM date) as day_of_year,
date,
year,
quarter,
month,
day_of_week,
daylight_hours,
apparenttemperaturehigh,
apparenttemperaturehightime,
apparenttemperaturelow,
apparenttemperaturelowtime,
precipintensitymaxtime,
sunrisetime,
sunsettime,
cloudcover,
dewpoint,
humidity,
precipaccumulation,
precipintensitymax,
precipprobability,
rain,
snow,
visibility,
windspeed,
us_holiday,
nats_single,
nats_double,
nats_attendance,
dc_bike_event,
dc_pop,
cabi_bikes_avail,
cabi_stations_alx,
cabi_stations_arl,
cabi_stations_ffx,
cabi_stations_mcn,
cabi_stations_mcs,
cabi_stations_wdc,
cabi_docks_alx,
cabi_docks_arl,
cabi_docks_ffx,
cabi_docks_mcn,
cabi_docks_mcs,
cabi_docks_wdc,
cabi_stations_tot,
cabi_docks_tot,
cabi_active_members_day_key,
cabi_active_members_monthly,
cabi_active_members_annual,
cabi_trips_wdc_to_wdc,
cabi_trips_wdc_to_wdc_casual,
dless_trips_all
from final_db"""

df = pd.read_sql(query, con=conn)

# Setting date to index for easier splitting
df.set_index(df.date, drop=True, inplace=True)
df.index = pd.to_datetime(df.index)

df['sin_day_of_year'] = np.sin(2*np.pi*df.day_of_year/365)
df['cos_day_of_year'] = np.cos(2*np.pi*df.day_of_year/365)

train = df.loc['2013-01-01':'2017-09-08']
test = df.loc['2017-09-09':'2018-04-30']

# Specify columns to keep and drop for X and y
drop_cols = ['date', 'dless_trips_all']
y_cols = ['cabi_trips_wdc_to_wdc', 'cabi_trips_wdc_to_wdc_casual']

feature_cols = [col for col in df.columns if (col not in y_cols) & (col not in drop_cols)]

# X y split
Xtrain = train[feature_cols]

# Our target variable here is all DC to DC trips
ytrain = train[y_cols[0]]
Xtest = test[feature_cols]
ytest = test[y_cols[0]]

# Pull out dockless trips
dless = test['dless_trips_all']

# Unpickle model
rf = joblib.load('../rf_total.pkl')

"""
Visualizations to create:
1. Feature Importances
2. Rank2d Pearson Ranking of Features
3. Residuals plot
4. Actual vs. Predicted with prediction error
"""

# Feature Importances
fig = plt.figure(figsize=(10,10))
ax = fig.add_subplot()
viz = FeatureImportances(rf, ax=ax)
viz.fit(Xtrain, ytrain)
viz.poof(outpath="rf_featureimportances.png")

# Rank2d
fig = plt.figure(figsize=(10,10))
ax = fig.add_subplot()
rank = Rank2D(features=feature_cols, algorithm='pearson', ax=ax)
rank.fit(Xtrain, ytrain)
rank.transform(Xtrain)
rank.poof(outpath="rf_rank2d.png")

# Residuals Plot
fig = plt.figure()
ax = fig.add_subplot()
resplot = ResidualsPlot(rf, ax=ax)
resplot.fit(Xtrain, ytrain)
resplot.score(Xtest, ytest)
resplot.poof(outpath="rf_resplot.png")

# Actual vs Predicted
rf.fit(Xtrain, ytrain)
yhat = rf.predict(Xtest)
error = ytest - yhat
data = pd.DataFrame({'t': test['date'],
                     'ytest': ytest,
                     'yhat': yhat,
                     'error': error,
                     'neg_error': np.negative(error),
                     'dless': dless})
fig, ax = plt.subplots()
plt.plot('t', 'ytest', data=data, color='blue', linewidth=1, label='actual')
plt.plot('t', 'yhat', data=data, color='orange', marker='o', linestyle="None", label='predicted', alpha=0.5)
plt.plot('t', 'error', data=data, color='gray')
plt.title('Random Forest')
plt.legend()
fig.savefig('rf_total.png')
