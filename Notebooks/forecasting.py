# -*- coding: utf-8 -*-
"""Forecasting.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1FbfeACMc1EAR3mbrU6dmjQr1IP1mWRbz

# Time Series
In the following notebook I will a train a model in order to forecast the total expenditure of Schools Directature

## Requirements
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from google.colab import drive
import joblib
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from lightgbm import LGBMRegressor
from sklearn.kernel_ridge import KernelRidge

"""# Data Review"""

drive.mount('/content/drive/')
folder_path = '/content/drive/MyDrive/Globant/Data/'
df = pd.read_csv(folder_path+'clean_data.csv', sep ='|')

#I filter only the category I'm interested and remove the negative transactions
df = df[df['DIRECTORATE'] == 'SCHOOLS']
df = df[df['ORIGINAL GROSS AMT']>0 ]

df

#I create the data frame I'm going to use and add aditional features
df_forecast = df.groupby('TRANS DATE').agg(total_expend = ('ORIGINAL GROSS AMT', np.sum)).reset_index().sort_values('TRANS DATE', ascending = True)
df_forecast['TRANS DATE'] = pd.to_datetime(df_forecast['TRANS DATE'], dayfirst = False)
df_forecast['dayofweek'] = df_forecast['TRANS DATE'].dt.dayofweek
df_forecast['quarter'] = df_forecast['TRANS DATE'].dt.quarter
df_forecast['month'] = df_forecast['TRANS DATE'].dt.month
df_forecast['year'] = df_forecast['TRANS DATE'].dt.year
df_forecast['dayofyear'] = df_forecast['TRANS DATE'].dt.dayofyear
df_forecast['dayofmonth'] = df_forecast['TRANS DATE'].dt.day
df_forecast['weekofyear'] = df_forecast['TRANS DATE'].dt.isocalendar().week

df_forecast.head()

fig = go.Figure([go.Scatter(x=df_forecast['TRANS DATE'], y=df_forecast['total_expend'])])
fig.show()

"""## Train/Test and Standarization"""

df_forecast.columns

df_forecast

#test with the last two months of the dataset
train = df_forecast.iloc[:320]
test = df_forecast.iloc[320:]
x = ['dayofweek', 'quarter', 'month', 'year','dayofyear', 'dayofmonth', 'weekofyear']
y = 'total_expend'

x_train = train[x]
y_train = train[y]
x_test = test[x]
y_test = test[y]

stnd_scl = StandardScaler()
x_train[x] = stnd_scl.fit_transform(x_train[x])
x_test[x] = stnd_scl.transform(x_test[x])

joblib.dump(stnd_scl, '/content/drive/MyDrive/Globant/Models/scaler_forecast.pkl')

"""#Models
I'm going to evaluate three models:

* LGBMRegressor
* XGBRegressor
* RidgeRegressor

 The model with less errors (RMSE) will be chosen


"""

xgb_model = xgb.XGBRegressor(booster='gbtree', objective='reg:linear', random_state=18)
lgbm_model = LGBMRegressor(random_state=18)
ridge_model = KernelRidge(kernel = 'rbf')

xgb_model.fit(x_train, y_train)
ridge_model.fit(x_train, y_train)
lgbm_model.fit(x_train, y_train)

pred_xgb_model = xgb_model.predict(x_test)
pred_ridge_model = ridge_model.predict(x_test)
pred_lgbm_model = lgbm_model.predict(x_test)

def eval_metrics(real, pred):
    rmse_ = np.sqrt(mean_squared_error(real, pred))
    mae = mean_absolute_error(real, pred)
    r2 = r2_score(real, pred)
    return print('rmse: ', rmse_, '\n',
                    'mae: ', mae, '\n',
                    'r2: ', r2)

print('Ridge')
eval_metrics(y_test, pred_ridge_model)
print('\n')
print('LGBM')
eval_metrics(y_test, pred_lgbm_model)
print('\n')
print('XGB ')
eval_metrics(y_test, pred_xgb_model)

fi = pd.DataFrame(data=lgbm_model.feature_importances_,
             index=lgbm_model.feature_name_,
             columns=['importance'])
fi.sort_values('importance').plot(kind='barh', title='Feature Importance')
plt.show()

joblib.dump(pred_lgbm_model, '/content/drive/MyDrive/Globant/Models/forecast.pkl')

"""Conclusion : The LGBM model is chosen because it has the best metrics/performance"""