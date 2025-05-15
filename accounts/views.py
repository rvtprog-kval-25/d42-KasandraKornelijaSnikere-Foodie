from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegisterForm, UpdateProfileForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from counter.models import UserParametres
from counter.utils import calculate_targets  # moved helper function here
from counter.models import WeightEntry
from counter.forms import WeightEntryForm
from datetime import timedelta
from django.utils import timezone
from counter.models import Food  # adjust if your Food model is elsewhere
@login_required
@login_required
@login_required
def profile_view(request):
    user = request.user
    form = UpdateProfileForm(instance=user)
    weight_form = WeightEntryForm()
    weight_entries = WeightEntry.objects.filter(user=user).order_by('date')

    try:
        params = UserParametres.objects.get(user=user)
        targets = calculate_targets(
            sex=params.sex,
            weight=params.weight,
            height=params.height,
            age=params.age,
            goal=params.goal,
            activity=params.activity
        )
    except UserParametres.DoesNotExist:
        params = None
        targets = None

    if request.method == 'POST':
        # Weight update
        if 'weight_entry' in request.POST:
            weight_form = WeightEntryForm(request.POST)
            if weight_form.is_valid():
                new_entry = weight_form.save(commit=False)
                new_entry.user = request.user
                new_entry.save()

                # Update weight in UserParametres
                if params:
                    params.weight = new_entry.weight
                    params.save()

                messages.success(request, "✅ Weight entry added successfully!")
                return redirect('profile')

        # Recalculate goals
        elif 'recalculate' in request.POST and params:
            targets = calculate_targets(
                sex=params.sex,
                weight=params.weight,
                height=params.height,
                age=params.age,
                goal=params.goal,
                activity=params.activity
            )
            params.calories_goal = targets['calories']
            params.protein_goal = targets['protein']
            params.fat_goal = targets['fat']
            params.carbs_goal = targets['carbs']
            params.save()
            messages.success(request, "✅ Goals recalculated successfully!")
            return redirect('profile')

        # Profile update
        else:
            form = UpdateProfileForm(request.POST, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, "✅ Profile updated successfully!")
                return redirect('profile')

    weight_entries = WeightEntry.objects.filter(user=user).order_by('date')
    latest_weight = weight_entries.last().weight if weight_entries.exists() else None
    diff = None
    if params and params.goal != 0 and params.target_weight and latest_weight:
        diff = round(params.target_weight - latest_weight, 1)
    # ⏰ Get today's date
    today = timezone.localtime().date()

    # 🧾 Fetch today's food entries
    food_entries = Food.objects.filter(user=user, search_date__date=today)

    # 🧮 Calculate today's totals
    total_calories = sum(entry.calories for entry in food_entries)
    total_protein = sum(getattr(entry, 'protein', 0) for entry in food_entries)
    total_fat = sum(getattr(entry, 'fat', 0) for entry in food_entries)
    total_carbs = sum(getattr(entry, 'carbohydrates', 0) for entry in food_entries)
    total_calories = sum(entry.calories for entry in food_entries)

    return render(request, 'accounts/profile.html', {
        'form': form,
        'targets': targets,
        'weight_form': weight_form,
        'weight_entries': weight_entries,
        'latest_weight': latest_weight,
        'goal_weight': params.target_weight if params and params.goal != 0 else None,
        'weight_diff': diff,
        'total_calories': total_calories,
        'total_protein': total_protein,
        'total_fat': total_fat,
        'total_carbs': total_carbs,
    })

def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User {user.username} registered successfully!")
            login(request, user)  # log the user in directly after registration
            return redirect('home')  # or 'main' if your main view is named that

        else:
            print(form.errors)  # Log errors to console for debug
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')  # adjust this to your actual home view
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')
