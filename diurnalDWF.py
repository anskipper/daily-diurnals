#import modules
# pandas for data storage, organization, and manipulation:
import pandas as pd
#datetime for date and time manipulation
import datetime as dt
from datetime import datetime,timedelta
#pyplot for plotting specifically
import matplotlib.pyplot as plt 
#numpy for data manipulation
import numpy as np 

flowDir = 'P:'+r'\PW-WATER SERVICES'+r'\TECHNICAL SERVICES'+r'\Anna'
fmNum = 53
if fmNum<10:
    flowmeter = r'\BC' +'0'+ str(fmNum) #+ 'A'
    fmName = 'BC' + '0'+ str(fmNum) #+ 'A'
else:
    flowmeter = r'\BC' + str(fmNum) + 'B'
    fmName = 'BC' + str(fmNum) + 'B'
extratext = '_28660533'
flowFile = flowDir +  flowmeter + extratext + '.txt'

#input is a text file from sliicer
#output is a dataframe with indices in datetime and columns of depth, velocity and flowrate respectively
def readSliicer(filename):
    df = pd.read_csv(filename,sep='	',header=2, index_col=0,names=['y','v','Q (MGD)'])
    df.index = pd.to_datetime(df.index)
    return(df)

df_flow = readSliicer(flowFile)

def findRainGage(filename,fmName):
    df = pd.read_csv(filename,index_col=0,sep='\t')
    rg = df.loc[fmName][0]
    print(rg)
    return(rg)

#eventually we should use a more sophisticated way of finding dry days but this is ok for now
def readRain(filename,gageName):
    df = pd.read_excel(filename,gageName,index_col=0)
    df.index = pd.to_datetime(df.index)
    return(df)

rainFile = 'H:'+ r'\Big Creek' r'\Big Creek Rain Gauges dry days.xlsx'
gageFile = flowDir + r'\FMtoRG.txt'
gageName = findRainGage(filename=gageFile,fmName=fmName)
df_rain = readRain(filename=rainFile,gageName=gageName)

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

startDate, endDate = defineDateRange(df_flow,df_rain)
df_flow = df_flow.loc[startDate:endDate,:]
df_rain = df_rain.loc[startDate:endDate,:]

rainthresh = 0.1 #in
bufferBefore = 2 #days
bufferAfter = 3 #EPA recommends 3 days

def findRain(df,rainthresh,bufferBefore,bufferAfter):
    df['Rain Bool'] = df>rainthresh
    rainDates = df.index[df['Rain Bool']]
    #filter out 2 days before rain
    beforeDates = rainDates - dt.timedelta(days=bufferBefore)
    #filter out 2 days after rain
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

df_rainDates = findRain(df_rain,rainthresh=rainthresh,bufferBefore=bufferBefore,bufferAfter=bufferAfter)

df_flow['Weather']='Dry'
def setWeather(df,df_rainDates):
    for j in range(0,len(df_rainDates.index)):
        df.loc[df_rainDates.iloc[j,0]:df_rainDates.iloc[j,1],'Weather']='Rain Event'
    return(df)

df_flow = setWeather(df=df_flow,df_rainDates=df_rainDates)
print("Weather catagorized!")

def findDryDays(df,weekCatagory):
    if weekCatagory == 'weekday':
        df = df[(df.index.dayofweek<5)]
    elif weekCatagory == 'weekend':
        df = df[df.index.dayofweek>=5]
    else:
        print('Please choose either "weekday" or "weekend" for argument weekCatagory')
    df = df[df['Weather']=='Dry']
    return(df)

df_dryWeekday = findDryDays(df=df_flow,weekCatagory='weekday')
df_dryWeekend = findDryDays(df=df_flow,weekCatagory='weekend')

def reorganizeFlowData(df,colVal):
    df['date']=df.index.date
    df['time']=df.index.time
    df = df.pivot(index='time',columns='date',values=colVal)
    return(df)

