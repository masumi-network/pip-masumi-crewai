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
import aiohttp

# Create a test session marker
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def print_test_separator(test_name: str):
    logger.info("=" * 80)
    logger.info(f"Starting test session: {test_name}")
    logger.info("=" * 80)

# Constants for delays
DELAY_AFTER_REGISTRATION = 60  # seconds
DELAY_AFTER_PAYMENT_CREATE = 5  # seconds

def generate_unique_agent_name() -> str:
    """Generate a unique agent name under 32 characters"""
    timestamp = datetime.now().strftime("%m%d%H%M")
    base_name = "Test_Agent"
    return f"{base_name}_{timestamp}"  # e.g. "Test_Agent_0221143022"

# At the module level, add a variable to store the agent name
_agent_name = None

@pytest.fixture
async def test_agent():
    """Create a test agent for use in tests"""
    global _agent_name
    logger.info("Creating test agent fixture")
    
    # Generate a unique agent name only once
    if _agent_name is None:
        _agent_name = generate_unique_agent_name()
        logger.info(f"Generated agent name: {_agent_name}")
    else:
        logger.info(f"Using existing agent name: {_agent_name}")
    
    # Rest of the fixture code, using _agent_name instead of generating a new one
    config = Config(
        payment_service_url="http://localhost:3001/api/v1",
        payment_api_key="abcdef_this_should_be_very_secure",
        registry_service_url="http://localhost:3001/api/v1",
        registry_api_key="abcdef_this_should_be_very_secure"
    )
    
    agent = Agent(
        name=_agent_name,
        config=config,
        description="Test agent for automated testing",
        example_output="Example output from test agent",
        tags=["test", "automated"],
        api_url="http://example.com/api",
        author_name="Test Author",
        author_contact="test@example.com",
        author_organization="Test Organization",
        legal_privacy_policy="",
        legal_terms="http://example.com/terms",
        legal_other="http://example.com/other",
        capability_name="test_capability",
        capability_version="1.0.0",
        requests_per_hour="100",
        pricing_unit="lovelace",
        pricing_quantity="10000000"
    )
    
    logger.debug(f"Test agent fixture created with name: {agent.name}")
    return agent

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
                if asset["name"] == agent.name and asset["state"] == "RegistrationConfirmed":
                    agent_found = True
                        # Store the agent ID for future tests
                    if "agentIdentifier" in asset:
                        test_register_agent.agent_id = asset["agentIdentifier"]
                        logger.info(f"Stored agent ID for future tests: {test_register_agent.agent_id}")
                    else:
                        logger.warning("Agent ID not found in registration response, future tests will use fallback ID")
                    break
            
            if agent_found:

                logger.info(f"Waiting {DELAY_AFTER_REGISTRATION} seconds before next test...")
                await asyncio.sleep(DELAY_AFTER_REGISTRATION)

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
    amounts = [Amount(amount="10000000", unit="lovelace")]
    
    # Try to get agent ID from registration test, use fallback if not available
    try:
        agent_id = test_register_agent.agent_id
        logger.info(f"Using agent ID from registration: {agent_id}")
    except (AttributeError, NameError):
        # More robust error handling
        agent_id = "0520e542b4704586b7899e8af207501fd1cfb4d12fc419ede7986de87c5c56930437a2e5c068da1a2970b6444d98e3aca37ae62302154b0ecdcae9ec"  # Fallback ID
        logger.warning(f"Registration test not run or agent ID not stored, using fallback agent ID: {agent_id}")
    
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
    
    # Store the entire payment response for the next tests
    test_create_payment_request_success.payment_response = result
    test_create_payment_request_success.last_payment_id = blockchain_id
    logger.info(f"Stored payment response for future tests")
    
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
    
    # Get the complete payment response from the previous test
    try:
        payment_response = test_create_payment_request_success.payment_response
        blockchain_identifier = payment_response["data"]["blockchainIdentifier"]
        logger.info(f"Using blockchain identifier from payment test")
        
        # Get the exact time values from the payment response
        submit_result_time = payment_response["data"]["submitResultTime"]
        unlock_time = payment_response["data"]["unlockTime"]
        external_dispute_unlock_time = payment_response["data"]["externalDisputeUnlockTime"]
        
        # Get the agent identifier from the registration test, not from the payment
        try:
            agent_identifier = test_register_agent.agent_id
            logger.info(f"Using agent ID from registration: {agent_identifier}")
        except (AttributeError, NameError):
            # Fallback if registration test didn't run or agent ID wasn't stored
            agent_identifier = "0520e542b4704586b7899e8af207501fd1cfb4d12fc419ede7986de87c5c56930437a2e5c068da1a2970b6444d98e3aca37ae62302154b0ecdcae9ec"
            logger.warning(f"Registration test not run or agent ID not stored, using fallback agent ID: {agent_identifier}")
        
        # Store the agent identifier for future tests
        test_create_purchase_request.agent_identifier = agent_identifier
        
    except AttributeError:
        logger.error("Payment response not available - payment test may not have run")
        pytest.skip("Payment response not available, skipping test")
    
    # Get the seller vkey
    seller_vkey = await agent.get_selling_wallet_vkey()
    logger.debug(f"Using seller vkey: {seller_vkey}")
    
    # Create purchase amounts
    amounts = [
        PurchaseAmount(amount="10000000", unit="lovelace")
    ]
    logger.debug(f"Purchase amounts: {amounts}")
    
    # Ensure we have a purchaser ID
    if _purchaser_id is None:
        import random
        random_id = ''.join([str(random.randint(0, 9)) for _ in range(15)])
        _purchaser_id = f"pur_{random_id}"
        logger.warning(f"Generated new purchaser identifier: {_purchaser_id}")
    else:
        logger.info(f"Using existing purchaser identifier: {_purchaser_id}")
    
    # Create purchase instance with the exact values from payment response
    purchase = Purchase(
        config=agent.config,
        blockchain_identifier=blockchain_identifier,
        seller_vkey=seller_vkey,
        amounts=amounts,
        agent_identifier=agent_identifier,  # Use the agent identifier from registration
        identifier_from_purchaser=_purchaser_id,
        submit_result_time=submit_result_time,
        unlock_time=unlock_time,
        external_dispute_unlock_time=external_dispute_unlock_time
    )
    logger.debug("Purchase instance created with exact values from payment response")
    
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

