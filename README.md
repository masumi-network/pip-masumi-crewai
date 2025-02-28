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
    # Create a payment request
    create_response = await payment.create_payment_request()
    print("Payment Request Created:", create_response)

    # Check payment status
    status_response = await payment.check_payment_status()
    print("Payment Status:", status_response)

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
transaction_hash = "your_transaction_hash_here"
payment_id = "your_payment_id_here"

response = await payment.complete_payment(
    blockchain_identifier=payment_id,
    submit_result_hash=transaction_hash
)
print("Payment Completed:", response)
```

### Monitoring Payments

```python
async def my_callback(payment_id):
    print(f"Payment {payment_id} confirmed!")

async def monitor():
    await payment.start_status_monitoring(my_callback)

asyncio.run(monitor())

# ... later, if you want to stop monitoring:
payment.stop_status_monitoring()
```

---

## Configuration

```python
from masumi_crewai.config import Config

config = Config(
    payment_service_url="https://api.masumi.network",
    payment_api_key="YOUR_API_KEY_HERE",
    registry_service_url="https://registry.masumi.network",
    registry_api_key="ANOTHER_API_KEY_HERE",
    preprod_address="some_custom_preprod_address",
    mainnet_address="some_custom_mainnet_address",
)
```

---

## Testing

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

