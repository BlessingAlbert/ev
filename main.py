from fastapi import FastAPI, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.oauth2.id_token
from google.auth.transport import requests
from google.cloud import firestore
from starlette.responses import FileResponse 
import os

app = FastAPI()

firestore_db = firestore.Client()

firebase_request_adapter = requests.Request()

app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    error_message = "No error here"
    return templates.TemplateResponse('index.html', {'request': request, 'error_message': error_message})

@app.get("/add", response_class=HTMLResponse)
async def add_ev(request: Request):
    return templates.TemplateResponse('add.html', {'request': request})

@app.post("/add", response_class=RedirectResponse)
async def add_ev(request: Request, name: str = Form(...), manufacturer: str = Form(...), year: int = Form(...),
                 battery_size: float = Form(...), wltp_range: float = Form(...), cost: float = Form(...),
                 power_kw: float = Form(...)):
    ev_data = {
        'name': name,
        'manufacturer': manufacturer,
        'year': year,
        'battery_size': battery_size,
        'wltp_range': wltp_range,
        'cost': cost,
        'power_kw': power_kw
    }
    firestore_db.collection('evs').add(ev_data)
    return RedirectResponse("/", status_code=status.HTTP_302_FOUND)

@app.get("/search-ev", response_class=HTMLResponse)
async def query_ev_form(request: Request):
    return templates.TemplateResponse('search-ev.html', {'request': request})

@app.post("/search-ev", response_class=HTMLResponse)
async def query_ev(request: Request, attribute: str = Form(...), value: str = Form(...)):
    if not attribute or not value:
        evs = firestore_db.collection('evs').stream()
    else:
        if attribute in ["name", "manufacturer"]:
            evs = firestore_db.collection('evs').where(attribute, '==', value).stream()
        else:
            value_float = float(value)
            evs = firestore_db.collection('evs').where(attribute, '>=', value_float - 0.01).where(attribute, '<=', value_float + 0.01).stream()

    evs_data = [doc.to_dict() for doc in evs]
    return templates.TemplateResponse('search-result.html', {'request': request, 'evs': evs_data})

@app.get("/ev/{ev_name}", response_class=HTMLResponse)
async def ev_details(request: Request, ev_name: str):
    ev_ref = firestore_db.collection('evs').where('name', '==', ev_name).limit(1).stream()
    ev_data = None
    ev_id = None 
    for doc in ev_ref:
        ev_data = doc.to_dict()
        ev_id = doc.reference.id  
        break  
    if ev_data:
        print(ev_data)
        return templates.TemplateResponse('details.html', {'request': request, 'ev_data': ev_data, 'ev_id': ev_id})  
    else:
        return HTMLResponse(content="EV not found", status_code=404)
    
@app.post("/ev/{ev_name}/edit", response_class=RedirectResponse)
async def edit_ev(request: Request, ev_name: str, name: str = Form(...), manufacturer: str = Form(...), year: int = Form(...),
                  battery_size: float = Form(...), wltp_range: float = Form(...), cost: float = Form(...),
                  power_kw: float = Form(...)):
    ev_ref = firestore_db.collection('evs').where('name', '==', ev_name).limit(1).get()
    ev_id = None
    for doc in ev_ref:
        ev_id = doc.id
    if ev_id:
        ev_ref = firestore_db.collection('evs').document(ev_id)
        ev_ref.update({'name': name, 'manufacturer': manufacturer, 'year': year,
                       'battery_size': battery_size, 'wltp_range': wltp_range,
                       'cost': cost, 'power_kw': power_kw})
        return RedirectResponse(f"/ev/{ev_name}", status_code=status.HTTP_303_SEE_OTHER)
    else:
        return HTMLResponse(content="EV not found", status_code=404)
    
@app.get('/get-meta/{ev_name}')
async def get_ev_meta(request: Request, ev_name: str):
    ev_query = firestore_db.collection('evs').where('name', '==', ev_name).limit(1).stream()
    ev_id = None

    for doc in ev_query:
        ev_id = doc.id
        break

    if ev_id:
        ev_meta_ref = firestore_db.collection('metadata').where('ev_id', '==', ev_id).stream()
        ev_meta_list = []

        for doc in ev_meta_ref:
            ev_meta = doc.to_dict()
            ev_meta_list.append(ev_meta)

        return ev_meta_list
    else:
        return JSONResponse({"message": "EV not found"}, status_code=404)
    
@app.post('/insert-meta/{ev_name}')
async def insert_ev_meta(request: Request, ev_name: str, review: str = Form(...), rating: int = Form(...)):
    ev_query = firestore_db.collection('evs').where('name', '==', ev_name).limit(1).stream()
    ev_id = None

    for doc in ev_query:
        ev_id = doc.id
        break

    if ev_id:
        data = {
            'ev_id': ev_id,
            'review': review,
            'rating': rating
        }

        evmeta_ref = firestore_db.collection('metadata')
        evmeta_ref.add(data)

        return JSONResponse({"message": "Review and rating inserted successfully"}, status_code=200)
    else:
        return JSONResponse({"message": "EV not found"}, status_code=404)
    
@app.get("/ev-list", response_class=HTMLResponse)
async def list_evs(request: Request):
    evs_ref = firestore_db.collection('evs')
    evs_docs = evs_ref.stream()
    evs_data = []
    for doc in evs_docs:
        ev = doc.to_dict()
        ev['id'] = doc.id  
        evs_data.append(ev)
    return templates.TemplateResponse("list.html", {"request": request, "evs": evs_data})

@app.delete("/delete/{ev_id}", response_class=RedirectResponse)
async def delete_ev(ev_id: str):
    ev_ref = firestore_db.collection('evs').document(ev_id)
    ev_ref.delete()
    return RedirectResponse("/ev-list", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/compare-evs")
async def select_evs(request: Request):
    evs_ref = firestore_db.collection('evs').stream()
    evs_data = []
    for doc in evs_ref:
        ev = doc.to_dict()
        ev['id'] = doc.id
        evs_data.append(ev)
    return JSONResponse({"evs": evs_data})

@app.get("/compare-ev", response_class=HTMLResponse)
async def select_ev(request: Request):
    return templates.TemplateResponse("compare-ev.html", {"request": request})