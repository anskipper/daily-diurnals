# imports
from diurnal import dryWeather as dw
from diurnal import findRainEvents as fre
import datetime as dt 
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

#set file locations
flowDir = 'P:\\PW-WATER SERVICES\\TECHNICAL SERVICES\\Anna'
rainFile = flowDir + '\\RG_daily_20180101-20190331.txt'
gageFile = flowDir + '\\FMtoRG.txt'

# set variables
rainthresh = 0.1 #in
bufferBefore = 1 #days (pre-comp)
bufferAfter = 2 #days (Recovery 1 & 2)

# plotting
colorWkd = 'xkcd:leaf green'
colorWke = 'xkcd:hunter green'
colorMean = 'xkcd:light purple'
colorRain = 'xkcd:dark sky blue'
gridColor = 'xkcd:grey'

# for testing
fmname = 'BC01A'
t = 'BC01A_28660533.txt'
flowFile = flowDir + "\\" + t

#functions
def readRaintxt(filename,useColList):
    df = pd.read_csv(filename,sep='\t',usecols=useColList,index_col=0)
    df.index = pd.to_datetime(df.index)
    return(df)
# FOR EVERY FLOWMETER:
# read in flow data
df_flow = dw.readSliicer(flowFile)
#read in rain data (daily)
# which gage corresponds to this flowmeter?
gageName = dw.findRainGage(filename=gageFile,fmName = fmname)
# read in the rain data as a dataframe with dates for indices
df_dailyrain = dw.readRaintxt(filename=rainFile,useColList=['Date',gageName])
# find the overlapping dates between the rain data and the flow data
startDate, endDate = dw.defineDateRange(df_flow,df_dailyrain)
# chop up the flow and rain dates so that they match the overlapping dates
df_flow = df_flow.loc[startDate:endDate,:]
df_dailyrain = df_dailyrain.loc[startDate:endDate,:]

# read in the 15 min date data file
rainFile15min = flowDir + '\\RG_15min_20180101-20190331.txt'
df_rain = dw.readRaintxt(filename=rainFile15min,useColList=['Datetime',gageName])

# find the dates on which there was rain; return a data frame that has the rain dates as indices, the before date (dependent on bufferBefore), and the after date (dependent on the bufferAfter)
df_rainDates = fre.findRainEvents(dfDaily=df_dailyrain,df15min=df_rain,rainthresh=rainthresh,bufferBefore=bufferBefore,bufferAfter=bufferAfter,gageName=gageName)

testDate = df_rainDates.index[0]

# add day of week column to daily rain totals
df_dailyrain['dayofweek'] = df_dailyrain.index.dayofweek

meanFile = flowDir+ '\\' + fmname + '\\' + fmname + '_meanFlows.csv'

def readTotalFlow(filename):
    df= pd.read_csv(filename,index_col=0)
    df.index = pd.to_datetime(df.index)
    df.index = df.index.time
    return(df)

df_means = readTotalFlow(filename=meanFile)

def getTimeDiff(date1,date2):
    date1 = pd.to_datetime(date1)
    date2 = pd.to_datetime(date2)
    if date2 >= date1:
        dateDiff = date2 - date1
    else:
        dateDiff = date1 - date2
    # convert to days and seconds
    days, seconds = dateDiff.days, dateDiff.seconds
    # covert to total hours and total minutes
    hours = days * 24 + seconds // 3600
    minutes = (seconds % 3600) // 60
    return(days,hours,minutes,seconds)

def constructMeanFlow(df_dailyrain,df_rainDates,df_means,stormNum):
    # find the days corresponding to the storm
    beforeDate = pd.to_datetime(df_rainDates.iloc[stormNum,0]).date()
    startTime = pd.to_datetime(df_rainDates.iloc[stormNum,0]).time()
    afterDate = pd.to_datetime(df_rainDates.iloc[stormNum,1]).date()
    endTime = pd.to_datetime(df_rainDates.iloc[stormNum,1]).time()
    weekdayVals = df_dailyrain.loc[beforeDate:afterDate,'dayofweek']
    # construct the mean flow
    meanFlow = []
    dateTimes = []
    color = []
    for k in range(0,len(weekdayVals)):
        #check to see whether weekday or weekend
        if weekdayVals[k]>4:
            col = 'Weekend'
            colorVal = colorWke
        else:
            col = 'Weekday'
            colorVal = colorWkd
        # if it's the before date
        if k==0:
            meanFlow.extend(df_means.loc[startTime:,col])
            color.extend([colorVal])
        # if it's the after date
        elif k==len(weekdayVals)-1:
            meanFlow.extend(df_means.loc[:endTime,col])
            color.extend([colorVal])
        # otherwise
        else:
            meanFlow.extend(df_means.loc[:,col])
            color.extend([colorVal])
    #construct datetime for plotting
    # find the difference between the start and end dates
    days,hours,minutes,seconds = getTimeDiff(df_rainDates.iloc[stormNum,1],df_rainDates.iloc[stormNum,0])
    numPeriods = hours*60/15 + minutes/15 +1 #60 hrs/mint * 1 meas/15min
    dateTimes = pd.date_range(df_rainDates.iloc[stormNum,0],periods=numPeriods,freq='15min')
    df = pd.DataFrame(data=meanFlow,index=dateTimes,columns=['Mean Flow'])
    df.index = pd.to_datetime(df.index)
    return(df,color)

