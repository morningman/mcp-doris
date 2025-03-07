"""Environment configuration for the MCP Doris server.

This module handles all environment variable configuration with sensible defaults
and type conversion.
"""

from dataclasses import dataclass
import os
from typing import Optional


@dataclass
class DorisConfig:
    """Configuration for Apache Doris connection settings.

    This class handles all environment variable configuration with sensible defaults
    and type conversion. It provides typed methods for accessing each configuration value.

    Required environment variables:
        DORIS_HOST: The hostname of the Doris server
        DORIS_PORT: The port number (default: 9030)
        DORIS_USER: The username for authentication
        DORIS_PASSWORD: The password for authentication

    Optional environment variables (with defaults):
        DORIS_DATABASE: Default database to use (default: None)
        DORIS_CONNECT_TIMEOUT: Connection timeout in seconds (default: 30)
        DORIS_READ_TIMEOUT: Read timeout in seconds (default: 300)
    """

    def __init__(self):
        """Initialize the configuration from environment variables."""
        self._validate_required_vars()

    @property
    def host(self) -> str:
        """Get the Doris host."""
        return os.environ["DORIS_HOST"]

    @property
    def port(self) -> int:
        """Get the Doris port.

        Defaults to 9030 (Doris MySQL protocol port).
        Can be overridden by DORIS_PORT environment variable.
        """
        return int(os.getenv("DORIS_PORT", "9030"))

    @property
    def username(self) -> str:
        """Get the Doris username."""
        return os.environ["DORIS_USER"]

    @property
    def password(self) -> str:
        """Get the Doris password."""
        return os.environ["DORIS_PASSWORD"]

    @property
    def database(self) -> Optional[str]:
        """Get the default database name if set."""
        return os.getenv("DORIS_DATABASE")

    @property
    def connect_timeout(self) -> int:
        """Get the connection timeout in seconds.

        Default: 30
        """
        return int(os.getenv("DORIS_CONNECT_TIMEOUT", "30"))

    @property
    def read_timeout(self) -> int:
        """Get the read timeout in seconds.

        Default: 300
        """
        return int(os.getenv("DORIS_READ_TIMEOUT", "300"))

    def get_client_config(self) -> dict:
        """Get the configuration dictionary for MySQL client.

        Returns:
            dict: Configuration ready to be passed to mysql.connector.connect()
        """
        config = {
            "host": self.host,
            "port": self.port,
            "user": self.username,
            "password": self.password,
            "connect_timeout": self.connect_timeout,
            "connection_timeout": self.read_timeout,
        }

        # Add optional database if set
        if self.database:
            config["database"] = self.database

        return config

    def _validate_required_vars(self) -> None:
        """Validate that all required environment variables are set.

        Raises:
            ValueError: If any required environment variable is missing.
        """
        missing_vars = []
        for var in ["DORIS_HOST", "DORIS_PORT", "DORIS_USER", "DORIS_PASSWORD"]:
            if var not in os.environ:
                missing_vars.append(var)

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )


# Global instance for easy access
config = DorisConfig() 
