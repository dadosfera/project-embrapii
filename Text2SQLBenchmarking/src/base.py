from abc import ABC, abstractmethod
from typing import Any, List, Dict, Union, Optional
import pandas as pd

class TextToSQLBase(ABC):

    @abstractmethod
    def generate_query(self, question: str, t: int) -> str:
        """
        Recebe uma pergunta em linguagem natural e retorna uma query SQL.
        
        Args:
            question (str): A pergunta do usuário (ex: "Quantos clientes temos?").
            timeout (int): tempo limite para a execução da query
            
        Returns:
            str: A query SQL gerada.
        """
        pass