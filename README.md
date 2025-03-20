# Masumi

Masumi Payment Module for Cardano blockchain integration.

## Installation

```bash
pip install masumi
```

## Usage

See documentation for usage details.

## Quick Start

### Configuration

```python
from masumi.config import Config

config = Config(
    payment_service_url="http://api.masumi.network",
    payment_api_key="YOUR_PAYMENT_API_KEY",
    registry_api_key="YOUR_REGISTRY_API_KEY"
)
```

### Payment Handling

```python
from masumi.payment import Payment, Amount
import asyncio

async def create_payment():
    # Initialize payment
    payment = Payment(
        agent_identifier="your_agent_id",
        amounts=[Amount(amount="1000000", unit="lovelace")],
        config=config,
        network="Preprod",
        identifier_from_purchaser="purchaser_123",
        input_data="data to be hashed"  # Optional
    )

    # Create payment request
    result = await payment.create_payment_request()
    blockchain_id = result["data"]["blockchainIdentifier"]

    # Check status
    status = await payment.check_payment_status()

    # Complete payment
    await payment.complete_payment(blockchain_id, "result_hash")

    # Monitor payments with callback
    async def on_payment_complete(payment_id):
        print(f"Payment {payment_id} completed!")

    await payment.start_status_monitoring(
        callback=on_payment_complete,
        interval_seconds=30
    )
```

### Purchase Management

```python
from masumi.purchase import Purchase, PurchaseAmount

async def create_purchase():
    purchase = Purchase(
        config=config,
        blockchain_identifier="blockchain_id",
        seller_vkey="seller_vkey",
        amounts=[PurchaseAmount(amount="1000000")],
        agent_identifier="agent_id",
        submit_result_time=1234567890,  # Unix timestamp
        unlock_time=1234567890,
        external_dispute_unlock_time=1234567890,
        input_data="data to be hashed"  # Optional
    )

    result = await purchase.create_purchase_request()
```

### Agent Registration

```python
from masumi.registry import Agent

async def register_agent():
    agent = Agent(
        name="MyAgent",
        config=config,
        description="Agent description",
        example_output=[{
            "name": "output_name",
            "url": "https://example.com/output",
            "mimeType": "application/json"
        }],
        tags=["AI", "Cardano"],
        api_base_url="https://api.myagent.com",
        author_name="Author Name",
        author_contact="author@email.com",
        author_organization="Organization",
        legal_privacy_policy="",
        legal_terms="https://terms.url",
        legal_other="",
        capability_name="capability",
        capability_version="1.0.0",
        requests_per_hour="100",
        pricing_unit="lovelace",
        pricing_quantity="1000000",
        network="Preprod"
    )

    # Register the agent
    result = await agent.register()

    # Check registration status
    wallet_vkey = await agent.get_selling_wallet_vkey("Preprod")
    status = await agent.check_registration_status(wallet_vkey)
```

## Testing

Run the test suite:

```bash
pytest tests/test_masumi.py -v
```

## Documentation

For detailed documentation, visit:
- [Masumi Docs](https://www.docs.masumi.network/)
- [Masumi Website](https://www.masumi.network/)

## License

MIT License
