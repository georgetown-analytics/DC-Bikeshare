
# coding: utf-8

# # CaBi ML fitting
# In this notebook, I extend the ML framework that I used on the UCI data to the CaBi data.
# 
# This version includes all variables labeled "for ML" in the data dictionary as an illustrative example.

# ## 0. Data load, shaping, and split
# * Read in data from AWS
#   * Aside - note multicollinearity
# * Encode time variable (day_of_year) as cyclical
# * Split into Xtrain, Xtest, ytrain, ytest based on date
#   * Specify feature and target columns

# In[1]:

# Read in data from AWS

from util_functions import *
import numpy as np
import pandas as pd

set_env_path()
conn, cur = aws_connect()

'''
For this nb, I only pull the date variable day_of_year for later transformation into cyclical time variables.
Not 100% sure on whether or not this precludes using things like OneHotEncoded day_of_week, but I omit that here.

I also omit actual temperature variables in favor of apparent temperature. 
Some other weather variables are omitted like moonphase and windbearing
'''

query = """
SELECT 
EXTRACT(DOY FROM date) as day_of_year,
date,
daylight_hours,
apparenttemperaturehigh,
apparenttemperaturelow,
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
cabi_dur_empty_wdc,
cabi_dur_full_wdc,
cabi_dur_empty_arl,
cabi_dur_full_arl,
cabi_dur_full_alx,
cabi_dur_empty_alx,
cabi_dur_empty_mcs,
cabi_dur_full_mcs,
cabi_dur_full_mcn,
cabi_dur_empty_mcn,
cabi_dur_full_ffx,
cabi_dur_empty_ffx,
cabi_dur_empty_tot,
cabi_dur_full_tot,
cabi_active_members_day_key,
cabi_active_members_monthly,
cabi_active_members_annual,
cabi_trips_wdc_to_wdc,
cabi_trips_wdc_to_wdc_casual
from final_db"""
pd.options.display.max_rows = None
pd.options.display.max_columns = None

df = pd.read_sql(query, con=conn)
df.set_index(df.date, drop=True, inplace=True)
df.index = pd.to_datetime(df.index)

print("We have {} instances and {} features".format(*df.shape))


# In[2]:

df.describe(percentiles=[.5]).round(3).transpose()


# In[3]:

def print_highly_correlated(df, features, threshold=0.75):
    """Prints highly correlated feature pairs in df"""
    corr_df = df[features].corr()
    # Select pairs above threshold
    correlated_features = np.where(np.abs(corr_df) > threshold)
    # Avoid duplication
    correlated_features = [(corr_df.iloc[x,y], x, y) for x, y in zip(*correlated_features) if x != y and x < y]
    # Sort by abs(correlation)
    s_corr_list = sorted(correlated_features, key=lambda x: -abs(x[0]))
    print("There are {} feature pairs with pairwise correlation above {}".format(len(corr_df.columns), threshold))
    for v, i, j in s_corr_list:
        cols = df[features].columns
        print("{} and {} = {:0.3f}".format(corr_df.index[i], corr_df.columns[j], v))


# In[4]:

# Note multicollinearity

print_highly_correlated(df, df.columns, threshold=0.75)


# In[5]:

# Encode day_of_year as cyclical
df['sin_day_of_year'] = np.sin(2*np.pi*df.day_of_year/365)
df['cos_day_of_year'] = np.cos(2*np.pi*df.day_of_year/365)


# ### Notes about dates in our data
# Start date = earliest 1/1/2013, flexible
# 
# Can use all of 2017 through September 8 as test set
# 
# For cross-validation, randomly assigned
# 
# Whatever % we use for train/test we should use for CV
# 
# Put date into index and use loc to do train test split
# 
# 
# * Split into Xtrain, Xtest, ytrain, ytest based on date
#   * Training dates = 2013-01-01 to 2016-12-31
#   * Test dates = 2017-01-01 to 2017-09-08
#   * New data (coincides with beginning of dockless pilot) = 2017-09-09 to present

# In[6]:

# Train test split
train = df.loc['2013-01-01':'2016-12-31']
test = df.loc['2017-01-01':'2017-09-08']
print(train.shape, test.shape)
tr = train.shape[0]
te = test.shape[0]
trpct = tr/(tr+te)
tepct = te/(tr+te)
print("{:0.3f} percent of the data is in the training set and {:0.3f} percent is in the test set".format(trpct, tepct))


