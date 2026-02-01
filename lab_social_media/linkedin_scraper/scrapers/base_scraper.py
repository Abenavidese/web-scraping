from abc import ABC, abstractmethod
from typing import List, Dict

class SocialScraper(ABC):
    """
    Clase base abstracta para todos los scrapers de redes sociales.
    Define la interfaz común que deben implementar.
    """

    @abstractmethod
    async def extract(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Extrae datos de la red social.
        
        Args:
            query (str): Término de búsqueda o URL.
            limit (int): Número máximo de items a extraer.
            
        Returns:
            List[Dict]: Lista de diccionarios con la información extraída.
        """
        pass
