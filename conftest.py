"""
Red de seguridad adicional para que pytest encuentre los modulos de src/
sin depender de que pytest.ini se haya leido bien (ver Manual de Estudiante,
seccion de instalacion: un pytest.ini guardado con el Bloc de notas de
Windows puede quedar con un BOM invisible que hace que la clave
"pythonpath" se ignore en silencio).

Los archivos .py si descartan el BOM automaticamente al ser parseados por
Python, asi que conftest.py es seguro incluso si el docente o el alumno lo
guardan con un editor de texto simple.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
