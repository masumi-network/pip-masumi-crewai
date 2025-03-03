import os
import logging
import sys
import asyncio
from masumi_crewai.payment import Payment, Amount
from masumi_crewai.config import Config

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
    force=True
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Dictionary to store payment results
payment_results = {}

# Callback function for completed payments
async def payment_completed_callback(payment_id):
    """Called when a payment is completed"""
    logger.info(f"🎉 Payment completed callback triggered for payment: {payment_id}")
    
    # Store the result
    payment_results[payment_id] = {
        "status": "completed",
        "timestamp": asyncio.get_event_loop().time()
    }
    
    # You could do other things here like:
    # - Update a database
    # - Send a notification
    # - Trigger the next step in your workflow
    
    logger.info(f"Payment results updated: {payment_results}")

async def main():
    """Example of using payment monitoring with callbacks"""
    logger.info("=" * 80)
    logger.info("Starting payment monitoring example")
    logger.info("=" * 80)
    
    # Create a config
    config = Config(
        payment_service_url="http://localhost:3001/api/v1",
        payment_api_key="abcdef_this_should_be_very_secure"
    )
    
    # Create a payment instance
    agent_id = "0520e542b4704586b7899e8af207501fd1cfb4d12fc419ede7986de814172d9a1284bbb58a82a82092ec8f682aa4040845472d81d759d246f5d18858"
    amounts = [Amount(amount="10000000", unit="lovelace")]
    payment = Payment(
        agent_identifier=agent_id,
        amounts=amounts,
        config=config,
        network="Preprod",
        identifier_from_purchaser="example_identifier"
    )
    
    logger.info("Payment instance created")
    
    # Create multiple payment requests to demonstrate monitoring multiple payments
    payment_ids = []
    
    try:
        # Create first payment
        logger.info("Creating first payment request")
        result1 = await payment.create_payment_request()
        payment_id1 = result1["data"]["blockchainIdentifier"]
        payment_ids.append(payment_id1)
        logger.info(f"First payment request created with ID: {payment_id1}")
        
        # Create second payment with different identifier
        payment.identifier_from_purchaser = "another_identifier"
        logger.info("Creating second payment request")
        result2 = await payment.create_payment_request()
        payment_id2 = result2["data"]["blockchainIdentifier"]
        payment_ids.append(payment_id2)
        logger.info(f"Second payment request created with ID: {payment_id2}")
        
        # Start monitoring with our callback function
        logger.info("Starting payment status monitoring with callback")
        await payment.start_status_monitoring(
            callback=payment_completed_callback,
            interval_seconds=30  # Use shorter interval for testing
        )
        
        # Let the monitoring run for a while
        logger.info("Monitoring started, will run for 5 minutes or until all payments complete")
        
        # Wait for up to 5 minutes or until all payments are processed
        max_wait_time = 300  # 5 minutes
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # Check if we've been waiting too long
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > max_wait_time:
                logger.info(f"Maximum wait time of {max_wait_time} seconds reached")
                break
                
            # Check if all payments have been processed
            all_processed = all(payment_id in payment_results for payment_id in payment_ids)
            if all_processed:
                logger.info("All payments have been processed!")
                break
                
            # Wait a bit before checking again
            logger.info(f"Waiting for payments to complete ({len(payment_results)}/{len(payment_ids)} done)")
            await asyncio.sleep(10)
        
        # Stop monitoring
        logger.info("Stopping monitoring")
        payment.stop_status_monitoring()
        
        # Show final results
        logger.info("Final payment results:")
        for payment_id, result in payment_results.items():
            logger.info(f"Payment {payment_id}: {result}")
        
        logger.info("Payment monitoring example completed")
        
    except Exception as e:
        logger.error(f"Error during payment monitoring example: {str(e)}")
        # Make sure to stop monitoring even if there's an error
        if payment._status_check_task:
            payment.stop_status_monitoring()
        raise

if __name__ == "__main__":
    # Run the example
    asyncio.run(main()) 