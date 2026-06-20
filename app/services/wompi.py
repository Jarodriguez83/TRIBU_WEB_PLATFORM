import hashlib
import httpx
from typing import Optional, Dict, Any
from app.config import settings

class WompiService:
    """
    Servicio de integración con la pasarela de pagos Wompi (Colombia).
    Documentación oficial: https://docs.wompi.co/
    """
    
    @staticmethod
    def generar_firma_integridad(referencia: str, total_cop: float, moneda: str = "COP") -> str:
        """
        Genera la firma de integridad requerida por Wompi para iniciar transacciones seguras.
        Fórmula: SHA256(referencia + monto_en_centavos + moneda + secreto_de_integridad)
        """
        monto_centavos = int(total_cop * 100)
        # Se usa la llave de eventos o privada como secreto de firma en desarrollo/producción
        # En producción de Wompi, hay una 'Llave de integridad' específica que se puede configurar aquí
        secreto = settings.WOMPI_EVENTS_KEY  # O una llave dedicada si estuviera configurada
        
        cadena = f"{referencia}{monto_centavos}{moneda}{secreto}"
        return hashlib.sha256(cadena.encode("utf-8")).hexdigest()

    @staticmethod
    def validar_firma_webhook(payload: Dict[str, Any]) -> bool:
        """
        Valida que el webhook recibido provenga realmente de Wompi.
        Wompi envía en el payload la propiedad `signature` con las propiedades que concatenaron
        y el checksum generado con la llave de eventos.
        """
        try:
            signature_info = payload.get("signature")
            if not signature_info:
                return False
            
            properties = signature_info.get("properties", [])
            received_checksum = signature_info.get("checksum")
            timestamp = payload.get("timestamp")
            
            # Wompi especifica el orden de las propiedades. Ej:
            # ['transaction.id', 'transaction.status', 'transaction.amount_in_cents', 'timestamp']
            data = payload.get("data", {})
            transaction = data.get("transaction", {})
            
            # Reconstruir la cadena concatenando los valores en el orden indicado
            cadena_concatenada = ""
            for prop in properties:
                if prop == "transaction.id":
                    cadena_concatenada += str(transaction.get("id", ""))
                elif prop == "transaction.status":
                    cadena_concatenada += str(transaction.get("status", ""))
                elif prop == "transaction.amount_in_cents":
                    cadena_concatenada += str(transaction.get("amount_in_cents", ""))
                elif prop == "timestamp":
                    cadena_concatenada += str(timestamp)
            
            # Añadir la llave de eventos (secreto) al final de la concatenación
            cadena_concatenada += settings.WOMPI_EVENTS_KEY
            
            # Calcular el hash SHA256
            calculated_checksum = hashlib.sha256(cadena_concatenada.encode("utf-8")).hexdigest()
            return calculated_checksum == received_checksum
        except Exception:
            return False

    @staticmethod
    async def consultar_transaccion(transaccion_id: str) -> Optional[Dict[str, Any]]:
        """
        Consulta el estado de una transacción directamente desde la API de Wompi.
        Útil para la redirección de retorno del usuario o conciliación.
        """
        url = f"{settings.WOMPI_BASE_URL}/transactions/{transaccion_id}"
        headers = {
            "Authorization": f"Bearer {settings.WOMPI_PUBLIC_KEY}"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, timeout=10.0)
                if response.status_code == 200:
                    return response.json().get("data")
                return None
            except Exception:
                return None
