# import necessary dependency

# Flask (Server)
from flask import Flask, jsonify, render_template, request, flash, redirect

# SQL Alchemy (ORM)
import sqlalchemy
from sqlalchemy import MetaData
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, desc,select

import pandas as pd
import numpy as np

connect_args={'check_same_thread':False},
#import Hw_15_query
engine = create_engine("sqlite:///DataSets/belly_button_biodiversity.sqlite",echo=True)
 #,connect_args={'check_same_thread':False},poolclass=StaticPool,echo=True)
 
# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

conn = engine.connect()
session = Session(engine)

#name the tables
OTU = Base.classes.otu
Samples = Base.classes.samples
Samples_Metadata = Base.classes.samples_metadata

# Create a MetaData instance
metadata = MetaData()

# reflect db schema to MetaData
metadata.reflect(bind=engine)


dialect = 'sqlite'
port = 3306



#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Database Setup
#################################################

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///DataSets/belly_button_biodiversity.sqlite"

#db = SQLAlchemy(app)


def get_names():
    s=conn.execute("select lowest_taxonomic_unit_found from OTU order by otu_id").fetchall()
    desc_list =[]
    for row in s:
        desc_list.append(row)
    desc_list_json = jsonify(desc_list)
    return (desc_list_json)


def get_otu():
    s=conn.execute("select lowest_taxonomic_unit_found as 'Otu_description' from OTU order by otu_id").fetchall()
    otu_names =[]
    for row in s:
        otu_names.append(row.Otu_description)
    return jsonify(otu_names)


def get_columns():
    #lets grab the column names
    columns = metadata.tables['samples'].columns.keys()
    column_names = columns[1:len(columns)]
    return jsonify(column_names)

def get_otu_id(sample_number):
    query_param = sample_number
    print("query param in get_otu_id is", query_param)
    otu_id=[]
    distribution=[]
    pie_dict =[]

    s = conn.execute("select  otu_id , query_param from samples order by query_param desc").fetchall()
    #print("output of query is",s)
    print("outputin function",s)
    for i in range(len(s[0:15])):
        print(s[i][0])
        print(s[i][1])
        otu_id.append(s[i][0])
        distribution.append(s[i][1])
    pie_dict.append(otu_id)
    pie_dict.append(distribution)
    print(pie_dict)
    return pie_dict

def get_wfreq(otu_id):
    input_bb = otu_id
    search_query=input_bb.split("_")
    query_param=search_query[1]
    print("query param is " , query_param)
    wfreq_data = conn.execute("select WFREQ from samples_metadata where sampleid=?",query_param).fetchone() 
    print("query result is " ,wfreq_data )
    return(wfreq_data[0])
    
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

#################################################
# Routes
#################################################


@app.route("/")
def index():
    return render_template("index.html")
    

@app.route("/names")
def get_columns():
    columns = metadata.tables['samples'].columns.keys()
    column_names = columns[1:len(columns)]
    return jsonify(column_names)

        
@app.route('/otu')
def otu():
    """Return a list of OTU descriptions."""
    results = session.query(OTU.lowest_taxonomic_unit_found).all()

    # Use numpy ravel to extract list of tuples into a list of OTU descriptions
    otu_list = list(np.ravel(results))
    return jsonify(otu_list)


@app.route("/metadata/<sample>")
def get_otu_id(sample):
    query_param=sample
    print("query param is " , query_param)
    """Return the MetaData for a given sample."""
    sel = [Samples_Metadata.SAMPLEID, Samples_Metadata.ETHNICITY,
           Samples_Metadata.GENDER, Samples_Metadata.AGE,
           Samples_Metadata.LOCATION, Samples_Metadata.BBTYPE]
    print("lets query with the param as", query_param)
    #results = conn.execute("select AGE,BBTYPE, ETHNICITY, GENDER , LOCATION from samples_metadata where sampleid=?",query_param).fetchall()
    results = session.query(*sel).\
        filter(Samples_Metadata.SAMPLEID == sample[3:]).all()
    print("query output is ", results)
    # Create a dictionary entry for each row of metadata information
    sample_metadata = {}
    for result in results:
        sample_metadata['SAMPLEID'] = result[0]
        sample_metadata['ETHNICITY'] = result[1]
        sample_metadata['GENDER'] = result[2]
        sample_metadata['AGE'] = result[3]
        sample_metadata['LOCATION'] = result[4]
        sample_metadata['BBTYPE'] = result[5]
        
       
    return jsonify(sample_metadata)


@app.route("/wfreq/<sample>")
def sample_wfreq(sample):
    """Return the Weekly Washing Frequency as a number."""

    # `sample[3:]` strips the `BB_` prefix
    results = session.query(Samples_Metadata.WFREQ).\
        filter(Samples_Metadata.SAMPLEID == sample[3:]).all()
    wfreq = np.ravel(results)

    # Return only the first integer value for washing frequency
    return jsonify(int(wfreq[0]))

#route('/samples/<sample>')
# Return a list of dictionaries containing sorted lists  for `otu_ids`and `sample_values`

@app.route('/samples/<sample>')
def samples(sample):
    """Return a list dictionaries containing `otu_ids` and `sample_values`."""
    stmt = session.query(Samples).statement
    df = pd.read_sql_query(stmt, session.bind)

    # Make sure that the sample was found in the columns, else throw an error
    if sample not in df.columns:
        return jsonify(f"Error! Sample: {sample} Not Found!"), 400

    # Return any sample values greater than 1
    df = df[df[sample] > 1]

    # Sort the results by sample in descending order
    df = df.sort_values(by=sample, ascending=0)

    # Format the data to send as json
    data = [{
        "otu_ids": df[sample].index.values.tolist(),
        "sample_values": df[sample].values.tolist()
    }]
    return jsonify(data)


if __name__ == "__main__":
 
    app.run(debug=True)
    

