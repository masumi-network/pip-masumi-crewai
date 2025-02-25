# Masumi CrewAI Payment Module

This repository provides an implementation of Masumi blockchain-based payments, enabling AI agents using CrewAI to interact with the Masumi network for seamless payments, transaction logging, and monitoring.

## 🚀 Installation

To install the package, ensure you have Python 3.8+ and `pip` installed. Then, run:

```bash
pip install pip-masumi-crewai
```

## 🔧 Usage

The `Payment` class in `payment.py` provides functionality to send and track payments on the Cardano blockchain using the Masumi network.

### Importing and Initializing

```python
from masumi_crewai.payment import Payment, Amount
from masumi_crewai.config import Config

# Initialize configuration
config = Config(payment_api_key="your_api_key_here", payment_service_url="https://api.masumi.network")

# Define payment amounts
amounts = [Amount(amount=1000000, unit="lovelace")]

# Initialize Payment instance
payment = Payment(agent_identifier="agent_123", amounts=amounts, config=config)
```

### Creating a Payment Request

```python
import asyncio

async def main():
    response = await payment.create_payment_request()
    print(f"Payment Request Created: {response}")

asyncio.run(main())
```

### Checking Payment Status

```python
async def check_status():
    status = await payment.check_payment_status()
    print(f"Payment Status: {status}")

asyncio.run(check_status())
```

### Completing a Payment

```python
async def complete():
    transaction_hash = "your_transaction_hash_here"
    payment_id = "your_payment_id_here"
    response = await payment.complete_payment(payment_id, transaction_hash)
    print(f"Payment Completed: {response}")

asyncio.run(complete())
```

### Monitoring Payments

```python
async def payment_callback(payment_id):
    print(f"Payment {payment_id} confirmed!")

async def start_monitoring():
    await payment.start_status_monitoring(payment_callback)

asyncio.run(start_monitoring())
```

To stop monitoring:

```python
payment.stop_status_monitoring()
```

## 🧪 Running Tests

To ensure everything is working as expected, you can run the test suite using:

```bash
pytest tests/test_masumi.py -v -s
```

Make sure you have `pytest` installed:

```bash
pip install pytest
```

## 📖 Documentation

For more details, check out the official Masumi documentation:

📚 [Masumi Docs](https://www.docs.masumi.network/)

## 🌐 Masumi Network

For more information about the Masumi Network and its capabilities, visit:

🔗 [Masumi Website](https://www.masumi.network/)