df_dryWeekday = reorganizeFlowData(df=df_dryWeekday,colVal='Q (MGD)')
df_dryWeekend = reorganizeFlowData(df=df_dryWeekend,colVal='Q (MGD)')

def saveDiurnals(flowmeter,df_flow,weekCatagory,plotType):
    global flowDir
    saveDir = flowDir + flowmeter
    saveName = r'\diurnal-dry-' + weekCatagory + '-' + plotType + '_' + str(df_flow.index.date[0]) +'-' + str(df_flow.index.date[-1])  + '.png'
    plt.savefig(saveDir+saveName)
    print('Figure saved!')

def prettyxTime(ax):
    ticks = ax.get_xticks()
    ax.set_xticks(np.linspace(ticks[0],24*3600,5))
    ax.set_xticks(np.linspace(ticks[0],24*3600,25),minor=True)

def plotDiurnalsAll(df,colorAll,colorMean,figsize,weekCatagory,df_flow):
    global flowmeter
    fig, ax = plt.subplots()
    df.plot(ax=ax,kind='line',figsize=figsize,legend=False,color=colorAll)
    meanLine = df.mean(axis=1)
    meanLine.plot(ax=ax,kind='line',figsize=figsize,legend=False,color=colorMean,linewidth=3)
    ax.set_title(fmName + ': '+ weekCatagory+' , Dry Weather')
    ax.set_ylabel('Q (MGD)')
    ax.set_ylim(bottom=0,top=1.1*df.max().max())
    ax.set_xlabel('Time of Day')
    prettyxTime(ax)
    saveDiurnals(flowmeter=flowmeter,df_flow=df_flow,weekCatagory=weekCatagory,plotType='all')
    return(fig,ax)

colorAll = 'xkcd:light grey'
colorWkd = 'xkcd:leaf green'
colorWke = 'xkcd:hunter green'
figSize = (12,6)

fig1,ax1 = plotDiurnalsAll(df=df_dryWeekday,colorAll=colorAll,colorMean=colorWkd, weekCatagory='Weekday', figsize=figSize,df_flow=df_flow)
fig2,ax2= plotDiurnalsAll(df=df_dryWeekend,colorAll=colorAll,colorMean=colorWke, weekCatagory='Weekend', figsize=figSize,df_flow=df_flow)

def plotQuantileDiurnals(df,figsize,color,weekCatagory,upQuantile,lowQuantile,df_flow):
    global flowmeter
    fig, ax = plt.subplots()
    meanLine = df.mean(axis=1)
    meanLine.plot(ax=ax,kind='line',figsize=figsize,legend=False,color=color,linewidth=2)
    ax.set_title(fmName + ': ' + weekCatagory+' , Dry Weather')
    ax.set_ylabel('Q (MGD)')
    
    ax.set_xlabel('Time of Day')
    ticks = ax.get_xticks()
    ax.set_xticks(np.linspace(ticks[0],24*3600,5))
    ax.set_xticks(np.linspace(ticks[0],24*3600,25),minor=True)
    # get quantiles
    quantUp = df.quantile(upQuantile,axis=1)
    quantUp.plot(ax=ax,style='--',linewidth=2,color=color)
    ax.fill_between(meanLine.index,meanLine,quantUp,alpha=0.2,facecolor=color)
    
    ax.set_ylim(bottom=0,top=1.2*quantUp.max())
    
    quantLow = df.quantile(lowQuantile,axis=1)
    quantLow.plot(ax=ax,style='--',linewidth=2,color=color)
    ax.fill_between(meanLine.index,meanLine,quantLow,alpha=0.2,facecolor=color)
    ax.legend(['mean','95' + r'% or 5' + r'% quantile'])

    saveDiurnals(flowmeter=flowmeter,df_flow=df_flow,weekCatagory=weekCatagory,plotType='quantile')

    return(fig,ax)

fig3,ax3 = plotQuantileDiurnals(df=df_dryWeekday,figsize=figSize,color=colorWkd, weekCatagory = 'Weekday',upQuantile=0.95,lowQuantile=0.05,df_flow=df_flow)
fig4,ax4 = plotQuantileDiurnals(df=df_dryWeekend,figsize=figSize,color=colorWke, weekCatagory = 'Weekend',upQuantile=0.95,lowQuantile=0.05,df_flow=df_flow)

