import numpy as np
import pandas as pd
import datetime as dt
'''
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
'''
def findRainEvents(dfDaily,df15min,rainthresh,bufferBefore,bufferAfter,gageName):
    startDate = dfDaily.index[0]
    endDate = dfDaily.index[-1]
    # where do the daily rain totals exceed the threshold?
    dfDaily['Rain Bool'] = dfDaily>rainthresh
    rainDates = dfDaily.index[dfDaily['Rain Bool']]
    # initialize before and after lists + datesProcessed list
    beforeDates = []
    afterDates = []
    datesProcessed = []
    stormDates = []
    for stormNum in range(0,len(rainDates)):
        ##print(stormNum)
        # get all the measurements taken that rain day
        s = df15min.loc[rainDates[stormNum]:rainDates[stormNum]+dt.timedelta(hours=23,minutes=45),gageName]
        # find time of rain
        startTime = s.index[s>0][0]
        # QUALITY FILTER
        # if the daily rain total is within 10% of the max value on that day, discard
        dailyMaxDiff = abs(dfDaily.loc[rainDates[stormNum],gageName] - s.max())/dfDaily.loc[rainDates[stormNum],gageName]
        # if the event has been added to a raindate already, pass
        if rainDates[stormNum] in datesProcessed:
            pass
        # if the daily rain total is within 10% of the max value on that day, pass      
        elif dailyMaxDiff<=0.1:
            pass
        # if it rains on the first date of analysis, skip it
        elif startTime-dt.timedelta(days=bufferBefore)<startDate:
            pass
        # if the rain date is too close to the end of the analysis period, then we dont really need to belabor ourselves
        elif startTime+dt.timedelta(days=2)>=endDate:
            # set the before date as usual
            beforeDates.extend([startTime-dt.timedelta(days=bufferBefore)])
            # set the storm date
            stormDates.extend([startTime])
            # set the after date to be the very end of the analysis period
            afterDates.extend(endDate+dt.timedelta(hours=23,minutes=45))
        # otherwise
        else:
            # add to dates processed
            datesProcessed.extend([rainDates[stormNum]]) 
            #find before date
            beforeDates.extend([startTime-dt.timedelta(days=bufferBefore)])
            # set the storm date
            stormDates.extend([startTime])
            # between end of rain day and 8 am next day, how much did it rain?
            nextMorningRain = df15min.loc[rainDates[stormNum]+dt.timedelta(days=1):rainDates[stormNum]+dt.timedelta(days=1,hours=8),gageName].values.sum()
            ##print(nextMorningRain)
            daycount = 0
            while nextMorningRain >= rainthresh/3.0:
                #update day count
                daycount +=1
                #calculate the next morningRain
                nextMorningRain = df15min.loc[rainDates[stormNum]+dt.timedelta(days=daycount+1):rainDates[stormNum]+dt.timedelta(days=daycount+1,hours=8),gageName].values.sum()
                #print(nextMorningRain)
                # if the next days daily rainy total exceeds the threshold, go ahead and add the next day to dates processed
                if dfDaily.loc[rainDates[stormNum]+dt.timedelta(days=daycount),gageName]>rainthresh:
                    # add the date to the processed list
                    datesProcessed.extend([rainDates[stormNum]+dt.timedelta(days=daycount)])
                else:
                    pass
            s = df15min.loc[datesProcessed[-1]:datesProcessed[-1]+dt.timedelta(hours=23,minutes=45),gageName]
            endTime = s.index[s>0][-1]
            afterDates.extend([endTime+dt.timedelta(days=bufferAfter)])    
            ##print('Storm on ' + str(rainDates[stormNum]) + ' processed.')
    #assign to new dataframe
    df_rainDates = pd.DataFrame({'Before': beforeDates, 'After': afterDates, 'Storm' : stormDates})
    #find the storms correspond
    #rearrange for some reason...
    df_rainDates = df_rainDates[['Before','After','Storm']]
    df_rainDates.set_index('Storm',inplace=True)
    df_rainDates.index = pd.to_datetime(df_rainDates.index)
    return(df_rainDates)

#df_rainDates = findRainEvents(dfDaily=df_dailyrain,df15min=df_rain,rainthresh=rainthresh,bufferBefore=bufferBefore,bufferAfter=bufferAfter,gageName=gageName)