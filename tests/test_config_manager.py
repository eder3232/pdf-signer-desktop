import pytest
from app.core.config_manager import ConfigManager
import os
import json
import tempfile

@pytest.fixture
def temp_config_file():
    """Crea un archivo de configuración temporal"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.remove(temp_path)

def test_config_initialization(temp_config_file):
    manager = ConfigManager(temp_config_file)
    assert isinstance(manager.config, dict)
    assert "default_signature_size" in manager.config

def test_save_and_load_config(temp_config_file):
    manager = ConfigManager(temp_config_file)
    test_value = "/ruta/test"
    manager.set_value("last_directory", test_value)
    
    # Crear nueva instancia para verificar persistencia
    new_manager = ConfigManager(temp_config_file)
    assert new_manager.get_value("last_directory") == test_value

def test_signature_config(temp_config_file):
    manager = ConfigManager(temp_config_file)
    
    # Añadir configuración de firma
    signature_config = {
        "position": {"x": 100, "y": 200},
        "size": {"width": 50, "height": 25},
        "rotation": 0
    }
    manager.add_signature_config("firma1", signature_config)
    
    # Verificar configuración guardada
    loaded_config = manager.get_signature_config("firma1")
    assert loaded_config == signature_config

def test_invalid_json_file(temp_config_file):
    # Crear archivo JSON inválido
    with open(temp_config_file, 'w') as f:
        f.write("invalid json content")
    
    manager = ConfigManager(temp_config_file)
    assert manager.config == manager.default_config

def test_get_value_with_default():
    manager = ConfigManager()
    default_value = "valor_por_defecto"
    value = manager.get_value("clave_no_existente", default_value)
    assert value == default_value 