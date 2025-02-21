import os
import logging

# Configure logging before any imports
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

import pytest
from masumi_crewai.registry import Agent, Author, Legal, Capability, Pricing
from masumi_crewai.config import Config

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

@pytest.mark.asyncio
async def test_register_agent():
    logger.info("Starting test_register_agent")
    
    # Create config
    config = Config(
        registry_service_url="http://localhost:3001/api/v1",
        registry_api_key="abcdef_this_should_be_very_secure"
    )
    
    # Create test data
    author = Author(
        name="Author Name",
        contact="author@example.com",
        organization="Author Organization"
    )
    
    legal = Legal(
        privacy_policy="Privacy Policy URL",
        terms="Terms of Service URL",
        other="Other Legal Information URL"
    )
    
    capability = Capability(
        name="Capability Name",
        version="1.0.0"
    )
    
    pricing = [
        Pricing(
            unit="usdm",
            quantity="500000000"
        )
    ]
    
    # Create agent
    agent = Agent(
        config=config,
        name="Test Agent",
        api_url="https://api.example.com",
        description="Test Agent Description",
        author=author,
        legal=legal,
        selling_wallet_vkey="wallet_vkey",
        capability=capability,
        requests_per_hour="100",
        pricing=pricing
    )
    
    logger.info("Registering agent")
    result = await agent.register()
    
    # Verify the response
    assert "data" in result
    assert "id" in result["data"]
    logger.info(f"Agent registered with ID: {result['data']['id']}")
    
    logger.info("Agent registration test passed successfully") 