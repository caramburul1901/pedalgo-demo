"""
PedalGo - Sistema de alquiler de bicicletas compartidas (bike-sharing).

Modulo de dominio: gestion de bicicletas y reservas.

Caso ancla usado en Calidad y Pruebas de Software (UPN) para la demo de
GitHub Actions + Kiwi TCMS. Los identificadores REQ-xxx y DEF-xxx en los
comentarios y en los nombres de las pruebas hacen referencia a los
requisitos y defectos ya documentados para PedalGo en el curso.
"""


class BicicletaNoEncontradaError(Exception):
    """Se lanza cuando se referencia una bicicleta que no existe."""


class BicicletaNoDisponibleError(Exception):
    """Se lanza cuando se intenta reservar una bicicleta que no esta disponible
    (ya reservada o reportada en falla). Cubre REQ-006: una bicicleta con una
    falla reportada no debe aparecer disponible para reserva."""


class ReservaNoEncontradaError(Exception):
    """Se lanza cuando se referencia una reserva que no existe."""


class RepositorioBicicletas:
    """Almacen en memoria de bicicletas. En un proyecto real esto seria una
    base de datos; para la demo basta con un diccionario."""

    def __init__(self):
        self._bicicletas = {}

    def registrar(self, bici_id, ubicacion="Estacion Central"):
        self._bicicletas[bici_id] = {
            "id": bici_id,
            "estado": "disponible",
            "ubicacion": ubicacion,
        }

    def obtener(self, bici_id):
        bici = self._bicicletas.get(bici_id)
        if bici is None:
            raise BicicletaNoEncontradaError(
                f"No existe una bicicleta con id '{bici_id}'."
            )
        return bici

    def actualizar_estado(self, bici_id, nuevo_estado):
        bici = self.obtener(bici_id)
        bici["estado"] = nuevo_estado

    def reportar_falla(self, bici_id):
        """REQ-006: al reportar una falla, la bicicleta deja de estar
        disponible para reserva de inmediato."""
        self.actualizar_estado(bici_id, "en_falla")


class ServicioReservas:
    """Reglas de negocio de reserva y finalizacion de viajes."""

    TARIFA_BASE = 2.00          # S/ por desbloquear la bicicleta
    TARIFA_POR_MINUTO = 0.30    # S/ por minuto de uso
    MINUTOS_LIBRES = 10         # primeros 10 minutos incluidos en la tarifa base

    def __init__(self, repositorio_bicicletas):
        self._repo = repositorio_bicicletas
        self._reservas = {}
        self._siguiente_id = 1
        # Historial de cobros por usuario (simula la cuenta/billetera del
        # usuario). Es el estado que revela si un cobro se duplico.
        self._historial_cobros = {}

    def calcular_tarifa(self, minutos):
        """Calcula el costo de un viaje segun los minutos de uso."""
        if minutos < 0:
            raise ValueError("Los minutos de uso no pueden ser negativos.")
        minutos_cobrables = max(0, minutos - self.MINUTOS_LIBRES)
        return round(self.TARIFA_BASE + minutos_cobrables * self.TARIFA_POR_MINUTO, 2)

    def reservar(self, bici_id, usuario_id):
        """Reserva una bicicleta para un usuario.

        REQ-006: si la bicicleta esta en falla (o ya reservada), no se
        permite la reserva -> BicicletaNoDisponibleError.
        """
        bici = self._repo.obtener(bici_id)
        if bici["estado"] != "disponible":
            raise BicicletaNoDisponibleError(
                f"La bicicleta '{bici_id}' no esta disponible "
                f"(estado actual: '{bici['estado']}')."
            )

        reserva_id = self._siguiente_id
        self._siguiente_id += 1
        self._reservas[reserva_id] = {
            "id": reserva_id,
            "bici_id": bici_id,
            "usuario_id": usuario_id,
            "finalizada": False,
            "monto_cobrado": None,
        }
        self._repo.actualizar_estado(bici_id, "reservada")
        return reserva_id

    def finalizar(self, reserva_id, minutos_uso):
        """Finaliza una reserva y cobra el viaje.

        DEF-002 (corregido): finalizar dos veces la misma reserva NO debe
        duplicar el cobro. La primera vez que se finaliza, se calcula y se
        guarda el monto; si se vuelve a llamar a finalizar() sobre una
        reserva ya finalizada, se devuelve el mismo monto ya cobrado sin
        volver a ejecutar calcular_tarifa() ni recobrar.
        """
        reserva = self._reservas.get(reserva_id)
        if reserva is None:
            raise ReservaNoEncontradaError(
                f"No existe una reserva con id '{reserva_id}'."
            )

        # --- FIX DEF-002: guarda de idempotencia -------------------------
        # Si se elimina o comenta este bloque "if", volver a llamar a
        # finalizar() sobre la misma reserva recalcula y "recobra" el
        # viaje -- esta es la reproduccion en vivo del defecto DEF-002
        # para la demo de GitHub Actions (romper la prueba a proposito).
        if reserva["finalizada"]:
        return reserva["monto_cobrado"]
        # -------------------------------------------------------------

        monto = self.calcular_tarifa(minutos_uso)
        reserva["finalizada"] = True
        reserva["monto_cobrado"] = monto
        self._repo.actualizar_estado(reserva["bici_id"], "disponible")

        usuario_id = reserva["usuario_id"]
        self._historial_cobros.setdefault(usuario_id, [])
        self._historial_cobros[usuario_id].append(monto)

        return monto

    def obtener_reserva(self, reserva_id):
        reserva = self._reservas.get(reserva_id)
        if reserva is None:
            raise ReservaNoEncontradaError(
                f"No existe una reserva con id '{reserva_id}'."
            )
        return reserva

    def total_cobrado(self, usuario_id):
        """Suma de todos los cobros aplicados a un usuario. Si DEF-002 se
        reintroduce (se quita la guarda de idempotencia), este total queda
        duplicado cada vez que se vuelve a finalizar la misma reserva."""
        return round(sum(self._historial_cobros.get(usuario_id, [])), 2)
