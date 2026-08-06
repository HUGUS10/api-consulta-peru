from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import re

app = FastAPI(
    title="API Consulta Peru (DNI / RUC)",
    description="Servicio backend para consulta de documentos sin autenticación",
    version="1.0.0"
)

# Configuración de CORS para permitir peticiones desde Vercel o local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

@app.get("/")
def home():
    return {"status": "ok", "message": "API de consulta DNI/RUC activa"}

# ==========================================
# ENDPOINT CONSULTA DNI (8 DÍGITOS)
# ==========================================
@app.get("/api/dni/{dni}")
def consultar_dni(dni: str):
    dni = dni.strip()
    if len(dni) != 8 or not dni.isdigit():
        raise HTTPException(status_code=400, detail="El DNI debe contener exactamente 8 dígitos numéricos.")

    try:
        # Petición a endpoint público espejo de RENIEC
        url = f"https://dniruc.apisperu.com/api/v1/dni/{dni}"
        # Como fallback/respaldo interno si falla la consulta primaria:
        url_alt = f"https://api.apis.net.pe/v1/dni?numero={dni}"

        res = requests.get(url_alt, headers=HEADERS, timeout=8)
        
        if res.status_code == 200:
            data = res.json()
            nombres = data.get("nombres", "").strip()
            app_paterno = data.get("apellidoPaterno", "").strip()
            app_materno = data.get("apellidoMaterno", "").strip()
            nombre_completo = f"{nombres} {app_paterno} {app_materno}".strip()

            return {
                "success": True,
                "dni": dni,
                "nombre_completo": nombre_completo,
                "nombres": nombres,
                "apellido_paterno": app_paterno,
                "apellido_materno": app_materno
            }
        
        raise HTTPException(status_code=404, detail="DNI no encontrado o servicio de RENIEC no disponible.")

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error de conexión con el servicio DNI: {str(e)}")


# ==========================================
# ENDPOINT CONSULTA RUC (11 DÍGITOS)
# ==========================================
@app.get("/api/ruc/{ruc}")
def consultar_ruc(ruc: str):
    ruc = ruc.strip()
    if len(ruc) != 11 or not ruc.isdigit():
        raise HTTPException(status_code=400, detail="El RUC debe contener exactamente 11 dígitos numéricos.")

    try:
        # Petición a API pública de SUNAT/RUC
        url = f"https://api.apis.net.pe/v1/ruc?numero={ruc}"
        res = requests.get(url, headers=HEADERS, timeout=8)

        if res.status_code == 200:
            data = res.json()
            razon_social = data.get("nombre", "").strip()
            direccion = data.get("direccion", "").strip()
            estado = data.get("estado", "").strip()
            condicion = data.get("condicion", "").strip()

            return {
                "success": True,
                "ruc": ruc,
                "razon_social": razon_social,
                "direccion": direccion if direccion else "SIN DIRECCIÓN REGISTRADA",
                "estado": estado,
                "condicion": condicion
            }

        raise HTTPException(status_code=404, detail="RUC no encontrado o servicio de SUNAT no disponible.")

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error de conexión con el servicio RUC: {str(e)}")