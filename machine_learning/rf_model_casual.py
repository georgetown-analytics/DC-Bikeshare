"""
CaBi ML fitting - Random Forest - Casual rides

This is the result of converting our Jupyter Notebook to a .py file.

In this notebook I use RandomForestRegressor to fit on our training data,
1/1/2013 to 9/8/2017, score the model using 5-fold cross-validation,
then predict on our test data, 9/9/2017 to 4/30/2018.

Dependent variable = casual DC to DC CaBi rides.

0. Data load, shaping, and split
* Read in data from AWS
  * Check for high pairwise correlation
* Encode time variable (day_of_year) as cyclical
* Split into Xtrain, Xtest, ytrain, ytest based on date
  * Specify feature and target columns
"""

# Read in data from AWS

from util_functions import *
import numpy as np
import pandas as pd
from pprint import pprint

set_env_path()
conn, cur = aws_connect()

query = """
SELECT
EXTRACT(DOY FROM date) as day_of_year,
date,
year,
quarter,
month,
CASE WHEN day_of_week = any('{0,6}') THEN 1 ELSE 0 END as weekend_dummy,
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
cabi_trips_wdc_to_wdc_casual
from final_db"""

pd.options.display.max_rows = None
pd.options.display.max_columns = None

df = pd.read_sql(query, con=conn)

# Setting date to index for easier splitting
df.set_index(df.date, drop=True, inplace=True)
df.index = pd.to_datetime(df.index)

print("We have {} instances and {} features".format(*df.shape))


# Summary statistics
df.describe(percentiles=[.5]).round(3).transpose()

def print_highly_correlated(df, features, threshold=0.75):
    """
    Prints highly correlated feature pairs in df. Threshold set at 0.75 by default.
    Selects pairs where abs(r) is above the threshold, puts them in a DataFrame,
    making sure to avoid duplication, then sorts by abs(r) and prints.
    """
    corr_df = df[features].corr()
    correlated_features = np.where(np.abs(corr_df) > threshold)
    correlated_features = [(corr_df.iloc[x,y], x, y) for x, y in zip(*correlated_features) if x != y and x < y]
    s_corr_list = sorted(correlated_features, key=lambda x: -abs(x[0]))
    print("There are {} feature pairs with pairwise correlation above {}".format(len(s_corr_list), threshold))
    for v, i, j in s_corr_list:
        cols = df[features].columns
        print("{} and {} = {:0.3f}".format(corr_df.index[i], corr_df.columns[j], v))

# Check for multicollinearity (this is the full dataset so it includes our targets)
# Doesn't really matter for RF, but good to show
print_highly_correlated(df, df.columns)


# Encode day of year as cyclical
df['sin_day_of_year'] = np.sin(2*np.pi*df.day_of_year/365)
df['cos_day_of_year'] = np.cos(2*np.pi*df.day_of_year/365)

"""
* Split into Xtrain, Xtest, ytrain, ytest based on date
  * Training dates = 2013-01-01 to 2017-09-08
  * Test dates = 2017-09-09 to 2018-04-30
    * Coincides with dockless pilot
"""

train = df.loc['2013-01-01':'2017-09-08']
test = df.loc['2017-09-09':'2018-04-30']

tr = train.shape[0]
te = test.shape[0]
trpct = tr/(tr+te)
tepct = te/(tr+te)

print("{:0.3f} percent of the data is in the training set and {:0.3f} percent is in the test set".format(trpct, tepct))

# Specify columns to keep and drop for X and y
drop_cols = ['date']
y_cols = ['cabi_trips_wdc_to_wdc', 'cabi_trips_wdc_to_wdc_casual']

feature_cols = [col for col in df.columns if (col not in y_cols) & (col not in drop_cols)]

# X y split
Xtrain = train[feature_cols]

# Our target variable here is casual DC to DC trips
ytrain = train[y_cols[1]]
Xtest = test[feature_cols]
ytest = test[y_cols[1]]

"""
1. Model Hyperparameter Tuning

* Scoring functions
* RandomizedSearchCV
* GridSearchCV
  * Compare GridSearch and RandomizedSearch scores and parameters
"""

from sklearn.metrics import mean_squared_error as mse
from sklearn.metrics import r2_score
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import KFold

def score_model(model):
    """
    Fits a model using the training set, predicts using the test set, and then calculates
    and reports goodness of fit metrics.
    """
    model.fit(Xtrain, ytrain)
    yhat = model.predict(Xtest)
    r2 = r2_score(ytest, yhat)
    me = mse(ytest, yhat)
    print("Results from {}: \nr2={:0.3f} \nMSE={:0.3f}".format(model, r2, me))

def cv_score(model, n_splits=5):
    """
    Evaluates a model by 5-fold cross-validation and prints mean and 2*stdev of scores.
    Shuffles before cross-validation but sets random_state=7 for reproducibility.
    """
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=7)
    scores = cross_val_score(model, Xtrain, ytrain, cv=kf,
                             scoring=None,
                             n_jobs=-1, verbose=3)
    print(scores)
    print("R^2: {:0.3f} (+/- {:0.3f})".format(scores.mean(), scores.std() * 2))

"""
RandomizedSearchCV
We need to find appropriate values for our hyperparameters.
We can start by using RandomizedSearchCV to cast a wide net.
"""

# Number of trees in random forest
n_estimators = [int(x) for x in np.linspace(200, 2000, 10)]

# Number of features to consider at every split
max_features = ['auto', 'sqrt']

