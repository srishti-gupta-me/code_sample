from numpy.core.arrayprint import dtype_is_implied
import streamlit as st
import pandas as pd
import numpy as np
from plotly.tools import FigureFactory as ff
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
import math
from PIL import Image


import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="Election Dashboard", page_icon="📚", layout="wide")
#This streamlit library function sets the page title as evident on the tab where the application is running and the favicon

st.header("Telangana Urban Local Body Election Data")
st.sidebar.subheader('Select Values')


read_and_cache_csv = st.cache(suppress_st_warning=True)(pd.read_csv)
#df = read_and_cache_csv('/home/srishti/code_sample/tl.csv', nrows=100000)
df = read_and_cache_csv('./tl.csv', nrows=100000)


def pie_chart(dp, labels, value, chart_title):
    fig = px.pie(
        dp, 
        names=labels, 
        values=value, 
        title=chart_title,
        color_discrete_sequence=px.colors.qualitative.Bold
    )

    fig.update_layout(
    title={
        'text': chart_title,
        'y':0.9,
        'x':0.5,
        'xanchor':'center',
        'yanchor':'top'})

    return fig.update_traces(
        hoverinfo="label+percent",
        textinfo="value",
        insidetextfont=dict(
            color="white"
        ),
    )


def bar_chart(df,x_var,y_var, title="", x_axis_title="",y_axis_title=""):
    fig = px.bar(
        df,
        x=x_var,
        y=y_var,
        title=title
    )

    fig.update_layout(
        autosize=False,
        height=600,
        title={
        'text': title,
        'y':0.9,
        'x':0.5,
        'xanchor':'center',
        'yanchor':'top'}
    )

    fig.update_xaxes(
        title=x_axis_title,
    )

    fig.update_yaxes(
        title=y_axis_title,
        showgrid=False,
    )


    return fig.update_traces(
        hoverinfo="text",
        insidetextfont=dict(
            color="white"
        ),
    )



def voter_turnout(df): 
    df['key']=df['LB_Type'].astype(str)+'_'+df['LB_Code'].astype(str)
    df_lb=pd.DataFrame({'key':df.groupby(['key'],dropna=False)['key'].unique().index,'Total_Votes':df.groupby(['key'],dropna=False)['Total_Votes'].sum().values,'Total_Electors':df.groupby(['key'],dropna=False)['Total_Electors'].sum().values})
    df_lb['Voter_Turnout_Percentage']=np.nan
    df_lb['Voter_Turnout_Percentage']=df_lb['Voter_Turnout_Percentage'].mask(df_lb['Total_Electors'].isna()==False,(df_lb['Total_Votes']*100/df_lb['Total_Electors']))
    df_lb=df_lb.merge(df[['LB_Name','key']], how='left', on='key').drop_duplicates()
    
    return bar_chart(df_lb,df_lb.LB_Name,"Voter_Turnout_Percentage","Voter Turnout Percentage in the Selected Local Bodies","Local Bodies Name","Voter Turnout Percentage")
    
    


def party_dynamics(df, chart_title):
     
    dp=pd.DataFrame({'Party':df.groupby(['Party_Abbreviation'],dropna=False).count().index,'Total_Count':df.groupby(['Party_Abbreviation'],dropna=False)['Party_Abbreviation'].count().values})

    dp['Percentage']=(dp['Total_Count']*100/sum(dp['Total_Count'])).round(2)

    dp_other=pd.DataFrame({'Party':'Others','Total_Count':[sum(dp[dp['Percentage']<1]['Total_Count'])],'Percentage':[sum(dp[dp['Percentage']<1]['Percentage'])]})

    dp=dp[dp['Percentage']>=1]

    dp=pd.concat([dp,dp_other])
    
    return pie_chart(dp,dp.Party,dp["Percentage"], chart_title)
    



if 'Selected_Year' not in st.session_state:
    st.session_state['Selected_Year']=df['Year'].unique()
    
if 'Selected_Poll' not in st.session_state:
    st.session_state['Selected_Poll']=df['Poll'].unique()
     
if 'Selected_District' not in st.session_state:
    st.session_state['Selected_District']=df['District'].unique()
    
    
if 'Selected_LB_Name' not in st.session_state:
    st.session_state['Selected_LB_Name']=df['LB_Name'].unique()
    
if 'Selected_Count' not in st.session_state:
    st.session_state['Selected_Count']=df['N_Cand'].max()
    
if 'Selected_Genre' not in st.session_state:
    st.session_state['Selected_Genre']="Lesser"
    
