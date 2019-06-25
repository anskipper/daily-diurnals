import pandas as pd 
import diurnal.fileIO as fio
import diurnal.dryWeather as dw
import diurnal.findRainEvents as fRE
import diurnal.wetWeather as ww
import datetime as dt
import matplotlib.pyplot as plt
import diurnal.plotting as plotting
import math as m

# directories and files
homeDir = 'P:\\PW-WATER SERVICES\\TECHNICAL SERVICES\\Anna'
flowDirYrs = homeDir + '\\Storm Analysis\\FlowData_20170101_20181231'
flowDirStorm = homeDir + '\\Storm Analysis\\FlowData_20190605_20190612'
upstreamFile = homeDir + '\\FMtoUpstream.csv'
gageFile = homeDir + '\\FMtoRG.txt'
hourlyFile = homeDir + '\\Storm Analysis\\rgHourly_20190605-20190612.txt'
dailyFile = homeDir + '\\Storm Analysis\\rgDaily_20170101-20181231.txt'
diameterFile = homeDir + '\\FMpipeDiameter.txt'

# analyze net i&i for June 8th storm and produce
stormDate = dt.datetime(2019,6,8)
# find the names of the csv files from sliicer
folders,textfiles,csvs = fio.findTextFiles(readDir=flowDirStorm)
plot = False
toformat = True
'''
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
    # create flow file and mean file
    flowFile = flowDirStorm + "\\" + fmData   
    meanFile = homeDir + '\\' + fmname[-1] + '\\' + fmname[-1] + '_meanFlows.csv'
    # find the rain gage and hourly file
    gageName = dw.findRainGage(filename=gageFile,fmName=fmname[-1])
    dfHourly = dw.readRaintxt(filename=hourlyFile,useColList=['DateTime',gageName])
    if plot:
        plotting.stormPlot(fmname[-1],stormDate,gageName,meanFile,hourlyFile,flowFile,diameterFile,format=toformat)
        plt.show()

    ##### GET THE GROSS VOLUME
    #tStart,eventDur,eventRT,stormDur,stormRT = fRE.stormAnalyzer(dfHourly=dfHourly,date=stormDate,gageName=gageName)
    grossQ = ww.stormGrossQ(stormDate=stormDate,fmname=fmname[-1],gageName=gageName,dfHourly=dfHourly,flowFile=flowFile,meanFile=meanFile,diameterFile=diameterFile,format=toformat)
    #fig,ax = plt.subplots()
    #grossQ.plot(ax=ax)
    #ax.set_title(fmname)
    #plt.show()
    delta = 15.0/24/60 # conversion from measurement increments to days for volume calculation
    grossVol.extend([delta*ww.abstrapz(grossQ)])
    # find dmax, t_dmax, and d_(1/3)
    dmax,t_dmax,dOneThird = ww.findDmax(flowFile=flowFile,date=stormDate)
    dmaxAll.extend([dmax])
    t_dmaxAll.extend([t_dmax])
    dOneThirdAll.extend([dOneThird])

df = pd.DataFrame({'GrossVol': grossVol, 'dMax' : dmaxAll, 'Time dMax': t_dmaxAll, 'd_1/3': dOneThirdAll},index=fmname)

# delete BC19A, BC59, and BC26 from list
badData = ['BC19A','BC59','BC26','BC61','RSPSM']

netVol = []
####### GET THE NET VOLUME #########
for fmData in csvs:
    fm = fmData.split('_')[0]
    if fm not in badData:
        flowFile = flowDirStorm + "\\" + fmData
        netQ = ww.stormNetII(upstreamFile=upstreamFile,flowDirStorm=flowDirStorm,fmName=fm,format=toformat,diameterFile=diameterFile,filelist=csvs,stormDate=stormDate,gageFile=gageFile,hourlyFile=hourlyFile,homeDir=homeDir,flowFile=flowFile,fmsToSkip=badData)
        #netQ.plot()
        #plt.show()
        netVol.extend([delta*ww.abstrapz(netQ)])
    else:
        netVol.extend([float('NaN')])

print(str(stormDate))

df['NetVol'] = netVol
df = df[['GrossVol','NetVol','Time dMax','dMax','d_1/3']]
df.to_csv(homeDir + '\\Storm Analysis\\ii_' + str(stormDate.date()) + '.csv')
for fm in badData:
    df = df[df.index != fm]

############### PLOTTING ###############
fig, ax = plt.subplots()
df['NetVol'].plot.barh(figsize=(7.5,12.5),ax=ax)
ax.set_title(str(stormDate.date()))
ax.set_xlabel('Net I&I (MG)')
ax.grid()

#plt.show()

plt.savefig(homeDir + '\\Storm Analysis\\netii_' + str(stormDate.date()) + '.png')

df.sort_values(by='Time dMax',ascending=True)

# create dataframe of net I&Is for each storm
dfnetII = pd.DataFrame({str(stormDate): netVol},index=fmname)
dfgrossII = pd.DataFrame({str(stormDate): grossVol},index=fmname)
dfdMax = pd.DataFrame({str(stormDate): dmaxAll},index=fmname)
dftimedMax = pd.DataFrame({str(stormDate): t_dmaxAll},index=fmname)
dfdOneThird = pd.DataFrame({str(stormDate): dOneThirdAll},index=fmname)
'''
possDates = ww.findStormsOfSize(drt=1.4,dailyFile=dailyFile)
stormDates = [dt.datetime(2017,7,11),dt.datetime(2018,8,1),
    dt.datetime(2018,8,1)]
flowDirStorm = [homeDir + '\\Storm Analysis\\FlowData_20170708_20170715',
    homeDir + '\\Storm Analysis\\FlowData_20180729_20180804']
hourlyFile = [homeDir + '\\Storm Analysis\\rgHourly_20170708-20170715.txt',
    homeDir + '\\Storm Analysis\\rgHourly_20180729-20180804.txt']

netVol = []
plot =  True
for date in stormDates:
    fmname = []
    grossVol = []
    dmaxAll = []
    t_dmaxAll = []
    dOneThirdAll = []
    count = 0

    folders,textfiles,csvs = fio.findTextFiles(readDir=flowDirStorm[count])
    
    for fmData in csvs:
        fmname.extend([fmData.split('_')[0]]) #think about how to do it for temp fms??
        # create flow file and mean file
        flowFile = flowDirStorm[count] + "\\" + fmData   
        meanFile = homeDir + '\\' + fmname[-1] + '\\' + fmname[-1] + '_meanFlows.csv'
        # find the rain gage and hourly file
        gageName = dw.findRainGage(filename=gageFile,fmName=fmname[-1])
        dfHourly = dw.readRaintxt(filename=hourlyFile[count],useColList=['DateTime',gageName])
        grossQ = ww.stormGrossQ(stormDate=date,fmname=fmname[-1],gageName=gageName,dfHourly=dfHourly,flowFile=flowFile,meanFile=meanFile,diameterFile=diameterFile,format=toformat)
        if len(grossQ)>1:
            if plot:
                plotting.stormPlot(fmname[-1],date,gageName,meanFile,hourlyFile[count],flowFile,diameterFile,format=toformat)
                plt.show()
            delta = 15.0/24/60 # conversion from measurement increments to days for volume calculation
            grossVol.extend([delta*ww.abstrapz(grossQ)])
            # find dmax, t_dmax, and d_(1/3)
            
        else:
            grossVol.extend(grossQ)
        
        dmax,t_dmax,dOneThird = ww.findDmax(flowFile=flowFile,date=date)
        dmaxAll.extend([dmax])
        t_dmaxAll.extend([t_dmax])
        dOneThirdAll.extend([dOneThird])
    count += 1
    dfgrossII = pd.DataFrame({str(date): grossVol},index=fmname)
    dfdMax = pd.DataFrame({str(date): dmaxAll},index=fmname)
    dftimedMax = pd.DataFrame({str(date): t_dmaxAll},index=fmname)
    dfdOneThird = pd.DataFrame({str(date): dOneThirdAll},index=fmname)