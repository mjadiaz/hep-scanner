from src.utils import run_scan
from src.parallel_scanner import SCANNER_DEFAULT_CONFIG
from src.parallel_scanner import HEP_DEFAULT_CONFIG

run_scan(
        SCANNER_DEFAULT_CONFIG,
        HEP_DEFAULT_CONFIG
        )
