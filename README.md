# code_sample
This repo builds a basic data visualisation dashboard for Telangana Municipal Election Data scraped from https://tsec.gov.in/home.do;jsessionid=A0929A7322CB7B00C1F39D16A41304B8 for year 2020 and 2021 across multiple wards and urban local bodies. 

1. telangana_scraped_data.csv --> This file contains the raw data scraped from the above website 
2. data_structure.py --> This script is used to structure the raw scraped data in telangana_scraped_data.csv
3. telangana_primary.csv --> This is the output post structuring which will be used to build the visualisations.
4. viz.py --> This is the script that deploys the Streamlit application, data source telangana_primary.csv
5. Pipfile --> Contains the requirements for Streamlit to build the application. Before building the application from viz.py, streamlit cloud install the requirements mentioned in the Pipfile

Streamlit Visualisation is available at : https://share.streamlit.io/srishti-gupta-me/code_sample/main/viz.py


