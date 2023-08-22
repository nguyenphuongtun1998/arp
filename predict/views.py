from django.shortcuts import render
from django.http import JsonResponse
import pandas as pd
import numpy as np
from predict.models import PredResults
from datetime import datetime, timedelta
import requests
import json
from bs4 import BeautifulSoup
import joblib
import sklearn

def predict(request):
    df = pd.read_csv(r"C:\Users\Hi\OneDrive - University of Bristol\Msc Business Analytics\1. Study\Applied Research Project\2. Data\i0_postcode_all.csv")  # Load your DataFrame here
    locations = df[df["type"] < 4]["area"].sort_values().tolist()
    context = {
        'locations': locations,
    }
    return render(request, 'predict.html', context)

def calculate_route(pickup_longitude, pickup_latitude, dropoff_longitude, dropoff_latitude):
    osrm_api_url = f"http://router.project-osrm.org/route/v1/car/{pickup_longitude},{pickup_latitude};{dropoff_longitude},{dropoff_latitude}?overview=false"
    response = requests.get(osrm_api_url)

    if response.status_code == 200:
        route_data = json.loads(response.content)
        if "routes" in route_data and len(route_data["routes"]) > 0:
            route = route_data["routes"][0]
            distance = route["distance"]/1000  # Distance in meters
            duration = route["duration"]/60  # Duration in seconds
            return distance, duration
        else:
            return None, None
    else:
        return None, None

def fuel_prices(url):
    #url="https://api.everviz.com/gsheet?googleSpreadsheetKey=1Bif9pSSRMpRTn3M3j_Y_lKm2HIQmtj7GH4PwtjLYdkg&worksheet=Weekly%20Fuel%20highcharts!A1:ZZ"
    response = requests.get(url)
    data = response.json()

    date = data["values"][0][1:]
    petrol_price = data["values"][1][1:]
    diesel_price = data["values"][2][1:]

    i0_fuel_price = pd.DataFrame({
                        "request_date": date,
                        "petrol_price": petrol_price,
                        "diesel_price": diesel_price     
        })

    i0_fuel_price = i0_fuel_price[i0_fuel_price["petrol_price"] != ""]

    i0_fuel_price["request_date"] = pd.to_datetime(i0_fuel_price["request_date"])
    i0_fuel_price["petrol_price"] = pd.to_numeric(i0_fuel_price["petrol_price"])
    i0_fuel_price["diesel_price"] = pd.to_numeric(i0_fuel_price["diesel_price"])
    i0_fuel_price.set_index('request_date', inplace=True)

    # Resample to daily frequency (including Saturday and Sunday)
    i0_fuel_price = i0_fuel_price.resample('D').ffill().reset_index()
    return i0_fuel_price

