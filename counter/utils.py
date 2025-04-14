def calculate_targets(sex, weight, height, age, goal, activity):
    if sex == 1:
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    activity_multipliers = {
        1: 1.2,
        2: 1.375,
        3: 1.55,
        4: 1.725,
        5: 1.9
    }
    tdee = bmr * activity_multipliers.get(activity, 1.2)

    if goal == 1:  # lose weight
        tdee *= 0.85
    elif goal == 2:  # gain weight
        tdee *= 1.10

    protein_kcal = tdee * 0.20
    fat_kcal     = tdee * 0.30
    carbs_kcal   = tdee * 0.50

    protein_g = round(protein_kcal / 4, 1)
    fat_g     = round(fat_kcal / 9, 1)
    carbs_g   = round(carbs_kcal / 4, 1)

    return {
        'bmr': round(bmr),
        'calories': round(tdee),
        'protein': protein_g,
        'fat': fat_g,
        'carbs': carbs_g
    }
