import pandas as pd
import numpy as np

def Growing(x,y):
    growth = (x-y)/y
	growth = growth / 12
    return growth

def building_months(city, grow):
	df_dc_month['temp'] = df_dc_month[city] * df_dc_month[grow]
	df_dc_month['temp'] = df_dc_month['temp'].shift(1)
	df_dc_month.loc[df_dc_month[city].isnull(),city] = df_dc_month['temp'] + df_dc_month[city].shift(1)
	print (df_dc_month)
	del df_dc_month['temp']
	
	

### Reading in CSV FROM IPMUS Download
df = pd.read_csv('C:/Users/Noah/Documents/GT Data Science/usa_00005.dat/usa_00007.csv/usa_00007.csv')
### GENERATING Biking as a percentage of overall transportation methods.
### Statecip = 98 is DC and TRANWORK = 40 is BIKING
df_dc_dummies = df[['YEAR','CITYPOP','STATEICP','CITY','TRANWORK']]
temp = pd.get_dummies(df_dc_dummies['TRANWORK'])
df_dc_dummies = pd.concat([df_dc_dummies, temp[40]], axis=1)
df_dc_dummies.rename(columns={40:'BIKING'}, inplace=True)
df_dc_dummies = df_dc_dummies.groupby(['YEAR','STATEICP'])['BIKING'].agg(['sum','count'])
df_dc_dummies['PCT_BIKE'] = df_dc_dummies['sum'] / df_dc_dummies['count']
df_dc_dummies = df_dc_dummies.reset_index()
df_dc_dummies = df_dc_dummies[df_dc_dummies['STATEICP']==98]
### Creating Monthly Population data. for 17/18, start at 1/16 and pull the number forwarder growing. 
### Percentage of bike commuters is the same as the 2016 number. 
df_dc = df[['YEAR','CITYPOP','STATEICP','CITY']]
df_dc = df_dc.drop_duplicates()
df_dc = df_dc[df_dc['STATEICP']==98]
df_dc['t-1']=df_dc['CITYPOP'].shift(1)
df_dc['Grow_Rate'] = Growing(df_dc['CITYPOP'], df_dc['t-1'])
df_dc['months'] = 1
df_dc = pd.merge(df_dc, df_dc_dummies, on=['YEAR'], how='left')
df_dc = df_dc[['YEAR', 'CITYPOP','t-1', 'Grow_Rate', 'months','PCT_BIKE']]
month = np.arange(1,13,1)
df_dc_month = pd.DataFrame([(d, tup.YEAR) for tup in df_dc.itertuples() for d in month], columns=['months', 'YEAR'])
df_dc_month = pd.merge(df_dc_month, df_dc, on=['YEAR','months'], how='left')
slice_1 = df_dc_month[['YEAR','months']][df_dc_month['YEAR'] >= 2015]
slice_1['YEAR'] = slice_1['YEAR'] + 2
df_dc_month = df_dc_month.append(slice_1) 
df_dc_month['Grow_Rate'] = df_dc_month['Grow_Rate'].fillna(method='ffill')
df_dc_month['PCT_BIKE'] = df_dc_month['PCT_BIKE'].fillna(method='ffill')
df_dc_month = df_dc_month.reset_index()

for x in range(11):
	building_months('CITYPOP','Grow_Rate')	
	
df_dc_month['CITYPOP'] = df_dc_month['CITYPOP'].fillna(value=0)

for x in df_dc_month.index:
	if df_dc_month.loc[[x],'CITYPOP'].item()==0:
		df_dc_month['temp'] = df_dc_month['CITYPOP'] * df_dc_month['Grow_Rate']
		df_dc_month['temp'] = df_dc_month['temp'].shift(1)
		df_dc_month.loc[[x],'CITYPOP'] = df_dc_month['temp'] + df_dc_month['CITYPOP'].shift(1)
		del df_dc_month['temp']
		
df_dc_month = df_dc_month[['CITYPOP', 'Grow_Rate', 'PCT_BIKE', 'YEAR', 'months']]
df_dc_month = df_dc_month.dropna(how='any')
#HAVE NOT SAVED OUT A FILE YET
print(df_dc_month)