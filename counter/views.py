
import io
import matplotlib
matplotlib.use('Agg')

from datetime import date, timedelta, datetime

from django.shortcuts import redirect
from django.http import HttpResponse
from django.template.loader import get_template
from django.utils import timezone

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from xhtml2pdf import pisa

from .forms import (
    CalorieSetupForm,
    WeightEntryForm,
    CustomFoodForm
)
from .models import WeightEntry
from counter.utils import calculate_targets


from django.conf import settings
import openai
from django.utils.safestring import mark_safe

openai.api_key = settings.OPENAI_API_KEY

import openai
from django.contrib.auth.decorators import login_required
from .forms import MealPlanRequestForm
from .models import UserParametres

# 🔮 AI prompt generation
def generate_meal_plan(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful dietitian who creates meal plans based on nutritional targets."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=700,
        temperature=0.7
    )
    return response['choices'][0]['message']['content']


# 👨‍🍳 Meal plan view
from django.utils.safestring import mark_safe
import re

@login_required
def meal_plan_view(request):
    user_params = UserParametres.objects.filter(user=request.user).first()
    calorie_goal = int(user_params.calories_goal) if user_params and user_params.calories_goal else 2000

    meal_plan = None
    sections = {}
    summary = None

    if request.method == "POST":
        form = MealPlanRequestForm(request.POST)
        if form.is_valid():
            diet = form.cleaned_data['diet_preference']
            include = form.cleaned_data['include_foods']
            exclude = form.cleaned_data['exclude_foods']

            prompt = (
                f"Create a daily meal plan (breakfast, lunch, dinner) for a person with a {calorie_goal} kcal target.\n"
            )
            if diet and diet != "none":
                prompt += f"The meal plan should follow a {diet} diet.\n"
            if include:
                prompt += f"Make sure to include these foods: {include}.\n"
            if exclude:
                prompt += f"Please avoid these foods: {exclude}.\n"
            prompt += "Include approximate calories per meal and try to balance macronutrients."

            try:
                meal_plan = generate_meal_plan(prompt)
                normalized_plan = "\n" + meal_plan.strip()
                # Ensure proper dict structure
                pattern = r"\n(?=(Breakfast|Lunch|Dinner|Snacks(?: \(.*?\))?):)"
                split_plan = re.split(pattern, normalized_plan)

                # parts = ['', 'Breakfast', '...content...', 'Lunch', '...content...', ...]
                for i in range(1, len(split_plan), 2):
                    section_title = split_plan[i].strip()
                    content = split_plan[i + 1].strip()

                    # ✅ Try to extract summary text if it's in the last section
                    section_text = content  # default
                    if i + 2 >= len(split_plan):
                        # Try to extract summary *only if it's clearly separate*
                        parts = content.strip().split("\n\n", 1)
                        if len(parts) == 2 and len(
                                parts[1].split()) > 20:  # crude check to avoid splitting short blurbs
                            section_text = parts[0].strip()
                            summary = parts[1].strip()

                    sections[section_title] = mark_safe(section_text)


            except Exception as e:
                meal_plan = f"⚠️ Error contacting AI: {str(e)}"
    else:
        form = MealPlanRequestForm()
    print("Sections:", sections)

    return render(request, 'meal_plan.html', {
        'form': form,
        'meal_plan': meal_plan,
        'sections': sections,
        'summary': summary
    })

@login_required
def download_weight_pdf(request):
    start = request.GET.get('start_date')
    end = request.GET.get('end_date')

    try:
        start_date = datetime.strptime(start, '%Y-%m-%d').date()
        end_date = datetime.strptime(end, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        messages.error(request, "Invalid date range.")
        return redirect('profile')

    entries = WeightEntry.objects.filter(
        user=request.user,
        date__range=(start_date, end_date)
    ).order_by('date')

    if not entries.exists():
        messages.warning(request, "No weight entries found for this range.")
        return redirect('profile')

    # Summary
    start_weight = entries.first().weight
    end_weight = entries.last().weight
    difference = end_weight - start_weight
    summary = f"Net change: {'+' if difference >= 0 else ''}{difference:.1f} kg"

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    # 🧾 Title and metadata
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 770, "📉 Weight Progress Report")

    p.setFont("Helvetica", 12)
    p.drawString(50, 745, f"From {start_date} to {end_date}")
    p.drawString(50, 725, f"User: {request.user.username}")

    # 🗒️ Weight Logs
    y = 700
    p.setFont("Helvetica", 11)
    p.drawString(50, y, "Entries:")
    y -= 20

    for entry in entries:
        formatted_date = entry.date.strftime('%Y-%m-%d')
        p.drawString(60, y, f"{formatted_date}: {entry.weight} kg")
        y -= 18
        if y < 100:
            p.showPage()
            y = 750

    # ✏️ Final Summary at the bottom
    if y < 140:
        p.showPage()
        y = 750
    y -= 20
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "📊 Summary")
    y -= 20
    p.setFont("Helvetica", 11)
    p.drawString(60, y, summary)

    p.save()
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="weight_progress_report.pdf"'
    return response



