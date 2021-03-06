from numpy.core.arrayprint import dtype_is_implied
import streamlit as st
import pandas as pd
import numpy as np
from plotly.tools import FigureFactory as ff
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
import math

import time 
import warnings
warnings.filterwarnings("ignore")

#Function to set page configuration
st.set_page_config(page_title="Election Dashboard", page_icon="📚", layout="wide")

st.header("Telangana Urban Local Body Election Data")

st.markdown('Visualise Party share in the Urban Local Body Elections across the wards.')
st.sidebar.subheader('Select Values')

#Reading data into a dataframe
read_and_cache_csv = st.cache(suppress_st_warning=True)(pd.read_csv)
df = read_and_cache_csv('./telangana_primary.csv', nrows=100000)



#Function to develop Pie Chart on the filtered dataframe
@st.cache
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
    

#Function to develop Bar Chart on the filtered dataframe
@st.cache
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



#Function to calculate the voter turnout in the selected Local Body, calling bar_chart()function on the manipulated dataframe
@st.cache
def voter_turnout(df): 
    df['key']=df['LB_Type'].astype(str)+'_'+df['LB_Code'].astype(str)
    
    df_lb=pd.DataFrame({'key':df.groupby(['key'],dropna=False)['key'].unique().index,'Total_Votes':df.groupby(['key'],dropna=False)['Total_Votes'].sum().values,'Total_Electors':df.groupby(['key'],dropna=False)['Total_Electors'].sum().values})
    
    df_lb['Voter_Turnout_Percentage']=np.nan
    
    df_lb['Voter_Turnout_Percentage']=df_lb['Voter_Turnout_Percentage'].mask(((df_lb['Total_Electors'].isna()==False) |(df['Total_Electors'].astype(float)==0.0)),(df_lb['Total_Votes'].astype(float)*100/df_lb['Total_Electors'].astype(float)))
    
    df_lb=df_lb.merge(df[['LB_Name','key']], how='left', on='key').drop_duplicates()
    return df_lb
    

#Function to calculate the Party occurance count in the filtered dataframe
@st.cache
def party_dynamics(df, chart_title):
     
    dp=pd.DataFrame({'Party':df.groupby(['Party'],dropna=False).count().index,'Total_Count':df.groupby(['Party'],dropna=False)['Party'].count().values})

    dp['Percentage']=(dp['Total_Count']*100/sum(dp['Total_Count'])).round(2)
     
    #For Party where the percentage share of party is less than 1%, it is clubbed under 'Others' category
    
    #Clubbing rows into one 'Others' where Party share is less than 1%
    dp_other=pd.DataFrame({'Party':'Others','Total_Count':[sum(dp[dp['Percentage']<1]['Total_Count'])],'Percentage':[sum(dp[dp['Percentage']<1]['Percentage'])]})
    
    #Filtering dataframe Party Share Percentage is greater than 1%
    dp=dp[dp['Percentage']>=1]
    
    #Consolidating both dataframe into one
    dp=pd.concat([dp,dp_other])
    
    #Calling Pie chart 
    return pie_chart(dp,dp.Party,dp["Percentage"], chart_title)
    


#To monitor session states of variables on the side-bar filter

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



#Sidebar Year filter
filtered_year_list = st.sidebar.multiselect('Year', df['Year'].astype(int).unique())

#Sidebar Poll Filter
filtered_poll_list = st.sidebar.multiselect('Poll', df['Poll'].unique())
st.sidebar.markdown('Poll = 0 : General Election', unsafe_allow_html=True)
st.sidebar.markdown('Poll > 0 : Bye Election', unsafe_allow_html=True)

#Sidebar District filter
filtered_district_list = st.sidebar.multiselect('District', df['District'].unique())

#Sidebar LB Name Filter, allows to filter Local Body based on selected District, as the number of LB_Name are huge, providing all the LB_Name all the time
#may lead unecessary clicks and no data rendered

filtered_LB_Name= st.sidebar.multiselect('Local Body Name', df[df['District'].isin(filtered_district_list)]['LB_Name'].unique())

#Sidebar Number of Candidate filter
Candidate_count = st.sidebar.slider('Number of candidate', value=float(df['N_Cand'].max()), min_value=float(df['N_Cand'].min()), max_value=float(df['N_Cand'].max()), step=float(1))

#Additional feature to the Candidate_count slider, to aid the filtering  
genre = st.sidebar.radio("", ('Greater', 'Lesser', 'Equal'), index=1, help="Select one to filter wards with Number of Candidate greater/lesser/equal to the value")

#All the filters need to be converted into one query statement to filter the dataframe

#Creating query for the Candidate_Count, this query will be merged with all the other filters later 

if st.session_state['Selected_Count']!=Candidate_count:
    st.session_state['Selected_Count']=Candidate_count

