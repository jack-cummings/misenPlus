from utils import gsheet_init, get_food, get_meals, prep_meal_df, write_meal_df
import pandas as pd
import os

sa = gsheet_init()
user_sh = sa.open_by_key(os.environ['user_sheet_id']).sheet1
meal_sh = sa.open_by_key(os.environ['meal_sheet_id']).sheet1
entries = pd.DataFrame(user_sh.get_all_records()).values.tolist()

for entry in entries:
    food_df = get_food(entry[3], entry[2])
    meal_df_temp = get_meals(food_df)
    meal_df = prep_meal_df(entry[1], entry[3], meal_df_temp)
    write_meal_df(meal_sh,meal_df)
    print('x')
