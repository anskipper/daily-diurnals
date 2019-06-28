import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt

homeDir = 'P:\\PW-WATER SERVICES\\TECHNICAL SERVICES\\Anna'
filename = homeDir + '\\Storm Analysis\\netii_comp.csv'
dfnetII = pd.read_csv(filename)
stormDate = dt.datetime(2019,6,8)
print(dfnetII.columns)

figComp1,axComp1 = plt.subplots()
dfnetII.sort_values(by=str(stormDate.date()),ascending=True,inplace=True)
# SPLIT INTO TWO #
dfnetII.iloc[0:len(dfnetII.index)/2,:].plot.barh(figsize=(7.5,12.5),ax=axComp1)
axComp1.set_xlabel('Net I&I (MG)')
axComp1.set_xscale('log')
axComp1.grid()
plt.savefig(homeDir + '\\Storm Analysis\\netii_compHigh.png')

figComp2,axComp2 = plt.subplots()
dfnetII.iloc[len(dfnetII.index)/2+1:,:].plot.barh(figsize=(7.5,12.5),ax=axComp2)
axComp2.set_xlabel('Net I&I (MG)')
axComp2.set_xscale('log')
axComp2.grid()
plt.savefig(homeDir + '\\Storm Analysis\\netii_compLow.png')
