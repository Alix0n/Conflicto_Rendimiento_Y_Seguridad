import hashlib
import hmac
import json
import base64
import secrets
from datetime import datetime, timedelta
from typing import Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from passlib.context import CryptContext
import jwt
from config.configuracion import CLAVE_CIFRADO, SECRETO_JWT, ALGORITMO_JWT, EXPIRACION_TOKEN_MINUTOS

_contexto_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
_CLAVE_BYTES = CLAVE_CIFRADO.encode("utf-8")[:32]

def cifrar_dato(dato: str) -> str:
    iv = secrets.token_bytes(16)
    cipher = Cipher(algorithms.AES(_CLAVE_BYTES), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    datos_bytes = dato.encode("utf-8")
    relleno = 16 - (len(datos_bytes) % 16)
    datos_bytes += bytes([relleno] * relleno)
    cifrado = encryptor.update(datos_bytes) + encryptor.finalize()
    return base64.b64encode(iv + cifrado).decode("utf-8")

def descifrar_dato(dato_cifrado: str) -> str:
    raw = base64.b64decode(dato_cifrado.encode("utf-8"))
    iv, cifrado = raw[:16], raw[16:]
    cipher = Cipher(algorithms.AES(_CLAVE_BYTES), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    datos_bytes = decryptor.update(cifrado) + decryptor.finalize()
    relleno = datos_bytes[-1]
    return datos_bytes[:-relleno].decode("utf-8")

def generar_hash_transaccion(datos: dict) -> str:
    campos_criticos = {
        "usuario_id": datos.get("usuario_id"),
        "monto":      datos.get("monto"),
        "tipo":       datos.get("tipo"),
        "timestamp":  datos.get("timestamp"),
    }
    mensaje = json.dumps(campos_criticos, sort_keys=True, ensure_ascii=False)
    return hmac.new(_CLAVE_BYTES, mensaje.encode("utf-8"), hashlib.sha256).hexdigest()


def verificar_integridad(datos: dict, hash_guardado: str) -> bool:
    hash_calculado = generar_hash_transaccion(datos)
    return hmac.compare_digest(hash_calculado, hash_guardado)

def hashear_contrasena(contrasena: str) -> str:
    return _contexto_pwd.hash(contrasena)

def verificar_contrasena(contrasena: str, hash_guardado: str) -> bool:
    return _contexto_pwd.verify(contrasena, hash_guardado)

#Tokens
def crear_token(usuario_id: str, rol: str) -> str:
    expira = datetime.utcnow() + timedelta(minutes=EXPIRACION_TOKEN_MINUTOS)
    payload = {
        "sub": usuario_id,
        "rol": rol,
        "exp": expira,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, SECRETO_JWT, algorithm=ALGORITMO_JWT)

def verificar_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRETO_JWT, algorithms=[ALGORITMO_JWT])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None