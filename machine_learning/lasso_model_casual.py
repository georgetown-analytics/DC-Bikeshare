
"""
CaBi ML fitting - Lasso - Casual rides

This is the result of converting our Jupyter Notebook to a .py file.

In this script I use lasso to fit on our training data, 1/1/2013 to 9/8/2017,
score the model using 5-fold cross-validation,
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

set_env_path()
conn, cur = aws_connect()

query = """
SELECT
EXTRACT(DOY FROM date) as day_of_year,
CASE WHEN day_of_week = any('{0,6}') THEN 1 ELSE 0 END as weekend_dummy,
date,
daylight_hours,
apparenttemperaturehigh,
cloudcover,
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
dc_bike_event,
dc_pop,
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
    Prints highly correlated feature pairs in df.
    """
    corr_df = df[features].corr()
    # Select pairs above threshold
    correlated_features = np.where(np.abs(corr_df) > threshold)
    # Avoid duplication
    correlated_features = [(corr_df.iloc[x,y], x, y) for x, y in zip(*correlated_features) if x != y and x < y]
    # Sort by abs(correlation)
    s_corr_list = sorted(correlated_features, key=lambda x: -abs(x[0]))
    print("There are {} feature pairs with pairwise correlation above {}".format(len(s_corr_list), threshold))
    for v, i, j in s_corr_list:
        cols = df[features].columns
        print("{} and {} = {:0.3f}".format(corr_df.index[i], corr_df.columns[j], v))

# Check for multicollinearity (this is the full dataset so it includes our targets)
print_highly_correlated(df, df.columns)

# Encode day_of_year as cyclical
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
print(train.shape, test.shape)

tr = train.shape[0]
te = test.shape[0]
trpct = tr/(tr+te)
tepct = te/(tr+te)

print("{:0.3f} percent of the data is in the training set and {:0.3f} percent is in the test set".format(trpct, tepct))

# Specify columns to keep and drop for X and y
drop_cols = ['date', 'day_of_year']
y_cols = ['cabi_trips_wdc_to_wdc', 'cabi_trips_wdc_to_wdc_casual']

feature_cols = [col for col in df.columns if (col not in y_cols) & (col not in drop_cols)]

# X y split
Xtrain_raw = train[feature_cols]

# Our target variable here is casual DC to DC trips
ytrain = train[y_cols[1]]
Xtest_raw = test[feature_cols]
ytest = test[y_cols[1]]
print(Xtrain_raw.shape, ytrain.shape, Xtest_raw.shape, ytest.shape)

"""
1. Preprocessing

We want to use PolynomialFeatures and StandardScaler in a Pipeline, but we only want to scale continuous features.

Here, I do the polynomial transformation first and then feed it through a pipeline because I wasn't able to get it all working in one pipeline.

* Use PolynomialFeatures to create quadratic and interaction terms
  * Convert back to DataFrame
  * Drop redundant variables
* Use Pipeline and FeatureUnion to selectively scale/ignore certain variables
* Fit and transform using pipeline to get final Xtrain and Xtest
"""

# Imports and custom classes
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.preprocessing import PolynomialFeatures, StandardScaler, MinMaxScaler
from sklearn.base import BaseEstimator, TransformerMixin

class Columns(BaseEstimator, TransformerMixin):
    """
    This is a custom transformer for splitting the data into subsets for FeatureUnion.
    """
    def __init__(self, names=None):
        self.names = names

    def fit(self, X, y=None, **fit_params):
        return self

    def transform(self, X):
        return X[self.names]

pf = PolynomialFeatures(2, include_bias=False)

Xtrain_pf_array = pf.fit_transform(Xtrain_raw)
Xtest_pf_array = pf.transform(Xtest_raw)

# Get feature names
Xtrain_cols = pf.get_feature_names(Xtrain_raw.columns)

# Convert arrays to dfs with the new pf column names
Xtrain_pf = pd.DataFrame(Xtrain_pf_array, columns=Xtrain_cols)
Xtest_pf = pd.DataFrame(Xtest_pf_array, columns=Xtrain_cols)

# Dropping squared dummies and nonsensical interaction terms

to_drop = [
    'rain^2', 'snow^2', 'us_holiday^2', 'nats_single^2', 'nats_double^2',
    'dc_bike_event^2', 'sin_day_of_year^2', 'cos_day_of_year^2',
    'sin_day_of_year cos_day_of_year', 'weekend_dummy^2'
]

Xtrain_pf2 = Xtrain_pf.drop(labels=to_drop, axis=1)
Xtest_pf2 = Xtest_pf.drop(labels=to_drop, axis=1)

# Defining binary and continuous variables
# We want to MinMaxScale the binary variables and StandardScale the continuous variables

binary = [col for col in Xtrain_pf2.columns if Xtrain_pf2[col].nunique() == 2]
cont = [col for col in Xtrain_pf2.columns if col not in binary]

# FeatureUnion in our pipeline shifts the ordering of the variables so we need to save the ordering here
cols = binary + cont

pipeline = Pipeline([
    ('features', FeatureUnion([
        ('binary', Pipeline([
            ('bincols', Columns(names=binary)),
            ('minmax', MinMaxScaler())
        ])),
        ('continuous', Pipeline([
            ('contcols', Columns(names=cont)),
            ('scaler', StandardScaler())
        ]))
    ]))
])

# Fit and transform to create our final Xtrain and Xtest

pipeline.fit(Xtrain_pf2)
Xtrain_scaled = pipeline.transform(Xtrain_pf2)
Xtest_scaled = pipeline.transform(Xtest_pf2)

# Put everything back into dfs
Xtrain = pd.DataFrame(Xtrain_scaled, columns=cols)
Xtest = pd.DataFrame(Xtest_scaled, columns=cols)

# Check to see if the transforms worked as intended
Xtrain.describe(percentiles=[.5]).round(3).transpose()

"""
2. Model Fitting

