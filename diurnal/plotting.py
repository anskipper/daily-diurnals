import matplotlib.pyplot as plt 
import numpy as np
import findRainEvents as fre 
import wetWeather as ww
import dryWeather as dw

# save the quantile and regular diurnals
def saveDiurnals(df_flow,weekCatagory,plotType,saveDir):
#    saveDir = flowDir + flowmeter
    saveName = r'\diurnal-dry-' + weekCatagory + '-' + plotType + '_' + str(df_flow.index.date[0]) +'-' + str(df_flow.index.date[-1])  + '.png'
    plt.savefig(saveDir+saveName)
    print('Figure saved!')

def prettyxTime(ax):
    ticks = ax.get_xticks()
    ax.set_xticks(np.linspace(ticks[0],24*3600,5))
    ax.set_xticks(np.linspace(ticks[0],24*3600,25),minor=True)

def plotDiurnalsAll(df,colorAll,colorMean,figsize,weekCatagory,df_flow,fmName,saveDir):
    fig, ax = plt.subplots()
    df.plot(ax=ax,kind='line',figsize=figsize,legend=False,color=colorAll)
    meanLine = df.mean(axis=1)
    meanLine.plot(ax=ax,kind='line',figsize=figsize,legend=False,color=colorMean,linewidth=3)
    ax.set_title(fmName + ': '+ weekCatagory+' , Dry Weather')
    ax.set_ylabel('Q (MGD)')
    ax.set_ylim(bottom=0,top=1.1*df.max().max())
    ax.set_xlabel('Time of Day')
    prettyxTime(ax)
    ax.grid(which='major',color='xkcd:grey',axis='both')
    saveDiurnals(df_flow=df_flow,weekCatagory=weekCatagory,plotType='all',saveDir=saveDir)
    return(fig,ax)

def plotQuantileDiurnals(df,figsize,color,weekCatagory,upQuantile,lowQuantile,df_flow,fmName,saveDir):
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
    ax.grid(which='major',color='xkcd:grey',axis='both')
    saveDiurnals(df_flow=df_flow,weekCatagory=weekCatagory,plotType='quantile',saveDir=saveDir)

    return(fig,ax)

def saveCombined(saveDir,plotType):
    #saveDir = 'H:'+r'\Big Creek'+r'\Subbasin '  + flowmeter
    saveName = r'\weekdayVsweekend_' + plotType + '.png'
    plt.savefig(saveDir+saveName)
    print('Figure saved!')

def plotTogether(meanLine1,meanLine2,gwi,plotgwi,color1,color2,colorg,figsize,plotType,norm,saveDir,fmname):
    fig, ax = plt.subplots()
    meanLine1.plot(ax=ax,kind='line',figsize=figsize,legend=False,color=color1,linewidth=2)
    meanLine2.plot(ax=ax,kind='line',figsize=figsize,legend=False,color=color2,linewidth=2)
    if plotgwi:
        ax.plot([meanLine1.index[0],meanLine1.index[-1]],[gwi,gwi],color=colorg,label='GWI',linewidth=2)
        ax.legend(['Weekday','Weekend','GWI = ' + str(round(gwi,2)) + ' MGD'])
        ax.set_title(fmname + ': Weekday vs. Weekend, Dry Weather')
    else:
        ax.legend(['Weekday','Weekend'])
        ax.set_title(fmname + ': Normalized Sanitary Flow')
    prettyxTime(ax)
    ax.set_ylabel('Q (MGD)')
    if norm: 
        ax.set_ylim(bottom=0,top=2)
    else: 
        ax.set_ylim(bottom=0,top=1.2*max(meanLine1.max(),meanLine2.max()))
    ax.set_xlabel('Time of Day')
    ax.grid(which='major',color='xkcd:grey',axis='both')
    saveCombined(saveDir=saveDir,plotType=plotType)
    return(fig,ax)

# plotting the wet weather with the means
def stormPlot(fmname,stormDate,gageName,meanFile,hourlyFile):
    dfHourly = dw.readRaintxt(filename=hourlyFile,useColList=['DateTime',gageName])
    tStart,eventDur,eventRT,stormDur,stormRT = fre.stormAnalyzer(dfHourly,stormDate,gageName)
    dfMeans = ww.readTotalFlow(filename=meanFile)
    dfStormMeans,colorMean = fre.constructMeanFlow(tStart,stormDur,dfMeans)