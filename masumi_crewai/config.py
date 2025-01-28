import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """
    Centralized configuration for the masumi_crewai package.
    """
    def __init__(self):
        # Registry Service
        self.registry_service_url = os.getenv("REGISTRY_SERVICE_URL")
        self.registry_api_key = os.getenv("REGISTRY_API_KEY")

        # Payment Service
        self.payment_service_url = os.getenv("PAYMENT_SERVICE_URL")
        self.payment_api_key = os.getenv("PAYMENT_API_KEY")

        # Payment Service V2
        self.payment_service_url_v2 = os.getenv("PAYMENT_SERVICE_URL_V2")
        self.payment_api_key_v2 = os.getenv("PAYMENT_API_KEY_V2")

        # Contract Address (fixed and used for payments)
        self.contract_address = os.getenv("CONTRACT_ADDRESS")

        # Validate required configurations
        self._validate()

    def _validate(self):
        """
        Validate that all required configuration parameters are set.
        Raises ValueError if any required parameter is missing.
        """
        required_configs = {
            "REGISTRY_SERVICE_URL": self.registry_service_url,
            "REGISTRY_API_KEY": self.registry_api_key,
            "PAYMENT_SERVICE_URL": self.payment_service_url,
            "PAYMENT_API_KEY": self.payment_api_key,
            "PAYMENT_SERVICE_URL_V2": self.payment_service_url_v2,
            "PAYMENT_API_KEY_V2": self.payment_api_key_v2,
            "CONTRACT_ADDRESS": self.contract_address,
        }

        missing_configs = [key for key, value in required_configs.items() if not value]
        if missing_configs:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_configs)}"
            )

# Initialize the configuration
config = Config()