# for each storm: for j in range(0,len(df_rainDates.index))
#set day of week
plot = True
#plot for now
colorWkd = 'xkcd:leaf green'
olorWke = 'xkcd:hunter green'
colorMean = 'xkcd:light purple'
colorRain = 'xkcd:dark sky blue'
gridColor = 'xkcd:grey'

integrate = True
measInc = 15/24/60.0 #as days
iTotal = []
grossvol = []

#trapezoid integration, but only positive values
def abstrapz(y,x=None,dx=1.0):
    y = np.asanyarray(y)
    if x is None:
        d = dx
    else:
        x = np.asanyarray(x)
        d = np.diff(x)
    ret = (d * (y[1:] +y[:-1]) / 2.0)
    return ret[ret>0].sum()  #The important line

for stormNum in range(0,len(df_rainDates.index)):
    # read in the instantaneous flow and instantaneous rain
    s_flow = df_flow.loc[df_rainDates.iloc[stormNum,0]:df_rainDates.iloc[stormNum,1],'Q (MGD)']
    s_rain = df_rain.loc[df_rainDates.iloc[stormNum,0]:df_rainDates.iloc[stormNum,1],gageName]
    s_rain.index = s_flow.index
    # get the time difference between the before and after dates
    days,hours,minutes,seconds = getTimeDiff(df_rainDates.iloc[stormNum,1],df_rainDates.iloc[stormNum,0])

    stormDate = pd.to_datetime(pd.to_datetime(df_rainDates.index[stormNum]).date())
    # construct mean flow for rain event dates
    dfMeanFlow, color = constructMeanFlow(df_dailyrain = df_dailyrain,df_rainDates=df_rainDates,df_means=df_means,stormNum=stormNum)
    
    if plot:
        fig,ax= plt.subplots()
        s_flow.plot(ax=ax,kind='line',color=colorMean,linewidth=2)
        ax.set_ylabel('Q (MGD)')
        ax.set_ylim(bottom=0,top=1.2*s_flow.max())
        ax2 = ax.twinx()
    
        s_rain.plot(ax=ax2,kind='area',color=colorRain)
        indx = pd.to_datetime(df_rainDates.index[stormNum]).date()
        dailyrainMax = df_dailyrain.loc[indx-dt.timedelta(days=bufferBefore):indx+dt.timedelta(days=bufferAfter),gageName].values.max()
        ax2.set_ylim(bottom=0,top=dailyrainMax)
        ax2.set_ylabel('i (in)')

        count = 0
        
        dates = [stormDate + dt.timedelta(days=x) for x in range(0, days+1)]
        for date in dates:
            datemask = (dfMeanFlow.index <= date) & (dfMeanFlow.index >= date -     dt.timedelta(days=1))
            dfMeanFlow.loc[datemask,'Mean Flow'].plot(ax=ax,kind='line',color=color [count])
            count += 1

        ax.legend(['Q',' weekday mean','weekend mean'],bbox_to_anchor=(0., 1.02, 1., .102), loc=3, borderaxespad=0.,mode='expand',ncol=2)
        print(stormNum, df_dailyrain.loc[indx,gageName])
        plt.show()
        plt.close(fig)

    elif integrate:
        sDiff=  s_flow-dfMeanFlow.loc[:,'Mean Flow']
        measInc = 15.0/24/60 #in days
        iTotal.extend([s_rain.sum()])
        grossvol.extend([measInc*abstrapz(sDiff)]) #in MILLION GALLONS

dfiAndi = pd.DataFrame({'Rain Total': iTotal, 'Gross I&I': grossvol})
dfiAndi.set_index(df_rainDates.index)