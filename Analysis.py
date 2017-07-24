
# coding: utf-8

# In[ ]:

'''
Analysis on how the ownership of a token holder change
'''


# In[ ]:

from bs4 import BeautifulSoup
import urllib3
#disable the annoying security warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import re
import pandas
import numpy
from time import sleep


# In[ ]:

#the base url for etherscan
baseUrl='https://etherscan.io/'
#the connection pool
pool=urllib3.PoolManager()
def html_convert_top100(tokenid, classname):
    '''
    Get the top 100 owners of the coin
    '''
    global baseUrl
    global pool
    funUrl_chart='token/tokenholderchart/'
    r=pool.request('GET',baseUrl+funUrl_chart+tokenid)
    html=r.data
    soup = BeautifulSoup(html)
    table = soup.find("table", attrs=classname)
    headings = [th.get_text() for th in table.find("tr").find_all("th")]
    for idx in range(len(headings)):
        headings[idx]=str(headings[idx])
    datasets = []
    for row in table.find_all("tr")[1:]:
        dataset = (td.get_text() for td in row.find_all("td"))
        ls=list(dataset)
        datasets.append(ls)

    '''
    Clean the data
    '''
    for idx in range(len(datasets)):
        for idxx in range(len(datasets[idx])):
            tmp=re.sub(r'\([^)]*\)', '', datasets[idx][idxx])
            tmp=tmp.strip()
            tmp=str(tmp)
            datasets[idx][idxx]=tmp

    '''
    Create pandas dataframe and convert it to float
    '''
    df=pandas.DataFrame(datasets, columns=headings)
    df['Quantity (Token)']=df['Quantity (Token)'].str.replace(',','')
    df['Quantity (Token)']=df['Quantity (Token)'].astype(numpy.float64)
    df['Percentage']=df['Percentage'].str.strip('%')
    df['Percentage']=df['Percentage'].astype(numpy.float64)/100
    return df

def owners_tr(ownerid, tokenname, classname):
    global baseUrl
    global pool
    transUrl='tokentxns?a='
    nextlinks=[]
    nextlinks.append(transUrl+ownerid)
    '''
    trans_dic={
        tx:{
            Value:'', 
            Block:''
        }
    }
    '''
    trans_dic={}
    i=1
    while len(nextlinks)>0:
        print "processing page "+str(i)+" of owner"+ownerid
        link=nextlinks.pop()
        r=pool.request('GET',baseUrl+link)
        html=r.data
        soup = BeautifulSoup(html)
        '''
        Get the next link
        '''
        a_tag=soup.find_all('a', id="ContentPlaceHolder1_HyperLinkNext",href=True)
        if a_tag[0]['href']!='#':
            next_link=a_tag[0]['href']
            nextlinks.append(next_link)
        table = soup.find("table", attrs=classname)
        headings = [th.get_text() for th in table.find("tr").find_all("th")]
        for idx in range(len(headings)):
            headings[idx]=str(headings[idx])
            if headings[idx]=='':
                headings[idx]='direction'
        datasets = []
        for row in table.find_all("tr")[1:]:
            dataset = (td.get_text() for td in row.find_all("td"))
            ls=list(dataset)
            datasets.append(ls)
        '''
        Clean the data
        '''
        for idx in range(len(datasets)):
            for idxx in range(len(datasets[idx])):
                tmp=re.sub(r'\([^)]*\)', '', datasets[idx][idxx])
                tmp=tmp.strip()
                tmp=str(tmp)
                datasets[idx][idxx]=tmp
        '''
        Create pandas dataframe and convert it to float
        '''
        df=pandas.DataFrame(datasets, columns=headings)
        df['Token']=df['Token'].str.upper()
        df=df.loc[df['Token'] == tokenname]
        df['Value']=df['Value'].str.replace(',','')
        df['Value']=df['Value'].astype(numpy.float64)
        for index, row in df.iterrows():
            if row['Value']!=0:
                if row['direction'] == 'OUT':
                    val=-row['Value']
                else:
                    val=row['Value']
                trans_dic[row['TxHash']]={}
                trans_dic[row['TxHash']]['Value']=val
        
        txurl='tx/'
        for tx in trans_dic:
            block=''
            req=pool.request('GET',baseUrl+txurl+tx)
            html_tx=req.data
            tx_soup=BeautifulSoup(html_tx)
            tx_a_tag=tx_soup.find_all('a',href=True)
            for tag in tx_a_tag:
                if '/block/' in tag['href']:
                    block=str(tag.getText())
                    trans_dic[tx]['Block']=block
        i=i+1
        #set a lag here to reduce CPU pressure
        sleep(0.001)
    return trans_dic

def ICO_TOKEN(tokenid, tokenname):

    df=html_convert_top100(tokenid, "table table-hover ")
    '''
    Construct the ownership table
    '''
    owners={}
    for index, row in df.iterrows():
        owners[row['Address']]=row['Quantity (Token)']
    '''
    Construct the ownership transaction table
    '''
    trans_history={}
    for owner in owners:
        trans_history[owner]=owners_tr(owner,tokenname, 'table table-hover ')
    
    '''
    Backout the transaction history
    '''
    headtable=['Block Height', 'Owner', 'TransactionID', 'TOKEN', 'BALANCE']
    content=[]
    o=1
    for owner in owners:
        print "processing owner "+str(o)+" there are total "+len(owners)+" owners"
        balance=owners[owner]
        trans=trans_history[owner]
        for t in trans:
            entry=[]
            #transaction ID
            TID=t
            #Block Height
            Block=trans[t]['Block']
            balance=balance-trans[t]['Value']
            entry.append(Block)
            entry.append(owner)
            entry.append(TID)
            entry.append(tokenname)
            entry.append(balance)
            content.append(entry)
        o=o+1
    dataframe=pandas.DataFrame(content, columns=headtable)
    return dataframe
    
datahistory=ICO_TOKEN('0x86fa049857e0209aa7d9e616f7eb3b3b78ecfdb0','EOS')
datahistory.to_csv('top100.csv')

