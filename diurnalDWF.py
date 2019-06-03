'''read in an Excel file contained flowmeter data formatted as:

     BC50             Average=FifteenMinute  QualityFlag=FALSE  QualityValue=FALSE
   DateTime                 MP1\Dfinal            MP1\Vfinal           MP1\QFinal
MM/dd/yyyy HH:mm:ss           in                    ft/s                  MGD
1/1/2018 0:00              #.##                   #.##                 #.##
1/1/2018 0:15              #.##                   #.##                 #.##

and another Excel file containing rain gauge data formated as:

The analysis procedure is as follows:
(a) filter out: (1) rainy days, (2) 2 days before rainy day, (3) 2 days after rainy event, (4) holidays?
(b) separate into weekdays, Monday-Friday, and weekends (SN)
(c) ensemble average the weekday curve and weekend curve
(d) filter out all curves that are more than 2 standard deviations away from mean
(e) recalculate the means
(f) find groundwater infiltration (GWI) as 0.75*min(Q_avgWeekday, Q_avgWeekend)
(g) report the minimum of each curve and the mean of each curve
(h) calculate the sanitary flow (Q_avgWeekdaySanitary = Q_avgWeekday - Q_GWI)
(i) normalize each curve to its mean (Q_weekdayMean, Q_weekendMean)
(j) calculate the hourly values of Q_avgWeekdaySanitary and Q_avgWeekendSanitary

Produce the following files:
(1) diagnostic file containing:
 (a) list of filtered out days and the reason for being filtered
 (b) raw data of unfiltered weekdays
 (c) raw data of unfiltered weekend days
 (d) plots of weekday and weekend raw data (dots) with final ensemble mean shown on top (line)
 (e) data of time, weekday average, weekend average, and ground water infiltration
 (f) data of time, weekday average (min, mean), weekend average (min, mean), GWI, weekday sanitary flow, weekend sanitary flow, normalized weekday, normalized weekend, hour
(2) read file for InfoWorks ICM containing the normalized weekday and weekend values and the GWI

Produce the following plots:
(a) interactive diurnal raw plots with ensemble mean for both weekday and weekend (separate)
(b) weekday, weekend, and gwi time plots
(c) normalized diurnal sanitary plots (weekday, weekend)'''

##import modules
# pandas for data storage, organization, and manipulation:
import pandas as pd
#dates functionality from matplotlib
from matplotlib import dates as d 
#datetime for date and time manipulation
import datetime as dt 
#pyplot for plotting specifically
import matplotlib.pyplot as plt 
#numpy for data manipulation
import numpy as np 

#read in the excel file containing the flow data
#tell pandas what format types to expect to increase speed

filename_flow = "H:" + r"\Big Creek" +r"\Subbasin BC50" +r"\Flowdata" r"\BC50_28660533.xlsx"
sheetname_flow = "BC50_28660533"
index_dateColumn = 0 #column location of dates
#index_flowRate = 3 #column location of
# the date and time column is a Timestamp type; all other columns are numbers
#dateColumnName = "DateTime"
##def readFlowmeters(filename,sheetname,index_dateColumn,index_flowRate)
data_flowmeter = pd.read_excel(filename_flow,sheetname_flow)
#get the name of the date column
dateColumnName = data_flowmeter.columns[index_dateColumn]

#create a writable copy
df = data_flowmeter.copy()
#assign a day of the week to each date; 0 == Monday, 6==Sunday
df['dayofweek']=df[dateColumnName].dt.dayofweek # therefore df['dayofweek']<5 is a weekday, df['dayofweek']>=5 is a weekend
df['date']=pd.to_datetime(df[dateColumnName].dt.date)
df['time']=df[dateColumnName].dt.time
df[dateColumnName]=pd.to_datetime(df[dateColumnName].dt.strftime('%Y/%m/%d %H:%M'))

startDate = df['date'].iloc[0] #WHAT IS THE TYPE OF THIS DATE?
endDate = df['date'].iloc[-1]

df = df.set_index([dateColumnName])

#read in rain data
#tell pandas what format types to expect to increase speed
filename_rain = 'H:'+ r'\Big Creek' r'\Big Creek Rain Gauges dry days.xlsx'
sheetname_rain = 'BCRG04'
index_rain = 1
data_rain = pd.read_excel(filename_rain,sheetname_rain)
dfR = data_rain.copy()

#DEFINE DATE SLICER FUNCTION
dateMask = (dfR['Date']>=startDate) & (dfR['Date']<=endDate)
dfR = dfR.loc[dateMask]
#FOR TESTING ONLY, ADD A RAINY DAY TO THIS DATA!! REMOVE THIS LINE BELOW!! 
##dfR[dfR.columns[1]][3]=1

#find rainy days and assign to a new column
dfR["Rain Bool"] = dfR["Rain Total"]>0
rainDates = dfR.loc[dfR["Rain Total"]>0,'Date']#this is a series
#further filter out days based on proximity to rain
rainFiltered = rainDates.copy()
#filter out 2 days before rain
beforeDates = rainFiltered - dt.timedelta(days=2)
#filter out 2 days after rain
afterDates = rainFiltered + dt.timedelta(days=3)#EPA recommends 3 days
#assign to new dataframe
df_rainDates = pd.DataFrame({'Before': beforeDates, 'After': afterDates})

#check that the rain dates are within the specified range
if beforeDates.iloc[0]<startDate:
  df_rainDates.iloc[0,0]=startDate
elif afterDates.iloc[-1]>endDate:
  df_rainDates.iloc[-1,1]=endDate

#creates a tuple of the before date and the after date of a rain event
#df_rainDates['Wet Range']=list(zip(df_rainDates["Before"].dt.date,df_rainDates["After"].dt.date))
df_rainDates = df_rainDates.set_index(rainFiltered) # sets the actual rain day as the index

df["Weather"] = "Dry" #initially assume everything is dry
#assign a weather column in the flow meter data to say whether the day is considered "Dry"
for j in range(0,len(df_rainDates.index)):
  rainMask = (df['date']>=df_rainDates.iloc[j,0]) & (df['date']<=df_rainDates.iloc[j,1])
  df.loc[rainMask,"Weather"]="Rain Event"
#ensemble mean the dry weather diurnals
# use to_numeric() when you've selected what you want (e.g., dry weekdays)

#calculate standard deviations for each average location