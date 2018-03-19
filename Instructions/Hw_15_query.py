
# coding: utf-8

# In[1]:


# Import our dependencies
import pandas as pd
import os
from pathlib import Path
import csv
import matplotlib.pyplot as plt
import numpy as np
from flask import jsonify
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy


# In[2]:


# Dependencies and boilerplate
import sqlalchemy
from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import MetaData
from sqlalchemy import create_engine,inspect, MetaData


# In[3]:


# Create engine using the database file
engine = create_engine("sqlite:///Instructions/DataSets/belly_button_biodiversity.sqlite",echo=True)
# Declare a Base using `automap_base()
Base = automap_base()

# Use the Base class to reflect the database tables
Base.prepare(engine, reflect=True)

# Create a MetaData instance
metadata = MetaData()

# reflect db schema to MetaData
metadata.reflect(bind=engine)

#name the tables
Otu = Base.classes.otu
Samples = Base.classes.samples
Samples_Metadata = Base.classes.samples_metadata


# In[4]:


inspector = inspect(engine)
inspector.get_table_names()


# In[5]:


conn = engine.connect()
print(conn)


# In[6]:


def get_columns():
    #lets grab the column names
    columns = metadata.tables['samples'].columns.keys()
    column_names = columns[1:len(columns)]
    return (column_names)

test_column_name = get_columns()
#print(test_column_name)

df = pd.Series((test_column_name[0:] for name in test_column_name))
df.head()


# In[7]:


#conn.execute("select lowest_taxonomic_unit_found from OTU Limit 5 ").fetchall()


# In[8]:


def get_otu_desc():
    s=conn.execute("select lowest_taxonomic_unit_found from OTU order by otu_id").fetchall()
    names = [row[0] for row in s]
    return (names)

test_desc = get_otu_desc()
#print(test_desc)


# In[9]:


def get_metadata(sample_number):
    query_param = sample_number[3:]
    
    #print(query_param)
    s = conn.execute("select AGE,BBTYPE, ETHNICITY, GENDER , LOCATION from samples_metadata where sampleid=?",query_param).fetchall()
    print("output of query is",s)
     
    
       
    bb_metadata={"Age" : s[0][0],
                 "BBTYPE":s[0][1],
                 "ETHNICITY":s[0][2],
                 "GENDER":s[0][3],
                 "LOCATION":s[0][4],
                 "SAMPLEID":query_param
                }
    return(bb_metadata)


# In[10]:


test_metadata = get_metadata('BB_948')
print(test_metadata)


# In[11]:


def get_wfreq(otu_id):
    input_bb = otu_id
    search_query=input_bb.split("_")
    query_param=search_query[1]
    wfreq_data = conn.execute("select WFREQ from samples_metadata where sampleid=?",query_param).fetchone() 
    return(wfreq_data[0])





# In[12]:


test_metadata = get_wfreq('BB_940')
print(test_metadata)


# In[23]:


def get_otu_id(sample_number):
    query_param = sample_number
    otu_id=[]
    distribution=[]
    pie_dict =[]

    #print(query_param)
    s = conn.execute("select  otu_id , BB_940 from samples order by BB_940 desc").fetchall()
    #print("output of query is",s)
    print("outputin function",s[0:15])
    for i in range(len(s[0:15])):
        print(s[i][0])
        print(s[i][1])
        otu_id.append(s[i][0])
        distribution.append(s[i][1])
    pie_dict.append(otu_id)
    pie_dict.append(distribution)
    print(pie_dict)
    return pie_dict
    
      
 


# In[24]:


test_dict = get_otu_id('BB_940')


# In[25]:


#Create a PIE chart that uses data from your routes /samples/<sample> and /otu to display the top 10 samples.
#Use the Sample Value as the values for the PIE chart -
#Use the OTU ID as the labels for the pie chart
#Use the OTU Description as the hovertext for the chart

otu_id = get_otu_id('BB_940')[0]
print(otu_id)
descrip = get_otu_id('BB_940')[1]
print(descrip)

