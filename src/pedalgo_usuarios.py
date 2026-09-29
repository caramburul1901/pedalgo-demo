"""
PedalGo - Modulo de usuarios y seguridad de cuenta.

Cubre REQ-005 (seguridad de cuenta): registro con validaciones basicas y
bloqueo de cuenta tras intentos fallidos de inicio de sesion.
"""

import re

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
INTENTOS_MAXIMOS = 5


class DatosInvalidosError(Exception):
    """Se lanza cuando los datos de registro no cumplen las validaciones."""


class UsuarioYaExisteError(Exception):
    """Se lanza al intentar registrar un correo ya existente."""


class CredencialesInvalidasError(Exception):
    """Se lanza cuando el correo no existe o la contrasena es incorrecta."""


class CuentaBloqueadaError(Exception):
    """REQ-005: se lanza cuando la cuenta fue bloqueada por exceso de
    intentos fallidos de inicio de sesion."""


class RepositorioUsuarios:
    def __init__(self):
        self._usuarios = {}

    def existe(self, email):
        return email in self._usuarios

    def guardar(self, usuario):
        self._usuarios[usuario["email"]] = usuario

    def obtener(self, email):
        return self._usuarios.get(email)


class ServicioUsuarios:
    def __init__(self, repositorio_usuarios):
        self._repo = repositorio_usuarios

    def registrar(self, nombre, email, edad, password):
        if not nombre or not nombre.strip():
            raise DatosInvalidosError("El nombre es obligatorio.")
        if not EMAIL_REGEX.match(email or ""):
            raise DatosInvalidosError(f"El correo '{email}' no es valido.")
        if not (18 <= edad <= 99):
            raise DatosInvalidosError("La edad debe estar entre 18 y 99 anios.")
        if not password or len(password) < 8:
            raise DatosInvalidosError(
                "La contrasena debe tener al menos 8 caracteres."
            )
        if self._repo.existe(email):
            raise UsuarioYaExisteError(f"Ya existe una cuenta con el correo '{email}'.")

        self._repo.guardar({
            "nombre": nombre,
            "email": email,
            "edad": edad,
            "password": password,
            "intentos_fallidos": 0,
            "bloqueado": False,
        })
        return True

    def iniciar_sesion(self, email, password):
        """REQ-005: bloquea la cuenta al quinto intento fallido consecutivo."""
        usuario = self._repo.obtener(email)

        if usuario is not None and usuario["bloqueado"]:
            raise CuentaBloqueadaError(
                f"La cuenta '{email}' esta bloqueada por exceso de intentos "
                f"fallidos. Contacta a soporte para restablecerla."
            )

        if usuario is None or usuario["password"] != password:
            if usuario is not None:
                usuario["intentos_fallidos"] += 1
                if usuario["intentos_fallidos"] >= INTENTOS_MAXIMOS:
                    usuario["bloqueado"] = True
            raise CredencialesInvalidasError("Correo o contrasena incorrectos.")

        usuario["intentos_fallidos"] = 0
        return True