if 'Selected_Query' not in st.session_state:
    st.session_state['Selected_Query']='(Year==2020) | (Year==2021)'



filtered_year_list = st.sidebar.multiselect('Year', df['Year'].astype(int).unique())
#filtered_data=df[df['Year'].isin(filtered_year_list)]

if st.session_state['Selected_Year']!=filtered_year_list:
    st.session_state['Selected_Year']=filtered_year_list
    
    
filtered_poll_list = st.sidebar.multiselect('Poll', df['Poll'].unique())
st.sidebar.markdown('Poll = 0 : General Election', unsafe_allow_html=True)
st.sidebar.markdown('Poll > 0 : Bye Election', unsafe_allow_html=True)

if st.session_state['Selected_Poll']!=filtered_poll_list:
    st.session_state['Selected_Poll']=filtered_poll_list
    
filtered_district_list = st.sidebar.multiselect('District', df['District'].unique())

if st.session_state['Selected_District']!=filtered_district_list:
    st.session_state['Selected_District']=filtered_district_list
    
  
filtered_LB_Name= st.sidebar.multiselect('Local Body Name', df['LB_Name'].unique())

if st.session_state['Selected_LB_Name']!=filtered_LB_Name:
    st.session_state['Selected_LB_Name']=filtered_LB_Name
    
    
Candidate_count = st.sidebar.slider('Number of candidate', value=float(df['N_Cand'].max()), min_value=float(df['N_Cand'].min()), max_value=float(df['N_Cand'].max()), step=float(1))

if st.session_state['Selected_Count']!=Candidate_count:
    st.session_state['Selected_Count']=Candidate_count

genre = st.sidebar.radio("", ('Greater', 'Lesser', 'Equal'), index=1, help="Select one to filter wards with Number of Candidate greater/lesser/equal to the value")
if st.session_state['Selected_Genre']!=genre:
    st.session_state['Selected_Genre']=genre


if st.session_state['Selected_Genre'] =="Greater":
    query1="(N_Cand>{})".format(st.session_state['Selected_Count'])
    
elif st.session_state['Selected_Genre'] =="Lesser":
    query1="(N_Cand<{})".format(st.session_state['Selected_Count'])
else:
    query1="(N_Cand=={})".format(st.session_state['Selected_Count'])



filters={'Year':st.session_state['Selected_Year'],'Poll':st.session_state['Selected_Poll'],'District':st.session_state['Selected_District'],'LB_Name':st.session_state['Selected_LB_Name']}

values=[]

for i,j in enumerate(filters):
    query='(' +  ' | '.join([f'{j}=={v}' if str(v).isdecimal()==True else f"{j}=='{v}'" for v in filters[j]])  +')'
    values.append(query)
    
    query=' & '.join(i for i in values if len(i)>2)
    
query= query1 if len(query)<1 else query+' & '+query1


    
#st.text(query)


if st.session_state['Selected_Query']!=query:
    st.session_state['Selected_Query']=query
    

#st.write(st.session_state)

dx=df.loc[:,df.columns.isin(["Year","Poll","District","LB_Type","LB_Name","Ward_No","Ward_Reservation","Candidate_Name","Position","Status","N_Cand"])]

try:
    st.write(dx.query(st.session_state['Selected_Query']).style.format(precision=0))

except:
    st.write(dx.style.format(precision=0))
 

    
plot_all_cand= st.container()

col1, col2 = plot_all_cand.columns([5, 5])

col1.plotly_chart(party_dynamics(df.query(st.session_state['Selected_Query']), 'All Contesting Candidates'))

col2.plotly_chart(party_dynamics(df.query(st.session_state['Selected_Query']).query('Position==1'),'All Winner'))


plot_women_cand= st.container()
col3, col4 = plot_women_cand.columns([5, 5])

filtered_df=df.query(st.session_state['Selected_Query'])

col3.plotly_chart(party_dynamics(filtered_df[filtered_df['Ward_Reservation'].isin(['Backward Classes (Women)','Unreserved (Women)','Scheduled Caste (Women)','Scheduled Tribe (Women)']) ], 'All Women Ward Candidates'))

col4.plotly_chart(party_dynamics(filtered_df[filtered_df['Ward_Reservation'].isin(['Backward Classes (Women)','Unreserved (Women)','Scheduled Caste (Women)','Scheduled Tribe (Women)']) ].query('Position==1'), 'Winners in the women wards' ))




plot_turnout=st.container()

col5, col6 = plot_turnout.columns([4,1])
col5.plotly_chart(voter_turnout(filtered_df.copy()))


