# imports
from diurnal import dryWeather as dw
import datetime as dt 
import pandas as pd
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

# find the dates on which there was rain; return a data frame that has the rain dates as indices, the before date (dependent on bufferBefore), and the after date (dependent on the bufferAfter)
df_rainDates = dw.findRain(df=df_dailyrain,rainthresh=rainthresh,bufferBefore=bufferBefore,bufferAfter=bufferAfter)
# add day of week column to daily rain totals
df_dailyrain['dayofweek'] = df_dailyrain.index.dayofweek

testDate = df_rainDates.index[0]
# read in the 15 min date data file
rainFile15min = flowDir + '\\RG_15min_20180101-20190331.txt'
df_rain = dw.readRaintxt(filename=rainFile15min,useColList=['Datetime',gageName])

meanFile = flowDir+ '\\' + fmname + '\\' + fmname + '_sanitaryNorm.csv'

def reconstructTotalFlow(filename):
    df= pd.read_csv(filename,index_col=0)
    df.index = pd.to_datetime(df.index)
    df.index = df.index.time
    #transform back into total flow instead of sanitary flow:
    df.loc[:,'Weekday']=df.loc[:,'Weekday']*df.loc[df.index[0],'Weekday Mean'] + df.loc[df.index[0],'GWI']
    df.loc[:,'Weekend']=df.loc[:,'Weekend']*df.loc[df.index[0],'Weekend Mean'] + df.loc[df.index[0],'GWI']
    df = df.loc[:,['Weekday','Weekend']]
    return(df)

df_means = reconstructTotalFlow(filename=meanFile)

def constructMeanFlow(df_dailyrain,df_rainDates,df_means,stormNum):
    # find the days corresponding to the storm
    weekdayVals = df_dailyrain.loc[df_rainDates.iloc[stormNum,0]:df_rainDates.iloc[stormNum,1],'dayofweek']
    # construct the mean flow
    meanFlow = []
    color = []
    for j in weekdayVals:
        if j > 4: #weekend 
            meanFlow.extend(df_means.loc[:,'Weekend'])
            color.extend([colorWke])
        else:
            meanFlow.extend(df_means.loc[:,'Weekday'])
            color.extend([colorWkd])
    #construct datetime for plotting
    dateTimes = pd.date_range(df_rainDates.iloc[stormNum,0],periods=(bufferBefore+bufferAfter+1)*24,freq='60min')
    df = pd.DataFrame(data=meanFlow,index=dateTimes,columns=['Mean Flow'])
    df.index = pd.to_datetime(df.index)
    return(df,color)

# for each storm: for j in range(0,len(df_rainDates.index))
#set day of week
for stormNum in range(0,len(df_rainDates.index)):
    dfMeanFlow, color = constructMeanFlow(df_dailyrain = df_dailyrain,df_rainDates=df_rainDates,df_means=df_means,stormNum=stormNum)

    s_flow = df_flow.loc[df_rainDates.iloc[stormNum,0]:df_rainDates.iloc[stormNum,1] + dt.timedelta(hours=23,minutes=45),'Q (MGD)']
    s_rain = df_rain.loc[df_rainDates.iloc[stormNum,0]:df_rainDates.iloc[stormNum,1] + dt.timedelta(hours=23,minutes=45),gageName]
    s_rain.index = s_flow.index

    #plot for now
    colorWkd = 'xkcd:leaf green'
    colorWke = 'xkcd:hunter green'
    colorMean = 'xkcd:light purple'
    colorRain = 'xkcd:dark sky blue'
    gridColor = 'xkcd:grey'

    fig,ax= plt.subplots()
    s_flow.plot(ax=ax,kind='line',color=colorMean,linewidth=2)
    ax.set_ylabel('Q (MGD)')
    ax.set_ylim(bottom=0,top=1.2*s_flow.max())
    ax2 = ax.twinx()
    
    s_rain.plot(ax=ax2,kind='area',color=colorRain)
    ax2.set_ylim(bottom=0,top=df_dailyrain.loc[df_rainDates.index[stormNum],gageName])
    ax2.set_ylabel('i (in)')

    count = 0
    dates = [df_rainDates.index[stormNum] + dt.timedelta(days=x) for x in range(0, bufferAfter+bufferBefore+1)]
    for date in dates:
        plotdates = date + dt.timedelta(hours=23,minutes=45)
        datemask = (dfMeanFlow.index <= date) & (dfMeanFlow.index >= date -     dt.timedelta(days=1))
        dfMeanFlow.loc[datemask,'Mean Flow'].plot(ax=ax,kind='line',color=color [count])
        count += 1

    ax.legend(['Q',' weekday mean','weekend mean'],bbox_to_anchor=(0., 1.02, 1., .102), loc=3, borderaxespad=0.,mode='expand',ncol=2)
    print(df_dailyrain.loc[df_rainDates.index[stormNum],gageName])
    plt.show()
    plt.close(fig)

# find volume by integrating (Qi-Qm)over the rain period