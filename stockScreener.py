import requests
import re
import datetime
from bs4 import BeautifulSoup
from statistics import mean

def string_to_int(string):
    #print(string)
    multipliers = {'K':1000, 'M':1000000, 'B':1000000000, 'T':1000000000000}
    if re.match("^-*[0-9]+\.*[0-9]*\w$",string) == None:
        return string
    if string[-1].isdigit(): # check if no suffix
        return string
    mult = multipliers[string[-1]] # look up suffix to get multiplier
     # convert number to float, multiply by multiplier, then make int
    return str(int(float(string[:-1]) * mult))

def getStockData(symbol):
    global headerCount
    url = 'https://www.investagrams.com/Stock/PSE:' + symbol
    req = requests.get(url)
    soup = BeautifulSoup(req.content,'html.parser')
    colHeader=['Symbol']
    rowData=[symbol]
    
    #Current Price
    currentPriceTable=soup.find("div", class_="d-inline-flex")
    currentPriceInfo=currentPriceTable.find("span",id="lblStockLatestLastPrice",class_="mr-2")
    colHeader.append("Close")
    rowData.append(currentPriceInfo.text.strip().replace(',',""))
    
    #Stock Info
    stockInfoTable=soup.find("div" , class_="row m-0 pb-3")
    stockData=stockInfoTable.find_all("tr")
    for data in stockData:
        var=data.find_all("td")
        colHeader.append(var[0].text.strip().strip(':').replace(','," "))
        rowData.append(string_to_int(var[1].text.strip().replace(',',"")))
        
    #Fundamentals
    fundamentalAnalysisTable=soup.find("div", id='FundamentalAnalysisContent')
    stockData=fundamentalAnalysisTable.find_all("tr")
    for data in stockData:
        var=data.find_all("td")
        count=0
        for i in var:
            if count == 0:
                colHeader.append(i.text.strip().strip(':').replace(','," "))
                count = 1
            else:
                rowData.append(string_to_int(i.text.strip().replace(',',"")))
                count = 0
    #Technicals
    technicalAnalysisTable=soup.find("div", id='TechnicalAnalysisContent')
    techTable1=technicalAnalysisTable.find("table", class_="table stock-information-table")
    stockData1=techTable1.find_all("tr")
    for data in stockData1:
        var=data.find_all("td")
        for i in var:
            if count == 0:
                colHeader.append(i.text.strip().strip(':').replace(','," "))
                count = 1
            else:
                rowData.append(string_to_int(i.text.strip().replace(',',"")))
                count = 0
                
    techTable2=technicalAnalysisTable.find_all("table", class_="stock-information-table table table-hover table-bordered")
    maData=[]
    for data2 in techTable2:
        stockData2=data2.find("tbody")
        stockDataTr2=stockData2.find_all("tr")
        for td in stockDataTr2:
            var=td.find_all("td")
            count=0
            flg=None
            for i in var:
                if count == 0:
                    #print(i)
                    cntnt=i.text.strip().strip(':').replace(','," ")
                    flg=re.match("MA .*",cntnt)
                    #print(cntnt)
                    #print('ma' + cntnt)
                    if flg:
                        #print(cntnt)
                        #grp=re.match("(\S+)\s+\(\s+(\S+)\s+\)",cntnt)
                        #maData.append(float(grp.group(1)))
                        colHeader.append(cntnt+','+cntnt+" status")
                    else:
                        #print(cntnt)
                        colHeader.append(cntnt)
                    count = 1
                elif count == 1:
                    
                    cntnt=string_to_int(i.text.strip().replace(',',""))
                    #print(cntnt)
                    #print('ema' + cntnt)
                    if flg:
                        grp=re.match("(\S+)\s+\(\s+(\S+)\s+\)",cntnt)
                        maData.append(float(grp.group(1)))
                        rowData.append(grp.group(1) + ',' + grp.group(2))
                    else:
                        rowData.append(cntnt)
                    count=2
                    
                else:
                    count=0
                    continue
                    
    #Historical
    HistoricalAnalysisTable=soup.find("div", id='HistoricalDataContent')
    histTable1=HistoricalAnalysisTable.find("table", id="HistoricalDataTable")
    stockData1=histTable1.find_all("tr")
    volList=[]
    countBreaker=0
    for data in stockData1:
        var=data.find_all("td")[7].text
        #print(var)
        if countBreaker > 13:
            break
        elif countBreaker == 0:
            countBreaker=countBreaker+1
            continue
        countBreaker=countBreaker+1
        volList.append(string_to_int(var))
    currentVolume=int(volList[0])
    AvgVolume=round(sum([int(i) for i in volList])/(len(volList)-1),1)
    RelativeVolume=round(currentVolume/AvgVolume,2)
    colHeader.append("RVol")
    rowData.append(str(RelativeVolume))
    colHeader.append("RvolIndicator")
    if RelativeVolume >= 2:
        rowData.append("Yes")
    else:
        rowData.append("No")
    #print(RelativeVolume)
        #for i in var:
            #print(i.text.strip())
    
    colHeader.append("AOTS")
    divFlg=0
    if maData[0] == 0 or maData[1] == 0:
        divFlg = 1
    if divFlg==0:
        r1AOTS=(maData[0]-maData[1])/maData[0]
        r2AOTS=(maData[1]-maData[2])/maData[1]
    else:
        r1AOTS=0
        r2AOTS=0
        
    if maData[0] > maData[1] > maData[2] :
        rowData.append("Yes")
    elif maData[0]>maData[1] and maData[1] < maData[2] and (abs(r2AOTS)<=0.02):
        rowData.append("Buy in Tranches")
    elif maData[1]>maData[2] and maData[0] < maData[1] and (abs(r1AOTS)<=0.02):
        rowData.append("Buy in Tranches")     
    else:
        rowData.append("No")
        
    #Reversal Golden Cross
    colHeader.append("Reversal")
    r1Flg=0

    if (maData[1] < maData[2] and maData[0] > maData[1]) or (maData[1] > maData[2] and maData[0] < maData[1]) and divFlg==0:
        r1=(maData[0]-maData[2])/maData[0]
        r2=(maData[1]-maData[2])/maData[1]
        if (abs(r1)<=0.02) or (abs(r2)<=0.02):
            #print("Buy in tranches")
            r1Flg=1
            rowData.append("Buy in tranches")
        #print(symbol + " Reversal 1 Candidate")
    if divFlg == 1:
        r3=0
    else:
        r3=(maData[1]-maData[3])/maData[1]
    if (maData[0] > maData[2] and maData[1] > maData[2]) and (abs(r3)<=0.02):
        #print("Reversal soon")
        rowData.append("Reversal soon")
        r1Flg=1
    if r1Flg==0:
        #print("No")
        rowData.append("No")
        
    #MA9/EMA18 with RSI>45
    
    #RSI>50 and EMA9 acted as immediate support
        
    if headerCount==0:
        fh.write(','.join(colHeader))
        fh.write("\n")
        headerCount=1
    fh.write(','.join(rowData))
    fh.write("\n")

