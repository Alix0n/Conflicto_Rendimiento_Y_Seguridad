MONGO_URI = "mongodb+srv://alixon_lop:2xqGzQUGfv9UP2e0@cluster0.cslxo2a.mongodb.net/?appName=Cluster0"
NOMBRE_BD = "sistema_transacciones"

CLAVE_CIFRADO = "clave-secreta-32-bytes-exactos!!"   
ALGORITMO_JWT = "HS256"
SECRETO_JWT = "jwt-secreto-super-seguro-2024"
EXPIRACION_TOKEN_MINUTOS = 60

TAMANO_POOL_CONEXIONES = 50          
MAX_WORKERS_ASYNC = 100             
LIMITE_TRANSACCIONES_PAGINA = 50   

COMISIONES = {
    "retiro":       0.010,  
    "transferencia":0.015,   
    "pago":         0.007,   
}