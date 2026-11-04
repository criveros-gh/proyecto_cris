from unittest.mock import patch, Mock
import pytest
from src.consumir_gemini import enviar_peticion


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