# DC-Bikeshare
Cohort 11 Capstone Project for the Certificate of Data Science at Georgetown University School of Continuing Studies.
_Sebastian Bautista, Travis Gervais, Noah Newberger, and Mark Sussman_

## README Contents
1. [Abstract](#abstract)
1. [NDA Explanation](#nda-explanation)
1. [Background Information](#background-information)
1. [Data Sourcing](#data-sourcing)
1. [Data Architecture](#data-architecture)
1. [Capital Bikeshare Exploration](#capital-bikeshare-exploration)
1. [Machine Learning](#machine-learning)
1. [Acknowledgements](#acknowledgements)
1. [References](#references)

## Abstract

In September 2017, the DC Department of Transportation began a dockless bikeshare pilot program. The pilot program allowed 6 different dockless bikeshare operators to enter the DC market and begin offering their services, effectively putting them in direct competition with the 7.5 year old Capital Bikeshare system. Our project seeks to analyze the dockless pilot program to determine if the introduction of dockless bikes has impacted the demand among users for Capital Bikeshare (CaBI). We accomplish this analysis by gathering data on CaBi, the dockless bikeshare operators and external factors that we believe impact the DC bikeshare demand. Using historical data on Capital Bikeshare and the external factors we create two machine learning models using Lasso and Random Forest to predict the number of Capital Bikeshare rides that we would expect to see during the first eight months of the dockless pilot program. Then we compare our models' predicted values to the actual number of rides that occurred during the pilot program to determine if our models realistically estimated the impact that the dockless bikeshare pilot program has had an impact on Capital Bikeshare.

## NDA Explanation

Please note that in order to receive data shared with the DC Department of Transportation (DDOT) by the dockless operators participating in the dockless pilot, we as a Capstone Project team, had to sign a non-disclosure agreement with DDOT.  We have presented our finding to DDOT and agreed not to share any dockless specific analysis only in our report and presentation that can only be shared with Georgetown Data Science faculty and students and not for wider distribution.

The remainder of this README will walk through our finding that were Capital Bikeshare (CaBi) specific (i.e. stopping at our machine learning models, just before explaining the potential impact of the dockless bikeshare impact on CaBi)

## Background Information

In September 2010,  Capital Bikeshare (CaBi) began operating in the Washington, DC region with 1,100 bikes and 114 stations in Washington, DC and Arlington, VA (Motivate International, Inc, 2017). Since then CaBi has grown to approximately 437 stations and 4,500 bikes. It has expanded its coverage to include, Alexandria, VA, Montgomery County, MD, and Fairfax County, VA. The system, which sees an average of over 10,000 trips per day, has grown to be the third largest bikeshare system currently operating in the United States. 

In September 2017, the DC department of Transportation (DDOT) began a pilot program in Washington, DC which allowed for five dockless bikeshare companies to begin operating in the city (Sturdivant, 2017). Dockless bikeshare bikes differ notably from CaBi in that the bikes do not need to be taken from or returned to physical docking stations. Instead, the dockless bikes can be left anywhere in the city as long as they are on public property and they are not obstructing roadways or pedestrian walkways. The lack of infrastructural prerequisites meant that seemingly overnight several fleets of brightly colored bikes appeared on the streets. Under regulations established by DDOT for the dockless bikeshare pilot program, each operator is permitted to have a maximum of 400 vehicles on the street at any given time (Ryan, 2017). For the first several months of the pilot program, vehicle was synonymous with bike until electric scooters were introduced in March and Lime reduced the number of bikes in their fleet in order to increase the number of scooters (Seher, 2018).  The pilot program presented a unique opportunity to study the effect that the introduction of a new mode of might have on the demand for a well-established bikeshare system. In this paper we use machine learning to predict the demand for CaBi through the duration of the pilot program, and by comparing the predicted demand with the actual demand, we attempt to determine to what extent the dockless bikeshare operators have been able to disrupt the status quo. 

## Data Sourcing

The data that was gathered for this project fell into one of three categories: 

1. CaBi Data - Publicly available [system data](https://s3.amazonaws.com/capitalbikeshare-data/index.html) and [API](https://gbfs.capitalbikeshare.com/gbfs/gbfs.json)

2. Dockless Bikeshare Data - Data provided by DDOT and API
3. Misc Data - Data on a variety of factors, such as weather and population, that we believe would have an impact on the demand for bikeshares in Washington, DC. 

Most of the data that was used for this project is publicly available data which we either downloaded, scraped or used an API to pull down from a website. Exceptionally, we received dockless trip data from DDOT and dockless bikes available data from [Daniel Schep](https://schep.me/) who had already put together a site to track all the bikeshare systems in DC.  He was kind enough to share his stored API data with us so that we could actually analyze dockless bikeshare utilization rates, as the data we received from the operators was not reliable.  As we began sourcing our data, we set up a meeting with DDOT to explain to them the goals and scope of our project and offer our assistance to help analyze the efficacy of the pilot program.  DDOT  agreed to share the data that they had with us on the condition that we share our findings with them at the end of our analysis and we sign a nondisclosure agreement agreeing not to divulge any of the dockless data to the general public.

Under the rules of the pilot program, the dockless bikeshare operators are required to self-report data on a monthly basis to DDOT. The monthly reports include data on trip start and stop times, trip start and stop locations, and user id among other fields. The CSVs that we received required a significant amount of processing. For example, not every operator reported latitude and longitude trips starts/ends to the enough precision to determine actual location, which impacted our ability to compare trip locations across operators.  There were also inconsistencies with the start and end times for trips in the data that the dockless operators were self-reporting. In one extreme case it was discovered that the hours were missing from the timestamps for all trips for a particular operator. In another case, there were instances where the reported end time occurred before the reported start time which resulted in calculations for negative trip durations. 
Table descriptions and data dictionaries of all the data sources we used as can be found in our Github repo’s [data dictionary](https://github.com/georgetown-analytics/DC-Bikeshare/blob/master/DICTIONARY.md).


## Data Architecture

Diagram 1 shows the relationship of all CaBi related data.  Our main CaBi dataset, a series of publically available CSVs stored in an AWS S3 store provide start and end timstamps, start and end station ids, bike ids and trip type (member vs casual) for all 20 million trips taken since CaBi's inception.

In order to enhance the CaBi trip data, we leverage the CaBi API, specifically the system and station information.  In order to assign a CaBi Region (ie DC, Arlington, Alexandria) to each trip start and end, we joined the region_id from the system information to the foreign key region_id on the station information and then joined to the trip start and end based on station_id.  Having region_id at the trip start and end level, allowed us to break out trip counts by region combination and ultimtely limit our trip population to trips taken within DC as the point of comparison to dockless trips which bounded within DC.

CaBI Station Outage data scraped from [cabi tracker](http://cabitracker.com) by automatically downloading csv reports from every day since April 2011, providing the duration for each instance a station was either empty or full.

DDOT provided us with CaBi memberships (Annual, Monthly and Day Key) purchased per month going back to September 2010.  This data allowed us to estimate active memberships by assuming annual members are activate for the 11 months after membership purchase, while monthly memberships are only active for the month of purchase.  Day Key members were assumed to activate from the month of purchase in perpetuity.  The overwhelming majority of CaBi members are annual members.

**Diagram 1:** Capital Bikeshare Data Flow
![alt text](./readme_images/Data_Architecture_CaBiData.png "")

Diagram 2 shows the relationship of all dockless pilot related data.  The dockless trip data came in CSVs directly from DDOT and is similar to the CaBi Trip data, exchanging station information for start and end geo-coordinates 

CaBi station information is used here to determine closest CaBi Station that we used in some of our exploratory analysis.  We also used 
CaBi station outage data to determine if closest CaBi station had bikes when dockless trip started, but this analysis ended up not being material. 

We also compiled the pricing schemes for each dockless operator to calculate trip cost, but we didn't ended up not leveraging this data since start and end timestamps where suspect or non-existant, especially for Mobike.

Dockless bikes available on a daily basis comes from API for Jump, Spin and Lime, as Ofo and Mobike APIs not reliable (thanks again Daniel!).  We used to analyze utilization rates as compared to CaBi's rates.

**Diagram 2:** Dockless Bikeshare Data Flow
![alt text](./readme_images/Data_Architecture_DocklessData.png "")

Diagram 3 shows are secondary data sources.  Weather data is by far our most important secondary data source, which came from the [Dark Sky API](https://darksky.net/dev/docs)  The attributes shown below are just the most important of the many attributes available in the API.

WABA Bike Events was compiled using the Google Calendar API to pull all events from 2014 to present from Washington Area Bike Association [public calendar](http://www.waba.org/events/calendar/).  We then used domain knowledge to select those events to keep as significant.

[Open Data DC](http://opendata.dc.gov/datasets) has lots of great GIS data for DC.  We used the Advisory Neighborhood Commission GeoJSON to assign each dockless trip an ANC.  This geographic categorization was then leveraged to determine concentration of trips used
primarily for maps generated at the request of DDOT.  These maps are available in the appendix of our report.

We scraped the Washington Nationals 2010-2018 schedule and attendance data from [Baseball Reference](https://www.baseball-reference.com/teams/WSN/)

DC population data came from the DC Office of Planning and the American Community Survey.

**Diagram 3:** Secondary Data Flow
![alt text](./readme_images/Data_Architecture_SecondaryData.png "")


Diagram 4 shows how we brought all our data sources toget together into a AWS PostgreSQL database instance.  We used the [psycopg2](http://initd.org/psycopg/docs/) Python package to load all tables to our database.  The final database to be used for machine learning  generated by combining all these sources together and was feed into our machine learning pipeline so that we could predict daily CaBi demand for DC to DC rides for the dockless pilot period.

**Diagram 4:** Data Science
![alt text](./readme_images/Data_Architecture_DataFlowDiagram2.png "")

## Capital Bikeshare Exploration

We began our exploratory analysis by looking at the growth in the CaBi daily trips for from 2011 through 2017. Our goal was to determine the best time frame for our machine learning analysis by identifying when CaBi became well established in Washington, DC. Figure 1 shows that the number of trips per day increased fairly rapidly during the first four years of operation. During that time, approximately 222 new docking stations were added to the system. Beginning in 2014, the average number of trips taken each day has increased a slower rate, suggesting that the rapid expansion of the earlier years has ended as CaBi has become a fixture within DC’s public transportation system.

**Figure 1:** Average daily CaBi Trips by Year (Left: System Wide, Right: DC to DC trips)
![alt text](./readme_images/Capital_Bikeshare_Exploration_DailyCabiTrips.png "")

We also wanted to determine if behavior differed between the two user categories, member and casual. Members are defined as CaBi users that have purchased either an annual or monthly membership. Casual users are defined as users that have purchased a three-day, 24-hour pass or single trip pass (starting in June 2016). We examined the behavior of these two user types by plotting the bike utilization rate for members and casual users by year, month and day of the week in order to determine if there were significant differences in the usage patterns between these two groups. The bike utilization rate is defined as:

![img](http://latex.codecogs.com/svg.latex?%5Cfrac%7BtotalTrips%7D%7BtotalAvailableBikes%7D)

In Figure 2, we examine the average bike utilization rate by year by creating one subplot which shows the bike utilization rate for members and another subplot for the bike utilization rate of casual riders. In 2011, CaBi members accounted for a little under 2.5 rides per day for each active bike. That number grew to around 2.6 rides per day in 2012 before it slowly started declining to a little over 1.5 in 2017. What this shows is that by 2011 there was already a strong demand among members when CaBi had a relatively small fleet. CaBi has added bikes to their fleet over the years at a rate which has outpaced the growth in rides per day by CaBi members. The bike utilization rate for casual users has remained fairly constant since 2011. The third subplot in Figure 2 shows that from 2011 until 2016 around 80% of CaBi’s usage is coming from members. This percentage begins to dip in 2016 and 2017; one possible explanation being that CaBi introduced $2 single trip 30 minute rides in [June 2016](https://ggwash.org/view/41888/2-will-now-buy-you-a-capital-bikeshare-trip). This makes it easier for casual users to use CaBi, as they no longer need to purchase a 24-hour or 3 day pass.

**Figure 2:** Bike Utilization Rate for CaBi by Year

![alt text](./readme_images/Capital_Bikeshare_Exploration_Utilization_YearCasvsMem.png "")

Figure 3 shows the bike utilization rate by month for the two user types. The subplots clearly demonstrate the seasonality of usage for both members and casual users. For both user types, the utilization rate of the bikes is depressed during the colder winter months and peaks in the warmer summer months. However, the drop off in the utilization rate during the winter months for casual users is more substantial than it is for members. Members account for around 90% of trips during the months of December, January, and February, as seen in the third subplot of figure 3. However, that rate falls to a little over 75% in the summer months once the usage among casual riders begins to increase, starting around March. It’s important to note that our analysis of the dockless pilot program does not include the summer months since it began in September and has only been running for the past 9.5 months.

**Figure 3:** Bike Utilization Rate for CaBi by Month
![alt text](./readme_images/Capital_Bikeshare_Exploration_Utilization_MonthCasvsMem.png "")

Figure 4 shows the bike utilization rate for members and casual users by day of the week. The subplots show that there is a difference in the usage patterns of members and casual users. For members the bike utilization rate is highest on weekdays and lower on the weekends, suggesting that CaBi members may be using the bikes to commute to and from work. For casual users, the bike utilization rate peaks on the weekends and is significantly lower during the week. It is possible that some of the casual users are people coming to DC for tourism and purchasing one of the passes that CaBi offers or DC residents engage in non-habitual usage in their leisure time. The third subplot shows that trips taken by CaBi members account for about 85% of bike usage during the work week, while during the weekend that rate drops to less than 70%. Figures 3 and 4 suggest that usage patterns differ in a significant way between members and casual users.

**Figure 4**: CaBi Bike Utilization Rate by Day of Week
![alt text](./readme_images/Capital_Bikeshare_Exploration_Utilization_DOWCasvsMem.png "")

## Machine Learning

For our analysis, we use two competing machine learning models. In our models an instance is a single day and our goal is to predict the number of CaBi trips that start in DC and end in DC, taken on each day of the pilot program from September 9, 2017 to April 30, 2018. We only included DC to DC trips in our model because the pilot program restricts the dockless bikeshare operators to operate within the District of Columbia. We were able to determine the region where trips started and ended by using data that we collected from the CaBi API.  The time frame of our training data is limited to the period of time from January 1, 2013 to September 8, 2017. We started the training set in 2013 because of the rapid growth during the first two years of operation as shown in Figure 1, as well as data availability issues from the same time period.

#### Lasso

We identified 18 features that we believed would be important to incorporate into our model. These features included daylight hours, apparent high temperature, U.S. holidays, and Washington Nationals games. We decided to use a smaller feature set with the Lasso model in order to minimize the chances of including collinear variables as features in our model. Multicollinearity among explanatory features in a linear model can have detrimental effects on coefficient estimates. We also dropped some features because of leakage issues - for example, some of our features are related to the duration that CaBi stations are empty or full in each day. Although these features are extremely predictive of CaBi trips, trips and empty duration are simultaneously co-determined, so we drop these features because of endogeneity issues.

Next, we preprocessed the data. In order to incorporate data from multiple years into our model, we performed cyclical encoding on the day of year to ensure continuity between December and January. Figure 5 shows a ranking of feature importance for the 18 features that were selected for the lasso model when we ran it initially, without including any polynomial variables or interaction terms in the model. We did not achieve a good fit due to the model’s simplicity, however because of this simplicity it is easier to identify the explanatory power of each variable. For example, apparent high temperature had the strongest positive effect on the number of CaBi trips while whether or not the day was a US holiday had the strongest negative effect. Intuitively, this makes sense that as temperature rises so do the number of CaBi trips. It also seems intuitive that the CaBi system would see fewer rides on US holidays due to the absence of commuters.

**Figure 5**: Pearson Ranking of 18 Features Incorporated into Lasso Model
![alt text](./readme_images/Machine_Learning_lasso_rank2d.png "")

We used the Rank2D visualizer from the Yellowbrick package in order to visualize which of our 18 features had the strongest correlation. Not surprisingly, variables like daylight and apparent high temperature were positively correlated. Figure 6 shows a simplified Pearson ranking of the 18 features that were selected for the lasso model before applying PolynomialFeatures. It does not show all of the 180 features that were used in our final model after creating the interaction terms and polynomial features.  

**Figure 6**: Feature Importance of 18 Features Selected for Lasso Model
![alt text](./readme_images/Machine_Learning_lasso_featureimportances18.png "")

In order to improve the fit of our Lasso model, we had to increase its complexity. This was achieved by using PolynomialFeatures to create quadratic and interaction terms that we could incorporate into our model to introduce complexity by increasing the number of features in our model to 180. We initially tried using PolynomialFeatures of orders 2 and 3, but ultimately found that PolynomialFeatures(2) was most performant.   Creating interaction terms for our analysis was an important step because we believed that combinations of certain variables could have different impacts on CaBi demand, and these terms allow for a more complex linear relationship between our features and target variable.  For example, behavior might differ between a cold day with rain and a warm day with rain. We dropped any quadratic variables that were redundant such as those created from our binary features, e.g. U.S. holiday squared. We also standardized our continuous variables by passing them through StandardScaler so that they would all have a mean of 0 and standard deviation of 1. For our binary features, we used MinMaxScaler to ensure that if any changes were made to those features when we applied PolynomialFeatures to them, they would be returned to 0 and 1. 

In order to fit our model, we used 5-fold cross-validation and an alpha search space of 250 logarithmically spaced points between .01 and 10.  The highest performance we got from the lasso model had an alpha of approximately 4.6 and a mean R<sup>2</sup> value of 0.852 with a standard deviation of 0.0175. The model tended to over-predict the number of CaBi rides taken per day which is evidenced by the sum of the residuals being negative. Table 1 shows a ranking of feature importance for the top 10 features out of the 75 that were selected for the lasso model. The interpretation of these feature interactions is difficult due to the increased complexity of the model. However, there is cross-over between several of the features that were identified as important in our simplified model and features that were incorporated into the more complicated Lasso model, suggesting that these may be important. Features such as apparent high temperature, population, humidity and precipitation probability appear on both lists.

**Table 1**: Importance of Top 10 Features and Interaction Terms 

Feature Interaction |0 | Sorted 
--- | ---: | ---:
apparenttemperaturehigh - dc_pop | 2,400 | 2,400
dc_pop- cos_day_of_year | -2,266 | 2,266
daylight_hours - cos_day_of_year | 1,422 | 1,422
visibility - cos_day_of_year | -1,254 | 1,254
apparenttemperaturehigh - sin_day_of_year | 1,252 | 1,252
apparenttemperaturehigh^2 | 1,242 | 1,242
apparenttemperaturehigh - cos_day_of_year | 1,121 | 1,121
humidity - precipprobability | 1,003 | 1,003
visibility - sin_day_of_year | -732  |  732
precipprobability - visibility | 588 | 588



#### Random Forest

We wanted to experiment with a nonlinear regression method since we had already employed a linear regression model by using Lasso. Random forest, which uses bagging, seemed like a better option than using a boosting algorithm which could have potentially resulted in overfitting.  Additionally, random forest had the added bonus of not being negatively affected by multicollinearity among features like Lasso is. This enabled us to incorporate a larger set of 49 features into the model. We also did not need to do any preprocessing in terms of scaling or creating polynomial features to deal with interaction terms because of how decision trees consider features sequentially. Figure 7 shows the features ranked by importance, which basically means these features were used to create partitions. The five most important features for this model were apparent high temperature, number of active monthly CaBi users, apparent low temperature, the day of the year, and the sunset time. Note that these feature importances are less informative than those returned by Lasso since they don’t tell us anything about the direction of the effect, just relative magnitude.

**Figure 7**: Feature Importance of 49 Features Selected for Random Forest Model
![alt text](./readme_images/Machine_Learning_rf_featureimportances.png "")

In order to tune our hyperparameters for this model, we used RandomizedSearchCV to identify which hyperparameters to tune. There were 5,760 unique combinations of hyperparameters possible through the randomized search, and we tried 100 iterations over 5 folds. After confirming that this new model performed better than the untuned model, we used GridSearchCV with a smaller set of hyperparameters to then select the most performant combination. After performing 5-fold shuffled cross-validation we achieved a mean R<sup>2</sup> value of 0.902 with a standard deviation of 0.007. This model also tended to overpredict the number of CaBi rides. 

#### Results

Figure 8 plots the predicted values and the actual values for the number of CaBi rides for every date of the pilot program from September 9, 2017 to April 30, 2018. It also plots the prediction error for each day of the pilot program. Our model tended to overpredict the number of rides, as evidenced by the fact that the error term is less than 0 for most of the days within the pilot program. This suggests that the dockless pilot program might have had an impact on the demand for CaBi since there were fewer CaBi trips taken during the dockless period than our model predicted. 

**Figure 8**: Actual vs. Predicted CaBi Rides during Dockless Pilot
![alt text](./readme_images/Machine_Learning_rf_total.png "")


The remainder of our analysis compares our results from our machine learning model to dockless trip data provided by DDOT and therefore we cannot include that analysis here due to NDA restrictions.

## Acknowledgements

We'd like to thank Stefanie Brodie, Kim Lucas, and Jonathan Rodgers at the District Department of Transportation for sharing their dockless pilot and Capital Bikeshare data and domain expertise with us.  We'd also like to thank Daniel Schep for sharing his dockless API data with us.  Without his visionary software engineering, we wouldn't have been able to compare CaBi utilization rates with those of the dockless operators.

## References

Heining, A. (2017, September 22). We tried all four of D.C.'s dockless bike-share systems. Here's our review. Retrieved March/April, 2018, from https://www.washingtonpost.com/news/dr-gridlock/wp/2017/09/22/we-rode-all-four-of-d-c-s-dockless-bike-share-so-you-wouldnt-have-to/?noredirect=on&utm_term=.d8f7131bfc37

Motivate International, Inc. (2017). Press Kit. Retrieved February/March, 2018, from https://www.capitalbikeshare.com/press-kit

Ryan, K. (2013, October 23). How dockless bikes stack up against Capital Bikeshare in DC. Retrieved March/April, 2018, from https://wtop.com/dc/2017/12/dock-less-bikes-stack-capital-bikeshare-dc/slide/1/

Seher, C. (2018, March 13). It's Monumental: LimeBike's Lime-S Electric Scooters Now Available in DC. Retrieved from https://www.limebike.com/blog/its-monumental-limebikes-lime-s-electric-scooters-now-available-in-dc

Sturdivant, C. (2017, September 19). Dockless Bikeshare Program Rolls Out In D.C. On Wednesday. Retrieved from http://dcist.com/2017/09/dockless_bikeshare_dc.php


