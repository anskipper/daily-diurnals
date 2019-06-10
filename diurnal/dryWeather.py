# import other modules
import pandas as pd
import datetime as dt
import numpy as np

#input is a text file from sliicer
#output is a dataframe with indices in datetime and columns of depth, velocity and flowrate respectively
def readSliicer(filename):
    df = pd.read_csv(filename,sep='	',header=2, index_col=0,names=['y','v','Q (MGD)'])
    df.index = pd.to_datetime(df.index)
    return(df)

#finds the rain gage associated with each flow monitor
def findRainGage(filename,fmName):
    df = pd.read_csv(filename,index_col=0,sep='\t')
    rg = df.loc[fmName][0]
    print(rg)
    return(rg)

#reads in rain data from excel file and outputs a dataframe with the dates listed as the index and the rain amounts in a columns titled "Rain Total"
def readRain(filename,gageName):
    df = pd.read_excel(filename,gageName,index_col=0)
    df.index = pd.to_datetime(df.index)
    return(df)

# given two data frames with dates as the indices, find the longest overlap in dates
def defineDateRange(df1,df2):
    start1 = df1.index[0]
    start2 = df2.index[0]
    if start1<=start2:
        start = start2 #pick the later date
    else:
        start = start1
    end1 = df1.index[-1]
    end2 = df2.index[-1]
    if end1<=end2:
        end = end1
    else:
        end = end2
    return(start,end)

# given a data frame with dates in the index and rain totals in the column, find which days exceed a rain threshold and a certain amount of "buffer" days before and after that date; ensures that the last after buffer date does not exceed the date range in the original data
# create a new data frame that has the original rain date as the index, a before date column corresponding to the amount of buffer days before, and an after date column corresponding to the amount of buffer dats after
def findRain(df,rainthresh,bufferBefore,bufferAfter):
    startDate = df.index[0]
    endDate = df.index[-1]
    df['Rain Bool'] = df>rainthresh
    rainDates = df.index[df['Rain Bool']]
    #filter out days before rain
    beforeDates = rainDates - dt.timedelta(days=bufferBefore)
    #filter out days after rain
    afterDates = rainDates + dt.timedelta(days=bufferAfter)
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

# set the weather of the flow data data frame to either "Dry" or "Rain Event"
def setWeather(df,df_rainDates):
    df['Weather']='Dry'
    for j in range(0,len(df_rainDates.index)):
        df.loc[df_rainDates.iloc[j,0]:df_rainDates.iloc[j,1],'Weather']='Rain Event'
    return(df)

# find dry days on either the "weekday" or the "weekend"
def findDryDays(df,weekCatagory):
    if weekCatagory == 'weekday':
        df = df[(df.index.dayofweek<5)]
    elif weekCatagory == 'weekend':
        df = df[df.index.dayofweek>=5]
    else:
        print('Please choose either "weekday" or "weekend" for argument weekCatagory')
    df = df[df['Weather']=='Dry']
    return(df)

# reorganize the data such that the index is time of day, the columns represent different days, and the values are whichever is specified (e.g., Q)
def reorganizeFlowData(df,colVal):
    df['date']=df.index.date
    df['time']=df.index.time
    df = df.pivot(index='time',columns='date',values=colVal)
    return(df)

#find the GWI according to a certain method; for now, only the percent method is supported
def findGWI(df1,df2,method):
    if method == 'percent':
        m1 = df1.mean(axis=1)
        m2 = df2.mean(axis=1)
        gwi = 0.75*min(m1.min(),m2.min())
    else:
        print("I don't recognize that method...")
    return(gwi)

def findSanMean(df,gwi):
    dfMean = df.mean(axis=1)
    df_san = (dfMean-gwi)
    sanMean = df_san.mean()
    return(sanMean)

def findNormSanitaryFlow(df,gwi,colName):
    dfMean = df.mean(axis=1)
    df_san = (dfMean-gwi)
    sanMean = df_san.mean()
    ki = np.array([])
    for j in range(1,len(df_san),4): #4 meas/hr
        s = dfMean.iloc[j:j+3]
        smean = s.mean()
        ki = np.append(ki,smean/sanMean)
    snorm = ki*24/sum(ki) #adjust for the fact the sum should be equal to 24 hrs
    #make into a series/dataframe
    l = df.index[range(0,len(df.index),4)]
    snorm = pd.DataFrame(data=snorm,index=l.tolist(),columns=[colName])
    return(snorm)

def createcsv(snormWKD,snormWKE,dfWKD, dfWKE, gwi,saveDir,fmName):
    df_csv = pd.DataFrame(index=snormWKD.index,columns=['Weekday','Weekend','GWI','Weekday Mean','Weekend Mean'])
    df_csv['Weekday'] = snormWKD
    df_csv['Weekend'] = snormWKE
    sanMeanWKD = findSanMean(df=dfWKD,gwi=gwi)
    sanMeanWKE = findSanMean(df=dfWKE,gwi=gwi)
    df_csv.iloc[0,2:]=[gwi,sanMeanWKD,sanMeanWKE]

    df_csv.index.name = 'Time'
    #saveDir = 'H:'+r'\Big Creek'+r'\Subbasin ' + flowmeter
    #saveDir = flowDir + flowmeter
    saveName = "\\" + fmName + '_sanitaryNorm.csv'
    df_csv.to_csv(saveDir+saveName)
    return(df_csv)