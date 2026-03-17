import logging
import logging.config
import os
from pathlib import Path
import yaml


def setup_logging(
        config_file: str = "logging_config.yaml",
        default_level: int = logging.INFO,
        env_key: str = "LOG_CFG"
):
    """
    Configura o sistema de logging a partir de um arquivo YAML.

    :param config_file: Caminho para o arquivo de configuração YAML
    :param default_level: Nível de logging padrão se o arquivo não existir
    :param env_key: Variável de ambiente que pode sobrescrever o caminho do config
    """
    # Check if exists env variable for logging config
    config_path = os.getenv(env_key, config_file)
    config_path = Path(config_path)

    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            logging.config.dictConfig(config)
            logging.info(f"Logging configured from {config_path}")

        except Exception as e:
            print(f"Error loading logging config from {config_path}: {e}")
            print("Using basic logging configuration")
            _setup_basic_logging(default_level)
    else:
        print(f"Logging config file not found: {config_path}")
        print("Using basic logging configuration")
        _setup_basic_logging(default_level)


def _setup_basic_logging(level: int):
    """Configuração básica de logging como fallback."""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(logs_dir / "benchmark_generator.log", encoding='utf-8')
        ]
    )


def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger configurado.

    :param name: Nome do logger (ex:  __name__)
    :return: Logger configurado
    """
    return logging.getLogger(name)