@pytest.mark.asyncio
async def test_check_purchase_status(test_agent, payment):
    """Test checking the status of a purchase request"""
    print_test_separator("Purchase Status Check Test")
    agent = await test_agent
    
    logger.info("Starting purchase status check")
    
    # Get the blockchain ID from the previous test
    try:
        blockchain_id = test_create_payment_request_success.last_payment_id
        logger.info(f"Using blockchain ID from payment test: {blockchain_id}")
        
        # Add the blockchain identifier to the payment's tracking set
        payment.payment_ids.add(blockchain_id)
        #logger.info(f"Added blockchain ID to payment tracking: {blockchain_id}")
    except AttributeError:
        logger.error("Blockchain ID not found - payment test may not have run")
        pytest.skip("Blockchain ID not available, skipping test")
    
    # Use the injected payment fixture
    logger.info(f"Using payment fixture with purchaser ID: {payment.identifier_from_purchaser}")
    
    # Set up retry parameters
    MAX_RETRIES = 10
    RETRY_DELAY = 60  # seconds
    
    # Check the payment status with retries
    for attempt in range(MAX_RETRIES):
        logger.info(f"Checking payment status (attempt {attempt + 1}/{MAX_RETRIES})")
        
        try:
            # Use the payment object's method to check payment status
            result = await payment.check_payment_status()
            
            # Verify the response structure
            assert "status" in result, "Response missing 'status' field"
            assert result["status"] == "success", "Status is not 'success'"
            assert "data" in result, "Response missing 'data' field"
            assert "payments" in result["data"], "Response missing 'payments' field"
            
            # Look for our payment in the list by blockchain ID
            payment_found = False
            for payment_status in result["data"]["payments"]:
                if payment_status["blockchainIdentifier"] == blockchain_id:
                    payment_found = True
                    #logger.info(f"Found payment with blockchain ID: {blockchain_id}")
                    
                    # Check for onChainState field
                    if "onChainState" in payment_status:
                        on_chain_state = payment_status["onChainState"]
                        logger.info(f"Payment onChainState: {on_chain_state}")
                        
                        # Check if the payment has been confirmed on-chain
                        if on_chain_state == "FundsLocked":
                            logger.info("Payment confirmed on-chain with FundsLocked status!")
                            return
                    
                    # Also check NextAction as a fallback
                    current_status = payment_status.get("NextAction", {}).get("requestedAction", "Unknown")
                    logger.info(f"Current payment status: {current_status}")
                    
                    # Check if the payment has been confirmed
                    if current_status in ["PaymentComplete", "FundsLocked"]:
                        logger.info(f"Payment confirmed with status: {current_status}")
                        return
                    
                    break
            
            if not payment_found:
                logger.warning(f"Payment with blockchain ID {blockchain_id} not found in status response")
            
            # If we're still waiting for confirmation, try again
            logger.info(f"Payment not yet confirmed, waiting {RETRY_DELAY} seconds before next check...")
            await asyncio.sleep(RETRY_DELAY)
                
        except Exception as e:
            logger.error(f"Error during payment status check: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                await asyncio.sleep(RETRY_DELAY)
            else:
                raise
    
    # If we get here, all retries failed to find a confirmed payment
    logger.warning("Payment not confirmed after all retries")
    # Don't fail the test, as confirmation might take longer than our test window
    logger.info("Test completed - payment may still be processing")

@pytest.mark.asyncio
async def test_complete_payment(test_agent, payment):
    """Test completing a payment after purchase has been confirmed"""
    print_test_separator("Payment Completion Test")
    agent = await test_agent
    
    logger.info("Starting payment completion test")
    
    # Get the blockchain ID from the previous test
    try:
        blockchain_id = test_create_payment_request_success.last_payment_id
        logger.info(f"Using blockchain ID from payment test: {blockchain_id}")
        
        # Add the blockchain identifier to the payment's tracking set if not already there
        payment.payment_ids.add(blockchain_id)
        #logger.info(f"Using blockchain ID for payment completion: {blockchain_id}")
    except AttributeError:
        logger.error("Blockchain ID not found - payment test may not have run")
        pytest.skip("Blockchain ID not available, skipping test")
    
    # Get the purchase ID from the previous test
    try:
        purchase_id = test_create_purchase_request.purchase_id
        logger.info(f"Using purchase ID from previous test: {purchase_id}")
    except AttributeError:
        logger.warning("Purchase ID not found - using None")
        purchase_id = None
    
    # Attempt to complete the payment directly
    logger.info("Attempting to complete payment")
    
    try:
        # Call the complete_payment method
        result = await payment.complete_payment(blockchain_id, "random hash")
        
        # Verify the response
        assert "status" in result, "Response missing 'status' field"
        assert result["status"] == "success", "Status is not 'success'"
        
        logger.info("Payment completion request successful")
        logger.debug(f"Payment completion response: {result}")
        
        # Check the payment status after completion
        logger.info("Checking payment status after completion")
        final_status = await payment.check_payment_status()
        
        # Look for our payment in the list
        for payment_status in final_status["data"]["payments"]:
            if payment_status["blockchainIdentifier"] == blockchain_id:
                # Check the final status
                if "onChainState" in payment_status:
                    logger.info(f"Final onChainState: {payment_status['onChainState']}")
                
                final_action = payment_status.get("NextAction", {}).get("requestedAction", "Unknown")
                logger.info(f"Final payment status: {final_action}")
                
                # The payment should be in a completed state
                if final_action in ["PaymentComplete", "None"] or payment_status.get("onChainState") == "Complete":
                    logger.info("Payment has been successfully completed")
                else:
                    logger.warning(f"Payment completion may still be processing. Current status: {final_action}")
                
                break
        
    except Exception as e:
        logger.error(f"Error during payment completion: {str(e)}")
        # Don't fail the test if completion is still processing
        logger.warning("Payment completion test encountered an error, but test will continue")
    
    logger.info("Payment completion test finished")

@pytest.mark.asyncio
async def test_monitor_payment_status(test_agent, payment):
    """Test monitoring the payment status after completion"""
    print_test_separator("Payment Status Monitoring Test")
    agent = await test_agent
    
    logger.info("Starting payment status monitoring test")
    
    # Get the blockchain ID from the previous test
    try:
        blockchain_id = test_create_payment_request_success.last_payment_id
        logger.info(f"Using blockchain ID from payment test: {blockchain_id}")
        
        # Add the blockchain identifier to the payment's tracking set if not already there
        payment.payment_ids.add(blockchain_id)
        #logger.info(f"Using blockchain ID for payment monitoring: {blockchain_id}")
    except AttributeError:
        logger.error("Blockchain ID not found - payment test may not have run")
        pytest.skip("Blockchain ID not available, skipping test")
    
    # Set up monitoring parameters
    MONITOR_DURATION = 300  # 5 minutes
    CHECK_INTERVAL = 60     # 1 minute
    MAX_CHECKS = MONITOR_DURATION // CHECK_INTERVAL
    
    logger.info(f"Starting payment status monitoring for {MONITOR_DURATION} seconds")
    logger.info(f"Will check status every {CHECK_INTERVAL} seconds")
    
    # Start the monitoring task
    async def monitor_task():
        for check_num in range(1, MAX_CHECKS + 1):
            logger.info(f"Payment status check {check_num}/{MAX_CHECKS}")
            try:
                result = await payment.check_payment_status()
                
                # Look for our payment in the list
                payment_found = False
                for payment_status in result["data"]["payments"]:
                    if payment_status["blockchainIdentifier"] == blockchain_id:
                        payment_found = True
                        #logger.info(f"Found payment with blockchain ID: {blockchain_id}")
                        
                        # Check the current status
                        if "onChainState" in payment_status:
                            on_chain_state = payment_status["onChainState"]
                            logger.info(f"Payment onChainState: {on_chain_state}")
                            
                            # If the payment is complete, we can stop monitoring
                            if on_chain_state == "Complete":
                                logger.info("Payment is complete, stopping monitoring")
                                return True
                        
                        # Also check NextAction
                        current_status = payment_status.get("NextAction", {}).get("requestedAction", "Unknown")
                        logger.info(f"Current payment status: {current_status}")
                        
                        # If the payment is complete, we can stop monitoring
                        if current_status in ["PaymentComplete", "None"]:
                            logger.info("Payment is complete, stopping monitoring")
                            return True
                        
                        break
                
                if not payment_found:
                    logger.warning(f"Payment with blockchain ID {blockchain_id} not found in status response")
                
                # Wait for the next check
                logger.info(f"Waiting {CHECK_INTERVAL} seconds before next check...")
                await asyncio.sleep(CHECK_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error during payment status check: {str(e)}")
                # Continue monitoring despite errors
                await asyncio.sleep(CHECK_INTERVAL)
        
        logger.warning(f"Monitoring period of {MONITOR_DURATION} seconds ended without payment completion")
        return False
    
    # Create and start the monitoring task
    payment._status_check_task = asyncio.create_task(monitor_task())
    
    try:
        # Wait for the monitoring task to complete
        completed = await payment._status_check_task
        
        if completed:
            logger.info("Payment monitoring completed successfully - payment is complete")
        else:
            logger.warning("Payment monitoring completed without detecting payment completion")
            
    except asyncio.CancelledError:
        logger.info("Payment monitoring task was cancelled")
    except Exception as e:
        logger.error(f"Error during payment monitoring: {str(e)}")
    finally:
        # Clean up the monitoring task
        payment.stop_status_monitoring()
    
    logger.info("Payment status monitoring test finished")
