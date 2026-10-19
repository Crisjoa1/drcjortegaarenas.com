# Registrar una página nueva

Cada archivo `.json` de esta carpeta registra una página. `python3 _tools/build.py` la genera en español y en inglés.

```json
{
  "plantilla": "plantilla-iv.html",
  "tipo": "servicio",
  "revisado": "2026-10-19",
  "audiencia": {"es": "Viajeros y residentes en CDMX", "en": "Travelers and residents in Mexico City"},
  "citas": [
    {"nombre": "CDC Yellow Book 2026: High-Altitude Travel", "url": "https://..."}
  ],
  "es": {
    "path": "/hidratacion-intravenosa/",
    "title": "Hidratación intravenosa en CDMX con valoración médica | Dr. Ortega-Arenas",
    "description": "Hasta ~155 caracteres; responde qué es, dónde y desde cuánto.",
    "crumb": "Hidratación intravenosa"
  },
  "en": {
    "path": "/en/iv-hydration-mexico-city/",
    "title": "IV Hydration in Mexico City with Medical Assessment | Dr. Ortega-Arenas",
    "description": "...",
    "crumb": "IV hydration"
  }
}
```

- `tipo`: `servicio` o `guia`.
- `citas`: solo en las guías; deben ser fuentes reales y verificadas.
- Para una página que solo existe en español, omite `"en"`.
- Los títulos deben medir 60 caracteres o menos cuando sea posible.
