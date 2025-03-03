# Masumi CrewAI Payment Module

The **Masumi CrewAI** Payment Module provides a convenient way to integrate blockchain-based payment flows into AI agents using the **CrewAI** system. It abstracts the complexity of interacting with the Masumi/Cardano blockchain and offers high-level APIs for creating payment requests, monitoring status, handling purchase requests, and managing agent registrations on the Masumi network.

---

## Table of Contents
1. [Features](#features)  
2. [Installation](#installation)  
3. [Quick Start](#quick-start)  
   - [Basic Usage](#basic-usage)  
   - [Creating a Payment](#creating-a-payment)  
   - [Checking Payment Status](#checking-payment-status)  
   - [Completing a Payment](#completing-a-payment)  
   - [Monitoring Payments](#monitoring-payments)  
4. [Configuration](#configuration)  
5. [Advanced Usage](#advanced-usage)  
   - [Purchase Management](#purchase-management)  
   - [Agent Registration and Registry Queries](#agent-registration-and-registry-queries)  
6. [Testing](#testing)  
7. [Project Structure](#project-structure)  
8. [Documentation](#documentation)  
9. [License](#license)  
10. [Additional Resources](#additional-resources)

---

## Features

- **Blockchain Integration**: Interact seamlessly with the Cardano blockchain via the Masumi network.  
- **High-Level Payment API**: Create and manage payment requests using a simple Python interface.  
- **Async-Ready**: Use asynchronous functions for non-blocking operations (built on `aiohttp`).  
- **Configurable**: Use a central `Config` class to manage environment variables, API keys, and endpoints.  
- **Monitoring**: Built-in asynchronous monitoring of payment statuses with callback support.  
- **Purchase Flow**: Manage purchase requests that align with payment flows.  
- **Agent Registration**: Register AI agents and check their registration status within the Masumi network registry.

---

## Installation

Ensure you have Python 3.8+ installed. You can install the package from PyPI:

```bash
pip install pip-masumi-crewai
```

Alternatively, if you have the source code, install it locally:

```bash
pip install .
```

---

## Quick Start

### Basic Usage

Below is a minimal example demonstrating how to set up a **Payment** instance, create a payment request, check its status, and complete it.

```python
import asyncio
from masumi_crewai.payment import Payment, Amount
from masumi_crewai.config import Config

# 1. Create a configuration object with your API details
config = Config(
    payment_service_url="https://api.masumi.network",
    payment_api_key="YOUR_API_KEY_HERE"
)

# 2. Prepare a list of amounts (e.g., 1,000,000 lovelace = 1 ADA)
amounts = [
    Amount(amount=1000000, unit="lovelace")
]

# 3. Instantiate a Payment object
payment = Payment(
    agent_identifier="agent_123",
    amounts=amounts,
    config=config,
    network="Preprod",  # or "Mainnet"
    identifier_from_purchaser="purchaser_456"
)

# 4. Asynchronous usage example
async def main():
    response = await payment.create_payment_request()
    payment_id = response["data"]["blockchainIdentifier"]
    print(f"Payment Request Created with ID: {payment_id}")

# 5. Run the event loop
asyncio.run(main())
```

### Creating a Payment

```python
response = await payment.create_payment_request()
print("Payment Request Created:", response)
```

### Checking Payment Status

```python
status = await payment.check_payment_status()
print("Payment Status:", status)
```

### Completing a Payment

```python
async def complete():
    blockchain_id = "your_blockchain_identifier_here"
    submit_result_hash = "your_result_hash_here"
    response = await payment.complete_payment(blockchain_id, submit_result_hash)
    print(f"Payment Completed: {response}")

asyncio.run(complete())
```

### Monitoring Payments

The payment monitoring system automatically tracks the status of all payments and can execute a callback function when a payment is completed.

#### Using Callbacks with Monitoring

```python
# Define a callback function that will be called when a payment completes
async def payment_completed_callback(payment_id):
    print(f"🎉 Payment {payment_id} has been completed!")
    # You can perform additional actions here:
    # - Update a database
    # - Send a notification
    # - Trigger the next step in your workflow

async def start_monitoring():
    # Start monitoring with a callback and check every 30 seconds
    await payment.start_status_monitoring(
        callback=payment_completed_callback,
        interval_seconds=30
    )
    
    # Let the monitoring run (in a real application, you might keep it running indefinitely)
    print("Monitoring started, will run until stopped...")
    await asyncio.sleep(600)  # Run for 10 minutes
    
    # Stop monitoring when done
    payment.stop_status_monitoring()

asyncio.run(start_monitoring())
```

#### How Monitoring Works

1. When you call `start_status_monitoring()`, a background task is created that periodically checks the status of all payments being tracked.

2. The monitoring system:
   - Automatically checks all payment IDs in the `payment_ids` set
   - Removes completed payments from tracking
   - Calls your callback function when a payment completes
   - Stops automatically when there are no more payments to monitor

3. The callback function receives the payment ID as a parameter and can be either synchronous or asynchronous.

4. You can stop monitoring at any time by calling `stop_status_monitoring()`.

#### Example with Multiple Payments

```python
async def monitor_multiple_payments():
    # Create first payment
    result1 = await payment.create_payment_request()
    payment_id1 = result1["data"]["blockchainIdentifier"]
    
    # Create second payment with different identifier
    payment.identifier_from_purchaser = "another_identifier"
    result2 = await payment.create_payment_request()
    payment_id2 = result2["data"]["blockchainIdentifier"]
    
    # Start monitoring both payments
    await payment.start_status_monitoring(
        callback=payment_completed_callback,
        interval_seconds=30
    )
    
    # The monitoring will continue until all payments complete or until stopped
    
    # To stop monitoring manually:
    # payment.stop_status_monitoring()
```

## 🧪 Running Tests

To ensure everything is working as expected, you can run the test suite using:

```bash
pip install pytest
pytest tests/test_masumi.py -v -s
```

---

## Project Structure

```
masumi_crewai
├── config.py     # Contains the Config class for global/package-wide configuration
├── payment.py    # Payment and Amount classes for handling payments on the Cardano blockchain
├── purchase.py   # Purchase class for advanced purchase flows (locking, disputes, etc.)
├── registry.py   # Agent class for registry operations such as registration and verification
├── utils.py      # (Currently empty) Utility functions for future expansions
└── __init__.py   # Package initializer
tests
├── test_masumi.py  # End-to-end and unit tests for the masumi_crewai package
pytest.ini          # Configures pytest logging/output
setup.py            # Defines the package setup metadata
```

---

## Documentation

- **[Masumi Docs](https://www.docs.masumi.network/)**  
- **[Masumi Website](https://www.masumi.network/)**

---

## License

This package is distributed under the **MIT License**. See the [LICENSE](https://opensource.org/licenses/MIT) for more details.

---

## Additional Resources

- **Cardano Documentation**: [Cardano Docs](https://docs.cardano.org/)  
- **CrewAI**: AI agent orchestration.  
- **aiohttp**: [aiohttp Docs](https://docs.aiohttp.org/)  
- **pytest**: [Pytest Docs](https://docs.pytest.org/en/stable/).

For any questions, bug reports, or contributions, please open an issue or pull request in the [GitHub repository](https://github.com/masumi-network).

---

*© 2025 Masumi Network. Built with ❤️ by [Patrick Tobler](mailto:patrick@nmkr.io) and contributors.*

