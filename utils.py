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

def gsheet_init():
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

    return sa


def get_food(user_zip, brand):
    if brand == 'Harris Teeter':
        food = HT_Scraper(user_zip)
    else:
        print('dif store')
    return food

def get_meals(df):
    tagged = df[((df['tag']!='none') & (df['is_deal']==1))]
    sampledf = tagged.groupby('tag', group_keys=False).apply(lambda df: df.sample(1))
    if sampledf.shape[0] <=9:
        extra_row_count = 10 - sampledf.shape[0]
        sup_df = sampledf.sample(extra_row_count)
        outdf = pd.concat([sampledf, sup_df])
    print(outdf.shape)
    outdf['recipe_info'] = tagged['tag'].apply(lambda x: get_recipies(x))
    return outdf

def get_recipies(item):
    print('start res')
    # Get Recipe URL
    url = (f'https://www.foodnetwork.com/search/{item.replace(" ","-")}-/COURSE_DFACET:0/tag%23meal-part:main-dish/CUSTOM_FACET:RECIPE_FACET')
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    links = soup.find_all("a")  # Find all elements with the tag <a>
    out = [link.get('href') for link in links if str(link.get("href")).startswith('//www.foodnetwork.com/recipes')]
    urls = [x for x in set(out[9:])]
    print( f'{len(urls)} urls found')
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

def prep_meal_df(contact,zipcode,food_df):
    df = pd.DataFrame(food_df[['name', 'recipe_info']])
    df['rec_url'] = df['recipe_info'].apply(lambda x: x[0])
    df['img_url'] = df['recipe_info'].apply(lambda x: x[1])
    df['title'] = df['recipe_info'].apply(lambda x: re.sub('-[0-9]+','',x[2]).replace('-',' '))
    df['contact'] = contact
    df['zip'] = zipcode
    mpid = random.randint(10**14,(10**15)-1)
    df['mpid'] = mpid
    df = df.drop('recipe_info', axis=1)
    print(mpid)
    return df

def write_meal_df(sh,df):
    # #write to google
    vals = df.values.tolist()
    for val in vals:
        sh.append_row(val, table_range="A1:D1")
    #sh.update([df.columns.values.tolist()] + df.values.tolist())

    return 'done'