def findGWI(df1,df2,method):
    if method == 'percent':
        m1 = df1.mean(axis=1)
        m2 = df2.mean(axis=1)
        gwi = 0.75*min(m1.min(),m2.min())
    else:
        print("I don't recognize that method...")
    return(gwi)

gwi = findGWI(df1=df_dryWeekday,df2=df_dryWeekend,method='percent')

#FINISH WRITING THIS PART

def saveCombined(flowmeter,plotType):
    #saveDir = 'H:'+r'\Big Creek'+r'\Subbasin '  + flowmeter
    global flowDir
    saveDir = flowDir + flowmeter
    saveName = r'\weekdayVsweekend_' + plotType + '.png'
    plt.savefig(saveDir+saveName)
    print('Figure saved!')

def plotTogether(meanLine1,meanLine2,gwi,plotgwi,color1,color2,colorg,figsize,plotType,norm):
    fig, ax = plt.subplots()
    meanLine1.plot(ax=ax,kind='line',figsize=figsize,legend=False,color=color1,linewidth=2)
    meanLine2.plot(ax=ax,kind='line',figsize=figsize,legend=False,color=color2,linewidth=2)

    if plotgwi:
        ax.plot([meanLine1.index[0],meanLine1.index[-1]],[gwi,gwi],color=colorg,label='GWI',linewidth=2)
        ax.legend(['Weekday','Weekend','GWI = ' + str(round(gwi,2)) + ' MGD'])
        ax.set_title(fmName + ': Weekday vs. Weekend, Dry Weather')
    else:
        ax.legend(['Weekday','Weekend'])
        ax.set_title(fmName + ': Normalized Sanitary Flow')
    prettyxTime(ax)
    ax.set_ylabel('Q (MGD)')
    if norm: 
        ax.set_ylim(bottom=0,top=2)
    else: 
        ax.set_ylim(bottom=0,top=1.2*max(meanLine1.max(),meanLine2.max()))
    ax.set_xlabel('Time of Day')
    saveCombined(flowmeter=flowmeter,plotType=plotType)
    return(fig,ax)

colorg = 'xkcd:slate blue'
fig5, ax5 = plotTogether(meanLine1=df_dryWeekday.mean(axis=1),meanLine2=df_dryWeekend.mean(axis=1),gwi=gwi,color1=colorWkd,color2=colorWke,colorg = colorg,figsize = (12,6),plotgwi=True,plotType = 'totalFlow',norm=False)

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

snormWKD = findNormSanitaryFlow(df=df_dryWeekday,gwi=gwi,colName = 'Weekday')
snormWKE = findNormSanitaryFlow(df=df_dryWeekend,gwi=gwi,colName = 'Weekend')

fig6, ax6 = plotTogether(meanLine1=snormWKD,meanLine2=snormWKE,gwi=gwi,color1=colorWkd,color2=colorWke,colorg = colorg,figsize = (12,6),plotgwi=False,plotType = 'normSanitaryFlow',norm=True)

#save snorms to CSV
df_csv = pd.DataFrame(index=snormWKD.index,columns=['Weekday','Weekend','GWI','Weekday Mean','Weekend Mean'])
df_csv['Weekday'] = snormWKD
df_csv['Weekend'] = snormWKE
sanMeanWKD = findSanMean(df=df_dryWeekday,gwi=gwi)
sanMeanWKE = findSanMean(df=df_dryWeekend,gwi=gwi)
df_csv.iloc[0,2:]=[gwi,sanMeanWKD,sanMeanWKE]

df_csv.index.name = 'Time'
#saveDir = 'H:'+r'\Big Creek'+r'\Subbasin ' + flowmeter
saveDir = flowDir + flowmeter
saveName = flowmeter + '_sanitaryNorm.csv'
df_csv.to_csv(saveDir+saveName)