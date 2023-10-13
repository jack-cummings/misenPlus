from fastapi import FastAPI, Request, BackgroundTasks, Response, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import sqlite3
import os
from utils import gsheet_init
import pandas as pd
from datetime import datetime
from fastapi.responses import RedirectResponse
import starlette.status as status

# Launch app and mount assets
app = FastAPI()
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
templates = Jinja2Templates(directory="templates")
# init DB
#con = sqlite3.connect("temp.db")
sa = gsheet_init()
meal_sh = sa.open_by_key(os.environ['meal_sheet_id']).sheet1
df = pd.DataFrame(meal_sh.get_all_records())


@app.get("/")
async def home(request: Request):
    try:
        return templates.TemplateResponse('index_v3.html', {"request": request})

    except Exception as e:
        print(e)
        return templates.TemplateResponse('error.html', {"request": request})

@app.post("/save_input")
async def save_input(request: Request, background_tasks: BackgroundTasks):
    try:
        # Collect User Input
        body = await request.body()
        print(body)
        out_list = []
        for x in body.decode('UTF-8').split('&')[:-1]:
            out_list.append(x.split('=')[1].replace('+', ' ').replace('%40', '@'))
        print(out_list)

        sa = gsheet_init()
        user_sh = sa.open_by_key(os.environ['user_sheet_id']).sheet1
        cols = ['Timestamp', 'Email Address', 'Where do you do your grocery shopping?', 'What is your zip code?']
        vals = [datetime.now().strftime("%m/%d/%Y, %H:%M:%S")]+(out_list)
        df = pd.DataFrame([vals], columns= cols)
        user_sh.append_row(vals, table_range = "A1:D1")

        response = RedirectResponse(url='/thank_you', status_code=status.HTTP_302_FOUND)


        return response

    except Exception as e:
        print(e)
        return templates.TemplateResponse('error.html', {"request": request})

@app.get("/thank_you")
async def home(request: Request):
    try:
        return templates.TemplateResponse('index_v3.html', {"request": request})

    except Exception as e:
        print(e)
        return templates.TemplateResponse('error.html', {"request": request})

@app.get("/meals")

async def meals(request: Request):
    try:
        mpid = request.query_params['mpid']
        mpdf = df[df['mpid']== int(mpid)]
        params = {}
        params['request'] = request
        for i in range(0,10):
            params[f'rec_url_{i+1}'] = mpdf.rec_url.values[i]
            params[f'img_url_{i+1}'] = mpdf.img_url.values[i]
            params[f'title_{i+1}'] = mpdf.title.values[i]
            params[f'ing_{i+1}'] = mpdf.name.values[i]
        return templates.TemplateResponse('meals.html', params)

    except Exception as e:
        print(e)
        return templates.TemplateResponse('error.html', {"request": request})


if __name__ == '__main__':
    if os.environ['MODE'] == 'dev':
        import uvicorn
        uvicorn.run(app, port=4242, host='0.0.0.0')