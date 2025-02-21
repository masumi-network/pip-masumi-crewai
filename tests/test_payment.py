import os
import logging

# Set mock environment variables BEFORE any other imports

# Configure logging before any imports
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Now we can import everything else
import pytest
import asyncio
from datetime import datetime, timezone
from masumi_crewai.payment import Payment, Amount
from masumi_crewai.config import Config

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

@pytest.fixture
def payment():
    logger.info("Creating payment fixture")
    config = Config(
        payment_service_url="http://localhost:3001/api/v1",
        payment_api_key="abcdef_this_should_be_very_secure"
    )
    amounts = [Amount(amount="5000000", unit="lovelace")]
    payment = Payment(
        agent_identifier="dcdf2c533510e865e3d7e0f0e5537c7a176dd4dc1df69e83a703976b02e8980383e6173ac6e2f55e91b6e5ffa3a2ea8d17c00a381e4cf1f4541a1dc9",
        amounts=amounts,
        config=config,
        network="Preprod"
    )
    logger.debug(f"Payment fixture created with agent: {payment.agent_identifier}")
    return payment

@pytest.mark.asyncio
async def test_create_payment_request_success(payment):
    logger.info("Starting test_create_payment_request_success")
    
    logger.info("Executing create_payment_request")
    result = await payment.create_payment_request()
    
    logger.debug(f"Received result: {result}")
    
    # Verify the response has the expected structure
    assert "data" in result
    assert "blockchainIdentifier" in result["data"]
    blockchain_id = result["data"]["blockchainIdentifier"]
    assert blockchain_id in payment.payment_ids
    
    # Store the ID for the next test
    test_create_payment_request_success.last_payment_id = blockchain_id
    logger.info("Payment request creation test passed successfully")
    return blockchain_id

@pytest.mark.asyncio
async def test_check_existing_payment_status(payment):
    logger.info("Starting test_check_existing_payment_status")
    
    # Get the ID from the previous test and add it to payment_ids
    payment_id = test_create_payment_request_success.last_payment_id
    logger.info(f"Checking status for payment: {payment_id}")
    payment.payment_ids.add(payment_id)  # Add the ID to the new payment instance
    
    # Check the payment status
    status_result = await payment.check_payment_status()
    logger.debug(f"Status check result: {status_result}")
    
    # Verify the response
    assert "data" in status_result
    assert "payments" in status_result["data"]
    
    # Find our payment in the list
    payment_found = False
    for payment_status in status_result["data"]["payments"]:
        if payment_status["blockchainIdentifier"] == payment_id:
            payment_found = True
            logger.info(f"Found payment status: {payment_status["NextAction"]["requestedAction"]}")
            # Verify it has the expected fields
            assert "requestedAction" in payment_status["NextAction"]
            break
    
    assert payment_found, f"Payment with ID {payment_id} not found in status response"
    logger.info("Payment status check test passed successfully")