# Maximum number of levels in tree
max_depth = [int(x) for x in np.linspace(10, 110, 11)]
max_depth.append(None)

# Minimum number of samples required to split a node
min_samples_split = [2, 5, 10]

# Minimum number of samples required at each leaf node
min_samples_leaf = [1, 2, 3, 4]

# Method of selecting samples for training each tree
bootstrap = [True, False]

# Create the parameter grid
param_distributions = {'n_estimators': n_estimators,
               'max_features': max_features,
               'max_depth': max_depth,
               'min_samples_split': min_samples_split,
               'min_samples_leaf': min_samples_leaf,
               'bootstrap': bootstrap}


# Altogether, there are 10 \* 2 \* 12 \* 3 \* 4 \* 2 = 5760 combinations.
# We randomly sample 100 times per fold.
from sklearn.model_selection import RandomizedSearchCV
from sklearn.ensemble import RandomForestRegressor

# Use the random grid to search for best hyperparameters
# First create the base model to tune
rf = RandomForestRegressor()

# Random search of parameters, using 5-fold cross-validation,
# search across 100 different combinations, and use all available cores
cv = KFold(n_splits=5, shuffle=True, random_state=7)
ran_search = RandomizedSearchCV(estimator=rf,
                               param_distributions=param_distributions,
                               n_iter=100, cv=cv, verbose=3, n_jobs=-1)

# Fit the random search model
ran_search.fit(Xtrain, ytrain)

# We're interested in seeing if there's any improvement between the untuned default RF model and our new one.
rf_random = ran_search.best_estimator_

print("Cross-validation score for base RF")
cv_score(rf)

print("\nCross-validation score for RF tuned by RandomizedSearchCV")
cv_score(rf_random)
print()

print("\nParameters chosen by RandomizedSearchCV")
pprint(ran_search.best_params_)

"""
GridSearchCV
Slight increase in performance with the parameters suggested by RandomizedSearchCV.
Next, we use GridSearchCV which iterates over all of the possible combinations instead of randomly sampling.
*Note: User input required in the next section to create the GridSearch parameter grid based on RandomizedSearch results.*
"""
from sklearn.model_selection import GridSearchCV

# Create the parameter grid based on the results of the random search
param_grid = {
    'bootstrap': [True],
    'max_depth': [60, 70, 80],
    'max_features': ['auto'],
    'min_samples_leaf': [1, 2],
    'min_samples_split': [2, 5],
    'n_estimators': [700, 800, 900]
}

# Create a base model
rf = RandomForestRegressor()

# Instantiate the grid search model
cv = KFold(n_splits=5, shuffle=True, random_state=7)
grid_search = GridSearchCV(estimator=rf, param_grid=param_grid,
                           scoring=None,
                           cv=cv, n_jobs=-1, verbose=3)

# Fit the grid search to the data
grid_search.fit(Xtrain, ytrain)

# How does this new model compare to the RandomizedSearchCV model?
rf_best = grid_search.best_estimator_

print("Cross-validation score for untuned RF")
cv_score(rf)
print("\nCross-validation score for RF tuned by RandomizedSearchCV")
cv_score(rf_random)
print("\nCross-validation score for RF tuned by GridSearchCV")
cv_score(rf_best)

# How do parameters differ between specifications?
print("RandomizedSearchCV params:")
pprint(ran_search.best_params_)
print("\nGridSearchCV params:")
pprint(grid_search.best_params_)


# Which features are most important?
feature_importances = pd.DataFrame(rf_best.feature_importances_,
                                   index=Xtrain.columns,
                                   columns=['importance']).sort_values('importance', ascending=False)
# Print 20 most important features
feature_importances.head(20)

"""
2. Model Fitting

* Fit on training data and predict on test data
  * Check residuals and prediction error graphs (yellowbrick)
* Plot predicted values vs actuals (yhat, ytest)
* Calculate and plot residuals (ytest - yhat)
"""

# How do our models perform on the test data?
score_model(rf)
score_model(rf_random)
score_model(rf_best)

# What do our residuals look like?
from yellowbrick.regressor import ResidualsPlot
resplot = ResidualsPlot(rf_best)
resplot.fit(Xtrain, ytrain)
resplot.score(Xtest, ytest)
g = resplot.poof()

# What does our prediction error look like?
from yellowbrick.regressor import PredictionError
prederr = PredictionError(rf_best)
prederr.fit(Xtrain, ytrain)
prederr.score(Xtest, ytest)
g = prederr.poof()

# Next, we pull out our fitted values (yhat) and actuals (ytest) to see how they compare.
# We also calculate our residuals by subtracting our fitted values from the actuals.
import matplotlib.pyplot as plt

rf_best.fit(Xtrain, ytrain)

yhat = rf_best.predict(Xtest)
resid = ytest - yhat

data = pd.DataFrame({'t': range(1, len(yhat) + 1),
                     'ytest': ytest,
                     'yhat': yhat,
                     'resid': resid})

plt.plot('t', 'ytest', data=data, color='blue', linewidth=1, label='actual')
plt.plot('t', 'yhat', data=data, color='orange', marker='o', linestyle="None", label='predicted', alpha=0.5)
plt.plot('t', 'resid', data=data, color='gray')
plt.legend()
plt.show()

from sklearn.externals import joblib
joblib.dump(rf_best, 'rf_casual.pkl')
# To get it out later,
# model = joblib.load('rf_casual.pkl')
