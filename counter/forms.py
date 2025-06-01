
from .models import WeightEntry
from django import forms
from counter.models import UserParametres
from django import forms
from .models import Food
from django import forms
from django import forms

def validate_positive_weight(value):
    if value <= 0:
        raise forms.ValidationError("Weight must be a positive number.")
    if value > 500:
        raise forms.ValidationError("Weight exceeds realistic human values.")

class MealPlanRequestForm(forms.Form):
    diet_preference = forms.ChoiceField(
        choices=[
            ('none', 'No preference'),
            ('vegetarian', 'Vegetarian'),
            ('vegan', 'Vegan'),
            ('keto', 'Keto'),
            ('low_carb', 'Low Carb'),
            ('high_protein', 'High Protein'),
        ],
        required=False
    )
    include_foods = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'placeholder': 'E.g., chicken, broccoli', 'rows': 1})
    )
    exclude_foods = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'placeholder': 'E.g., dairy, gluten', 'rows': 1})
    )
class WeightEntryForm(forms.ModelForm):
    weight = forms.FloatField(validators=[validate_positive_weight])
    class Meta:
        model = WeightEntry
        fields = ['weight']
        widgets = {
            'weight': forms.NumberInput(attrs={'step': '0.1', 'class': 'form-control', 'placeholder': 'Enter your weight (kg)'})
        }
    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight <= 0:
            raise forms.ValidationError("Weight must be a positive number.")
        if weight < 25 or weight > 400:
            raise forms.ValidationError("Weight must be within a realistic human range (25–400 kg).")
        return weight


class CalorieSetupForm(forms.ModelForm):
    weight = forms.FloatField(validators=[validate_positive_weight])
    target_weight = forms.FloatField(validators=[validate_positive_weight])
    class Meta:
        model = UserParametres
        fields = ['sex', 'age', 'height', 'weight', 'goal', 'activity', 'target_weight']
        widgets = {
            'sex': forms.Select(choices=[(1, 'Male'), (2, 'Female')]),
            'goal': forms.Select(attrs={'id': 'id_goal'}, choices=[
                (0, 'Maintain weight'),
                (1, 'Lose weight'),
                (2, 'Gain weight')
            ]),
            'activity': forms.Select(choices=[
                (1, 'Sedentary (little/no exercise)'),
                (2, 'Lightly active (1–3 days/week)'),
                (3, 'Moderately active (3–5 days/week)'),
                (4, 'Very active (6–7 days/week)'),
                (5, 'Super active (physical job or 2x training)')
            ]),
            'target_weight': forms.NumberInput(attrs={
                'placeholder': 'Your target weight (kg)',
                'step': '0.1',
                'id': 'id_target_weight'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['target_weight'].required = False

    def clean(self):
        cleaned_data = super().clean()
        goal = cleaned_data.get('goal')
        weight = cleaned_data.get('weight')
        target_weight = cleaned_data.get('target_weight')

        # Tikai ja abi ir derīgi skaitļi (nav None)
        if weight is not None and target_weight is not None:
            if goal == 1:  # Lose weight
                if target_weight >= weight:
                    self.add_error('target_weight',
                                   "⚠️ To lose weight, your target weight must be less than your current weight.")
            elif goal == 2:  # Gain weight
                if target_weight <= weight:
                    self.add_error('target_weight',
                                   "⚠️ To gain weight, your target weight must be greater than your current weight.")

        return cleaned_data


class CustomFoodForm(forms.Form):
    name = forms.CharField(label="Food Name", max_length=100)
    calories_per_100g = forms.FloatField(label="Calories (per 100g)")
    protein_per_100g = forms.FloatField(label="Protein (g per 100g)")
    fat_per_100g = forms.FloatField(label="Fat (g per 100g)")
    carbs_per_100g = forms.FloatField(label="Carbohydrates (g per 100g)")
    fiber_per_100g = forms.FloatField(label="Fiber (g per 100g)", required=False)
    portion = forms.FloatField(label="Portion (g)", help_text="How much did you eat?")


