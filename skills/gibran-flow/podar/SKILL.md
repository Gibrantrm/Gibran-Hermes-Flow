---
name: podar
description: "Gibran Flow: /podar (mensual). Limpia reglas de .hermes.md y revisa propuestas y métricas del flujo."
version: 1.0.1
metadata:
  hermes:
    tags: [gibran-flow, mantenimiento]
---

# podar

Propones; el usuario decide. No borres nada sin aprobación.

1. En el repo actual, lee `.hermes.md`. Propón:
   - quitar reglas que ya no aplican (el código que mencionan ya no existe: verifícalo con rg),
   - fusionar duplicadas,
   - reglas que aparecen en 2+ repos → subir al flujo (propuesta en `propuestas-de-mejora.md`).
   Meta: 60 líneas o menos.
2. Lee `${HERMES_SKILL_DIR}/../../../metricas/correcciones.md`: correcciones del mes
   por categoría, comparadas con el mes anterior. Una línea por categoría.
3. Lee `propuestas-de-mejora.md`: lista las pendientes con tu recomendación (aplicar/descartar).
4. Presenta todo en una tabla. Aplica a `.hermes.md` solo lo aprobado.
