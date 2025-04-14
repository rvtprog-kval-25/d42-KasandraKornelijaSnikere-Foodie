
from .models import WeightEntry
from django import forms
from counter.models import UserParametres
from django import forms
from .models import Food
class WeightEntryForm(forms.ModelForm):
    class Meta:
        model = WeightEntry
        fields = ['weight']
        widgets = {
            'weight': forms.NumberInput(attrs={'step': '0.1', 'class': 'form-control', 'placeholder': 'Enter your weight (kg)'})
        }


class CalorieSetupForm(forms.ModelForm):
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

        # ✅ Only check if target is filled
        if goal == 1 and target_weight is not None:  # Lose weight
            if target_weight >= weight:
                raise forms.ValidationError(
                    "⚠️ To lose weight, your target weight must be less than your current weight.")

        elif goal == 2 and target_weight is not None:  # Gain weight
            if target_weight <= weight:
                raise forms.ValidationError(
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


