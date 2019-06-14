import pandas as pd
import datetime as dt
from diurnal import dryWeather as dw

#set file locations
flowDir = 'P:\\PW-WATER SERVICES\\TECHNICAL SERVICES\\Anna'
rainFile = flowDir + '\\RG_daily_20180101-20190331.txt'
gageFile = flowDir + '\\FMtoRG.txt'
fmname = 'BC01A'

# set variables
rainthresh = 0.1 #in
bufferBefore = 1 #days (pre-comp)
bufferAfter = 2 #days (Recovery 1 & 2)

# which gage corresponds to this flowmeter?
gageName = dw.findRainGage(filename=gageFile,fmName = fmname)
# read in the rain data as a dataframe with dates for indices
df_dailyrain = dw.readRaintxt(filename=rainFile,useColList=['Date',gageName])
rainFile15min = flowDir + '\\RG_15min_20180101-20190331.txt'
df_rain = dw.readRaintxt(filename=rainFile15min,useColList=['Datetime',gageName])

def findRainEvents(dfDaily,df15min,rainthresh,bufferBefore,bufferAfter,gageName):
    startDate = dfDaily.index[0]
    endDate = dfDaily.index[-1]
    # where do the daily rain totals exceed the threshold?
    dfDaily['Rain Bool'] = dfDaily>rainthresh
    rainDates = dfDaily.index[dfDaily['Rain Bool']]
    # initialize count and before, after lists
    count = 0
    beforeDates = []
    afterDates = []
    while count < len(rainDates):
        print(count)
        # all the measurements taken that rain day
        s = df15min.loc[rainDates[count]:rainDates[count]+dt.timedelta(hours=23,minutes=45),gageName]
        # QUALITY FILTER
        # if the daily rain total is within 10% of the max value on that day, discard
        dailyMaxDiff = abs(dfDaily.loc[rainDates[count],gageName] - s.max())/dfDaily.loc[rainDates[count],gageName]
        if dailyMaxDiff<=0.1:
            beforeDates.extend(['Faulty RG'])
            afterDates.extend(['Faulty RG'])
            count += 1
            print('Storm ' + str(count) + ' discounted.')
        else:
            # find time of rain
            startTime = s.index[s>0][0]
            #find before date
            beforeDates.extend([startTime-dt.timedelta(days=bufferBefore)])
            # between end of rain day and 8 am next day, how much did it rain?
            nextMorningRain = df15min.loc[rainDates[count]+dt.timedelta(days=1):rainDates[count]+dt.timedelta(days=1,hours=8),gageName].sum()
            while nextMorningRain >= rainthresh/3.0:
                # if the next days daily rainy total exceeds the threshold, go ahead and add one to the count
                if dfDaily.loc[rainDates[count]+dt.timedelta(days=1),gageName]>rainthresh:
                    count += 1
                else:
                    pass
                nextMorningRain = df15min.loc[rainDates[count]+dt.timedelta(days=1):rainDates[count]+dt.timedelta(days=1,hours=8),:].sum()
            #did it rain > rainthres/3.0 during last 8 hours of the day?
            ##eveningRain = df15min.loc[rainDates[count]+dt.timedelta(hours=16):rainDates[count+dt.timedelta(hours=23,minutes=45)],:].sum()
            afterDates.extend([rainDates[count]+dt.timedelta(bufferAfter)])
            print('Storm on ' + str(rainDates[count]) + ' processed.')
            count += 1
    #assign to new dataframe
    df_rainDates = pd.DataFrame({'Before': beforeDates, 'After': afterDates})
    #rearrange for some reason...
    df_rainDates = df_rainDates[['Before','After']]
    df_rainDates = df_rainDates.set_index(rainDates)
    #check that the rain dates are within the specified range
    if beforeDates[0]<startDate:
        df_rainDates.iloc[0,0]=startDate
    elif afterDates[-1]>endDate:
        df_rainDates.iloc[-1,1]=endDate
    return(df_rainDates)

df_rainDates = findRainEvents(dfDaily=df_dailyrain,df15min=df_rain,rainthresh=rainthresh,bufferBefore=bufferBefore,bufferAfter=bufferAfter,gageName=gageName)