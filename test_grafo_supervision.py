import pytest

import grafo_supervision as gs


@pytest.fixture
def app():
    return gs.construir_grafo()


def test_el_grafo_se_detiene_en_el_punto_de_supervision(app):
    cfg = gs.solicitar_despliegue(app, "abc123")
    pend = gs.pendiente(app, cfg)
    assert pend["huella_propuesta"] == "abc123"
    assert "aprobar" in pend["motivo"]
    # aplicar NO corrio: el resultado sigue vacio
    assert app.get_state(cfg).values["resultado"] == ""
    assert app.get_state(cfg).next == ("supervisar",)


def test_camino_de_aprobacion(app):
    cfg = gs.solicitar_despliegue(app, "abc123")
    final = gs.resolver(app, cfg, True)
    assert final["aprobado"] is True
    assert final["resultado"] == "activada"
    assert gs.pendiente(app, cfg) is None


def test_camino_de_rechazo(app):
    cfg = gs.solicitar_despliegue(app, "abc123")
    final = gs.resolver(app, cfg, False)
    assert final["aprobado"] is False
    assert final["resultado"].startswith("rechazada")


def test_no_se_puede_resolver_dos_veces(app):
    cfg = gs.solicitar_despliegue(app, "abc123")
    gs.resolver(app, cfg, True)
    with pytest.raises(ValueError, match="ninguna aprobacion pendiente"):
        gs.resolver(app, cfg, True)


def test_resolver_exige_booleano_estricto(app):
    cfg = gs.solicitar_despliegue(app, "abc123")
    for malo in ("no", "", 1, 0, None):
        with pytest.raises(TypeError):
            gs.resolver(app, cfg, malo)
    # y la solicitud sigue pendiente: nada se aprobo por error
    assert gs.pendiente(app, cfg) is not None


def test_huella_esperada_distinta_no_aprueba(app):
    cfg = gs.solicitar_despliegue(app, "version-nueva")
    with pytest.raises(ValueError, match="no es la que la persona reviso"):
        gs.resolver(app, cfg, True, huella_esperada="otra-version")
    assert gs.pendiente(app, cfg) is not None
    assert gs.resolver(app, cfg, True, huella_esperada="version-nueva")["resultado"] == "activada"


def test_solicitudes_independientes_no_se_pisan(app):
    cfg1 = gs.solicitar_despliegue(app, "v1")
    cfg2 = gs.solicitar_despliegue(app, "v2")
    assert cfg1["configurable"]["thread_id"] != cfg2["configurable"]["thread_id"]
    gs.resolver(app, cfg2, False)
    assert gs.pendiente(app, cfg1)["huella_propuesta"] == "v1"
    assert gs.resolver(app, cfg1, True)["huella_nueva"] == "v1"


def test_thread_id_desconocido_no_tiene_pendiente(app):
    cfg = {"configurable": {"thread_id": "no-existe"}}
    assert gs.pendiente(app, cfg) is None
    with pytest.raises(ValueError):
        gs.resolver(app, cfg, True)
