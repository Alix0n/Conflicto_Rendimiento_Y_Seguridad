from datetime import datetime, timezone
from typing import Optional

from config.configuracion import COMISIONES
from datos.repositorios import RepositorioUsuarios, RepositorioTransacciones
from seguridad.seguridad import (cifrar_dato, descifrar_dato,generar_hash_transaccion, verificar_integridad)

_repo_usuarios      = RepositorioUsuarios()
_repo_transacciones = RepositorioTransacciones()

class ServicioTransacciones:

    @staticmethod
    def calcular_comision(monto: float, tipo: str) -> float:
        tasa = COMISIONES.get(tipo, 0.01)
        return round(monto * tasa, 3)

    @staticmethod
    async def validar_saldo(usuario_id: str, monto: float, tipo: str) -> bool:
        if tipo not in ("retiro", "pago"):
            return True
        usuario = await _repo_usuarios.buscar_por_id(usuario_id)
        if not usuario:
            return False
        saldo_actual = float(descifrar_dato(usuario["saldo_cifrado"]))
        comision     = ServicioTransacciones.calcular_comision(monto, tipo)
        return saldo_actual >= (monto + comision)

    #Registrar transacción
    async def registrar(self, usuario_id: str, monto: float, tipo: str) -> dict:
        if tipo not in COMISIONES:
            raise ValueError(f"Tipo de transacción no válido: {tipo}")

        if monto <= 0:
            raise ValueError("El monto debe ser mayor a cero.")

        saldo_ok = await self.validar_saldo(usuario_id, monto, tipo)
        if not saldo_ok:
            raise ValueError("Saldo insuficiente para realizar la transacción.")

        comision  = self.calcular_comision(monto, tipo)
        timestamp = datetime.now(timezone.utc).isoformat()

        datos_hash = {
            "usuario_id": usuario_id,
            "monto":      monto,
            "tipo":       tipo,
            "timestamp":  timestamp,
        }
        hash_integridad = generar_hash_transaccion(datos_hash)

        documento = {
            "usuario_id":     usuario_id,
            "monto_cifrado":  cifrar_dato(str(monto)),     #dato cifrado
            "comision":       comision,
            "tipo":           tipo,
            "timestamp":      timestamp,
            "hash_integridad": hash_integridad,           
            "monto":          monto,                       #para cálculos internos
        }

        transaccion_id = await _repo_transacciones.guardar(documento)
        await self._actualizar_saldo_usuario(usuario_id, monto, comision, tipo)

        return {
            "id":        transaccion_id,
            "tipo":      tipo,
            "monto":     monto,
            "comision":  comision,
            "timestamp": timestamp,
            "hash":      hash_integridad,
        }

    async def _actualizar_saldo_usuario(
        self, usuario_id: str, monto: float, comision: float, tipo: str
    ):
        usuario      = await _repo_usuarios.buscar_por_id(usuario_id)
        saldo_actual = float(descifrar_dato(usuario["saldo_cifrado"]))

        if tipo in ("retiro", "pago", "transferencia"):
            nuevo_saldo = saldo_actual - monto - comision

        await _repo_usuarios.actualizar_saldo(
            usuario_id, cifrar_dato(str(round(nuevo_saldo, 4)))
        )

    @staticmethod
    async def verificar_transaccion(transaccion_id: str) -> dict:
        tx = await _repo_transacciones.buscar_por_id(transaccion_id)
        if not tx:
            return {"valida": False, "mensaje": "Transacción no encontrada."}

        datos = {
            "usuario_id": tx["usuario_id"],
            "monto":      tx["monto"],
            "tipo":       tx["tipo"],
            "timestamp":  tx["timestamp"],
        }
        valida = verificar_integridad(datos, tx["hash_integridad"])
        return {
            "valida":   valida,
            "mensaje":  "Transacción íntegra." if valida else "¡ALERTA: Transacción manipulada!",
            "hash":     tx["hash_integridad"],
        }

    @staticmethod
    async def generar_resumen(usuario_id: str) -> dict:
        filas = await _repo_transacciones.resumen_por_usuario(usuario_id)
        historial = await _repo_transacciones.listar_por_usuario(usuario_id, limite=20)

        for tx in historial:
            tx["monto_visible"] = float(descifrar_dato(tx["monto_cifrado"]))
            tx["_id"] = str(tx["_id"])
            del tx["monto_cifrado"]
            del tx["monto"]       

        return {
            "por_tipo":  filas,
            "historial": historial,
        }

class ServicioUsuarios:

    async def obtener_saldo(self, usuario_id: str) -> float:
        usuario = await _repo_usuarios.buscar_por_id(usuario_id)
        if not usuario:
            raise ValueError("Usuario no encontrado.")
        return float(descifrar_dato(usuario["saldo_cifrado"]))