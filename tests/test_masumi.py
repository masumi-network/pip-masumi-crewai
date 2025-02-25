import os
import logging
import sys
from datetime import datetime, timezone, timedelta

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
from masumi_crewai.registry import Agent
from masumi_crewai.payment import Payment, Amount
from masumi_crewai.config import Config
from masumi_crewai.purchase import Purchase, PurchaseAmount

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
    
    MAX_RETRIES = 1
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
                if asset["name"] == agent.name and asset["state"] == "RegistrationConfirmed":
                    agent_found = True
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

# At the module level, add a variable to store the purchaser ID
_purchaser_id = None

@pytest.fixture
def payment():
    global _purchaser_id
    logger.info("Creating payment fixture")
    config = Config(
        payment_service_url="http://localhost:3001/api/v1",
        payment_api_key="abcdef_this_should_be_very_secure"
    )
    amounts = [Amount(amount="20000000", unit="lovelace")]
    
    # Try to get agent ID from registration test, use fallback if not available
    try:
        agent_id = test_register_agent.agent_id
        logger.info(f"Using agent ID from registration: {agent_id}")
    except AttributeError:
        agent_id = "0520e542b4704586b7899e8af207501fd1cfb4d12fc419ede7986de812ef8e159469109820efb7510d1d02482148a5fedd4f1fab05d9cd12b411a4e7"  # Fallback ID
        logger.warning(f"Registration test not run, using fallback agent ID: {agent_id}")
    
    # Create unique identifier for this purchaser (15-25 chars) using random numbers
    if _purchaser_id is None:
        import random
        random_id = ''.join([str(random.randint(0, 9)) for _ in range(15)])
        _purchaser_id = f"pur_{random_id}"
    
    logger.info(f"Using purchaser identifier: {_purchaser_id} (length: {len(_purchaser_id)})")
    
    payment_obj = Payment(
        agent_identifier=agent_id,
        amounts=amounts,
        config=config,
        network="Preprod",
        identifier_from_purchaser=_purchaser_id
    )
    
    # No need to store on the fixture anymore
    logger.debug(f"Payment fixture created with agent: {payment_obj.agent_identifier}")
    return payment_obj

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
    
    # Store the ID and time values for the next tests
    test_create_payment_request_success.last_payment_id = blockchain_id
    test_create_payment_request_success.time_values = result["time_values"]
    logger.info(f"Stored time values: {result['time_values']}")
    
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
    logger.debug(f"Status check result.")
    
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

@pytest.mark.asyncio
async def test_create_purchase_request(test_agent):
    global _purchaser_id
    """Test creating a purchase request"""
    print_test_separator("Purchase Request Test")
    agent = await test_agent
    
    logger.info("Setting up purchase request")
    
    # Get the seller vkey (same as we use for registration)
    seller_vkey = await agent.get_selling_wallet_vkey()
    logger.debug(f"Using seller vkey: {seller_vkey}")
    
    # Create purchase amounts
    amounts = [
        PurchaseAmount(amount="20000000", unit="lovelace")
    ]
    logger.debug(f"Purchase amounts: {amounts}")
    
    # Use the global purchaser ID
    if _purchaser_id is None:
        import random
        random_id = ''.join([str(random.randint(0, 9)) for _ in range(15)])
        _purchaser_id = f"pur_{random_id}"
        logger.warning(f"Generated new purchaser identifier: {_purchaser_id}")
    else:
        logger.info(f"Using existing purchaser identifier: {_purchaser_id}")
    
    # Get blockchain identifier from payment test or use agent_id as fallback
    try:
        blockchain_identifier = test_create_payment_request_success.last_payment_id
        logger.info(f"Using blockchain identifier from payment test.")
    except AttributeError:
            logger.warning(f"Problem with payment test.")
    # Get agent_id for agent_identifier parameter
    try:
        agent_id = test_register_agent.agent_id
        logger.info(f"Using agent ID from registration: {agent_id}")
    except AttributeError:
        agent_id = "0520e542b4704586b7899e8af207501fd1cfb4d12fc419ede7986de812ef8e159469109820efb7510d1d02482148a5fedd4f1fab05d9cd12b411a4e7"
        logger.warning(f"Registration test not run, using fallback agent ID: {agent_id}")
    
    # Get time values from previous payment test or generate new ones if not available
    try:
        time_values = test_create_payment_request_success.time_values
        logger.info(f"Using time values from payment test: {time_values}")
        submit_result_time = int(time_values["submitResultTime"])
        unlock_time = int(time_values["unlockTime"])
        external_dispute_unlock_time = int(time_values["externalDisputeUnlockTime"])
    except (AttributeError, KeyError):
        # If payment test wasn't run or didn't store time values, generate new ones
        logger.warning("Time values from payment test not available, generating new ones")
        future_time = int((datetime.now() + timedelta(hours=12)).timestamp())
        submit_result_time = unlock_time = external_dispute_unlock_time = future_time
        logger.debug(f"Generated time value: {future_time}")
    
    # Create purchase instance
    purchase = Purchase(
        config=agent.config,
        blockchain_identifier=blockchain_identifier,
        seller_vkey=seller_vkey,
        amounts=amounts,
        agent_identifier=agent_id,
        identifier_from_purchaser=_purchaser_id,
        submit_result_time=submit_result_time,
        unlock_time=unlock_time,
        external_dispute_unlock_time=external_dispute_unlock_time
    )
    logger.debug("Purchase instance created")
    
    # Create purchase request
    logger.info("Creating purchase request")
    result = await purchase.create_purchase_request()
    logger.debug(f"Purchase request result: {result}")
    
    # Verify the response
    assert "status" in result, "Response missing 'status' field"
    assert result["status"] == "success", "Status is not 'success'"
    assert "data" in result, "Response missing 'data' field"
    assert "id" in result["data"], "Response data missing 'id' field"
    assert "NextAction" in result["data"], "Response missing NextAction"
    assert result["data"]["NextAction"]["requestedAction"] == "FundsLockingRequested", \
        "Unexpected next action"
    
    # Store purchase ID for potential future tests
    test_create_purchase_request.purchase_id = result["data"]["id"]
    logger.info(f"Purchase request created with ID: {result['data']['id']}")
    
    logger.info("Purchase request test completed successfully")
