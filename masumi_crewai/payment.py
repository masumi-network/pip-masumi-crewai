from dataclasses import dataclass
from datetime import datetime
import asyncio
from typing import List, Optional, Dict, Any
import aiohttp
from .config import Config

@dataclass
class Amount:
    amount: int
    unit: str

class Payment:
    def __init__(self, agent_identifier: str, amounts: List[Amount], 
                 config: Config, network: str = "PREPROD"):
        self.agent_identifier = agent_identifier
        self.payment_contract_address = "addr_test1wrm4l7k9qgw9878ymvw223u45fje48tnhqsxk2tewe47z7se03mca"
        self.amounts = amounts
        self.network = network
        self.payment_type = "WEB3_CARDANO_V1"
        self.payment_id: Optional[str] = None
        self._status_check_task: Optional[asyncio.Task] = None
        self.config = config
        self._headers = {
            "token": config.payment_api_key,
            "Content-Type": "application/json"
        }

    async def create_payment_request(self, submit_result_time: str) -> Dict[str, Any]:
        payload = {
            "agentIdentifier": self.agent_identifier,
            "network": self.network,
            "paymentContractAddress": self.payment_contract_address,
            "amounts": [{"amount": amt.amount, "unit": amt.unit} for amt in self.amounts],
            "paymentType": self.payment_type,
            "submitResultTime": submit_result_time
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.config.payment_service_url}/payment/",
                headers=self._headers,
                json=payload
            ) as response:
                if response.status == 400:
                    raise ValueError(f"Bad request: {await response.text()}")
                if response.status == 401:
                    raise ValueError("Unauthorized: Invalid API key")
                if response.status == 500:
                    raise Exception("Internal server error")
                if response.status != 200:
                    raise Exception(f"Payment request failed: {await response.text()}")
                
                result = await response.json()
                self.payment_id = result["data"]["identifier"]
                return result

    async def check_payment_status(self) -> Dict[str, Any]:
        if not self.payment_id:
            raise ValueError("No payment ID available")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.config.payment_service_url}/payment/{self.payment_id}",
                headers=self._headers
            ) as response:
                if response.status != 200:
                    raise Exception(f"Status check failed: {await response.text()}")
                return await response.json()

    async def complete_payment(self, hash: str) -> Dict[str, Any]:
        if not self.payment_id:
            raise ValueError("No payment ID available. Create payment request first.")

        payload = {
            "network": self.network,
            "paymentContractAddress": self.payment_contract_address,
            "hash": hash,
            "identifier": self.payment_id
        }

        async with aiohttp.ClientSession() as session:
            async with session.patch(
                f"{self.config.payment_service_url}/payment/",
                headers=self._headers,
                json=payload
            ) as response:
                if response.status == 400:
                    raise ValueError(f"Bad request: {await response.text()}")
                if response.status == 401:
                    raise ValueError("Unauthorized: Invalid API key")
                if response.status == 500:
                    raise Exception("Internal server error")
                if response.status != 200:
                    raise Exception(f"Payment completion failed: {await response.text()}")
                
                return await response.json()

    async def start_status_monitoring(self, callback=None):
        async def monitor():
            while True:
                try:
                    status = await self.check_payment_status()
                    if callback:
                        await callback(status)
                    await asyncio.sleep(60)
                except Exception as e:
                    print(f"Status monitoring error: {e}")
                    await asyncio.sleep(60)

        self._status_check_task = asyncio.create_task(monitor())

    def stop_status_monitoring(self):
        if self._status_check_task:
            self._status_check_task.cancel() 