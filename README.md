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
    payment_id = response["data"]["blockchainIdentifier"]
    print(f"Payment Request Created with ID: {payment_id}")

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
