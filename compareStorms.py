import pandas as pd 
import diurnal.fileIO as fio
import diurnal.dryWeather as dw
import diurnal.findRainEvents as fRE
import diurnal.wetWeather as ww
import datetime as dt
import matplotlib.pyplot as plt
import diurnal.plotting as plotting

# directories and files
homeDir = 'P:\\PW-WATER SERVICES\\TECHNICAL SERVICES\\Anna'
flowDirYrs = homeDir + '\\Storm Analysis\\FlowData_20170101_20181231'
flowDirStorm = homeDir + '\\Storm Analysis\\FlowData_20190605_20190612'
upstreamFile = homeDir + '\\FMtoUpstream.csv'
gageFile = homeDir + '\\FMtoRG.txt'
hourlyFile = homeDir + '\\Storm Analysis\\rgHourly_20190605-20190612.txt'
dailyFile = homeDir + '\\Storm Analysis\\rgDaily_20170101-20181231.txt'

# analyze net i&i for June 8th storm and produce
stormDate = dt.datetime(2019,6,8)
# find the names of the csv files from sliicer
folders,textfiles,csvs = fio.findTextFiles(readDir=flowDirStorm)
plot = False

# set up empty lists for dataframe creation
fmname = []
grossVol = []
netVol = []
dmaxAll = []
t_dmaxAll = []
dOneThirdAll = []
########### FOR ALL THE FLOW METERS ###########
for fmData in csvs:
    fmname.extend([fmData.split('_')[0]]) #think about how to do it for temp fms??
    print(fmname[-1])
    # create flow file and mean file
    flowFile = flowDirStorm + "\\" + fmData   
    meanFile = homeDir + '\\' + fmname[-1] + '\\' + fmname[-1] + '_meanFlows.csv'
    # find the rain gage and hourly file
    gageName = dw.findRainGage(filename=gageFile,fmName=fmname[-1])
    dfHourly = dw.readRaintxt(filename=hourlyFile,useColList=['DateTime',gageName])

    if plot:
        plotting.stormPlot(fmname[-1],stormDate,gageName,meanFile,hourlyFile,flowFile)
        plt.show()

    ##### GET THE GROSS VOLUME
    #tStart,eventDur,eventRT,stormDur,stormRT = fRE.stormAnalyzer(dfHourly=dfHourly,date=stormDate,gageName=gageName)
    grossVol.extend([ww.stormGrossVol(stormDate=stormDate,fmname=fmname[-1],gageName=gageName,dfHourly=dfHourly,flowFile=flowFile,meanFile=meanFile)])
    # find dmax, t_dmax, and d_(1/3)
    dmax,t_dmax,dOneThird = ww.findDmax(flowFile=flowFile,date=stormDate)
    dmaxAll.extend([dmax])
    t_dmaxAll.extend([t_dmax])
    dOneThirdAll.extend([dOneThird])
 
df = pd.DataFrame({'GrossVol': grossVol, 'dMax' : dmaxAll, 'Time dMax': t_dmaxAll, 'd_1/3': dOneThirdAll},index=fmname)

netVol = []
####### GET THE NET VOLUME #########
for fm in fmname:
    netVol.extend([ww.stormNetII(dfGross=df,fmName=fm,upstreamFile=upstreamFile)])


df['NetVol'] = netVol
df = df[['GrossVol','NetVol','Time dMax','dMax','d_1/3']]
df.to_csv(homeDir + '\\Storm Analysis\\ii_' + str(stormDate.date()) + '.csv')
df = df[df.index != 'BC19']
df = df[df.index != 'RSPSM']
############### PLOTTING ###############
fig, ax = plt.subplots()
df['NetVol'].plot.barh(figsize=(7.5,12.5),ax=ax)
ax.set_title(str(stormDate.date()))
ax.set_xlabel('Net I&I (MG)')
ax.grid()

#plt.show()

plt.savefig(homeDir + '\\Storm Analysis\\netii_' + str(stormDate.date()) + '.png')

df.sort_values(by='Time dMax',ascending=True)

possDates = ww.findStormsOfSize(drt=1.4,dailyFile=dailyFile)
stormDates = [dt.datetime(2017,7,11),dt.datetime(2018,8,1),dt.datetime(2018,11,12)]
for date in stormDates:
