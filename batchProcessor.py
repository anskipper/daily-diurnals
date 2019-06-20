from os import walk
from os import makedirs
import diurnal.dryWeather as ddwf
import diurnal.plotting as dplt
import diurnal.wetWeather as ww
import pandas as pd

# set directories, files, etc
flowDir = 'P:\\PW-WATER SERVICES\\TECHNICAL SERVICES\\Anna'
gageFile = flowDir + '\\FMtoRG.txt'
dailyFile = flowDir + '\\RG_daily_20180101-20190331.txt'
hourlyFile = flowDir + '\\RG_hourly_20180101-20190331.txt'
upstreamFile = flowDir + '\\FMtoUpstream.csv'

# set variables
dry = True
rainthresh = 0.1 #in
bufferBefore = 2 #days
bufferAfter = 3 #days

wet = False
net = False

# set plotting parameters
plotDry = False
colorAll = 'xkcd:light grey'
colorWkd = 'xkcd:leaf green'
colorWke = 'xkcd:hunter green'
colorg = 'xkcd:slate blue'
figSize = (12,6)

def findTextFiles(readDir):
    d = []
    f = []
    t = []
    for (root,dirs,files) in walk(readDir,topdown=True):
        d.extend(dirs)
        f.extend(files)
        for x in f:
            if x.endswith('.txt'):
                t.extend([x])
        d = sorted(d)
        t = sorted(t)
        return(d,t)
        #break #we only want ot top directory, so break after the first yield

folders,textfiles = findTextFiles(readDir=flowDir)

# for every flowmeter in text files
for fmData in textfiles: #change t to textfiles after testing
        #find corresponding folder
        if fmData.startswith('BC') | fmData.startswith('FOR') | fmData.startswith('RSPS') :
        #if fmData.startswith('FOR'):
                fmname = fmData.split('_')[0] #think about how to do it for temp fms??
                #does the directory exist?
                if fmname not in folders:
                        #make the directory
                        makedirs(flowDir+"\\"+fmname)
                else:
                   pass
                ####### DIURNAL ANALYSIS #######
                #save all the output files to this directory
                saveDir = flowDir + "\\" + fmname
                flowFile = flowDir + "\\" + fmData
                if dry:
                        # DRY WEATHER ANALYSIS
                        df_flow,df_dryWeekday,df_dryWeekend,gwi,snormWKD,snormWKE,df_csv = ddwf.dryWeatherAnalysis(flowFile=flowFile,fmname=fmname,saveDir=saveDir,gageFile=gageFile,rainFile=dailyFile,rainthresh=rainthresh,bufferBefore=bufferBefore,bufferAfter=bufferAfter)

                        wkdMean =df_dryWeekday.mean(axis=1)
                        wkeMean = df_dryWeekend.mean(axis=1)
                        df = pd.DataFrame(index=wkdMean.index,columns=['Weekday','Weekend'])
                        df['Weekday']=wkdMean
                        df['Weekend']=wkeMean
                        df.index.name = 'Time'
                        saveName = "\\" + fmname + '_meanFlows.csv'
                        df.to_csv(saveDir+saveName)
                ######## PLOTTING ########
                elif plotDry:
                        # plot weekday mean with all weekday curves
                        fig1,ax1 = dplt.plotDiurnalsAll(df=df_dryWeekday,colorAll=colorAll,colorMean=colorWkd, weekCatagory='Weekday', figsize=figSize,df_flow=df_flow,fmName=fmname,saveDir=saveDir)
                        # plot weekend mean with all weekday curves
                        fig2,ax2= dplt.plotDiurnalsAll(df=df_dryWeekend,colorAll=colorAll,colorMean=colorWke, weekCatagory='Weekend', figsize=figSize,df_flow=df_flow,fmName=fmname,saveDir=saveDir)
                        # plot weekday mean with 95% and 5% quantiles
                        fig3,ax3 = dplt.plotQuantileDiurnals(df=df_dryWeekday,figsize=figSize,color=colorWkd, weekCatagory = 'Weekday',upQuantile=0.95,lowQuantile=0.05,df_flow=df_flow,fmName=fmname,saveDir=saveDir)
                        # plot weekend mean with 95% and 5% quantiles
                        fig4,ax4 = dplt.plotQuantileDiurnals(df=df_dryWeekend,figsize=figSize,color=colorWke, weekCatagory = 'Weekend',upQuantile=0.95,lowQuantile=0.05,df_flow=df_flow,fmName=fmname,saveDir=saveDir)
                        # plot the weeekday and weekend curves with GWI
                        fig5, ax5 = dplt.plotTogether(meanLine1=df_dryWeekday.mean(axis=1),meanLine2=df_dryWeekend.mean(axis=1),gwi=gwi,color1=colorWkd,color2=colorWke,colorg = colorg,figsize = (12,6),plotgwi=True,plotType = 'totalFlow',norm=False,saveDir=saveDir,fmname=fmname)
                        # plot the normalized weekday and weekend sanitary flow (Q - GWI)
                        fig6, ax6 = dplt.plotTogether(meanLine1=snormWKD,meanLine2=snormWKE,gwi=gwi,color1=colorWkd,color2=colorWke,colorg = colorg,figsize = (12,6),plotgwi=False,plotType = 'normSanitaryFlow',norm=True,saveDir=saveDir,fmname=fmname)
                ####### WET WEATHER ANALYSIS, GROSS I&I #######
                elif wet:
                        meanFile = saveDir + '\\' + fmname + '_meanFlows.csv'
                        dfStorms = ww.wetWeather(flowFile=flowFile,gageFile=gageFile,dailyFile=dailyFile,hourlyFile=hourlyFile,meanFile=meanFile,fmname=fmname,saveDir=saveDir)        
                elif net:
                        dfStorms = ww.netii(upstreamFile=upstreamFile,fmname=fmname,flowDir=flowDir,files=textfiles)                       
                else:
                        pass
                print(fmname + ' processing complete!')
        else:
                pass