if st.session_state['Selected_Genre']!=genre:
    st.session_state['Selected_Genre']=genre
    
if st.session_state['Selected_Genre'] =="Greater":
    query1="(N_Cand>{})".format(st.session_state['Selected_Count'])
elif st.session_state['Selected_Genre'] =="Lesser":
    query1="(N_Cand<{})".format(st.session_state['Selected_Count'])
else:
    query1="(N_Cand=={})".format(st.session_state['Selected_Count'])
    
    
if st.session_state['Selected_Year']!=filtered_year_list:
    st.session_state['Selected_Year']=filtered_year_list
    
if st.session_state['Selected_Poll']!=filtered_poll_list:
    st.session_state['Selected_Poll']=filtered_poll_list

if st.session_state['Selected_District']!=filtered_district_list:
    st.session_state['Selected_District']=filtered_district_list
    
if st.session_state['Selected_LB_Name']!=filtered_LB_Name:
    st.session_state['Selected_LB_Name']=filtered_LB_Name
    



#Taking all the values from the selected filters and making dict to iterate and form a query statement 
filters={'Year':st.session_state['Selected_Year'],'Poll':st.session_state['Selected_Poll'],'District':st.session_state['Selected_District'],'LB_Name':st.session_state['Selected_LB_Name']}

#Making a query statement from each single filter and placing it as an item in the list:values, later query statement which are from empty filters '()' will be removed
values=[]
for i,j in enumerate(filters):
    query='(' +  ' | '.join([f'{j}=={v}' if str(v).isdecimal()==True else f"{j}=='{v}'" for v in filters[j]])  +')'
    values.append(query)
    
    #consolidating all the elements from values list except '()'
    query=' & '.join(i for i in values if len(i)>2)

#concatinating query and query1, if query is emptying, default query statement is query1    
query= query1 if len(query)<1 else query+' & '+query1



#Session state for query
if st.session_state['Selected_Query']!=query:
    st.session_state['Selected_Query']=query
    
#st.write(st.session_state)

#Selecting only selected columns for display

dx=df.loc[:,df.columns.isin(["Year","Poll","District","LB_Type","LB_Name","Ward_No","Ward_Reservation","Candidate_Name","Position","Status","N_Cand"])]

head=st.button("Top 10 rows")
full=st.button('Display full filtered data')


head_placeholder = st.empty()
full_placeholder = st.empty()

head=True


if head:
    full_placeholder.empty()
    try:
        head_placeholder.dataframe(dx.query(st.session_state['Selected_Query']).head(10).style.format(precision=0))
    except:
        head_placeholder.dataframe(dx.head(10).style.format(precision=0))
else:
    pass
    
if full:
    head_placeholder.empty()
    try:
        full_placeholder.dataframe(dx.query(st.session_state['Selected_Query']).style.format(precision=0))
    except:
        full_placeholder.dataframe(dx.style.format(precision=0))
else:
    pass
    
    
    
st.markdown("""<hr/>""", unsafe_allow_html=True)

#Filtered dataframe
filtered_df=df.query(st.session_state['Selected_Query'])
    
    
st.subheader('Party share across all the filtered wards and local bodies')
plot_all_cand= st.container()
col1, col2 = plot_all_cand.columns([5, 5])
col1.plotly_chart(party_dynamics(filtered_df, 'All Contesting Candidates'),use_container_width=False)
col2.plotly_chart(party_dynamics(filtered_df.query('Position==1'),'All Winner'),use_container_width=False)

st.markdown("""<hr/>""", unsafe_allow_html=True)

st.subheader('Party share across all the filtered wards and local bodies for wards reserved for women candidate')
plot_women_cand= st.container()
col3, col4 = plot_women_cand.columns([5, 5])
col3.plotly_chart(party_dynamics(filtered_df[filtered_df['Ward_Reservation'].isin(['BC(W)','U(W)','SC(W)','ST(W)']) ], 'All Women Ward Candidates'),use_container_width=False)
col4.plotly_chart(party_dynamics(filtered_df[filtered_df['Ward_Reservation'].isin(['BC(W)','U(W)','SC(W)','ST(W)'])].query('Position==1'), 'Winners in the women wards' ),use_container_width=False)

st.markdown("""<hr/>""", unsafe_allow_html=True)

st.subheader('Voter Turnout Percentage across all the filtered dataset')

plot_turnout=st.container()
col5,col6,col7 = plot_turnout.columns([1,8,1])
df_lb=voter_turnout(filtered_df.copy())
col6.plotly_chart(bar_chart(df_lb,df_lb.LB_Name,"Voter_Turnout_Percentage","Voter Turnout Percentage in the Selected Local Bodies",
"Local Bodies Name","Voter Turnout Percentage"), use_container_width=True)



