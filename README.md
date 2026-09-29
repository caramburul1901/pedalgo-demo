# PedalGo — Proyecto de demo (GitHub Actions + Kiwi TCMS)

Curso: Calidad y Pruebas de Software (UPN). Este repositorio es el
proyecto que se usa para la demo en vivo de **GitHub Actions** (CI) y
como fuente de casos de prueba reales para **Kiwi TCMS**.

No es un proyecto de referencia teórico: las 21 pruebas de este
repositorio se ejecutaron de verdad con `pytest` antes de entregarlo.

## Qué hace PedalGo

Un sistema simplificado de alquiler de bicicletas compartidas
(bike-sharing): reservar una bicicleta, finalizar el viaje y cobrarlo, y
registro/login de usuarios con bloqueo de cuenta por seguridad.

## Estructura

```
pedalgo_demo_ci/
├── src/
│   ├── pedalgo.py            # Bicicletas y reservas (REQ-006, DEF-002)
│   └── pedalgo_usuarios.py   # Usuarios y seguridad de cuenta (REQ-005)
├── tests/
│   ├── test_pedalgo_bicicletas.py
│   └── test_pedalgo_usuarios.py
├── .github/workflows/ci.yml  # Workflow de GitHub Actions
├── conftest.py                # Red de seguridad de import (ver manual)
├── pytest.ini
└── requirements.txt
```

## Trazabilidad de requisitos y defectos usados en el curso

| ID | Descripción | Dónde vive |
|---|---|---|
| REQ-006 | Una bicicleta con una falla reportada no debe estar disponible para reserva | `test_REQ006_*` en `test_pedalgo_bicicletas.py` |
| REQ-005 | Seguridad de cuenta: bloqueo tras 5 intentos fallidos de inicio de sesión | `test_REQ005_*` en `test_pedalgo_usuarios.py` |
| DEF-002 | Finalizar dos veces la misma reserva no debe duplicar el cobro | `test_DEF002_*` en `test_pedalgo_bicicletas.py`, guarda de idempotencia en `ServicioReservas.finalizar()` |
| DEF-001 | Desbloqueo lento de la bicicleta en red 3G/4G (defecto de rendimiento, no automatizado) | Se usa como caso de prueba **manual** en Kiwi TCMS — ver el Manual de Estudiante/Guía Docente, no tiene prueba pytest asociada |

## Ejecutar las pruebas localmente

```bash
python3 -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate
pip install -r requirements.txt
pytest -v
```

Debe mostrar `21 passed`.

## Cómo "romper" DEF-002 a propósito (para la demo de GitHub Actions)

En `src/pedalgo.py`, dentro del método `finalizar()`, comenta las dos
líneas marcadas `# --- FIX DEF-002` (el bloque `if reserva["finalizada"]:
return reserva["monto_cobrado"]`). Guarda, haz commit y push: la prueba
`test_DEF002_finalizar_dos_veces_la_misma_reserva_no_duplica_el_cobro`
pasará a fallar y el check de GitHub Actions se pondrá en rojo. Para
corregirlo, descomenta esas mismas líneas y vuelve a hacer push.

Ver el detalle paso a paso, con número de línea exacto, en la Guía
Docente.
