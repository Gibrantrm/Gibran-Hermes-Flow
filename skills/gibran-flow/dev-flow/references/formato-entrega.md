# Formato de entrega (todos los agentes)

Termina SIEMPRE con este bloque, sin texto después:

    RESULTADO: hecho | bloqueado | necesita-decisión
    EVIDENCIA: comandos que ejecutaste y la parte relevante de su salida
    CAMBIOS: archivos tocados (ruta relativa) o "ninguno"
    HALLAZGOS:
    - archivo:línea — qué encontraste (confianza NN%)
    PENDIENTE: lo que no verificaste o quedó fuera; "nada" si nada

Reglas:
- Sin EVIDENCIA ejecutada, RESULTADO no puede ser "hecho".
- Datos personales (nombres, correos, teléfonos, CURP, RFC) enmascarados: `J*** P***`.
- Nunca incluyas credenciales ni cadenas de conexión.
