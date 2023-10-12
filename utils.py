import os
import openai
import gspread
import pandas as pd
import smtplib
import requests
from bs4 import BeautifulSoup
from scrapers import HT_Scraper
import random
import re

def pull_db():
    creds = {
      "type": os.environ['g_type'],
      "project_id": os.environ['g_proj_id'],
      "private_key_id": os.environ['g_priv_key_id'],
      "private_key": os.environ['g_priv_key'].replace('\\n', '\n'),
      "client_email": os.environ['g_client_email'],
      "client_id": os.environ['g_client_id'],
      "auth_uri": os.environ['g_auth_uri'],
      "token_uri": os.environ['g_token_uri'],
      "auth_provider_x509_cert_url": os.environ['g_auth_prov_cirt'],
      "client_x509_cert_url": os.environ['g_client_cirt_url'],
    }
    sa = gspread.service_account_from_dict(creds)
    sh = sa.open_by_key('1bVqJTqGu7rB_ED49lpq_q2YVGMiUlx7fDsSocBetZPI').sheet1
    ref_df = pd.DataFrame(sh.get_all_records())

    return ref_df

def get_food(user_zip, brand):
    if brand == 'Harris Teeter':
        food = HT_Scraper(user_zip)
    else:
        print('dif store')
    return food

def get_meals(df):
    tagged = df[((df['tag']!='none') & (df['is_deal']==1))].sample(10)
    tagged['recipe_info'] = tagged['tag'].apply(lambda x: get_recipies(x))
    return tagged

def get_recipies(item):
    print('start res')
    # Get Recipe URL
    url = (f'https://www.foodnetwork.com/search/{item.replace(" ","-")}-/COURSE_DFACET:0/tag%23meal-part:main-dish/CUSTOM_FACET:RECIPE_FACET')
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    links = soup.find_all("a")  # Find all elements with the tag <a>
    out = [link.get('href') for link in links if str(link.get("href")).startswith('//www.foodnetwork.com/recipes')]
    urls = [x for x in set(out[9:])]
    rec_url = urls[random.randint(0,len(urls)-1)]
    rec_url = f'https:{rec_url}'

    # Get Image URL
    try:
        response = requests.get(rec_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        lead = soup.find_all("div", {"class": "recipe-lead"})
        soup2 = BeautifulSoup(str(lead[0]), 'html.parser')
        links = soup2.find_all("img")  # Find all elements with the tag <a>
        img_link = [link.get('src') for link in links][0]
        img_link = f'https:{img_link}'
    except:
        img_link = 'failed'

    title = rec_url.split('/')[-1].split('-recipe')[0]

    return [rec_url, img_link, title]

def write_user_df(contact,zipcode,food_df):
    df = pd.DataFrame(food_df[['name', 'recipe_info']])
    df['rec_url'] = df['recipe_info'].apply(lambda x: x[0])
    df['img_url'] = df['recipe_info'].apply(lambda x: x[1])
    df['title'] = df['recipe_info'].apply(lambda x: x[2])
    df['contact'] = contact
    df['zip'] = zipcode

    #write to google
    print(df)
    df.to_csv('./out.csv')
    return 'done'