def getTop100Value():
    retVal = []
    url = 'https://www.pesobility.com/reports/most-active'
    req = requests.get(url)
    soup = BeautifulSoup(req.content,'html.parser')
    TopTable=soup.find("tbody")
    #type(TopTable)
    TableRows = TopTable.find_all("tr")
    #print(TableRows)
    count = 0
    for row in TableRows:
        details = row.find_all("td")
        if int(details[0].text) <= 150:
            retVal.append(details[1].text.strip())
    return retVal
#Main

#getTop100



headerCount=0
fname="stockScreener"+str(datetime.date.today()) + ".csv"
#fname='testh.csv'
fh=open(fname,"w")

#stockstoCheck=['2GO','8990P','AB','ABA','ABG','ABS','AC','ACE','ACEPH','ACEX','ACR','AEV','AGI','ALCO','ALHI','ALI','ALLHC','ANI','ANS','AP','APC','APL','APO','APX','AR','ARA','AT','ATI','ATN','AUB','AXLM','BC','BCB','BCOR','BCP','BDO','BEL','BH','BHI','BKR','BLFI','BLOOM','BMM','BPI','BRN','BSC','C','CA','CAB','CAT','CDC','CEB','CEI','CEU','CHI','CHIB','CHP','CIC','CIP','CLI','CNPF','COAL','COL','COSCO','CPG','CPM','CPV','CPVB','CROWN','CSB','CYBR','DAVIN','DD','DELM','DFNN','DITO','DIZ','DMC','DMCP','DMW','DNA','DNL','DWC','EAGLE','ECP','EEI','EG','ELI','EMP','EURO','EVER','EW','FAF','FB','FDC','FERRO','FEU','FFI','FGEN','FJP','FLI','FNI','FOOD','FPH','FPI','FRUIT','GEO','GERI','GLO','GMA7','GPH','GREEN','GSMI','HI','HLCM','HOME','HOUSE','HVN','I','ICT','IDC','IMI','IMP','ION','IPM','IPO','IRC','IS','JAS','JFC','JGS','JOH','KEP','KPH','KPPI','LAND','LBC','LC','LCB','LFM','LIHC','LMG','LOTO','LPZ','LR','LRP','LRW','LSC','LTG','MA','MAB','MAC','MACAY','MAH','MAHB','MARC','MAXS','MB','MBC','MBT','MED','MEG','MER','MFC','MFIN','MG','MHC','MJC','MJIC','MPI','MRC','MRSGI','MVC','MWC','MWIDE','MWP','NI','NIKL','NOW','NRCP','OM','OPM','ORE','OV','PA','PAL','PAX','PBB','PBC','PCOR','PERC','PGOLD','PHA','PHES','PHN','PHR','PIP','PIZZA','PLC','PMPC','PNB','PNX','PORT','PPC','PRC','PRIM','PRMX','PSB','PSE','PTC','PX','PXP','RCB','RCI','REG','RFM','RLC','RLT','ROCK','ROX','RRHI','SBS','SCC','SECB','SEVN','SFI','SGI','SGP','SHLPH','SHNG','SLF','SLI','SM','SMC','SMPH','SOC','SPC','SPM','SRDC','SSI','SSP','STI','STR','SUN','T','TBGI','TECH','TEL','TFC','TFHI','TUGS','UBP','UNI','UPM','URC','V','VITA','VLL','VMC','VUL','VVT','WEB','WIN','WLCON','WPI','X','ZHI']
stockstoCheck = getTop100Value()
#stockstoCheck=["MWC","ANI"]
for stock in stockstoCheck:
    print(stock)
    getStockData(stock)
fh.close()