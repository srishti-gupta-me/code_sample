import pandas as pd
import numpy as np
import re

import warnings 
warnings.filterwarnings("ignore")

#Load dataframe
df=pd.read_csv('telangana_scraped_data.csv')

#Renaming columns before structuring
df.rename({'Election Description':'Election_Type','Ward Name':'Ward_Name','ULB Name':'LB_Name','Sl No.':'OSN','Name of the Contesting candidate':'Candidate_Name','Votes Secured':'Votes','Party Affiliation':'Party','3':'info_string'}, axis=1, inplace=True)

#Dropping first column
df.drop('Unnamed: 0', axis=1, inplace=True)

#Describing Poll value, Casual Election means Bye-Election, General Election: 0 and Bye Election: 1
df['Poll']=0
df['Poll']=df['Poll'].mask((df['Election_Type']=='CASUAL ELECTIONS TO MUNICIPALITIES AND MUNICIPAL CORPORATIONS 2021')|(df['Election_Type']=='Casual Elections to GHMC, 2021'),1)

#df['Ward_Name'] contains Ward Number, spliting the info string with '-' and selecting the last item

df['Ward_No']=df['Ward_Name'].str.split('-').str[1]

#Spliting the info_string into relevant columns 
df['Ward_Reservation']=np.nan
df['Total_Electors']=np.nan
df['Valid_Votes']=np.nan
df['Rejected_Votes']=np.nan
df['NOTA_Values']=np.nan

df['Ward_Reservation']=df['info_string'].str.split(',').str[1].str.split(':').str[1].str.strip()

df['Total_Electors']=df['info_string'].str.split(',').str[2].str.split(':').str[1].str.strip()
df['Total_Electors']=df['Total_Electors'].mask(df['Total_Electors']=="--",np.nan)

df['Valid_Votes']=df['info_string'].str.split(',').str[3].str.split(':').str[1].str.strip()

df['Rejected_Votes']=df['info_string'].str.split(',').str[4].str.split(':').str[1].str.strip()

df['NOTA_Values']=df['info_string'].str.split(',').str[5].str.split(':').str[1].str.strip()


#Extracting Ward Name from info_string
df['Ward_Name']=np.nan
df['Ward_Name']=df['info_string'].str.split(',').str[0].str.split('-').str[1].str.strip()
df['Ward_Name']=df['Ward_Name'].mask(df['Ward_Name'].str.isnumeric()==True,np.nan)


#Giving each district a unique code starting from 1 
data={'District':df['District'].unique(),'District_Code':range(1,len(df['District'].unique())+1)}
district=pd.DataFrame(data)

#Merging it to main dataframe df
df=df.merge(district,how='left',on='District')


#Classifying local body into MC: Municipal Corporation and MCL: Municipal Council
df['LB_Type']='MCL'

#Local Body which are Municipal Corporation have 'MC' embedded in the string
df['LB_Type']=df['LB_Type'].mask(df['LB_Name'].str.contains(r'[M][C]')==True,'MC')

#Local Body that does not have 'MC' embedded in the string, but are Municipal Corporation
df['LB_Type']=df['LB_Type'].mask((df['LB_Name'].isin(['Badangpet','Bandlaguda Jagir','Jawaharnagar','Meerpet'])),'MC')


#Giving each Local Body with each LB_type a unqiue number, this will start from 1.
keys=list()
values=list()
#Generating LB_Code for main datatset
df['LB_Dis']=df['District_Code'].astype(str)+'%'+df['LB_Name'].astype(str)+df['LB_Type'].astype(str)

for k in df['LB_Type'].unique(): 
    keys.extend(df.loc[df['LB_Type']==k]['LB_Dis'].unique())
    values.extend(range(1,len(df.loc[df['LB_Type']==k]['LB_Dis'].unique())+1))  
    
#Merging the LB_Code generated into df dataframe

df=df.merge(pd.DataFrame({'LB_Dis':keys,'LB_Code':values}),how='left',on='LB_Dis')


#As each Ward can be recognised only when the Year,Poll are accompanied with the details of the local body it belongs to
#below variable key aims to make a unique identifier for each ward

df['key']=df['Year'].astype(str)+'%'+df['Poll'].astype(str)+'%'+df['LB_Type'].astype(str)+'%'+df['LB_Code'].astype(str)+'%'+df['Ward_No'].astype(str)
df['key']=df['key'].str.replace(' ','').str.strip()



'''
NOTA' is considered as a candidate in election, adding value for NOTA in each ward
Selection first row for each ward, idenitified using 'key' variable
'''

df1=df.drop_duplicates(subset=['key'],keep='first', inplace=False)

df1['Candidate_Name']='NOTA'

#OSN: Original Serial Number
df1['OSN']=np.nan

#Value in column NOTA_Values
df1['Votes']=df['NOTA_Values']

#Party and Status for NOTA will remain np.nan
df1['Party']=np.nan
df1['Status']=np.nan



#Calculating number of candidates in the ward, without taking NOTA in consideration
can={'key':df.groupby(['key'],dropna=False).size().index,'N_Cand':df.groupby(['key'],dropna=False).size().values}
can=pd.DataFrame(can)

#Adding dataset df1 of NOTA, to main dataset df
df=df.append(df1)

#Merging the N_Cand variable in dataframe can to dataframe df
df=df.merge(can,how='left',on='key')

'''
Position value is in accordance with the Votes secured by the candidate, however the NOTA value will 
be given last position in the ward
df1 dataframe selects NOTA candidate
'''

df1=df.loc[df['Candidate_Name']=='NOTA']
df1['Position']=df1['N_Cand']+1


#Dropping NOTA candidate from df dataframe to calculate Position value and will be merged later
df.drop(df1.index,axis=0,inplace=True)

df['Votes']=df['Votes'].astype(float)

df['Position']=df.groupby(['key'],dropna=False)['Votes'].rank(method='first', ascending=False, na_option='bottom')
df['Position']=df['Position'].astype(int)

df=df.append(df1)


# Calculating Total_Votes which is sum of all votes secured in a ward, dataframe total will have key and Total_votes
df['Votes']=df['Votes'].astype(float)

total={'key':df.groupby(['key'],dropna=False)['Votes'].sum().index,'Total_Votes':df.groupby(['key'],dropna=False)['Votes'].sum().values}
total=pd.DataFrame(total)

#Mergigng Total_Votes to df dataframe
df=df.merge(total,how='left',on='key')

#Sorting dataframe
df.sort_values(by=['Year','Poll','LB_Type','LB_Code','Ward_No'], inplace=True)



#Status as Elected should come for Position 1 
k=df.loc[(df['Position']!=1) & (df['Status']=='Elected')]['key']

#Where Position >1 for Status as Elected, candidate with Status==Elected to have Position=1 and others incremented by 1 

for k1 in k:
    for index,row in df.loc[df['key']==k1].iterrows():
        df.loc[index,'Position']=[df.loc[index,'Position']+1 if row['Status']!='Elected' else 1]

df['State_Name']='Telangana'
df['Valid_Votes']=df['Total_Votes']
df['Total_Votes']=df['Total_Votes'].astype(float)+df['Rejected_Votes'].astype(float)

df=df[["State_Name","Year","Poll","District","LB_Type","LB_Code","LB_Name","Ward_Name","Ward_No","Ward_Reservation","OSN","Candidate_Name","Party",
"Votes","Position","Status","N_Cand","Valid_Votes","Rejected_Votes","Total_Votes","Total_Electors"]]

df.to_csv('telangana_primary.csv', index=False)

