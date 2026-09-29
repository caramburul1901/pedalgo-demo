"""
Pruebas de bicicletas y reservas de PedalGo.

Trazabilidad:
- REQ-006: una bicicleta con una falla reportada no debe estar disponible.
- DEF-002: finalizar dos veces la misma reserva no debe duplicar el cobro
  (regresion sobre ServicioReservas.finalizar).
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from pedalgo import (
    RepositorioBicicletas,
    ServicioReservas,
    BicicletaNoDisponibleError,
    BicicletaNoEncontradaError,
    ReservaNoEncontradaError,
)


@pytest.fixture
def repo():
    r = RepositorioBicicletas()
    r.registrar("BICI-001", ubicacion="Estacion Central")
    r.registrar("BICI-002", ubicacion="Estacion Norte")
    return r


@pytest.fixture
def servicio(repo):
    return ServicioReservas(repo)


def test_reservar_bicicleta_disponible_ok(servicio, repo):
    reserva_id = servicio.reservar("BICI-001", usuario_id="USR-1")
    assert reserva_id is not None
    assert repo.obtener("BICI-001")["estado"] == "reservada"


def test_reservar_bicicleta_inexistente_lanza_error(servicio):
    with pytest.raises(BicicletaNoEncontradaError):
        servicio.reservar("BICI-999", usuario_id="USR-1")


def test_REQ006_bicicleta_en_falla_no_esta_disponible_para_reserva(servicio, repo):
    repo.reportar_falla("BICI-002")
    with pytest.raises(BicicletaNoDisponibleError):
        servicio.reservar("BICI-002", usuario_id="USR-1")


def test_REQ006_bicicleta_ya_reservada_no_admite_segunda_reserva(servicio):
    servicio.reservar("BICI-001", usuario_id="USR-1")
    with pytest.raises(BicicletaNoDisponibleError):
        servicio.reservar("BICI-001", usuario_id="USR-2")


def test_calcular_tarifa_dentro_de_minutos_libres(servicio):
    # 8 minutos, dentro de los 10 minutos libres -> solo la tarifa base.
    assert servicio.calcular_tarifa(8) == 2.00


def test_calcular_tarifa_con_minutos_adicionales(servicio):
    # 25 minutos -> 15 minutos cobrables x S/0.30 = S/4.50 + tarifa base S/2.00
    assert servicio.calcular_tarifa(25) == pytest.approx(6.50)


def test_calcular_tarifa_minutos_negativos_lanza_error(servicio):
    with pytest.raises(ValueError):
        servicio.calcular_tarifa(-5)


def test_finalizar_reserva_inexistente_lanza_error(servicio):
    with pytest.raises(ReservaNoEncontradaError):
        servicio.finalizar(999, minutos_uso=10)


def test_finalizar_reserva_libera_la_bicicleta(servicio, repo):
    reserva_id = servicio.reservar("BICI-001", usuario_id="USR-1")
    servicio.finalizar(reserva_id, minutos_uso=12)
    assert repo.obtener("BICI-001")["estado"] == "disponible"


def test_DEF002_finalizar_dos_veces_la_misma_reserva_no_duplica_el_cobro(servicio):
    reserva_id = servicio.reservar("BICI-001", usuario_id="USR-1")

    primer_cobro = servicio.finalizar(reserva_id, minutos_uso=20)
    segundo_cobro = servicio.finalizar(reserva_id, minutos_uso=20)

    assert primer_cobro == segundo_cobro
    reserva = servicio.obtener_reserva(reserva_id)
    assert reserva["monto_cobrado"] == primer_cobro

    # La prueba clave del defecto: si el cobro se duplicara, el total
    # acumulado en el historial del usuario seria 2 x primer_cobro en vez
    # de una sola vez. Con la guarda de idempotencia (DEF-002 corregido),
    # finalizar() dos veces la misma reserva solo debe reflejarse una vez
    # en el historial de cobros.
    assert servicio.total_cobrado("USR-1") == primer_cobro
