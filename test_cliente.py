from unittest.mock import patch, Mock
import pytest
from src.consumir_gemini import enviar_peticion
from cliente import con_reintento


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