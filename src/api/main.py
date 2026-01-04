from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title='Self-Healing API', version='0.7.0')

app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

@app.get('/')
async def root():
    return {'message': 'Self-Healing Platform', 'status': 'ok', 'version': '0.7.0'}

@app.get('/health')
async def health():
    return {'status': 'healthy'}
