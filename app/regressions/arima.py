from dateutil.relativedelta import relativedelta
from functools import reduce
from sklearn.metrics import mean_squared_error
from statsmodels.tsa.arima_model import ARIMA
import datetime as dt
import json
import numpy as np
import pandas as pd
import requests
import sys
import warnings

def evaluate_arima_model(X, arima_order):
    # prepare training dataset
    train_size = int(len(X) * 0.66)
    train, test = X[0:train_size], X[train_size:]
    history = [x for x in train]

    # make predictions
    predictions = list()
    for t in range(len(test)):
        model = ARIMA(history, order=arima_order)
        model_fit = model.fit(disp=0)
        yhat = model_fit.forecast()[0]
        predictions.append(yhat)
        history.append(test[t])

    # calculate out of sample error
    error = mean_squared_error(test, predictions)
    return error


'''
Evaluates combinations of p, d and q values for an ARIMA model
'''
def evaluate_models(dataset, p_values, d_values, q_values):
    dataset = dataset
    best_score, best_cfg = float('inf'), None
    for p in p_values:
        for d in d_values:
            for q in q_values:
                order = (p, d, q)
                try:
                    mse = evaluate_arima_model(dataset, order)
                    if mse < best_score:
                        best_score, best_cfg = mse, order
                except:
                    continue
    return (best_cfg)


def arima(API, params):
    r = requests.get(API, params=params) 
    measures = params['measures'].split(',')
    drilldowns = params['drilldowns'].split(',')

    measures = [measures[0]]
    df = pd.DataFrame(r.json()['data'])
    n_pred = 5 if params.get('pred') == None else int(params.get('pred'))

    # needed if the data comes with month names instead of numbers
    months = {'January':1, 'February':2, 'March':3, 'April':4, 'May':5, 'June':6, 'July':7, 'August':8, 'September':9, 'October':10, 'November':11, 'December':12}

    # Change format for date
    if 'Month' in drilldowns[0]:
        df['Month'] = df['Month'].map(months)
        df['Date'] = pd.to_datetime(df[['Year', 'Month']].assign(DAY=1))
        df['Date'] = df['Date'].dt.strftime('%Y-%m')
        
        X = pd.DataFrame(df, columns=measures).set_index(df['Date']).astype(float)
    
        rng = pd.date_range(df['Date'].iloc[-1], periods=n_pred+1, freq='MS').tolist()
        rng2 = rng[1:]
        list_pred = [d.strftime('%Y-%m') for d in rng2]
        
    elif 'Year' in drilldowns[0]:
        df['Date'] = pd.to_numeric(df['Year'], errors='coerce').astype('Int32')
        X = pd.DataFrame(df, columns=measures).set_index(df['Date'])
        list_pred = list(range(df['Date'].iloc[-1]+1, df['Date'].iloc[-1]+n_pred+1))            
        

    data2 = pd.DataFrame()
    info_final = pd.DataFrame()

    if len(drilldowns) > 1:
        items = df[drilldowns[1]].unique()

        for item in items:
            df_temp = df.loc[df[drilldowns[1]] == item]
            id_val = df_temp[drilldowns[1] + ' '+ 'ID'].loc[df_temp[drilldowns[1]]==item]
            # needed to get the best parameters for arima
            if (params.get('args') == None):
                p_values = range(2)
                d_values = range(2)
                q_values = range(2)
                warnings.filterwarnings('ignore')
                best_cfg = evaluate_models(
                    df_temp[measures].values, p_values, d_values, q_values)
            else:
                best_cfg = eval(params['args'])
            
            model = ARIMA(df_temp[measures], order=(best_cfg))
            results = model.fit(disp=0)
            predict = results.predict(start=1, end=len(df_temp))

            forecast, strderr, conf_int = results.forecast(steps=n_pred)

            # Predicted values in sample
            predict_df = pd.DataFrame({measures[0]: df_temp[measures].values.reshape(len(df_temp[measures].values),), measures[0] + ' Prediction': predict,
                                       measures[0] + ' Lower Bound': np.nan,
                                       measures[0] + ' Upper Bound': np.nan, drilldowns[1]: item, drilldowns[1] + ' ' + 'ID': id_val.values[0]})
            predict_df['Date'] = df['Date']   
            
            # Forecasted values out of sample
            forecast_df = pd.DataFrame({measures[0] + ' Prediction': forecast,
                                        measures[0] + ' Lower Bound': conf_int.flatten()[::2],
                                        measures[0] + ' Upper Bound': conf_int.flatten()[1::2], drilldowns[1]: item, drilldowns[1] + ' ' + 'ID': list(df[drilldowns[1]]).index(item)+1})
            forecast_df['Date'] = pd.DataFrame(list_pred)

            df_final = pd.concat([predict_df, forecast_df], ignore_index=False, sort=False)
            data2 = pd.concat([data2, df_final], ignore_index=True, sort=False)
           
            model_info = {
            drilldowns[1] : item,
            'args_used' : [best_cfg],
            'Model_info' : results.model.__class__.__name__,
            'Method' : model.method,
            'No. Observations' : results.nobs,
            'AIC' : results.aic,
            'BIC' : results.bic,
            'HQIC' : results.hqic
            }
            
            info_df = pd.DataFrame(model_info)
            info_final = pd.concat([info_final,info_df],ignore_index=False, sort=False)

    else:

        if (params.get('args') == None):
            p_values = range(2)
            d_values = range(2)
            q_values = range(2)
            warnings.filterwarnings('ignore')
            best_cfg = evaluate_models(X[measures].values, p_values, d_values, q_values)
        else:
            best_cfg = eval(params['args'])

     
        model = ARIMA(X[measures], order=(best_cfg))
        results = model.fit(disp=0)
        results.summary()

        predict = results.predict(start=1, end=len(X))
        forecast, strderr, conf_int = results.forecast(steps=n_pred)

        predict_df = pd.DataFrame({measures[0]: X[measures].values.reshape(len(X[measures].values),), measures[0] + ' Prediction': predict,
                                   measures[0] + ' Lower Bound': np.nan,
                                   measures[0] + ' Upper Bound': np.nan}).reset_index().drop('index',axis=1)
        predict_df['Date'] = df['Date']                    

        forecast_df = pd.DataFrame({measures[0] + ' Prediction': forecast,
                                    measures[0] + ' Lower Bound': conf_int.flatten()[::2],
                                    measures[0] + ' Upper Bound': conf_int.flatten()[1::2]})
        
        forecast_df['Date'] = pd.DataFrame(list_pred)

        df_final = pd.concat([predict_df, forecast_df], ignore_index=False, sort=False)
        
        data2 = data2.merge(df_final, how='outer', left_index=True, right_index=True) 


        model_info = {
            'args_used' : [best_cfg],
            'Model_info' : results.model.__class__.__name__,
            'Method' : model.method,
            'No. Observations' : results.nobs,
            'AIC' : results.aic,
            'BIC' : results.bic,
            'HQIC' : results.hqic
        }
        
        info_df = pd.DataFrame(model_info)
        info_final = pd.concat([info_final, info_df],ignore_index=False, sort=False)

    return {
        'predictions': data2.to_dict(orient='records'),
        'Model_info': info_final.to_dict(orient='records')
    }


if __name__ == '__main__':
    arima('https://api.oec.world/tesseract/data',
          {'drilldowns':'Year,Section','measures':'Trade Value','cube':'trade_s_esp_m_hs','parents':'true','Section':'1,2'})
