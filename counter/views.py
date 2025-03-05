from django.shortcuts import render
from .models import Food
import requests
import json


def home(request):
    if request.method == 'POST':
        query = request.POST.get('query', '')
        api_url = 'https://api.calorieninjas.com/v1/nutrition?query='
        headers = {'X-Api-Key': 'xFPnqF8LrRgfK1bzK4zj8A==kRpBsRyWWifIUUGY'}

        try:
            response = requests.get(api_url + query, headers=headers)
            response.raise_for_status()  # Pārbauda, vai pieprasījums bija veiksmīgs
            data = response.json()  # Nolasām atbildi kā vārdnīcu

            if "items" in data and len(data["items"]) > 0:
                items = data["items"]

                return render(request, 'home.html', {'api': items})
            else:
                return render(request, 'home.html', {'error': "No results found"})

        except Exception as e:
            print("API ERROR:", e)
            return render(request, 'home.html', {'error': "There was an error: " + str(e)})

    return render(request, 'home.html')

def food_search(request):
    if request.method == 'POST':
        food_name = request.POST.get('query', '')
        api_url = 'https://api.calorieninjas.com/v1/nutrition?query='
        headers = {'X-Api-Key': 'xFPnqF8LrRgfK1bzK4zj8A==kRpBsRyWWifIUUGY'}

        try:
            response = requests.get(api_url + food_name, headers=headers)
            response.raise_for_status()
            food_data = response.json()
            calories = None
            if "items" in food_data and len(food_data["items"]) > 0:
                calories = food_data["items"][0]['calories']
            return render(request, 'home.html', {
                'food_name': food_name,
                'calories': calories,
            })
        except requests.exceptions.RequestException as e:
            return render(request, 'home.html', {'error': str(e)})

    return render(request, 'home.html')