# In[7]:

# Specify columns to keep and drop for X and y
drop_cols = ['date', 'day_of_year']
y_cols = ['cabi_trips_wdc_to_wdc', 'cabi_trips_wdc_to_wdc_casual']

feature_cols = [col for col in df.columns if (col not in y_cols) & (col not in drop_cols)]

# Train test split
Xtrain_raw = train[feature_cols]
ytrain = train[y_cols[0]]
Xtest_raw = test[feature_cols]
ytest = test[y_cols[0]]
print(Xtrain_raw.shape, ytrain.shape, Xtest_raw.shape, ytest.shape)


# ### 1. Preprocessing
# 
# We want to use PolynomialFeatures and StandardScaler in a Pipeline, but we only want to scale continuous features.
# 
# We can do this by using FeatureUnion.
# 
# Here, I do the polynomial transformation first and then feed it through a pipeline because I wasn't able to get it all working in one pipeline.
# 
# * Use PolynomialFeatures to create quadratic and interaction terms
# * Create pipeline for selectively scaling certain variables
# * Fit and transform using pipeline to get final Xtrain and Xtest

# In[8]:

# Imports and custom classes
from sklearn.pipeline import Pipeline, FeatureUnion, make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler, MinMaxScaler
from sklearn.base import BaseEstimator, TransformerMixin

class Columns(BaseEstimator, TransformerMixin):
    ''' This is a custom transformer for splitting the data into subsets for FeatureUnion.
    '''
    def __init__(self, names=None):
        self.names = names

    def fit(self, X, y=None, **fit_params):
        return self

    def transform(self, X):
        return X[self.names]
    
class CustomPoly(BaseEstimator, TransformerMixin):
    ''' This is a custom transformer for making sure PolynomialFeatures
    outputs a labeled df instead of an array. It doesn't work as is, but
    I'm keeping the code here if we need it later.
    '''
    def __init__(self):
        self.pf = None
    
    def fit(self, X, y=None):
        self.pf = PolynomialFeatures(2, include_bias=False).fit(X)
        return self
    
    def transform(self, X):
        Xpf = self.pf.transform(X)
        colnames = self.pf.get_feature_names(X.columns)
        Xpoly = pd.DataFrame(Xpf, columns=colnames)
        return Xpoly


# In[9]:

# PolynomialFeatures
# Should ultimately be part of a Pipeline, but I had issues because my custom Columns class takes a df
# CustomPoly above is an attempt to output a df
pf = PolynomialFeatures(2, include_bias=False)
Xtrain_pf_array = pf.fit_transform(Xtrain_raw)
Xtest_pf_array = pf.transform(Xtest_raw)

# Get feature names 
Xtrain_cols = pf.get_feature_names(Xtrain_raw.columns)

# Output two DataFrames with the new poly columns
Xtrain_pf = pd.DataFrame(Xtrain_pf_array, columns=Xtrain_cols)
Xtest_pf = pd.DataFrame(Xtest_pf_array, columns=Xtrain_cols)

print(Xtrain_pf.shape, Xtest_pf.shape)


# In[10]:

# A lot of these variables are redundant, especially squared dummy variables
# All of these variables listed next are 'binary' but only a few are meaningful
# For now, let's just remove the squared terms
bin_vars = [col for col in Xtrain_pf.columns if Xtrain_pf[col].nunique() == 2]
bin_vars


# In[11]:

# Dropping squared dummies.
# Can expand to include things we deem not useful
# This part (or the initial SQL pull) can be expanded. There's a lot of noise after PF.
to_drop = ['rain^2', 'snow^2', 'us_holiday^2', 'nats_single^2', 'nats_double^2', 'dc_bike_event^2', 'cabi_dur_empty_ffx^2']

Xtrain_pf2 = Xtrain_pf.drop(labels=to_drop, axis=1)
Xtest_pf2 = Xtest_pf.drop(labels=to_drop, axis=1)

print(Xtrain_pf2.shape, Xtest_pf2.shape)


# In[12]:

