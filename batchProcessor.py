from os import walk
from os import makedirs

flowDir = 'P:'+r'\PW-WATER SERVICES'+r'\TECHNICAL SERVICES'+r'\Anna'

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
        break #we only want ot top directory, so break after the first yield

folders,textfiles = findTextFiles(readDir=flowDir)

t = textfiles[0:5] #for testing

for fmData in t:
        #find corresponding folder
        if fmData.startswith('BC') | fmData.startswith('FOR'):
                fmname = fmData.strsplit('_')
                #does the directory exist?
                if fmname not in folders:
                        #make the directory
                        makedirs(flowDir+"\\"+fmname)
                else:
                   pass
                     
        else:
                pass
        print(fmData)