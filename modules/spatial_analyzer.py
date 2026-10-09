import math
from typing import List, Dict

class SpatialAnalyzer:
    def __init__(self, summon_class_id: int = 0, wild_pokemon_class_id: int = 1, dead_pokemon_class_id: int = 2, radius_threshold: float = 0.15):
        """
        Inicializa o analisador espacial.
        
        Args:
            summon_class_id: ID da classe do Summon no modelo YOLO.
            wild_pokemon_class_id: ID da classe do Pokémon Selvagem no modelo YOLO.
            dead_pokemon_class_id: ID da classe de cadáveres para Auto Catch.
            radius_threshold: Distância máxima normalizada (0.0 a 1.0) para considerar um mob como "colado".
        """
        self.summon_class_id = summon_class_id
        self.wild_pokemon_class_id = wild_pokemon_class_id
        self.dead_pokemon_class_id = dead_pokemon_class_id
        self.radius_threshold = radius_threshold
        self.boxed_mob_count = 8

    def calculate_spatial_state(self, detections: List[Dict]) -> Dict:
        """
        Calcula o estado espacial das entidades na tela.
        
        Args:
            detections: Lista de dicionários gerados pelo VisionEngine.
            
        Returns:
            Dict com a contagem total de mobs e o estado 'is_boxed' (boxed_mob_count+ mobs no raio).
        """
        summon_center = None
        wild_pokemons = []
        dead_pokemons = []

        # Separar entidades baseadas no class_id
        for det in detections:
            cls_id = det["class_id"]
            box = det["box_relative"]
            center = (box["x_center"], box["y_center"])

            if cls_id == self.summon_class_id:
                summon_center = center
            elif cls_id == self.wild_pokemon_class_id:
                wild_pokemons.append(center)
            elif cls_id == self.dead_pokemon_class_id:
                dead_pokemons.append(center)

        mobs_on_screen = len(wild_pokemons)
        is_boxed = False

        mob_distances = []

        # Calcular distância euclidiana se o Summon estiver em tela
        if summon_center and mobs_on_screen > 0:
            mobs_in_radius = 0
            for mob_center in wild_pokemons:
                distance = math.sqrt(
                    (mob_center[0] - summon_center[0]) ** 2 + 
                    (mob_center[1] - summon_center[1]) ** 2
                )
                
                # Registra a distância absoluta
                mob_distances.append({
                    "center": mob_center,
                    "distance": distance
                })
                
                if distance <= self.radius_threshold:
                    mobs_in_radius += 1

            if mobs_in_radius >= self.boxed_mob_count:
                is_boxed = True

        return {
            "mobs_on_screen": mobs_on_screen,
            "is_boxed": is_boxed,
            "mob_distances": mob_distances,
            "dead_pokemons": dead_pokemons
        }
