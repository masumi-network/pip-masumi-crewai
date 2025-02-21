import os
import logging
import sys

# Force logging to stdout
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Configure logging before any imports
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
    force=True  # Override any existing logging configuration
)

# Ensure pytest doesn't capture logging
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

import pytest
import asyncio
from datetime import datetime, timezone
from masumi_crewai.registry import Agent
from masumi_crewai.payment import Payment, Amount
from masumi_crewai.config import Config

# Create a test session marker
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def print_test_separator(test_name: str):
    logger.info("=" * 80)
    logger.info(f"Starting test session: {test_name}")
    logger.info("=" * 80)

# Constants for delays
DELAY_AFTER_REGISTRATION = 10  # seconds
DELAY_AFTER_PAYMENT_CREATE = 5  # seconds

def generate_unique_agent_name() -> str:
    """Generate a unique agent name under 32 characters"""
    timestamp = datetime.now().strftime("%m%d%H%M")
    base_name = "Test_Agent"
    return f"{base_name}_{timestamp}"  # e.g. "Test_Agent_0221143022"

@pytest.fixture
async def test_agent():
    """Fixture to create and register an agent for tests"""
    logger.info("Creating agent fixture")
    
    # Generate unique name
    agent_name = generate_unique_agent_name()
    logger.info(f"Generated unique agent name: {agent_name}")
    
    config = Config(
        payment_service_url="http://localhost:3001/api/v1",
        payment_api_key="abcdef_this_should_be_very_secure"
    )
    logger.debug(f"Config created with URL: {config.payment_service_url}")
    
    agent = Agent(
        config=config,
        name=agent_name,
        api_url="https://api.example.com",
        description="Test Agent Description",
        author_name="Author Name",
        author_contact="author@example.com",
        author_organization="Author Organization",
        legal_privacy_policy="Privacy Policy URL",
        legal_terms="Terms of Service URL",
        legal_other="Other Legal Information URL",
        capability_name="Capability Name",
        capability_version="1.0.0",
        requests_per_hour="100",
        pricing_unit="lovelace",
        pricing_quantity="20000000"
    )
    logger.debug(f"Agent created with name: {agent.name} on network: {agent.network}")
    return agent  # Change back to return instead of yield

@pytest.mark.asyncio
async def test_register_agent(test_agent):
    """Test agent registration - should be run first to get agent ID"""
    agent = await test_agent  # Await the fixture
    print_test_separator("Agent Registration Test")
    
    logger.info("Starting agent registration process")
    logger.debug("Fetching selling wallet vkey before registration")
    result = await agent.register()  # Use the awaited agent
    
    logger.info("Verifying registration response")
    logger.debug(f"Full registration response: {result}")
    
    # Verify the response
    assert "data" in result, "Response missing 'data' field"
    assert "name" in result["data"], "Response data missing 'name' field"
    assert "success" in result["status"], "Response missing 'success' status"
    
    logger.info(f"Registration successful for agent: {result['data']['name']}")
    logger.debug(f"Registration status: {result['status']}")
    
    logger.info(f"Waiting {DELAY_AFTER_REGISTRATION} seconds before next test...")
    await asyncio.sleep(DELAY_AFTER_REGISTRATION)
    
    logger.info("Agent registration test completed successfully")

@pytest.mark.asyncio
async def test_check_registration_status(test_agent):
    """Test checking registration status - should be run after registration"""
    agent = await test_agent
    print_test_separator("Registration Status Check Test")
    
    MAX_RETRIES = 10
    RETRY_DELAY = 60  # seconds
    
    # Get the wallet vkey
    logger.info("Fetching selling wallet vkey")
    wallet_vkey = await agent.get_selling_wallet_vkey()
    logger.debug(f"Retrieved wallet vkey: {wallet_vkey}")
    
    for attempt in range(MAX_RETRIES):
        logger.info(f"Checking registration status (attempt {attempt + 1}/{MAX_RETRIES})")
        result = await agent.check_registration_status(wallet_vkey)
        
        try:
            # Verify the response
            assert "status" in result, "Response missing 'status' field"
            assert result["status"] == "success", "Status is not 'success'"
            assert "data" in result, "Response missing 'data' field"
            assert "assets" in result["data"], "Response data missing 'assets' field"
            
            # Verify our agent exists in the list
            agent_found = False
            for asset in result["data"]["assets"]:
                if asset["metadata"]["name"] == agent.name:
                    agent_found = True
                    logger.info(f"Found agent in registration status: {agent.name}")
                    logger.debug(f"Agent metadata: {asset['metadata']}")
                    break
            
            if agent_found:
                logger.info("Registration status check completed successfully")
                return  # Exit the function if agent is found
            
            logger.warning(f"Agent {agent.name} not found in registration status")
            
        except AssertionError as e:
            logger.error(f"Assertion failed: {str(e)}")
        
        if attempt < MAX_RETRIES - 1:  # Don't sleep after the last attempt
            logger.info(f"Waiting {RETRY_DELAY} seconds before next attempt...")
            await asyncio.sleep(RETRY_DELAY)
    
    # If we get here, all retries failed
    raise AssertionError(f"Agent {agent.name} not found in registration status after {MAX_RETRIES} attempts")

@pytest.fixture
def payment():
    logger.info("Creating payment fixture")
    config = Config(
        payment_service_url="http://localhost:3001/api/v1",
        payment_api_key="abcdef_this_should_be_very_secure"
    )
    amounts = [Amount(amount="5000000", unit="lovelace")]
    
    # Try to get agent ID from registration test, use fallback if not available
    try:
        agent_id = test_register_agent.agent_id
        logger.info(f"Using agent ID from registration: {agent_id}")
    except AttributeError:
        agent_id = "dcdf2c533510e865e3d7e0f0e5537c7a176dd4dc1df69e83a703976b02e8980383e6173ac6e2f55e91b6e5ffa3a2ea8d17c00a381e4cf1f4541a1dc9"  # Fallback ID
        logger.warning(f"Registration test not run, using fallback agent ID: {agent_id}")
    
    payment = Payment(
        agent_identifier=agent_id,
        amounts=amounts,
        config=config,
        network="Preprod"
    )
    logger.debug(f"Payment fixture created with agent: {payment.agent_identifier}")
    return payment

@pytest.mark.asyncio
async def test_create_payment_request_success(payment):
    print_test_separator("Payment Request Creation Test")
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
    
    logger.info(f"Waiting {DELAY_AFTER_PAYMENT_CREATE} seconds before next test...")
    await asyncio.sleep(DELAY_AFTER_PAYMENT_CREATE)
    
    logger.info("Payment request creation test passed successfully")
    return blockchain_id

@pytest.mark.asyncio
async def test_check_existing_payment_status(payment):
    print_test_separator("Payment Status Check Test")
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
            logger.info(f"Found payment status: {payment_status['NextAction']['requestedAction']}")
            # Verify it has the expected fields
            assert "requestedAction" in payment_status["NextAction"]
            break
    
    assert payment_found, f"Payment with ID {payment_id} not found in status response"
    logger.info("Payment status check test passed successfully")
