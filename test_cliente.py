from unittest.mock import patch, Mock
import pytest
import cliente
from src.consumir_gemini import enviar_peticion
from cliente import con_reintento, consultar_modelo


@pytest.fixture(autouse=True)
def reiniciar_costo_total():
    cliente.costo_total_sesion = 0
    yield


def test_enviar_peticion_credencial_invalida():
    respuesta_falsa = Mock(status_code=401)
    with patch("src.consumir_gemini.requests.post", return_value=respuesta_falsa):
        with pytest.raises(ValueError):
            enviar_peticion("https://ejemplo.test", {"pregunta": "test"})


def test_enviar_peticion_limite_de_uso():
    respuesta_falsa = Mock(status_code=429)
    with patch("src.consumir_gemini.requests.post", return_value=respuesta_falsa):
        with pytest.raises(TimeoutError):
            enviar_peticion("https://ejemplo.test", {"pregunta": "test"})


def test_enviar_peticion_exito():
    respuesta_falsa = Mock(status_code=200)
    respuesta_falsa.json.return_value = {"texto": "respuesta simulada"}
    with patch("src.consumir_gemini.requests.post", return_value=respuesta_falsa):
        resultado = enviar_peticion("https://ejemplo.test", {"pregunta": "test"})
    assert resultado == {"texto": "respuesta simulada"}


def test_con_reintento_agota_intentos():
    def siempre_falla():
        raise TimeoutError("simulado")

    with patch("cliente.time.sleep"):
        with pytest.raises(TimeoutError):
            con_reintento(siempre_falla, intentos=3)


def test_con_reintento_no_reintenta_value_error():
    llamadas = {"n": 0}

    def falla_con_value_error():
        llamadas["n"] += 1
        raise ValueError("credencial invalida")

    with patch("cliente.time.sleep") as mock_sleep:
        with pytest.raises(ValueError):
            con_reintento(falla_con_value_error)

    assert llamadas["n"] == 1
    mock_sleep.assert_not_called()


def test_con_reintento_espera_entre_intentos():
    intentos = {"n": 0}

    def funcion_que_falla_una_vez():
        intentos["n"] += 1
        if intentos["n"] == 1:
            raise TimeoutError("simulado")
        return "ok"

    with patch("cliente.time.sleep") as mock_sleep:
        resultado = con_reintento(funcion_que_falla_una_vez)

    assert resultado == "ok"
    assert intentos["n"] == 2
    mock_sleep.assert_called_once()


def test_registrar_costo_acumula():
    respuesta_falsa = {"usageMetadata": {"totalTokenCount": 1000}}
    costo = cliente.registrar_costo(respuesta_falsa)
    assert costo == cliente.COSTO_POR_1000_TOKENS
    assert cliente.costo_total_sesion == cliente.COSTO_POR_1000_TOKENS


def test_registrar_costo_suma_varias_operaciones():
    cliente.registrar_costo({"usageMetadata": {"totalTokenCount": 1000}})
    cliente.registrar_costo({"usageMetadata": {"totalTokenCount": 2000}})
    assert cliente.costo_total_sesion == pytest.approx(3 * cliente.COSTO_POR_1000_TOKENS)


def test_consultar_modelo_convierte_error():
    with patch("cliente.armar_peticion", return_value=("https://ejemplo.test", {})):
        with patch("cliente.con_reintento", side_effect=TimeoutError("simulado")):
            with pytest.raises(RuntimeError, match="no respondió"):
                consultar_modelo("pregunta de prueba")


def test_consultar_modelo_propaga_value_error():
    with patch("cliente.armar_peticion", return_value=("https://ejemplo.test", {})):
        with patch("cliente.con_reintento", side_effect=ValueError("credencial invalida")):
            with pytest.raises(ValueError, match="credencial invalida"):
                consultar_modelo("pregunta de prueba")


def test_consultar_modelo_exito_devuelve_texto_y_registra_costo():
    datos_falsos = {
        "candidates": [{"content": {"parts": [{"text": "hola mundo"}]}}],
        "usageMetadata": {"totalTokenCount": 1000},
    }
    with patch("cliente.armar_peticion", return_value=("https://ejemplo.test", {})):
        with patch("cliente.con_reintento", return_value=datos_falsos):
            resultado = consultar_modelo("pregunta de prueba")
    assert resultado == "hola mundo"
    assert cliente.costo_total_sesion == cliente.COSTO_POR_1000_TOKENS