import pymongo
import gridfs
import pandas as pd
import numpy as np
import datetime
from workflow_read_and_write import standard_read_from_db, standard_write_to_db

def add_los_age_and_binary_deathtime_columns(df):
    los_list = []
    age_list = []
    for i, row in df.iterrows():
        admit = pd.to_datetime(row['admittime'])
        discharge = pd.to_datetime(row['dischtime'])

        los_timedelta = discharge - admit
        los_days_int = los_timedelta.days
        los_list.append(abs(los_days_int))

        dob = pd.to_datetime(row['dob'])
        age = float(admit.year - dob.year)
        #patients older than 89 had their age shifted 300 years to follow HIPAA in MIMIC, the median age for this group is 91.4
        if age > 150:
            age = 91.4
        age_list.append(age)

    df['los'] = los_list
    df['death_time_present'] = df['deathtime'].notnull()
    df['age'] = age_list

    return df

def compare_times_for_readmission(row_admittime, sub_row_dischtime):
    readmit_threshold = pd.to_timedelta('30 days 00:00:00')
    zero_timedelta = pd.to_timedelta('0 days 00:00:00')
    
    time_between_visits = row_admittime - sub_row_dischtime

    readmit = False
    #first conditional statement filters out future subrow visits from the current row
    if time_between_visits >= zero_timedelta and time_between_visits <= readmit_threshold:
        readmit = True

    return readmit

def add_readmission_column(df):
    readmit_list = []
    readmit_threshold = pd.to_timedelta('30 days 00:00:00')
    zero_timedelta = pd.to_timedelta('0 days 00:00:00')
    for i, row in df.iterrows():
        current_admittime = pd.to_datetime(row['admittime'])
        
        patient_id = row['patient_id'] 
        is_patient = df['patient_id'] == patient_id
        same_patient_df = df[is_patient]

        readmit = False
        for i, subrow in same_patient_df.iterrows():
            #don't compare the row to itself
            if subrow['admission_id'] != row['admission_id']:
                sub_dischtime = pd.to_datetime(subrow['dischtime'])
                readmit = compare_times_for_readmission(current_admittime, sub_dischtime)
        readmit_list.append(readmit)
    df['readmission'] = readmit_list
    return df

def create_structured_data_features():
    df_json_encoded = standard_read_from_db('first_dataframe')
    df_json = df_json_encoded.decode()
    df = pd.read_json(df_json)

    df = add_los_age_and_binary_deathtime_columns(df)
    df = add_readmission_column(df)
    
    df_json = df.to_json()
    df_json_encoded = df_json.encode()
    standard_write_to_db('structured_data_features', df_json_encoded)

