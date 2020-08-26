import simplejson as json
import sys
import requests 
import pandas as pd 
from base import BaseClass, API, CUBES_API

def yn(x):
    value = x and x in ["true", "1", True]
    return value or False

params = json.loads(sys.argv[1]) # Query params

class Summary:
    def __init__(self, name):
        self.name = name

        # Gets custom params.
        window = params.get("window")
        prediction = params.get("prediction")
        periods = params.get("periods")

        self.window = int(window) if window else 3 # @param
        self.prediction = yn(prediction) if prediction else False
        self.periods = int(periods) if periods else None

    def call(self):
        """
        Dynamically, call each endpoint of complexity.
        Internally, each function that is related to an endpoint must to start with "_".
        Returns: 
            Complexity's function is invoked.
        """
        def func_not_found():
            print(f"No Function {self.name} Found!")
        func_name = f"_{self.name}"
        func = getattr(self, func_name, func_not_found) 
        func()

    def _rolling(self):
        api = requests.get(API, params=params)

        #params
        measure = params["measures"].split(",")[0]
        drilldowns = params["drilldowns"].split(",")
        type_time = ["Year", "Quarter", "Month", "Day"]

        # Get variables from Class
        window = self.window
        prediction = self.prediction
        periods = self.periods
        #raise Exception(periods)

        if(len(drilldowns) == 2):
            period = list(set(drilldowns).intersection(type_time))[0] 
            period_id = period if period == "Year" else period + " ID"
            index = 0 if drilldowns.index(period) else 1
            parameters = drilldowns[index]
            parameters_id = parameters + " ID"

        else: 
            parameters = drilldowns[0] 
            parameters_id = drilldowns[0] if drilldowns[0] == "Year" else drilldowns[0] + " ID"
            
        def fill_missing(period, parameters_id, df, list_params): 
            #fill missing rows in dataframe
            df_new_index = df.set_index(list_params)
            new_index = pd.MultiIndex.from_product(df_new_index.index.levels)
            new_df = df_new_index.reindex(new_index)

            df_complete = new_df.fillna(0)
            df_complete = df_complete.reset_index()
            df_complete = df_complete.rename(columns = {"level_0": period, "level_1": parameters_id}) if len(list_params) <= 2 else df_complete.rename(columns = {"level_0": "Year", "level_1": period, "level_2": parameters_id})
            
            #sort variable
            df_complete = df_complete.sort_values(by=[period, parameters_id], ascending=[True, True])

            return df_complete
        
        #Read api
        df = pd.DataFrame(api.json()["data"])
        
        #only Year
        if((len(drilldowns) == 1) & (parameters_id == "Year")):
            #if want to predict
            long = 2 if prediction == True else 1
            list_complete = list(range(min(df[parameters]), max(df[parameters])+long))

            #complete missing years
            if list_complete != list(df[parameters]):
                time_missing = list(set(list_complete).difference(set(df[parameters])))
                for k in range(len(time_missing)):
                    df = df.append({parameters : time_missing[k], measure: 0} , ignore_index=True)
            
            #sort variable
            df = df.sort_values(by=parameters, ascending=True)
            
            #rolling mean
            df["Trade Value Rolling Mean"] = df[measure].rolling(window=window,min_periods=periods,center=False).mean() 
            df["Trade Value Rolling Mean"] = df["Trade Value Rolling Mean"].shift(1) if prediction == True else df["Trade Value Rolling Mean"]
            df_final = df.dropna().reset_index(drop=True) 
        
        #only time != Year 
        elif((len(drilldowns) == 1) & (parameters_id != "Year")):
            #last dataframe
            last_data = max(df[df["Year"] == max(df["Year"])][parameters_id])
            last_data = last_data+1 if prediction == True else last_data
            
            #complete dataframe
            list_time = ["Year", parameters_id]
            df_complete = fill_missing("Year", parameters_id, df, list_time)
            
            #rolling mean
            df_complete["Trade Value Rolling Mean"] = df_complete[measure].rolling(window=window,min_periods=periods,center=False).mean() 
            df_complete["Trade Value Rolling Mean"] = df_complete["Trade Value Rolling Mean"].shift(1) if prediction == True else df_complete["Trade Value Rolling Mean"]
            df_rolling = df_complete.dropna().reset_index(drop=True) 
            df_final = df_rolling.drop(df_rolling[(df_rolling["Year"] == max(df_rolling["Year"])) & (df_rolling[parameters_id] > last_data)].index)
            
            #prediction
            if prediction == True:
                df_index = df[[parameters_id, parameters]].drop_duplicates()
                df_final = df_final.drop(columns = ["Quarter", "Quarter ID", parameters]) if parameters == "Month" else df_final.drop(columns = [parameters])
                df_final = df_final.merge(df_index, left_on=parameters_id, right_on=parameters_id, how="left")
        
        #Zone + time != Year
        elif((len(drilldowns) == 2) & (period != "Year")):
            #Create dataframe with zones 
            df_index = df[[parameters_id, parameters]].drop_duplicates()
            df_index_time = df[[period_id, period]].drop_duplicates()

            #fill missing rows
            list_params = ["Year", period_id, parameters_id]
            df_complete = fill_missing(period_id, parameters_id, df, list_params)

            #last dataframe
            last_data = max(df[df["Year"] == max(df["Year"])][period_id]) 
            last_year = max(df["Year"])

            drilldowns_list = df[parameters_id].unique()

            df_rolling = pd.DataFrame()
            for i in range(len(drilldowns_list)):
                df_filter = df_complete[df_complete[parameters_id] == drilldowns_list[i]]
                df_filter = df_filter.drop(df_filter[(df_filter["Year"] == max(df_filter["Year"])) & (df_filter[period_id] > last_data)].index)
                df_filter = df_filter.sort_values(by=["Year", period_id], ascending=[True, True])
                df_filter["Trade Value Rolling Mean"] = df_filter[measure].rolling(window=window,min_periods=periods,center=False).mean()

                if(prediction == True):
                    df_filter = df_filter.append({"Year": max(df["Year"]), period_id: last_data+1, parameters_id:  drilldowns_list[i], measure: 0} , ignore_index=True)
                    df_filter["Trade Value Rolling Mean"] = df_filter["Trade Value Rolling Mean"].shift(1)

                df_filter = df_filter.drop(columns = ["Quarter", "Quarter ID", parameters, period]) if period == "Month" else  df_filter.drop(columns = [parameters, period])
                df_rolling = pd.concat([df_rolling, df_filter]).dropna().reset_index(drop=True)

            #Add names of ID
            df_final = df_rolling.merge(df_index, left_on=parameters_id, right_on=parameters_id, how="left")
            df_final = df_final.merge(df_index_time, left_on=period_id, right_on=period_id, how="left")
            
        #Zone + Year
        else:
            #Create dataframe with zones 
            df_index = df[[parameters_id, parameters]].drop_duplicates()
            list_parameters = [period, parameters_id]
            df_complete = fill_missing(period, parameters_id, df, list_parameters)

            last_period = df[period].unique()[-1]
            drilldowns_list = df[parameters_id].unique()

            df_rolling = pd.DataFrame()
            for i in range(len(drilldowns_list)):
                df_filter = df_complete[df_complete[parameters_id] == drilldowns_list[i]]
                df_filter["Trade Value Rolling Mean"] = df_filter[measure].rolling(window=window,min_periods=periods,center=False).mean()

                if(prediction == True):
                    df_filter = df_filter.append({period : last_period+1, parameters_id:  drilldowns_list[i], measure: 0} , ignore_index=True)
                    df_filter["Trade Value Rolling Mean"] = df_filter["Trade Value Rolling Mean"].shift(1)

                df_filter = df_filter.drop(columns = [parameters]) 
                df_rolling = pd.concat([df_rolling, df_filter]).dropna().reset_index(drop=True)
                
            #Add names of ID
            df_final = df_rolling.merge(df_index, left_on=parameters_id, right_on=parameters_id, how="left")
            
        output = {
            "data": json.loads(df_final.to_json(orient="records"))    
        }
        print(json.dumps(output)) 

if __name__ == "__main__":
    # Based on API used, generates the internal function's name.
    name = str(sys.argv[2])
    
    # Executes the function according to its name.
    Summary(name).call()
