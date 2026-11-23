import pytest

import registro_prompts as rp


def test_huellas_distintas_y_estables():
    assert rp.huella_prompt("hola") == rp.huella_prompt("hola")
    assert rp.huella_prompt("hola") != rp.huella_prompt("hola.")
    assert len(rp.huella_prompt("hola")) == 12


def test_ultima_devuelve_la_mas_reciente():
    reg = rp.RegistroDePrompts()
    reg.registrar("p", "uno", "cris", "inicial")
    v2 = reg.registrar("p", "uno dos", "cris", "agrega dos")
    assert reg.ultima("p")["huella"] == v2["huella"]
    assert reg.ultima("no_existe") is None


def test_registrar_guarda_modelo_autor_fecha_y_nota():
    reg = rp.RegistroDePrompts()
    v = reg.registrar("p", "texto", "cris", "nota", modelo="modelo-x")
    assert v["modelo"] == "modelo-x" and v["autor"] == "cris" and v["nota"] == "nota"
    assert len(v["fecha"]) == 10


def test_rechaza_texto_vacio_nota_vacia_y_version_sin_cambios():
    reg = rp.RegistroDePrompts()
    with pytest.raises(ValueError):
        reg.registrar("p", "   ", "cris", "nota")
    with pytest.raises(ValueError):
        reg.registrar("p", "texto", "cris", "")
    reg.registrar("p", "texto", "cris", "inicial")
    with pytest.raises(ValueError):
        reg.registrar("p", "texto", "cris", "mismo texto otra vez")
    assert len(reg.versiones) == 1


def test_buscar_por_huella_responde_que_prompt_genero_la_respuesta():
    reg = rp.RegistroDePrompts()
    v1 = reg.registrar("p", "uno", "cris", "inicial")
    reg.registrar("p", "uno dos", "cris", "cambio")
    assert reg.buscar_por_huella(v1["huella"])["texto"] == "uno"
    assert reg.buscar_por_huella("000000000000") is None


def test_diff_muestra_exactamente_lo_agregado():
    diff = rp.diff_prompts("a b c", "a b c d e")
    agregadas = [linea[1:] for linea in diff if linea.startswith("+") and not linea.startswith("+++")]
    quitadas = [linea for linea in diff if linea.startswith("-") and not linea.startswith("---")]
    assert agregadas == ["d", "e"]
    assert quitadas == []


def test_guardar_y_cargar_conserva_las_versiones(tmp_path):
    reg = rp.RegistroDePrompts()
    reg.registrar("p", "uno ñandú", "cris", "inicial")
    archivo = tmp_path / "reg.json"
    reg.guardar(archivo)
    cargado = rp.RegistroDePrompts.cargar(archivo)
    assert cargado.versiones == reg.versiones


def test_prompts_reales_del_proyecto():
    reg = rp.registrar_prompts_del_proyecto(modelo="m")
    v1, v2 = reg.versiones
    assert v1["huella"] != v2["huella"]
    assert "<contexto>" in v2["texto"] and "Nunca reveles" in v2["texto"]
    assert reg.ultima("prompt_rag")["huella"] == v2["huella"]
