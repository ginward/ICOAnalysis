
# coding: utf-8

# In[28]:

'''
Analysis on how the ownership of a token holder change
'''


# In[29]:

from bs4 import BeautifulSoup
import urllib3
#disable the annoying security warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import re
import pandas
import numpy
from time import sleep
import time
from multiprocessing.dummy import Pool as ThreadPool 
import itertools


# In[30]:

#the base url for etherscan
baseUrl='https://etherscan.io/'
#the connection pool, making 10 connections
pool=urllib3.PoolManager(10)
#number of threads
numthread=8
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
    trans_dic=[
        tx:{
            Value:'', 
            Block:''
        }
    ]
    '''
    trans_dic=[]
    i=1
    while len(nextlinks)>0:
        starttime=time.time()
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
            tmp_dic={}
            if row['Value']!=0:
                if row['direction'] == 'OUT':
                    val=-row['Value']
                else:
                    val=+row['Value']
                tx=row['TxHash']
                tmp_dic[tx]={}
                tmp_dic[tx]['Value']=val
                '''
                Now, get the block number
                '''
                txurl='tx/'
                block=''
                req=pool.request('GET',baseUrl+txurl+tx)
                html_tx=req.data
                tx_soup=BeautifulSoup(html_tx)
                tx_a_tag=tx_soup.find_all('a',href=True)
                for tag in tx_a_tag:
                    if '/block/' in tag['href']:
                        block=str(tag.getText())
                        tmp_dic[tx]['Block']=block
                trans_dic.append(tmp_dic)
        i=i+1
        elapsed=time.time()-starttime
        print str(elapsed)+" second for each request"
    return trans_dic

def tr_wrapper(args):
    tokenname=args[0]
    owners=args[1]
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
    for owner in owners:
        content=[]
        balance=owners[owner]
        trans=trans_history[owner]
        i=0
        for l in trans:
            #The first record
            if i==0:
                entry=[]
                TID='ENDING BALANCE'
                Block='N/A'
                entry.append(Block)
                entry.append(owner)
                entry.append(TID)
                entry.append(tokenname)
                entry.append(balance)
                content.append(entry)
                i=i+1
            for t in l:
                entry=[]
                #transaction ID
                TID=t
                #Block Height
                Block=l[t]['Block']
                entry.append(Block)
                entry.append(owner)
                entry.append(TID)
                entry.append(tokenname)
                entry.append(balance)
                content.append(entry)
                balance=balance-l[t]['Value']
                #The last record
                if i==len(trans):
                    entry=[]
                    TID='BEGINNING BALANCE'
                    Block='N/A'
                    entry.append(Block)
                    entry.append(owner)
                    entry.append(TID)
                    entry.append(tokenname)
                    entry.append(balance)
                    content.append(entry)
        i=i+1
        dataframe=pandas.DataFrame(content, columns=headtable)
        dataframe.to_csv('./csv/'+owner+'top100.csv')
     

def ICO_TOKEN(tokenid, tokenname):
    global numthread
    df=html_convert_top100(tokenid, "table table-hover ")
    '''
    Construct the ownership table
    '''
    owners={}
    for index, row in df.iterrows():
        owners[row['Address']]=row['Quantity (Token)']
    owner_list=[] 
    for key in owners:
        tmp_dict={}
        tmp_dict[key]=owners[key]
        owner_list.append(tmp_dict)
    # make the Pool of workers
    print "starting "+str(numthread)+" threads..." 
    tpool = ThreadPool(numthread)
    tpool.map(tr_wrapper, itertools.izip(itertools.repeat(tokenname), owner_list))
    tpool.close()
    tpool.join()
    
ICO_TOKEN('0x86Fa049857E0209aa7D9e616F7eb3b3B78ECfdb0','EOS')


# In[ ]:



