from typing import List, Dict, Optional
import logging
import aiohttp
from .config import Config

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class Agent:
    DEFAULT_NETWORK = "Preprod"
    DEFAULT_SMART_CONTRACT_ADDRESS = "addr_test1wqv9sc853kpurfdqv5f02tmmlscez20ks0p5p6aj76j0xac2jqve7"
    
    async def get_selling_wallet_vkey(self) -> str:
        """Fetch selling wallet vkey from payment source for the current smart contract address"""
        logger.info("Fetching selling wallet vkey from payment source")
        logger.debug(f"Using smart contract address: {self.smart_contract_address}")
        
        payment_headers = {
            "token": self.config.payment_api_key,
            "Content-Type": "application/json"
        }
        logger.debug(f"Using payment headers: {payment_headers}")
        
        try:
            async with aiohttp.ClientSession() as session:
                logger.debug("Making GET request to payment source endpoint")
                async with session.get(
                    f"{self.config.payment_service_url}/payment-source/",
                    headers=payment_headers,
                    params={"take": "10"}
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Failed to fetch payment sources: {error_text}")
                        raise ValueError(f"Failed to fetch payment sources: {error_text}")
                    
                    result = await response.json()
                    logger.debug(f"Received payment sources response: {result}")
                    
                    for source in result["data"]["paymentSources"]:
                        logger.debug(f"Checking payment source with address: {source['smartContractAddress']}")
                        if source["smartContractAddress"] == self.smart_contract_address:
                            if source["SellingWallets"]:
                                vkey = source["SellingWallets"][0]["walletVkey"]
                                logger.info(f"Found matching selling wallet vkey: {vkey}")
                                return vkey
                    
                    logger.error(f"No selling wallet found for address: {self.smart_contract_address}")
                    raise ValueError(f"No selling wallet found for smart contract address: {self.smart_contract_address}")
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error while fetching payment sources: {str(e)}")
            raise

    async def check_registration_status(self, wallet_vkey: str) -> Dict:
        """Check registration status for a given wallet vkey"""
        logger.info(f"Checking registration status for wallet vkey: {wallet_vkey}")
        logger.debug(f"Network: {self.network}")
        
        try:
            async with aiohttp.ClientSession() as session:
                logger.debug("Making GET request to registry endpoint")
                params = {
                    "walletVKey": wallet_vkey,
                    "network": self.network
                }
                logger.debug(f"Query parameters: {params}")
                
                async with session.get(
                    f"{self.config.payment_service_url}/registry/",
                    headers=self._headers,
                    params=params
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Status check failed with status {response.status}: {error_text}")
                        raise ValueError(f"Status check failed: {error_text}")
                    
                    result = await response.json()
                    logger.debug(f"Received registration status response: {result}")
                    
                    # Verify this agent exists in the response
                    if "data" in result and "assets" in result["data"]:
                        for asset in result["data"]["assets"]:
                            if asset["metadata"]["name"] == self.name:
                                logger.info(f"Found registered agent: {self.name}")
                                logger.debug(f"Agent metadata: {asset['metadata']}")
                                return result
                    
                    logger.warning(f"Agent {self.name} not found in registration status")
                    return result
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error while checking registration status: {str(e)}")
            raise

    def __init__(
        self,
        config: Config,
        name: str,
        api_url: str,
        description: str,
        author_name: str,
        author_contact: str,
        author_organization: str,
        legal_privacy_policy: str,
        legal_terms: str,
        legal_other: str,
        capability_name: str,
        capability_version: str,
        requests_per_hour: str,
        pricing_unit: str,
        pricing_quantity: str,
        network: str = DEFAULT_NETWORK,
        smart_contract_address: str = DEFAULT_SMART_CONTRACT_ADDRESS,
        example_output: str = "example_output",
        tags: List[str] = None
    ):
        self.config = config
        self.network = network
        self.smart_contract_address = smart_contract_address
        self.example_output = example_output
        self.tags = tags or ["tag1", "tag2"]
        self.name = name
        self.api_url = api_url
        self.description = description
        self.author_name = author_name
        self.author_contact = author_contact
        self.author_organization = author_organization
        self.legal_privacy_policy = legal_privacy_policy
        self.legal_terms = legal_terms
        self.legal_other = legal_other
        self.capability_name = capability_name
        self.capability_version = capability_version
        self.requests_per_hour = requests_per_hour
        self.pricing_unit = pricing_unit
        self.pricing_quantity = pricing_quantity
        
        self._headers = {
            "token": config.payment_api_key,
            "Content-Type": "application/json"
        }
        
        logger.info(f"Initializing Agent instance for {name}")
        logger.debug(f"Network: {network}")
        logger.debug(f"Smart contract address: {smart_contract_address}")
        
        logger.debug(f"Agent initialized with config URL: {config.payment_service_url}")
        logger.debug(f"Using payment API key: {'*' * len(config.payment_api_key)}")

    async def register(self) -> Dict:
        """Register a new agent with the registry service"""
        logger.info(f"Starting registration for agent: {self.name}")
        logger.debug(f"Network: {self.network}")
        
        selling_wallet_vkey = await self.get_selling_wallet_vkey()
        logger.info(f"Retrieved selling wallet vkey: {selling_wallet_vkey}")
        
        payload = {
            "network": self.network,
            "smartContractAddress": self.smart_contract_address,
            "example_output": self.example_output,
            "tags": self.tags,
            "name": self.name,
            "api_url": self.api_url,
            "description": self.description,
            "author": {
                "name": self.author_name,
                "contact": self.author_contact,
                "organization": self.author_organization
            },
            "legal": {
                "privacy_policy": self.legal_privacy_policy,
                "terms": self.legal_terms,
                "other": self.legal_other
            },
            "capability": {
                "name": self.capability_name,
                "version": self.capability_version
            },
            "requests_per_hour": self.requests_per_hour,
            "pricing": [
                {
                    "unit": self.pricing_unit,
                    "quantity": self.pricing_quantity
                }
            ],
            "sellingWalletVkey": selling_wallet_vkey
        }
        logger.debug(f"Registration payload prepared: {payload}")
        
        try:
            async with aiohttp.ClientSession() as session:
                logger.debug("Making POST request to registry endpoint")
                async with session.post(
                    f"{self.config.payment_service_url}/registry/",
                    headers=self._headers,
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Registration failed with status {response.status}: {error_text}")
                        raise ValueError(f"Registration failed: {error_text}")
                    
                    result = await response.json()
                    logger.info(f"Agent {self.name} registered successfully")
                    logger.debug(f"Registration response: {result}")
                    return result
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error during registration: {str(e)}")
            raise 