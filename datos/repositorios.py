from datetime import datetime
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorClient  
from bson import ObjectId

from config.configuracion import MONGO_URI, NOMBRE_BD, TAMANO_POOL_CONEXIONES

_cliente: Optional[AsyncIOMotorClient] = None

def obtener_cliente() -> AsyncIOMotorClient:
    global _cliente
    if _cliente is None:
        _cliente = AsyncIOMotorClient(
            MONGO_URI,
            maxPoolSize=TAMANO_POOL_CONEXIONES,  
            serverSelectionTimeoutMS=5000,
        )
    return _cliente

def obtener_bd():
    return obtener_cliente()[NOMBRE_BD]

class RepositorioUsuarios:

    def __init__(self):
        self.coleccion = obtener_bd()["usuarios"]

    async def crear_indices(self):
        await self.coleccion.create_index("nombre_usuario", unique=True)

    async def crear_usuario(self, datos: dict) -> str:
        resultado = await self.coleccion.insert_one(datos)
        return str(resultado.inserted_id)

    async def buscar_por_nombre(self, nombre_usuario: str) -> Optional[dict]:
        return await self.coleccion.find_one({"nombre_usuario": nombre_usuario})

    async def buscar_por_id(self, usuario_id: str) -> Optional[dict]:
        return await self.coleccion.find_one({"_id": ObjectId(usuario_id)})

    async def actualizar_saldo(self, usuario_id: str, nuevo_saldo: float):
        await self.coleccion.update_one(
            {"_id": ObjectId(usuario_id)},
            {"$set": {"saldo_cifrado": nuevo_saldo}}
        )

class RepositorioTransacciones:

    def __init__(self):
        self.coleccion = obtener_bd()["transacciones"]

    async def crear_indices(self):
        await self.coleccion.create_index([("usuario_id", 1), ("timestamp", -1)])
        await self.coleccion.create_index("timestamp")

    async def guardar(self, transaccion: dict) -> str:
        resultado = await self.coleccion.insert_one(transaccion)
        return str(resultado.inserted_id)

    async def buscar_por_id(self, transaccion_id: str) -> Optional[dict]:
        return await self.coleccion.find_one({"_id": ObjectId(transaccion_id)})

    async def listar_por_usuario(self, usuario_id: str, limite: int = 50) -> List[dict]:
        cursor = self.coleccion.find(
            {"usuario_id": usuario_id},
            sort=[("timestamp", -1)],
            limit=limite
        )
        return await cursor.to_list(length=limite)

    async def resumen_por_usuario(self, usuario_id: str) -> dict:
        pipeline = [
            {"$match": {"usuario_id": usuario_id}},
            {"$group": {
                "_id": "$tipo",
                "total_monto": {"$sum": "$monto"},
                "total_comision": {"$sum": "$comision"},
                "cantidad": {"$sum": 1},
            }},
        ]
        cursor = self.coleccion.aggregate(pipeline)
        return await cursor.to_list(length=100)