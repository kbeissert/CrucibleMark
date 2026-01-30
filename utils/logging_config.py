import logging
import sys
from pathlib import Path

def setup_logging(log_file: Path = Path("logs/crucible.log")):
    """
    Konfiguriert das Logging-System.
    - Datei: Speichert alles (DEBUG level) für Fehlersuche.
    - Konsole: Zeigt nur wichtige Infos (INFO level), filtert technisches Rauschen.
    """
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
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_format = logging.Formatter('%(message)s')

    # 1. File Handler (Detailliert, speichert Warnungen/Errors von Libraries)
    file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='a')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_format)
    root_logger.addHandler(file_handler)

    # 2. Console Handler (Sauber, für den Benutzer)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_format)
    
    # Filter für die Konsole: Unterdrücke technische Logs von Bibliotheken
    class NoisyLibFilter(logging.Filter):
        def filter(self, record):
            # Liste der Bibliotheken, deren Logs wir nicht im Terminal wollen (aber im File)
            noisy_libs = ["transformers", "sentence_transformers", "urllib3", "huggingface_hub", "httpx", "httpcore"]
            if any(record.name.startswith(lib) for lib in noisy_libs):
                # Erlaube Errors, blockiere alles darunter (z.B. Warnings, Info)
                return record.levelno >= logging.ERROR
            return True
            
    console_handler.addFilter(NoisyLibFilter())
    root_logger.addHandler(console_handler)

    # Spezifische Logger-Levels zurücksetzen, falls sie woanders auf ERROR gesetzt wurden.
    # Wir wollen sie fangen, nur nicht anzeigen.
    for lib in ["transformers", "sentence_transformers", "urllib3", "huggingface_hub", "httpx"]:
        logging.getLogger(lib).setLevel(logging.WARNING)
