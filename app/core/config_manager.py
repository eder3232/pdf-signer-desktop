import json
from typing import Dict, Any, Optional
import os

class ConfigManager:
    def __init__(self, config_path: str = "config.json"):
        """
        Inicializa el gestor de configuración
        
        Args:
            config_path (str): Ruta al archivo de configuración JSON
        """
        self.config_path = config_path
        self.default_config = {
            "last_directory": "",
            "signatures": {},
            "default_signature_size": {
                "width": 100,
                "height": 50
            },
            "preview_quality": "high",
            "auto_save": True
        }
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """
        Carga la configuración desde el archivo JSON
        
        Returns:
            Dict[str, Any]: Configuración cargada o configuración por defecto
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Combinar con defaults para asegurar todas las keys
                    return {**self.default_config, **loaded_config}
            return self.default_config.copy()
        except json.JSONDecodeError:
            return self.default_config.copy()

    def save_config(self) -> None:
        """Guarda la configuración actual en el archivo JSON"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def get_value(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de la configuración
        
        Args:
            key (str): Clave de configuración
            default (Any): Valor por defecto si no existe la clave
            
        Returns:
            Any: Valor de configuración
        """
        return self.config.get(key, default)

    def set_value(self, key: str, value: Any) -> None:
        """
        Establece un valor en la configuración
        
        Args:
            key (str): Clave de configuración
            value (Any): Valor a establecer
        """
        self.config[key] = value
        self.save_config()

    def add_signature_config(
        self,
        signature_id: str,
        config: Dict[str, Any]
    ) -> None:
        """
        Añade o actualiza la configuración de una firma
        
        Args:
            signature_id (str): Identificador único de la firma
            config (Dict[str, Any]): Configuración de la firma
        """
        if "signatures" not in self.config:
            self.config["signatures"] = {}
        self.config["signatures"][signature_id] = config
        self.save_config()

    def get_signature_config(
        self,
        signature_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene la configuración de una firma específica
        
        Args:
            signature_id (str): Identificador único de la firma
            
        Returns:
            Optional[Dict[str, Any]]: Configuración de la firma o None si no existe
        """
        return self.config.get("signatures", {}).get(signature_id) 