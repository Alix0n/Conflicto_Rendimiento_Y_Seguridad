Taller 1 – Conflicto entre Rendimiento y Seguridad

Este proyecto corresponde a la práctica 1 de ingeniería de software II, cuyo objetivo es diseñar e implementar un sistema de procesamiento de transacciones financieras que cumpla simultáneamente con dos atributos de calidad fundamentales correspondientes a rendimiento y seguridad.

El contexto del ejercicio planteado es: El sistema simula una plataforma utilizada por aproximadamente 5.000 usuarios concurrentes, encargada de procesar transacciones financieras durante el día. Dentro de las consideraciones se tiene que: el sistema debe procesar la mayor cantidad posible de transacciones por segundo, debe minimizar el tiempo de respuesta, debe garantizar la integridad de la información, debe proteger datos sensibles y evitar manipulaciones indebidas.

Funcionalidades Implementadas

- Registro de transacciones (monto, usuario, tipo).
- Cálculo automático de comisión según tipo de transacción.
- Validación de saldo disponible.
- Persistencia de datos.
- Generación de resumen de transacciones.

El sistema fue diseñado bajo una estructura modular, permitiendo:

- Separación entre lógica de negocio y persistencia.
- Implementación de validaciones de seguridad.
- Optimización de procesos críticos para mejorar rendimiento.
- Posibilidad de escalar o reforzar seguridad según el contexto estratégico.

Comando para clonar el respositorio: git clone "https://github.com/Alix0n/Conflicto_Rendimiento_Y_Seguridad.git"
Comando para ejecutar: python main.py
