import os
import requests
import time
from .config import config  # Import the centralized configuration

class RemoteCrew:
    def __init__(self):
        """
        Initialize the RemoteCrew using the centralized configuration.
        """
        self.registry_service_url = config.registry_service_url
        self.payment_service_url = config.payment_service_url
        self.registry_api_key = config.registry_api_key
        self.payment_api_key = config.payment_api_key
        self.contract_address = config.contract_address  # Fixed contract address from config

    def _make_registry_request(self, endpoint, params=None):
        """
        Make a request to the Registry Service.

        Args:
            endpoint (str): The API endpoint to call.
            params (dict): Query parameters for the request.

        Returns:
            dict: The JSON response from the Registry Service.
        """
        headers = {
            "Authorization": f"Bearer {self.registry_api_key}"
        }
        url = f"{self.registry_service_url}/{endpoint}"
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def _make_payment_request(self, endpoint, method="POST", data=None):
        """
        Make a request to the Payment Service.

        Args:
            endpoint (str): The API endpoint to call.
            method (str): HTTP method (default is POST).
            data (dict): JSON payload for the request.

        Returns:
            dict: The JSON response from the Payment Service.
        """
        headers = {
            "Authorization": f"Bearer {self.payment_api_key}",
            "Content-Type": "application/json"
        }
        url = f"{self.payment_service_url}/{endpoint}"
        if method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PATCH":
            response = requests.patch(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        response.raise_for_status()
        return response.json()

    def load_crew(self, asset_id, policy_id):
        """
        Fetch details about a remote crew from the Registry Service.

        Args:
            asset_id (str): The asset ID of the remote crew.
            policy_id (str): The policy ID of the remote crew.

        Returns:
            dict: Details about the remote crew, including its base URL and sellervKey.
        """
        params = {
            "asset_id": asset_id,
            "policy_id": policy_id
        }
        response = self._make_registry_request("registry-entry", params=params)
        
        # Extract the sellervKey and base URL from the response
        entries = response.get("data", {}).get("entries", [])
        if not entries:
            raise ValueError("No entries found in the registry response.")
        
        crew_details = entries[0]  # Assuming the first entry is the correct one
        return {
            "base_url": crew_details.get("api_url"),
            "sellervKey": crew_details.get("sellervKey")
        }

    def start_job(self, crew_base_url, input_data):
        """
        Start a job on the remote crew.

        Args:
            crew_base_url (str): The base URL of the remote crew.
            input_data (str): The input data for the job.

        Returns:
            str: The job ID returned by the remote crew.
        """
        url = f"{crew_base_url}/start_job"
        payload = {
            "input_data": input_data
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json().get("job_id")

    def pay_for_job(self, job_id, seller_vkey, amounts, network="PREPROD", payment_type="WEB3_CARDANO_V1"):
        """
        Pay for a job using the Payment Service.
        """
        payload = {
            "identifier": job_id,
            "network": network,
            "sellerVkey": seller_vkey,
            "contractAddress": self.contract_address,
            "amounts": amounts,
            "paymentType": payment_type,
            "unlockTime": "2024-12-01T23:00:00.000Z",
            "refundTime": "2024-12-02T23:00:00.000Z",
            "submitResultTime": "2024-12-01T22:00:00.000Z"
        }
        return self._make_payment_request("purchase", data=payload)

    def check_job_status(self, crew_base_url, job_id):
        """
        Check the status of a job.

        Args:
            crew_base_url (str): The base URL of the remote crew.
            job_id (str): The job ID to check.

        Returns:
            dict: The job status.
        """
        url = f"{crew_base_url}/status"
        params = {
            "job_id": job_id
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def request_refund(self, job_id, seller_vkey, network="PREPROD"):
        """
        Request a refund for a job.

        Args:
            job_id (str): The job ID to request a refund for.
            seller_vkey (str): The seller's verification key.
            network (str): The blockchain network (default is PREPROD).

        Returns:
            dict: The refund response.
        """
        payload = {
            "identifier": job_id,
            "network": network,
            "sellerVkey": seller_vkey,
            "address": self.contract_address  # Use the fixed contract address from config
        }
        return self._make_payment_request("purchase", method="PATCH", data=payload)

    def call(self, asset_id, policy_id, input_data, network="PREPROD"):
        """
        Execute the full workflow:
        1. Load the remote crew details.
        2. Start a job on the remote crew.
        3. Pay for the job.
        4. Poll for job status until completion or timeout.
        5. Handle refunds if the job doesn't complete in time.

        Args:
            asset_id (str): The asset ID of the remote crew.
            policy_id (str): The policy ID of the remote crew.
            input_data (str): The input data for the job.
            network (str): The blockchain network (default is PREPROD).

        Returns:
            str: The final result of the job or a refund message.
        """
        # Step 1: Load remote crew details
        crew_details = self.load_crew(asset_id, policy_id)
        crew_base_url = crew_details.get("base_url")
        seller_vkey = crew_details.get("sellervKey")
        
        if not crew_base_url or not seller_vkey:
            raise ValueError("Failed to load crew details from the registry.")

        # Step 2: Start a job
        job_id = self.start_job(crew_base_url, input_data)

        # Step 3: Pay for the job
        amounts = [{"amount": 1000000, "unit": "lovelace"}]
        self.pay_for_job(job_id, seller_vkey, amounts, network=network)

        # Step 4: Poll for job status
        start_time = time.time()
        while True:
            status = self.check_job_status(crew_base_url, job_id)
            if status.get("status") == "completed":
                return status.get("result")

            # Check if the submitResultTime has passed
            if time.time() - start_time > 3600:  # Example timeout (1 hour)
                break

            time.sleep(10)  # Poll every 10 seconds

        # Step 5: Request a refund if the job didn't complete
        self.request_refund(job_id, seller_vkey, network=network)
        return "Job did not complete in time. Refund requested."