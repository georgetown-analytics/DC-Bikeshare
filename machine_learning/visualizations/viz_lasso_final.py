"""
This script generates visualizations for our final presentation.
Our dependent variable is total DC to DC CaBi trips taken,
and the model used here is Lasso.

Output = 5 graphs in png format.
"""

from util_functions import *
import numpy as np
import pandas as pd
from pprint import pprint
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.externals import joblib
from yellowbrick.regressor import ResidualsPlot, AlphaSelection
from yellowbrick.features import Rank2D
from yellowbrick.features.importances import FeatureImportances
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.preprocessing import PolynomialFeatures, StandardScaler, MinMaxScaler
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.linear_model import LassoCV
from sklearn.model_selection import KFold

set_env_path()
conn, cur = aws_connect()

query = """
SELECT
EXTRACT(DOY FROM date) as day_of_year,
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
cabi_trips_wdc_to_wdc_casual,
dless_trips_all
from final_db"""

pd.options.display.max_rows = None
pd.options.display.max_columns = None

df = pd.read_sql(query, con=conn)

# Setting date to index for easier splitting
df.set_index(df.date, drop=True, inplace=True)
df.index = pd.to_datetime(df.index)

# Encode day_of_year as cyclical
df['sin_day_of_year'] = np.sin(2*np.pi*df.day_of_year/365)
df['cos_day_of_year'] = np.cos(2*np.pi*df.day_of_year/365)

train = df.loc['2013-01-01':'2017-09-08']
test = df.loc['2017-09-09':'2018-04-30']

# Specify columns to keep and drop for X and y
drop_cols = ['date', 'day_of_year', 'dless_trips_all']
y_cols = ['cabi_trips_wdc_to_wdc', 'cabi_trips_wdc_to_wdc_casual']

feature_cols = [col for col in df.columns if (col not in y_cols) & (col not in drop_cols)]

# X y split
Xtrain_raw = train[feature_cols]

# Our target variable here is all DC to DC trips
ytrain = train[y_cols[0]]
Xtest_raw = test[feature_cols]
ytest = test[y_cols[0]]

# Pull out dockless trips
dless = test['dless_trips_all']

# Custom class
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

to_drop = [
    'rain^2', 'snow^2', 'us_holiday^2', 'nats_single^2', 'nats_double^2',
    'dc_bike_event^2', 'sin_day_of_year^2', 'cos_day_of_year^2',
    'sin_day_of_year cos_day_of_year'
]

Xtrain_pf2 = Xtrain_pf.drop(labels=to_drop, axis=1)
Xtest_pf2 = Xtest_pf.drop(labels=to_drop, axis=1)

binary = [col for col in Xtrain_pf2.columns if Xtrain_pf2[col].nunique() == 2]
cont = [col for col in Xtrain_pf2.columns if col not in binary]

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

# Unpickle model
lasso = joblib.load('../lasso_total.pkl')

"""
Visualizations to create:
1. Rank2d Pearson Ranking of Features
2. Feature Importance
3. Residuals plot
4. Actual vs. Predicted with prediction error
5. Alpha Selection
"""

# Rank2d (naive, 18 variable case)
fig = plt.figure()
ax = fig.add_subplot()
rank = Rank2D(features=feature_cols, algorithm='pearson', ax=ax)
Xt = Xtrain[feature_cols]
rank.fit(Xt, ytrain)
rank.transform(Xt)
rank.poof(outpath="lasso_rank2d.png")

# Feature Importances (naive, 18 variable case)
fig = plt.figure()
ax = fig.add_subplot()
featimp = FeatureImportances(lasso, ax=ax)
featimp.fit(Xt, ytrain)
featimp.poof(outpath="lasso_featureimportances18.png")

# Residuals Plot
fig = plt.figure()
ax = fig.add_subplot()
resplot = ResidualsPlot(lasso, ax=ax)
resplot.fit(Xtrain, ytrain)
resplot.score(Xtest, ytest)
resplot.poof(outpath="lasso_resplot.png")

# Actual vs Predicted
lasso.fit(Xtrain, ytrain)
yhat = lasso.predict(Xtest)
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
plt.title('Lasso')
plt.legend()
fig.savefig('lasso_total.png')
plt.show()

# Alpha Selection
fig, ax = plt.subplots()
alphas = np.logspace(-2, 1, 250)
cv = KFold(n_splits=5, shuffle=True, random_state=7)
lasso = LassoCV(alphas=alphas, n_alphas=250, fit_intercept=True, normalize=False,
                cv=cv, tol=0.0001, n_jobs=-1, verbose=1)
visualizer = AlphaSelection(lasso, ax=ax)
visualizer.fit(Xtrain, ytrain)
visualizer.poof(outpath="lasso_alphaselection.png")
