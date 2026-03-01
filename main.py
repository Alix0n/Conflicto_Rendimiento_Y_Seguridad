#python main.py

import asyncio
import uvicorn
from datos.repositorios import RepositorioUsuarios, RepositorioTransacciones


async def inicializar_bd():
    print("Inicializando índices en MongoDB...")
    await RepositorioUsuarios().crear_indices()
    await RepositorioTransacciones().crear_indices()
    print("Índices listos.")


if __name__ == "__main__":
    asyncio.run(inicializar_bd())

    print("\nIniciando servidor en http://localhost:8000\n")
    uvicorn.run(
        "presentacion.api:app",
        host="0.0.0.0",
        port=8000,
        workers=1,          
        loop="asyncio",
        reload=True,       
    )