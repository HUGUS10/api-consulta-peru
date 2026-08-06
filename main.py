from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

@app.get("/")
def read_root():
    return {"status": "API de consulta SUNAT activa"}

@app.get("/api/ruc/{ruc}")
def consultar_ruc(ruc: str):
    if len(ruc) != 11 or not ruc.isdigit():
        raise HTTPException(status_code=400, detail="El RUC debe tener 11 dígitos numéricos")

    url = f"https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/jcrS00Alias?accion=consPorRuc&nroRuc={ruc}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="No se pudo conectar con SUNAT")

        soup = BeautifulSoup(response.text, 'html.parser')
        
        h4_tags = soup.find_all('h4')
        razon_social = ""
        for tag in h4_tags:
            text = tag.text.strip()
            if ruc in text:
                parts = text.split('-', 1)
                if len(parts) > 1:
                    razon_social = parts[1].strip()
                break

        if not razon_social:
            raise HTTPException(status_code=404, detail="RUC no encontrado en SUNAT")

        return {
            "success": True,
            "ruc": ruc,
            "razon_social": razon_social
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
