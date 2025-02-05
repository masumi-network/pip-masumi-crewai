# Masumi Crewai Python Package

This package provides an interface for handling payments via the Masumi Node using asynchronous API requests. It simplifies the process of creating payment requests, checking payment statuses, and completing payments on the Cardano blockchain.

---

## Features

- **Asynchronous Payment Handling**: Supports creating, checking, and completing payments.
- **Configurable Network Selection**: Works on different Cardano networks (default: `PREPROD`).
- **Automated Payment Monitoring**: Built-in function for tracking payment status.
- **Secure API Authentication**: Uses API keys for authorization.

---

## Installation

To install the package, use:

```bash
pip install masumi-crewai
```

Or install from source:

```bash
git clone https://github.com/masumi-network/pip-masumi-crewai.git
cd pip-masumi-crewai
pip install .
```

---

## Usage

### 1. Importing and Configuring the Payment Client

```python
from masumi_crewai import Payment, Amount
from masumi_crewai.config import Config
import asyncio

# Initialize configuration
config = Config(payment_api_key="your_api_key", payment_service_url="https://api.masumi.network")

# Define the payment amount
amounts = [Amount(amount=1000000, unit="lovelace")]

# Create a Payment instance
payment = Payment(agent_identifier="agent_123", amounts=amounts, config=config)
```

---

### 2. Creating a Payment Request

```python
async def create_payment():
    submit_time = "2025-02-05T12:00:00Z"  # Example timestamp
    response = await payment.create_payment_request(submit_result_time=submit_time)
    print(response)

asyncio.run(create_payment())
```

---

### 3. Checking Payment Status

```python
async def check_status():
    status = await payment.check_payment_status()
    print(status)

asyncio.run(check_status())
```

---

### 4. Completing the Payment

```python
async def complete():
    tx_hash = "your_transaction_hash_here"
    result = await payment.complete_payment(hash=tx_hash)
    print(result)

asyncio.run(complete())
```

---

### 5. Monitoring Payment Status

```python
async def monitor_status():
    async def callback(status):
        print("Payment status update:", status)

    await payment.start_status_monitoring(callback)

asyncio.run(monitor_status())
```

To stop monitoring:

```python
payment.stop_status_monitoring()
```

---

## Configuration

The package requires an API key and service URL for the Masumi Payment Service. These should be stored in a `Config` object:

```python
from masumi_crewai.config import Config

config = Config(
    payment_api_key="your_api_key_here",
    payment_service_url="https://api.masumi.network"
)
```

---

## Requirements

- Python 3.7+
- `aiohttp` for async HTTP requests

---

## Contributing

Contributions are welcome! To contribute:
1. Fork the repository.
2. Make your changes.
3. Submit a pull request.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## Contact

For any questions or issues, please open an issue on the [GitHub repository](https://github.com/masumi-network/pip-masumi-crewai).
