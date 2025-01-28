from dataclasses import dataclass
from datetime import datetime
import asyncio
from typing import List, Optional, Dict, Any
import aiohttp
from .config import config

@dataclass
class Amount:
    amount: int
    unit: str

class Payment:
    def __init__(self, agent_identifier: str, seller_vkey: str, amounts: List[Amount], 
                 network: str = "PREPROD", payment_type: str = "WEB3_CARDANO_V1"):
        self.agent_identifier = agent_identifier
        self.seller_vkey = seller_vkey
        self.contract_address = config.contract_address
        self.amounts = amounts
        self.network = network
        self.payment_type = payment_type
        self.payment_id: Optional[str] = None
        self._status_check_task: Optional[asyncio.Task] = None
        self._headers = {
            "Authorization": f"Bearer {config.payment_api_key_v2}",
            "Content-Type": "application/json"
        }

    async def create_payment_request(self, unlock_time: str, submit_result_time: str, 
                                   refund_time: str) -> Dict[str, Any]:
        payload = {
            "agentIdentifier": self.agent_identifier,
            "network": self.network,
            "sellerVkey": self.seller_vkey,
            "contractAddress": self.contract_address,
            "amounts": [{"amount": amt.amount, "unit": amt.unit} for amt in self.amounts],
            "paymentType": self.payment_type,
            "unlockTime": unlock_time,
            "submitResultTime": submit_result_time,
            "refundTime": refund_time
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{config.payment_service_url_v2}/payment",
                headers=self._headers,
                json=payload
            ) as response:
                if response.status != 200:
                    raise Exception(f"Payment request failed: {await response.text()}")
                
                result = await response.json()
                self.payment_id = result["data"]["identifier"]
                return result

    async def check_payment_status(self) -> Dict[str, Any]:
        params = {
            "network": self.network,
            "contractAddress": self.contract_address,
            "limit": 1
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{config.payment_service_url_v2}/payment",
                headers=self._headers,
                params=params
            ) as response:
                if response.status != 200:
                    raise Exception(f"Status check failed: {await response.text()}")
                return await response.json()

    async def complete_payment(self, hash: str) -> Dict[str, Any]:
        if not self.payment_id:
            raise ValueError("No payment ID available. Create payment request first.")

        payload = {
            "network": self.network,
            "sellerVkey": self.seller_vkey,
            "contractAddress": self.contract_address,
            "hash": hash,
            "identifier": self.payment_id
        }

        async with aiohttp.ClientSession() as session:
            async with session.patch(
                f"{config.payment_service_url_v2}/payment",
                headers=self._headers,
                json=payload
            ) as response:
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
                    await asyncio.sleep(60)  # Check every minute
                except Exception as e:
                    print(f"Status monitoring error: {e}")
                    await asyncio.sleep(60)  # Wait before retrying

        self._status_check_task = asyncio.create_task(monitor())

    def stop_status_monitoring(self):
        if self._status_check_task:
            self._status_check_task.cancel() 