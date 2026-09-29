"""
Pruebas de registro y seguridad de cuenta de PedalGo.

Trazabilidad: REQ-005 (seguridad de cuenta) - validaciones de registro y
bloqueo de cuenta tras 5 intentos fallidos de inicio de sesion.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from pedalgo_usuarios import (
    RepositorioUsuarios,
    ServicioUsuarios,
    DatosInvalidosError,
    UsuarioYaExisteError,
    CredencialesInvalidasError,
    CuentaBloqueadaError,
)


@pytest.fixture
def servicio():
    return ServicioUsuarios(RepositorioUsuarios())


def test_registrar_usuario_valido(servicio):
    assert servicio.registrar("Ana Torres", "ana@correo.com", 28, "clave1234")


@pytest.mark.parametrize("edad", [17, 100, -1])
def test_registrar_edad_fuera_de_rango(servicio, edad):
    with pytest.raises(DatosInvalidosError):
        servicio.registrar("Ana Torres", "ana@correo.com", edad, "clave1234")


def test_registrar_email_invalido(servicio):
    with pytest.raises(DatosInvalidosError):
        servicio.registrar("Ana Torres", "no-es-un-correo", 28, "clave1234")


def test_registrar_password_corta(servicio):
    with pytest.raises(DatosInvalidosError):
        servicio.registrar("Ana Torres", "ana@correo.com", 28, "123")


def test_registrar_email_duplicado(servicio):
    servicio.registrar("Ana Torres", "ana@correo.com", 28, "clave1234")
    with pytest.raises(UsuarioYaExisteError):
        servicio.registrar("Ana Otra", "ana@correo.com", 30, "otraClave1")


def test_login_correcto(servicio):
    servicio.registrar("Ana Torres", "ana@correo.com", 28, "clave1234")
    assert servicio.iniciar_sesion("ana@correo.com", "clave1234")


def test_login_password_incorrecta_lanza_error(servicio):
    servicio.registrar("Ana Torres", "ana@correo.com", 28, "clave1234")
    with pytest.raises(CredencialesInvalidasError):
        servicio.iniciar_sesion("ana@correo.com", "otra-clave")


def test_REQ005_bloqueo_cuenta_tras_5_intentos_fallidos(servicio):
    servicio.registrar("Ana Torres", "ana@correo.com", 28, "clave1234")

    for _ in range(5):
        with pytest.raises(CredencialesInvalidasError):
            servicio.iniciar_sesion("ana@correo.com", "clave-incorrecta")

    # El sexto intento (incluso con la clave correcta) ya encuentra la
    # cuenta bloqueada.
    with pytest.raises(CuentaBloqueadaError):
        servicio.iniciar_sesion("ana@correo.com", "clave1234")


def test_login_correcto_resetea_contador_de_intentos_fallidos(servicio):
    servicio.registrar("Ana Torres", "ana@correo.com", 28, "clave1234")

    for _ in range(3):
        with pytest.raises(CredencialesInvalidasError):
            servicio.iniciar_sesion("ana@correo.com", "clave-incorrecta")

    assert servicio.iniciar_sesion("ana@correo.com", "clave1234")

    # Tras un login correcto el contador vuelve a 0: 3 fallos mas
    # (menos de 5) no deberian bloquear la cuenta.
    for _ in range(3):
        with pytest.raises(CredencialesInvalidasError):
            servicio.iniciar_sesion("ana@correo.com", "clave-incorrecta")

    assert servicio.iniciar_sesion("ana@correo.com", "clave1234")