def download_diary_pdf(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if not start_date or not end_date:
        messages.error(request, "Please select both dates.")
        return redirect('diary')

    entries = Food.objects.filter(
        user=request.user,
        search_date__date__range=(start_date, end_date)
    )

    total_calories = sum(e.calories for e in entries)
    total_protein = sum(e.protein for e in entries)
    total_fat = sum(e.fat for e in entries)
    total_carbs = sum(e.carbohydrates for e in entries)

    template = get_template('download_diary_pdf.html')
    html = template.render({
        'entries': entries,
        'start': start_date,
        'end': end_date,
        'total_calories': total_calories,
        'total_protein': total_protein,
        'total_fat': total_fat,
        'total_carbs': total_carbs,
        'user': request.user,
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="food_diary_report.pdf"'
    pisa.CreatePDF(html, dest=response)
    return response


@login_required
def custom_food_entry_view(request):
    name = request.GET.get('name', '')

    if request.method == 'POST':
        form = CustomFoodForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            portion = data['portion']
            factor = portion / 100  # to scale values from per 100g

            Food.objects.create(
                user=request.user,
                name=data['name'],
                calories=data['calories_per_100g'] * factor,
                protein=data['protein_per_100g'] * factor,
                fat=data['fat_per_100g'] * factor,
                carbohydrates=data['carbs_per_100g'] * factor,
                fiber=data.get('fiber_per_100g', 0) * factor if data.get('fiber_per_100g') else 0,
                search_date=timezone.now()
            )

            messages.success(request, f"{data['name'].title()} ({portion}g) added to your diary!")
            return redirect('diary')
    else:
        form = CustomFoodForm(initial={'name': name})

    return render(request, 'custom_food_entry.html', {'form': form})


@login_required
def weight_progress_view(request):
    entries = WeightEntry.objects.filter(user=request.user).order_by('-date')
    form = WeightEntryForm()

    if request.method == 'POST':
        form = WeightEntryForm(request.POST)
        if form.is_valid():
            weight_entry = form.save(commit=False)
            weight_entry.user = request.user
            weight_entry.save()
            messages.success(request, "📈 Weight entry added!")
            return redirect('profile#weight')  # paliek uz svara tab
        else:
            # Ja forma nav derīga, parādi kļūdas ziņojumu
            request.session['weight_form_data'] = request.POST
            messages.warning(request, "⚠️ Invalid weight entry. Please check the value.")
            return redirect('profile')
    return render(request, 'accounts/profile.html', {
        'weight_form': form,
        'weight_entries': entries,
        'active_tab': 'weight'  # pievienojam mainīgo
    })
from accounts.forms import UpdateProfileForm
@login_required
def profile_view(request):
    form = UpdateProfileForm(instance=request.user)

    # Atkārtoti ielādēt pēdējo mēģinājumu svara formai
    if 'weight_form_data' in request.session:
        weight_form = WeightEntryForm(request.session.pop('weight_form_data'))
    else:
        weight_form = WeightEntryForm()

    entries = WeightEntry.objects.filter(user=request.user).order_by('-date')

    return render(request, 'accounts/profile.html', {
        'form': form,
        'weight_form': weight_form,
        'weight_entries': entries,
        'active_tab': 'weight' if request.path == '/profile/' and '#weight' in request.get_full_path() else 'profile'
    })

@login_required
def recalculate_goals_view(request):
    try:
        params = UserParametres.objects.get(user=request.user)
        targets = calculate_targets(
            sex=params.sex,
            weight=params.weight,
            height=params.height,
            age=params.age,
            goal=params.goal,
            activity=params.activity
        )
        params.calories_goal = targets['calories']
        params.save()
        messages.success(request, "✅ Calorie and macro goals recalculated!")
    except UserParametres.DoesNotExist:
        messages.warning(request, "⚠️ You need to complete calorie setup first.")

    return redirect('profile')


@login_required
def calorie_setup_view(request):
    try:
        param = UserParametres.objects.get(user=request.user)
    except UserParametres.DoesNotExist:
        param = None

    if request.method == 'POST':
        form = CalorieSetupForm(request.POST, instance=param)
        if form.is_valid():
            updated = form.save(commit=False)
            updated.user = request.user
            updated.date_time = date.today()

            # ✅ Save calories to the model
            targets = calculate_targets(
                sex=updated.sex,
                weight=updated.weight,
                height=updated.height,
                age=updated.age,
                goal=updated.goal,
                activity=updated.activity
            )
            updated.calories_goal = targets['calories']
            updated.save()

            # ✅ Log new weight entry
            WeightEntry.objects.create(
                user=request.user,
                weight=updated.weight,
                date=datetime.now()
            )

            messages.success(request, "🎯 Your calorie goals were updated!")
            return redirect('profile')
    else:
        form = CalorieSetupForm(instance=param)

    return render(request, 'calorie_setup.html', {'form': form})


@login_required
def delete_food_entry(request, food_id):
    food = get_object_or_404(Food, id=food_id, user=request.user)
    food.delete()
    messages.success(request, f"{food.name.capitalize()} was removed from your diary.")

    # ⬅️ Redirect back to the correct date
    date_str = request.GET.get('date')
    if date_str:
        return redirect(f'/diary/?date={date_str}')
    return redirect('diary')

@login_required
def diary_view(request):
    # 1️⃣ Get selected date from URL, or default to today
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = timezone.localtime().date()
    else:
        selected_date = timezone.localtime().date()

    # 2️⃣ Fetch food entries for that date
    food_entries = Food.objects.filter(user=request.user, search_date__date=selected_date)

    # 3️⃣ Calculate totals
    total_calories = sum(entry.calories for entry in food_entries)
    total_carbs = sum(getattr(entry, 'carbohydrates', 0) for entry in food_entries)
    total_protein = sum(getattr(entry, 'protein', 0) for entry in food_entries)
    total_fat = sum(getattr(entry, 'fat', 0) for entry in food_entries)
    total_fiber = sum(getattr(entry, 'fiber', 0) for entry in food_entries)

    # 4️⃣ Get user's calorie goal from profile
    try:
        params = UserParametres.objects.get(user=request.user)
        targets = calculate_targets(
            sex=params.sex,
            weight=params.weight,
            height=params.height,
            age=params.age,
            goal=params.goal,
            activity=params.activity


        )
        calorie_goal = targets['calories']
    except UserParametres.DoesNotExist:
        calorie_goal = 2000

    # 5️⃣ Prepare context
    calories_remaining = max(0, calorie_goal - total_calories)
    context = {
        'food_entries': food_entries,
        'total_calories': total_calories,
        'total_carbs': total_carbs,
        'total_protein': total_protein,
        'total_fat': total_fat,
        'total_fiber': total_fiber,
        'calorie_goal': calorie_goal,
        'protein_goal': targets['protein'],  # ✅ add
        'fat_goal': targets['fat'],  # ✅ add
        'carbs_goal': targets['carbs'],  # ✅ add
        'calories_remaining': calories_remaining,
        'today': selected_date,
        'prev_date': selected_date - timedelta(days=1),
        'next_date': selected_date + timedelta(days=1),
    }

    return render(request, 'diary.html', context)
from django.shortcuts import render, get_object_or_404
from .models import Food
from django.contrib import messages
import requests

def home(request):
    if request.user.is_authenticated:
        if not UserParametres.objects.filter(user=request.user).exists():
            return redirect('calorie_setup')
    context = {}

    if request.method == 'POST' and 'query' in request.POST:
        query = request.POST.get('query', '')
        api_url = 'https://api.calorieninjas.com/v1/nutrition?query='
        headers = {'X-Api-Key': 'xFPnqF8LrRgfK1bzK4zj8A==kRpBsRyWWifIUUGY'}

        try:
            response = requests.get(api_url + query, headers=headers)
            response.raise_for_status()
            data = response.json()

            if "items" in data and len(data["items"]) > 0:
                food_item = data["items"][0]
                request.session['last_food'] = food_item  # Save for portion entry
                context['api'] = [food_item]
            else:
                # Check for custom food
                custom_foods = Food.objects.filter(name__icontains=query, user=request.user).order_by('-search_date')
                if custom_foods.exists():
                    food_item = custom_foods[0]
                    request.session['last_food'] = {
                        'name': food_item.name,
                        'calories': food_item.calories,
                        'carbohydrates_total_g': food_item.carbohydrates,
                        'protein_g': food_item.protein,
                        'fat_total_g': food_item.fat,
                        'fiber_g': food_item.fiber,
                        'is_custom': True
                    }
                    context['custom_food'] = food_item
                else:
                    context['error'] = f"No results found for '{query}'."
                    context['no_result_query'] = query

        except Exception as e:
            context['error'] = "API error: " + str(e)

    elif request.method == 'POST' and 'portion' in request.POST and request.user.is_authenticated:
        portion = float(request.POST['portion'])
        food_data = request.session.get('last_food')

        if food_data:
            total_calories = food_data['calories'] * portion / 100
            carbs = food_data.get('carbohydrates_total_g', 0) * portion / 100
            protein = food_data.get('protein_g', 0) * portion / 100
            fat = food_data.get('fat_total_g', 0) * portion / 100
            fiber = food_data.get('fiber_g', 0) * portion / 100

            Food.objects.create(
                name=food_data['name'],
                calories=total_calories,
                user=request.user,
                carbohydrates=carbs,
                protein=protein,
                fat=fat,
                fiber=fiber,
                portion=portion

            )

            messages.success(request, f"{food_data['name'].capitalize()} ({portion}g) added to your diary!")

            if food_data.get('is_custom'):
                context['custom_food'] = food_data
            else:
                context['api'] = [food_data]

    return render(request, 'home.html', context)


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

