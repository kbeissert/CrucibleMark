import logging
import sys
import yaml
from pathlib import Path

# Central Config Path
ROOT_DIR = Path(__file__).parent.parent
CONFIG_PATH = ROOT_DIR / "benchmark_config.yaml"


def _load_logging_config():
    """Lädt Logging-Config aus YAML oder nutzt Defaults."""
    defaults = {
        "file_path": "logs/crucible.log",
        "console_level": "INFO",
        "file_level": "DEBUG",
    }
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data.get("logging", defaults)
    except Exception:
        pass
    return defaults


def setup_logging(log_file: Path = None):
    """
    Konfiguriert das Logging-System basierend auf benchmark_config.yaml.
    """
    config = _load_logging_config()

    # 1. Determine Log File Path
    if log_file is None:
        # Resolve path relative to root if not absolute
        p = Path(config.get("file_path", "logs/crucible.log"))
        if not p.is_absolute():
            log_file = ROOT_DIR / p
        else:
            log_file = p

    # 2. Determine Levels
    console_lvl_str = config.get("console_level", "INFO").upper()
    file_lvl_str = config.get("file_level", "DEBUG").upper()

    console_level = getattr(logging, console_lvl_str, logging.INFO)
    file_level = getattr(logging, file_lvl_str, logging.DEBUG)

    # Create logs directory if not exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    # Wir setzen den Root-Logger auf DEBUG, damit er grundsätzlich alles empfängt.
    # Die Handler filtern dann selbst.
    root_logger.setLevel(logging.DEBUG)

    # Alte Handler entfernen, um Dopplungen zu vermeiden
    if root_logger.handlers:
        root_logger.handlers.clear()

    # Formatter
    file_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_format = logging.Formatter("%(message)s")

    # 1. File Handler (Detailliert, speichert Warnungen/Errors von Libraries)
    file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="a")
    file_handler.setLevel(file_level)
    file_handler.setFormatter(file_format)
    root_logger.addHandler(file_handler)

    # 2. Console Handler (Sauber, für den Benutzer)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_format)

    # Filter für die Konsole: Unterdrücke technische Logs von Bibliotheken
    class NoisyLibFilter(logging.Filter):
        def filter(self, record):
            # Liste der Bibliotheken, deren Logs wir nicht im Terminal wollen (aber im File)
            noisy_libs = [
                "transformers",
                "sentence_transformers",
                "urllib3",
                "huggingface_hub",
                "httpx",
                "httpcore",
            ]
            if any(record.name.startswith(lib) for lib in noisy_libs):
                # Erlaube Errors, blockiere alles darunter (z.B. Warnings, Info)
                return record.levelno >= logging.ERROR
            return True

    console_handler.addFilter(NoisyLibFilter())
    root_logger.addHandler(console_handler)

    # Spezifische Logger-Levels zurücksetzen, falls sie woanders auf ERROR gesetzt wurden.
    # Wir wollen sie fangen, nur nicht anzeigen.
    for lib in [
        "transformers",
        "sentence_transformers",
        "urllib3",
        "huggingface_hub",
        "httpx",
    ]:
        logging.getLogger(lib).setLevel(logging.WARNING)
