from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import asyncio
import logging
from typing import List, Optional, Dict, Any, Set
import aiohttp
from .config import Config

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler if no handlers exist
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

@dataclass
class Amount:
    """
    Represents a payment amount in a specific unit.
    
    Attributes:
        amount (int): The payment amount (e.g., 1000000 for 1 ADA)
        unit (str): The currency unit (e.g., 'lovelace' for ADA)
    """
    amount: int
    unit: str

class Payment:
    """
    Handles Cardano blockchain payment operations including creation, monitoring, and completion.
    
    This class manages payment requests and their lifecycle, supporting multiple concurrent
    payment tracking. It uses the Masumi payment service for all payment operations.
    
    Attributes:
        agent_identifier (str): Unique identifier for the agent making payments
        payment_contract_address_preprod (str): Smart contract address for preprod network
        payment_contract_address_mainnet (str): Smart contract address for mainnet
        amounts (List[Amount]): List of payment amounts and their units
        network (str): Network to use ('PREPROD' or 'MAINNET')
        payment_type (str): Type of payment (fixed to 'WEB3_CARDANO_V1')
        payment_ids (Set[str]): Set of active payment IDs being tracked
        config (Config): Configuration for API endpoints and authentication
    """

    def __init__(self, agent_identifier: str, amounts: List[Amount], 
                 config: Config, network: str = "PREPROD"):
        """
        Initialize a new Payment instance.
        
        Args:
            agent_identifier (str): Unique identifier for the agent
            amounts (List[Amount]): List of payment amounts
            config (Config): Configuration object with API details
            network (str, optional): Network to use. Defaults to "PREPROD"
        """
        logger.info(f"Initializing Payment instance for agent {agent_identifier} on {network} network")
        self.agent_identifier = agent_identifier
        self.payment_contract_address_preprod = "addr_test1wqarcz6uad8l44dkmmtllud2amwc9t0xa6l5mv2t7tq4szgagm7r2"
        self.payment_contract_address_mainnet = "addr1wyarcz6uad8l44dkmmtllud2amwc9t7tq4szgxq0zv0"
        self.amounts = amounts
        self.network = network
        self.payment_type = "WEB3_CARDANO_V1"
        self.payment_ids: Set[str] = set()
        self._status_check_task: Optional[asyncio.Task] = None
        self.config = config
        self._headers = {
            "token": config.payment_api_key,
            "Content-Type": "application/json"
        }
        logger.debug(f"Payment amounts configured: {[f'{a.amount} {a.unit}' for a in amounts]}")

    async def create_payment_request(self) -> Dict[str, Any]:
        """
        Create a new payment request.
        
        Creates a payment request with the specified amounts and adds the payment ID
        to the tracking set. The payment deadline is automatically set to 12 hours
        from creation.
        
        Returns:
            Dict[str, Any]: Response from the payment service containing payment details
            
        Raises:
            ValueError: If the request is invalid
            Exception: If there's a network or server error
        """
        logger.info(f"Creating new payment request for agent {self.agent_identifier}")
        
        if self.network == "PREPROD":
            self.payment_contract_address = self.payment_contract_address_preprod
            logger.debug("Using PREPROD network contract address")
        else:
            self.payment_contract_address = self.payment_contract_address_mainnet
            logger.debug("Using MAINNET network contract address")

        future_time = datetime.now(timezone.utc) + timedelta(hours=12)
        formatted_time = future_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        logger.debug(f"Payment deadline set to {formatted_time}")

        payload = {
            "agentIdentifier": self.agent_identifier,
            "network": self.network,
            "paymentContractAddress": self.payment_contract_address,
            "amounts": [{"amount": amt.amount, "unit": amt.unit} for amt in self.amounts],
            "paymentType": self.payment_type,
            "submitResultTime": formatted_time
        }
        logger.debug(f"Payment request payload prepared: {payload}")

        try:
            async with aiohttp.ClientSession() as session:
                logger.debug("Sending payment request to API")
                async with session.post(
                    f"{self.config.payment_service_url}/payment/",
                    headers=self._headers,
                    json=payload
                ) as response:
                    if response.status == 400:
                        error_text = await response.text()
                        logger.error(f"Bad request error: {error_text}")
                        raise ValueError(f"Bad request: {error_text}")
                    if response.status == 401:
                        logger.error("Unauthorized: Invalid API key")
                        raise ValueError("Unauthorized: Invalid API key")
                    if response.status == 500:
                        logger.error("Internal server error from payment service")
                        raise Exception("Internal server error")
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Payment request failed with status {response.status}: {error_text}")
                        raise Exception(f"Payment request failed: {error_text}")
                    
                    result = await response.json()
                    result["submitResultTime"] = formatted_time
                    new_payment_id = result["data"]["identifier"]
                    self.payment_ids.add(new_payment_id)
                    logger.info(f"Payment request created successfully. Payment ID: {new_payment_id}")
                    logger.debug(f"Full payment response: {result}")
                    return result
        except aiohttp.ClientError as e:
            logger.error(f"Network error during payment request: {str(e)}")
            raise

    async def check_payment_status(self) -> Dict[str, Any]:
        """
        Check the status of all tracked payments.
        
        Retrieves the current status of all payments being tracked and automatically
        removes payments that have been confirmed.
        
        Returns:
            Dict[str, Any]: Response containing status of all payments
            
        Raises:
            ValueError: If no payment IDs are being tracked
            Exception: If the status check fails
        """
        if not self.payment_ids:
            logger.warning("Attempted to check payment status with no payment IDs")
            raise ValueError("No payment IDs available")

        logger.debug(f"Checking status for payment IDs: {self.payment_ids}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.config.payment_service_url}/payment/",
                    headers=self._headers
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Status check failed: {error_text}")
                        raise Exception(f"Status check failed: {error_text}")
                    
                    result = await response.json()
                    logger.debug(f"Received status response: {result}")
                    
                    payments = result.get("data", {}).get("payments", [])
                    for payment in payments:
                        payment_id = payment["identifier"]
                        status = payment["status"]
                        if payment_id in self.payment_ids:
                            logger.debug(f"Payment {payment_id} status: {status}")
                            if status == "CONFIRMED":
                                logger.info(f"Payment {payment_id} confirmed, removing from tracking")
                                self.payment_ids.remove(payment_id)
                    
                    return result
        except aiohttp.ClientError as e:
            logger.error(f"Network error during status check: {str(e)}")
            raise

    async def complete_payment(self, payment_id: str, hash: str) -> Dict[str, Any]:
        """
        Complete a payment with a transaction hash.
        
        Args:
            payment_id (str): ID of the payment to complete
            hash (str): Transaction hash from the blockchain
            
        Returns:
            Dict[str, Any]: Response confirming payment completion
            
        Raises:
            ValueError: If payment_id is not being tracked or request is invalid
            Exception: If completion fails
        """
        logger.info(f"Attempting to complete payment {payment_id} with hash {hash}")
        
        if payment_id not in self.payment_ids:
            logger.error(f"Payment ID {payment_id} not found in tracked payments")
            raise ValueError(f"Payment ID {payment_id} not found in tracked payments")

        payload = {
            "network": self.network,
            "paymentContractAddress": self.payment_contract_address,
            "hash": hash,
            "identifier": payment_id
        }
        logger.debug(f"Payment completion payload: {payload}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    f"{self.config.payment_service_url}/payment/",
                    headers=self._headers,
                    json=payload
                ) as response:
                    if response.status == 400:
                        error_text = await response.text()
                        logger.error(f"Bad request during completion: {error_text}")
                        raise ValueError(f"Bad request: {error_text}")
                    if response.status == 401:
                        logger.error("Unauthorized during completion: Invalid API key")
                        raise ValueError("Unauthorized: Invalid API key")
                    if response.status == 500:
                        logger.error("Internal server error during completion")
                        raise Exception("Internal server error")
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Payment completion failed: {error_text}")
                        raise Exception(f"Payment completion failed: {error_text}")
                    
                    result = await response.json()
                    if result.get("data", {}).get("status") == "PaymentDone":
                        logger.info(f"Payment {payment_id} completed successfully")
                        self.payment_ids.remove(payment_id)
                    return result
        except aiohttp.ClientError as e:
            logger.error(f"Network error during payment completion: {str(e)}")
            raise

    async def start_status_monitoring(self, callback) -> None:
        """
        Start monitoring payment statuses.
        
        Starts an asynchronous task that continuously monitors payment statuses and
        calls the provided callback function when payments are confirmed.
        
        Args:
            callback: Async function to call when a payment is confirmed.
                     Will be called with payment_id as argument.
        
        Raises:
            ValueError: If callback is not callable
        """
        if not callable(callback):
            logger.error("Invalid callback provided to status monitoring")
            raise ValueError("Callback must be a callable function")

        logger.info("Starting payment status monitoring")

        async def monitor():
            while True:
                try:
                    if not self.payment_ids:
                        logger.debug("No payments to monitor, waiting...")
                        await asyncio.sleep(60)
                        continue

                    logger.debug("Checking payment statuses...")
                    response = await self.check_payment_status()
                    payments = response.get("data", {}).get("payments", [])
                    
                    for payment in payments:
                        payment_id = payment.get("identifier")
                        status = payment.get("status")
                        
                        if payment_id in self.payment_ids:
                            logger.debug(f"Payment {payment_id} status: {status}")
                            if status == "CONFIRMED":
                                logger.info(f"Payment {payment_id} confirmed, executing callback")
                                try:
                                    await callback(payment_id)
                                except Exception as e:
                                    logger.error(f"Error in callback for payment {payment_id}: {str(e)}")
                                self.payment_ids.remove(payment_id)
                                logger.debug(f"Payment {payment_id} removed from tracking")

                    await asyncio.sleep(60)
                except Exception as e:
                    logger.error(f"Error in status monitoring: {str(e)}")
                    await asyncio.sleep(60)

        self._status_check_task = asyncio.create_task(monitor())
        logger.info("Status monitoring task started")

    def stop_status_monitoring(self) -> None:
        """
        Stop the payment status monitoring.
        
        Cancels the monitoring task if it's running.
        """
        if self._status_check_task:
            logger.info("Stopping payment status monitoring")
            self._status_check_task.cancel()
            self._status_check_task = None
        else:
            logger.debug("No monitoring task to stop") 