def predict_chances(request):

    if request.POST.get('action') == 'post':

        # Receive data from client
        client_name = request.POST.get('client_name')
        request_date_str = request.POST.get('request_date')
        start_date_str = request.POST.get('start_date')
        vehicle_size = int(request.POST.get('vehicle_size'))
        pickup_postcode_1 = request.POST.get('pickup_postcode_1').lower()
        pickup_city_1 = request.POST.get('pickup_city_1').lower()
        dropoff_postcode_1 = request.POST.get('dropoff_postcode_1').lower()
        dropoff_city_1 = request.POST.get('dropoff_city_1').lower()
        number_pickups = int(request.POST.get('number_pickups'))
        number_shifts = int(request.POST.get('number_shifts'))
        number_trips = int(request.POST.get('number_trips'))
        number_waits_returns = int(request.POST.get('number_waits_returns'))
        weekday = int(request.POST.get('weekday'))
        weekend = int(request.POST.get('weekend'))
        unsociable_hours = int(request.POST.get('unsociable_hours'))

        # Import i0 files
        i0_postcode_all = pd.read_csv(r"C:\Users\Hi\OneDrive - University of Bristol\Msc Business Analytics\1. Study\Applied Research Project\2. Data\i0_postcode_all.csv")
        i0_fuel_price = fuel_prices("https://api.everviz.com/gsheet?googleSpreadsheetKey=1Bif9pSSRMpRTn3M3j_Y_lKm2HIQmtj7GH4PwtjLYdkg&worksheet=Weekly%20Fuel%20highcharts!A1:ZZ")
        print(i0_fuel_price)

        # Transform data
        request_date = datetime.strptime(request_date_str, '%Y-%m-%d')
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')

        pickup_location_1 = pickup_postcode_1 if pickup_postcode_1.strip() else pickup_city_1
        pickup_latitude_1 = i0_postcode_all.loc[i0_postcode_all['area'] == pickup_location_1, 'Latitude'].values[0]
        pickup_longitude_1 = i0_postcode_all.loc[i0_postcode_all['area'] == pickup_location_1, 'Longitude'].values[0]
        
        dropoff_location_1 = dropoff_postcode_1 if dropoff_postcode_1.strip() else dropoff_city_1
        dropoff_latitude_1 = i0_postcode_all.loc[i0_postcode_all['area'] == dropoff_location_1, 'Latitude'].values[0]
        dropoff_longitude_1 = i0_postcode_all.loc[i0_postcode_all['area'] == dropoff_location_1, 'Longitude'].values[0]

        route_distance, route_duration = calculate_route(pickup_longitude_1, pickup_latitude_1,
                                                         dropoff_longitude_1, dropoff_latitude_1)
        
        travel_distance = route_distance * number_trips
        travel_duration = route_duration * number_trips

        weekday_only = weekday*1-weekend
        weekend_only = weekend*1-weekday

        petrol_price_7 = i0_fuel_price.loc[i0_fuel_price['request_date'] == request_date - timedelta(days=7), 'petrol_price'].values[0]
        diesel_price_7 = i0_fuel_price.loc[i0_fuel_price['request_date'] == request_date - timedelta(days=7), 'diesel_price'].values[0]

        #request_date_minus_7 = request_date - timedelta(days=7)

        # Filter the DataFrame and calculate petrol_price_7
        #matching_rows = i0_fuel_price['request_date'] == request_date_minus_7
        #if matching_rows.any():
        #    petrol_price_7 = i0_fuel_price.loc[matching_rows, 'petrol_price'].values[0]
        #    diesel_price_7 = i0_fuel_price.loc[matching_rows, 'diesel_price'].values[0]
        #else:
        #    petrol_price_7 = None
        #    diesel_price_7 = None

        #Print just for checking
        print(vehicle_size, travel_duration, 
                                 number_trips, number_waits_returns, number_pickups,
                                 weekend, weekday, 
                                 #weekend_only, weekday_only,
                                 unsociable_hours, petrol_price_7, diesel_price_7, 
                                 #pred_price, lower_price, upper_price
                                 )
        print("Scikit-Learn Version:", sklearn.__version__)

        # Unpickle model
        model = pd.read_pickle(r"C:\Users\Hi\OneDrive - University of Bristol\Msc Business Analytics\1. Study\Applied Research Project\Django\gb_model.pickle")        
        model_lower = pd.read_pickle(r"C:\Users\Hi\OneDrive - University of Bristol\Msc Business Analytics\1. Study\Applied Research Project\Django\gb_lower_model.pickle")
        model_upper = pd.read_pickle(r"C:\Users\Hi\OneDrive - University of Bristol\Msc Business Analytics\1. Study\Applied Research Project\Django\gb_upper_model.pickle")
        
        #model = joblib.load(r"C:\Users\Hi\OneDrive - University of Bristol\Msc Business Analytics\1. Study\Applied Research Project\1. Code\gb_model.pkl")
        #model_lower = joblib.load(r"C:\Users\Hi\OneDrive - University of Bristol\Msc Business Analytics\1. Study\Applied Research Project\1. Code\gb_lower_model.pkl")
        #model_upper = joblib.load(r"C:\Users\Hi\OneDrive - University of Bristol\Msc Business Analytics\1. Study\Applied Research Project\1. Code\gb_upper_model.pkl")


        # Make prediction
        x_var = [vehicle_size,  travel_duration, 
                                 number_trips, number_waits_returns, number_pickups,
                                 #weekend, weekday, 
                                 #weekend_only, weekday_only,
                                 unsociable_hours, petrol_price_7, diesel_price_7]

        result = model.predict([x_var])
        result_lower = model_lower.predict([x_var])
        result_upper = model_upper.predict([x_var])

        pred_price = np.exp(result[0])
        lower_price = np.exp(result_lower[0])
        upper_price = np.exp(result_upper[0])


        

        PredResults.objects.create(client_name=client_name,
                                    request_date=request_date,
                                    start_date=start_date,
                                    vehicle_size=vehicle_size,
                                    pickup_postcode_1=pickup_postcode_1,
                                    pickup_city_1=pickup_city_1,
                                    dropoff_postcode_1=dropoff_postcode_1,
                                    dropoff_city_1=dropoff_city_1,
                                    number_pickups=number_pickups,
                                    number_shifts=number_shifts,
                                    number_trips=number_trips,
                                    number_waits_returns=number_waits_returns,
                                    weekday=weekday,
                                    weekend=weekend,
                                    unsociable_hours=unsociable_hours,
                                    pred_price=pred_price,
                                    lower_price=lower_price,
                                    upper_price=upper_price
                                   )

        return JsonResponse({'result': pred_price, 
                             'result_lower': lower_price,
                             'result_upper': upper_price,
                             'client_name': client_name,
                            'request_date': request_date,
                            'start_date': start_date,
                            'vehicle_size': vehicle_size,
                            'pickup_postcode_1': pickup_postcode_1,
                            'pickup_city_1': pickup_city_1,
                            'dropoff_postcode_1': dropoff_postcode_1,
                            'dropoff_city_1': dropoff_city_1,
                            'number_pickups': number_pickups,
                            'number_shifts': number_shifts,
                            'number_trips': number_trips,
                            'number_waits_returns': number_waits_returns,
                            'weekday': weekday,
                            'weekend': weekend,
                            'unsociable_hours': unsociable_hours,
                             },
                            safe=False)



def view_results(request):
    # Submit prediction and show all
    data = {"dataset": PredResults.objects.all()}
    return render(request, "results.html", data)