"""
Output Config - Standard handler for parsing and accessing properties of the JSON output configurations.
"""
import json
import logging
from typing import Any, Dict, List, Union

logger = logging.getLogger(__name__)

class OutputConfig:
    """
    Encapsulates rules defined in config/output-config.json.
    """

    def __init__(self, config_source: Union[str, Dict[str, Any]]):
        """
        Load configuration from path or dictionary.
        """
        if isinstance(config_source, str):
            try:
                with open(config_source, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
            except Exception as e:
                logger.error("Failed to load output config JSON from %s: %s", config_source, e)
                self._config = {}
        else:
            self._config = config_source or {}

    @property
    def fields(self) -> List[Dict[str, Any]]:
        """Returns the list of field projection specifications."""
        return self._config.get("fields", [])

    @property
    def include_provenance(self) -> bool:
        """Returns whether provenance tracks should be included globally."""
        return self._config.get("include_provenance", True)

    @property
    def include_confidence(self) -> bool:
        """Returns whether confidence trust scores should be included globally."""
        return self._config.get("include_confidence", True)

    @property
    def on_missing(self) -> str:
        """Missing field behavior: 'null' or 'omit'."""
        return self._config.get("on_missing", "null")
