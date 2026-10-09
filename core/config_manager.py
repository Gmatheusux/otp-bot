import copy
import json
import os
import logging

from modules.screen_calibration import DEFAULT_CALIBRATION, migrate_calibration

logger = logging.getLogger("ConfigManager")


def _deep_merge(base: dict, override: dict) -> dict:
    """Mescla override sobre base sem perder chaves novas dos defaults."""
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


DEFAULT_CONFIG = {
    "cooldowns": {
        "heal": 2.0, "attack": 1.5, "loot": 0.5, "catch": 1.0, "revive": 5.0,
        "auto_combo": 2.0, "defensive_buff": 10.0, "stance": 2.0,
    },
    "hotkeys": {"pause": "f8", "kill": "f9", "record": "f10", "play": "f11", "catch_key": "f4"},
    # monitor 0 = automático (o principal do Windows, único que os cliques alcançam)
    "engine": {"fps_target": 30, "offensive_mode": False, "model_path": "models/otp_yolo.pt", "confidence": 0.5, "monitor": 0},
    "pokemon_profile": {
        "auto_combo_key": "f1",
        "revive_key": "f2",
        "defensive_buff_key": "",  # sem padrão: o jogador escolhe no console
    },
    "features": {
        # Lidos ao vivo pela decision_thread
        "combat": {
            "auto_combo": True,
            "kite_combo": True,
            "boxed_defense": True,
            "boxed_mobs": 8,
            "boxed_radius_pct": 15,
            "revive_on_boxed": True,
            "stop_route_when_boxed": True,
        },
        # Desligado por padrão: o jogador liga depois de conferir a leitura da postura na Calibração
        "stance": {"auto": False, "normal": "offensive", "lure": "defensive", "combo": "offensive"},
        "catch": {"enabled": True},
        # Limites humanos de todas as entradas (core/humanizer.py)
        "human": {"max_apm": 180, "reaction_ms": 240, "cooldown_jitter_pct": 12, "hesitation": True},
        "safety": {"gm_monitor": True, "chat_roi": [10, 600, 400, 30]},
        # Planejados: a UI já salva, o bot ainda não executa
        "target": {"auto_target": False, "range": 7, "ignore": [], "shiny_priority": False, "shiny_words": ["shiny"]},
        "heal": {
            "potion": {"enabled": False, "hp_percent": 60, "key": "f5"},
            # Cura com pokémon: desligada até o jogador configurar e ligar manualmente
            "pokemon_heal": {
                "enabled": False,
                "hp_percent": 90,
                "swap_method": "pokebar",   # "pokebar" (clica na posição) ou "key"
                "healer_slot": 2,
                "healer_name": "",
                "healer_key": "",
                "farm_slot": 1,
                "farm_key": "",
                "rotation": [],
                "rotation_delay_ms": 800,
                "summon_wait_ms": 1500,
                "use_revive": True,
                "revive_key": "",           # vazio = tecla de revive do perfil
                "cooldown_s": 15,
            },
            "medicine": {"enabled": False, "key": "f7"},
        },
        "route": {"loop": True, "wait_first_waypoint": False, "vary_path": False, "vary_sqm": 1},
        "alerts": {
            "player_on_screen": True, "gm_message": True, "private_message": False, "death": True,
            "sound": True, "volume": 100, "telegram": False, "telegram_chat_id": "",
        },
        "extras": {"food": {"enabled": False, "key": "", "interval_s": 300}},
        "guild": {"daily": False, "tier": "normal", "element": "normal"},
    },
    "calibration": copy.deepcopy(DEFAULT_CALIBRATION),
}


class ConfigManager:
    """Gerenciador de configurações para carregar parâmetros dinâmicos via config.json"""
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> dict:
        if not os.path.exists(self.config_path):
            logger.error(f"Arquivo {self.config_path} não encontrado! Usando defaults.")
            return self._default_config()

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            # Antes da mescla: senão os perfis padrão entram e a calibração antiga não é convertida
            if "calibration" in loaded:
                loaded["calibration"] = migrate_calibration(loaded["calibration"])
            return _deep_merge(self._default_config(), loaded)
        except Exception as e:
            logger.error(f"Erro ao carregar {self.config_path}: {e}")
            return self._default_config()

    def _save_config(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar {self.config_path}: {e}")

    def _default_config(self) -> dict:
        return copy.deepcopy(DEFAULT_CONFIG)

    def get_cooldowns(self) -> dict:
        return self.config.get("cooldowns", {})

    def get_hotkeys(self) -> dict:
        return self.config.get("hotkeys", {})

    def get_engine_config(self) -> dict:
        return self.config.get("engine", {})

    def get_pokemon_profile(self) -> dict:
        return self.config.get("pokemon_profile", {})

    def get_features(self) -> dict:
        return self.config.get("features", {})

    def update_defensive_buff_key(self, new_key: str):
        """Atualiza a tecla de buff defensivo dinamicamente e salva no arquivo."""
        if "pokemon_profile" not in self.config:
            self.config["pokemon_profile"] = {}

        self.config["pokemon_profile"]["defensive_buff_key"] = new_key
        logger.info(f"Tecla de buff defensivo atualizada para: {new_key}")

        # Salva o estado atualizado da configuração em arquivo
        self._save_config()

    def update_full_config(self, new_config: dict):
        """Sobrescreve a configuração inteira e salva no disco dinamicamente."""
        self.config = _deep_merge(self._default_config(), new_config)
        logger.info("Configuração global atualizada via API Dashboard.")
        self._save_config()
