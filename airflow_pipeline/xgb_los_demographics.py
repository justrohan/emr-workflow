from sklearn.preprocessing import LabelBinarizer
import xgboost as xgb
import pandas as pd
import pickle
from workflow_read_and_write import standard_read_from_db, xgb_write_to_db

def make_one_hot(df):

    gender_one_hot = pd.DataFrame()
    gender_one_hot['Male'] = (df['gender'] == 'M').astype(float)
    gender_one_hot['Female'] = (df['gender'] == 'F').astype(float)
    
    lb = LabelBinarizer()
    ethnicity = df['ethnicity']
    eth_df = (pd.DataFrame(lb.fit_transform(ethnicity), columns=lb.classes_,index=df.index))
    
    lb = LabelBinarizer()
    insurance = df['insurance']
    ins_df = (pd.DataFrame(lb.fit_transform(insurance), columns=lb.classes_,index=df.index))

    combined = pd.concat([gender_one_hot, eth_df, ins_df], axis=1)

    demo_one_hot = pd.DataFrame()
    for column in combined.columns:
        new_column = column
        if '[' in new_column:
            new_column = new_column.replace('[', '')
        if ']' in new_column:
            new_column = new_column.replace(']', '')
        if ',' in new_column:
            new_column = new_column.replace(',', '_')
        if ' ' in new_column:
            new_column = new_column.replace(' ', '_')
        demo_one_hot[new_column] = combined[column]

    return demo_one_hot

def train_xgb_model(df, one_hot_df):
    labels = pd.DataFrame(df['los'])
    data = xgb.DMatrix(one_hot_df, label=labels)

    #tuning opportunity (grid search)
    parameters = {
            'booster': 'gbtree', 
            'tree_method':'gpu_hist', 
            'predictor':'gpu_predictor', 
            'subsample':0.5, 
            'sampling_method': 'uniform', 
            'objective':'reg:linear'
            }

    bst = xgb.train(parameters, data)
    
    return bst
    
def add_predictions_column(df, one_hot_df, bst):
    data = xgb.DMatrix(one_hot_df)
    predictions = bst.predict(data)
    df['xgb_demo_ent_pred'] = predictions

    return df

def make_top_n_features(bst, one_hot, n):
    scores = bst.get_score(importance_type='gain')
    #https://stackoverflow.com/questions/613183/how-do-i-sort-a-dictionary-by-value
    scores_sorted = {k: v for k, v in sorted(scores.items(), key=lambda item: item[1])}
    top_n_features = list(scores_sorted)[-n:]
    
    top_n_df = pd.DataFrame()
    for feature in top_n_features:
        top_n_df[feature] = one_hot[feature]
    
    return top_n_df

def make_predictions():
    df_json_encoded = standard_read_from_db('entity_columns')
    df = pd.read_json(df_json_encoded.decode())
    
    one_hot_df = make_one_hot(df)

    bst = train_xgb_model(df, one_hot_df)
    
    df = add_predictions_column(df, one_hot_df, bst)

    top_n_df = make_top_n_features(bst, one_hot_df, 5)

    df_json_encoded = df.to_json().encode()
    top_n_df_json_encoded = top_n_df.to_json().encode()
    bst_pickle = pickle.dumps(bst)

    xgb_write_to_db('demo_xgb_los', df_json_encoded, top_n_df_json_encoded, bst_pickle)
