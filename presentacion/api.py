from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import time

from seguridad.seguridad import (hashear_contrasena, verificar_contrasena, crear_token, verificar_token, cifrar_dato)
from datos.repositorios import RepositorioUsuarios, RepositorioTransacciones
from negocio.servicios import ServicioTransacciones, ServicioUsuarios

app = FastAPI(title="Sistema de Transacciones Financieras", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="presentacion")

_repo_usuarios = RepositorioUsuarios()
_svc_tx        = ServicioTransacciones()
_svc_usuarios  = ServicioUsuarios()

@app.middleware("http")
async def middleware_tiempo(request: Request, call_next):
    inicio = time.perf_counter()
    respuesta = await call_next(request)
    duracion = time.perf_counter() - inicio
    respuesta.headers["X-Tiempo-Respuesta-ms"] = f"{duracion * 1000:.2f}"
    return respuesta

class EsquemaRegistro(BaseModel):
    nombre_usuario: str = Field(..., min_length=3, max_length=50)
    contrasena:     str = Field(..., min_length=6)
    saldo_inicial:  float = Field(default=1000.0, ge=0)

class EsquemaLogin(BaseModel):
    nombre_usuario: str
    contrasena:     str

class EsquemaTransaccion(BaseModel):
    monto: float = Field(..., gt=0)
    tipo:  str   = Field(..., pattern="^(retiro|transferencia|pago)$")

async def obtener_usuario_actual(request: Request) -> dict:
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Token requerido.")
    payload = verificar_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido o expirado.")
    return payload

#Endpoints
@app.get("/", response_class=HTMLResponse)
async def inicio(request: Request):
    """Sirve la interfaz HTML."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/registro", status_code=201)
async def registrar_usuario(datos: EsquemaRegistro):
    existente = await _repo_usuarios.buscar_por_nombre(datos.nombre_usuario)
    if existente:
        raise HTTPException(status_code=409, detail="El nombre de usuario ya existe.")

    hash_pwd = hashear_contrasena(datos.contrasena)
    saldo_cifrado = cifrar_dato(str(datos.saldo_inicial))

    usuario_id = await _repo_usuarios.crear_usuario({
        "nombre_usuario": datos.nombre_usuario,
        "hash_contrasena": hash_pwd,
        "saldo_cifrado":   saldo_cifrado,  
        "rol": "usuario",
    })
    return {"mensaje": "Usuario creado.", "id": usuario_id}

@app.post("/api/login")
async def iniciar_sesion(datos: EsquemaLogin):
    usuario = await _repo_usuarios.buscar_por_nombre(datos.nombre_usuario)
    if not usuario or not verificar_contrasena(datos.contrasena, usuario["hash_contrasena"]):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas.")

    token = crear_token(str(usuario["_id"]), usuario["rol"])
    return {"token": token, "usuario": datos.nombre_usuario}

@app.post("/api/transacciones")
async def crear_transaccion(
    datos: EsquemaTransaccion,
    usuario_actual: dict = Depends(obtener_usuario_actual)
):
    try:
        resultado = await _svc_tx.registrar(
            usuario_id=usuario_actual["sub"],
            monto=datos.monto,
            tipo=datos.tipo,
        )
        return {"exito": True, "transaccion": resultado}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/resumen")
async def obtener_resumen(usuario_actual: dict = Depends(obtener_usuario_actual)):
    resumen = await _svc_tx.generar_resumen(usuario_actual["sub"])
    saldo   = await _svc_usuarios.obtener_saldo(usuario_actual["sub"])
    return {"saldo_actual": saldo, **resumen}

@app.get("/api/transacciones/{transaccion_id}/verificar")
async def verificar_transaccion(
    transaccion_id: str,
    usuario_actual: dict = Depends(obtener_usuario_actual)
):
    return await _svc_tx.verificar_transaccion(transaccion_id)

@app.get("/api/saldo")
async def obtener_saldo(usuario_actual: dict = Depends(obtener_usuario_actual)):
    saldo = await _svc_usuarios.obtener_saldo(usuario_actual["sub"])
    return {"saldo": saldo}

#Inicio del servidor
if __name__ == "__main__":
    uvicorn.run(
        "presentacion.api:app",
        host="0.0.0.0",
        port=8000,
        workers=4,
        loop="uvloop",
        reload=False,
    )