from selenium import webdriver
from selenium.webdriver.support.ui import Select
import time
import pandas as pd 
from openpyxl import workbook
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager

options = webdriver.ChromeOptions()

options.add_argument('--ignore-certificate-errors')
options.add_argument('--incognito')
options.add_argument('--headless')

driver = webdriver.Chrome(ChromeDriverManager().install())
url = 'https://tsec.gov.in/knowPRUrban.se'

driver.get(url)

time.sleep(1)

year_selector = Select(driver.find_element_by_id('year'))
year_selector.select_by_index(1) #1 for 2020, 2 for 2021
time.sleep(1)
election_selector = Select(driver.find_element_by_id('electionFor')) #Election Description selector
election_selector.select_by_index(1) #2 options for 2020, 3 for 2021. Select accordingly

driver.find_element_by_xpath("//input[@value='A']").click() #Select All Contesting Candidates Radio Button


mainlist = [] #parent list to contain data for each row

district_selector = driver.find_element_by_id('district_id') 
district_options = district_selector.find_elements_by_tag_name('option') #get list of all district options

district_list = [] #store district names as labels

for i in range(1, len(district_options)): #write all district names into the list
    district_list.append(district_options[i].text)

for district in range(1, len(district_options)): #For each district
    district_name = district_list[district - 1] #get district name from list

    district_selector2 = Select(driver.find_element_by_id('district_id'))
    district_selector2.select_by_index(district) #actually select the district

    time.sleep(2)

    submit_btn = driver.find_element_by_id('add') #click submit button once to reset the ULB selector
    submit_btn.click()

    time.sleep(2)


    ULB_selector = driver.find_element_by_id('ulb_id')
    ULB_options = ULB_selector.find_elements_by_tag_name('option') #get list of all ULB options

    ULB_list = [] #store ULB names as labels

    for i in range(1, len(ULB_options)):
        ULB_list.append(ULB_options[i].text) #write all ULB names into the list
    
    for ULB in range(1, len(ULB_options)): #For each ULB within the district
        ULB_name = ULB_list[ULB - 1] #get ULB name from list

        ULB_selector2 = Select(driver.find_element_by_id('ulb_id'))
        ULB_selector2.select_by_index(ULB)  #actually select the ULB

        time.sleep(2)

        Ward_selector = driver.find_element_by_id('ward_id')
        Ward_options = Ward_selector.find_elements_by_tag_name('option')  #get list of all Wards options within the ULB

        Ward_list = [] #store Ward numbers as labels

        for i in range(1, len(Ward_options)):
            Ward_list.append(Ward_options[i].text) #write all Ward numbers into the list
        
        for Ward in range(1, len(Ward_options)):
            Ward_name = Ward_list[Ward - 1] #get Ward number from list


            Ward_selector2 = Select(driver.find_element_by_id('ward_id'))
            Ward_selector2.select_by_index(Ward)  #actually select the Ward

            submit_btn = driver.find_element_by_id('add') 
            submit_btn.click() #press Submit button

            time.sleep(1)
            
            try:
                nodata_heading = driver.find_element_by_tag_name('h4') #to check if data is absent. This heading tag is not present on pages with data.
                #print('No Data')

            except:
                maintable = driver.find_elements_by_id('GridView1') 

                repeatrow = [] #to contain labels that are to be repeated for each candidate row in a ward
                repeatrow.append(district_name)
                repeatrow.append(ULB_name)
                repeatrow.append(Ward_name)

                repeating = driver.find_element_by_xpath("//table[@id='GridView1']/tbody/tr[2]/td") #Ward Level general information about reservation, votes etc
                repeatrow.append(repeating.text) 

                allrows = driver.find_elements_by_xpath("//table[@id='GridView1']/tbody/tr") #rows with candidate information

                for i in range(2, len(allrows)): #exclude first row as they are headers
                    celldata = allrows[i].find_elements_by_tag_name('td') #find all cells with text information
                    row_list = []
                    row_list.extend(repeatrow) #append general ward information and labels before adding candidate information to each row

                    for cell in celldata:
                        row_list.append(cell.text) #add candidate information to each row
                    print(row_list)
                    mainlist.append(row_list) #add each row to mainlist

        df = pd.DataFrame(mainlist) #output mainlist dataframe to xlsx after each ULB
        df.to_csv('telangana_scraped_data.csv')
        #print(f'{district_name} - {ULB_name} - {Ward_name}')