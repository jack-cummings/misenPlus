from utils import pull_db, get_food, get_meals, get_recipies

entries = pull_db().values.tolist()
for entry in entries:
    food = get_food(entry[3], entry[2])
    print('food done')
    meals = get_meals(food)
    print('meals done')
    recipies, imgs = get_recipies(meals)
    print(meals)
    print(recipies)