* Define functions for scoring
* Score model using 5-fold cross-validation
* Fit on training data and predict on test data
  * Check residuals and prediction error graphs (yellowbrick)
* Plot predicted values vs actuals (yhat, ytest)
* Calculate and plot residuals (ytest - yhat)
"""

from sklearn.metrics import mean_squared_error as mse
from sklearn.metrics import mean_absolute_error as mae
from sklearn.metrics import median_absolute_error as medae
from sklearn.metrics import explained_variance_score as evs
from sklearn.metrics import r2_score
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import KFold

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

def score_model(model):
    """
    Fits a model using the training set, predicts using the test set, and then calculates
    and reports goodness of fit metrics and alpha.
    """
    model.fit(Xtrain, ytrain)
    yhat = model.predict(Xtest)
    r2 = r2_score(ytest, yhat)
    me = mse(ytest, yhat)
    ae = mae(ytest, yhat)
    mede = medae(ytest, yhat)
    ev = evs(ytest, yhat)
    print("Results from {}: \nr2={:0.3f} \nMSE={:0.3f} \nMAE={:0.3f} \nMEDAE={:0.3f} \nEVS={:0.3f} \nalpha={:0.3f}".format(model, r2, me, ae, mede, ev, model.alpha_))

"""
* Specify hyperparameters
* Instantiate model
* Score model by 5-fold cross-validation
"""

from sklearn.linear_model import LassoCV

# Alphas to search over
alphas = np.logspace(-3, 1, 250)

# Instantiate model
cv = KFold(n_splits=5, shuffle=True, random_state=7)
lasso = LassoCV(alphas=alphas, n_alphas=250, fit_intercept=True, normalize=False,
                cv=cv, tol=0.0001, n_jobs=-1, verbose=1)

# Cross-validation
cv_score(lasso)

# Which variables were selected?
lasso.fit(Xtrain, ytrain)

# Put coefficients and variable names in df
lassodf = pd.DataFrame(lasso.coef_, index=Xtrain.columns)

# Select nonzeros
results = lassodf[(lassodf.T != 0).any()]

# Sort by magnitude
results['sorted'] = results[0].abs()
results.sort_values(by='sorted', inplace=True, ascending=False)

print("Lasso chooses {} variables".format(len(results)))
print(results)

# How does our model perform on the test data?
score_model(lasso)

# What do our residuals look like?
from yellowbrick.regressor import ResidualsPlot
resplot = ResidualsPlot(lasso)
resplot.fit(Xtrain, ytrain)
resplot.score(Xtest, ytest)
g = resplot.poof()

# What does our prediction error look like?
from yellowbrick.regressor import PredictionError
prederr = PredictionError(lasso)
prederr.fit(Xtrain, ytrain)
prederr.score(Xtrain, ytrain)
g = prederr.poof()

# Next, we pull out our fitted values (yhat) and actuals (ytest) to see how they compare.
# We also calculate our residuals by subtracting our fitted values from the actuals.
import matplotlib.pyplot as plt

lasso.fit(Xtrain, ytrain)

yhat = lasso.predict(Xtest)
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

# Pickle model
from sklearn.externals import joblib
joblib.dump(lasso, 'lasso_casual.pkl')
# To get it out later,
# model = joblib.load('lasso_casual.pkl')