# Defining binary and continuous variables
# We have normal 0,1 binary variables, binary variables outside 0,1 that were created by PF, and continuous variables
# We want to ignore the 0,1s, MinMaxScale the non 0,1 binary variables, and StandardScale the continuous variables
binary = ['rain', 'snow', 'us_holiday', 'nats_single', 'nats_double', 'dc_bike_event']
binarypf = [col for col in Xtrain_pf2.columns if (Xtrain_pf2[col].nunique() == 2) & (col not in binary)]
cont = [col for col in Xtrain_pf2.columns if (col not in binary) & (col not in binarypf)]

# FeatureUnion in our pipeline shifts the ordering of the variables so we need to save the ordering here
cols = binary + binarypf + cont

pipeline = Pipeline([
    ('features', FeatureUnion([
        ('binary', Pipeline([
            ('bincols', Columns(names=binary))
        ])),
        ('binarypf', Pipeline([
            ('binpfcols', Columns(names=binarypf)),
            ('minmax', MinMaxScaler())
        ])),
        ('continuous', Pipeline([
            ('contcols', Columns(names=cont)),
            ('scaler', StandardScaler())
        ]))
    ]))   
])


# In[13]:

# Fit and transform to create our final Xtrain and Xtest

pipeline.fit(Xtrain_pf2)
Xtrain_scaled = pipeline.transform(Xtrain_pf2)
Xtest_scaled = pipeline.transform(Xtest_pf2)

Xtrain = pd.DataFrame(Xtrain_scaled, columns=cols)
Xtest = pd.DataFrame(Xtest_scaled, columns=cols)
print(Xtrain.shape, Xtest.shape)


# In[14]:

# Note a ton of extra, probably useless variables

Xtrain.describe(percentiles=[.5]).round(3).transpose()


# ### 2. Model Fitting

# In[15]:

from sklearn.metrics import mean_squared_error as mse
from sklearn.metrics import mean_absolute_error as mae
from sklearn.metrics import median_absolute_error as medae
from sklearn.metrics import explained_variance_score as evs
from sklearn.metrics import r2_score


# In[16]:

def score_model(model, alpha=False):
    ''' 
    This function fits a model using the training set, predicts using the test set, and then calculates 
    and reports goodness of fit metrics and alpha if specified and available.
    
    All of the model parameters are also reported, which I find extremely useful.
    
    I wanted to include all of the available regression metrics to see how they compare and comove.
    I ran into an ValueError when trying to include MSLE (mean squared log error). 
    Could be related to ln0 being undefined?
    '''
    model.fit(Xtrain, ytrain)
    yhat = model.predict(Xtest)
    r2 = r2_score(ytest, yhat)
    me = mse(ytest, yhat)
    ae = mae(ytest, yhat)
    mede = medae(ytest, yhat)
    ev = evs(ytest, yhat)
    
    if alpha == True:
        print("Results from {}: \nr2={:0.3f} \nMSE={:0.3f}               \nMAE={:0.3f} \nMEDAE={:0.3f} \nEVS={:0.3f} \nalpha={:0.3f}".format(model, r2, me, 
                                                                                  ae, mede, ev, model.alpha_))
    else:
        print("Results from {}: \nr2={:0.3f} \nMSE={:0.3f}               \nMAE={:0.3f} \nMEDAE={:0.3f} \nEVS={:0.3f}".format(model, r2, me, ae, mede, ev))


# In[17]:

'''Elastic Net'''
from sklearn.linear_model import ElasticNetCV

# Alphas to search over
alphas = np.logspace(-3, 2, 100)

# Suggested l1_ratio from docs
l1_ratio = [.1, .5, .7, .9, .95, .99, 1]

en = ElasticNetCV(l1_ratio=l1_ratio, alphas=alphas, fit_intercept=True, normalize=False)

score_model(en, alpha=True)
print("L1 ratio=",en.l1_ratio_)


# In[18]:

'''Lasso'''
from sklearn.linear_model import LassoCV

lasso = LassoCV(alphas=alphas, fit_intercept=True, normalize=False)
score_model(lasso, alpha=True)


# In[19]:

'''Ridge'''
from sklearn.linear_model import RidgeCV

rr = RidgeCV(alphas=alphas, fit_intercept=True, normalize=False)

score_model(rr, alpha=True)


# In[20]:

'''RF'''
from sklearn.ensemble import RandomForestRegressor

rf = RandomForestRegressor() 
score_model(rf)

