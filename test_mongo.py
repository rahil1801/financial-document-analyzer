import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ServerSelectionTimeoutError, OperationFailure

# Replace these with your actual environment variables or hardcoded strings
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://rahilalamyt80:NQcVBnb4S9vWMl9r@cluster-chatbot.gdw4c.mongodb.net/")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "financial_analyzer")

async def verify_connection():
    print(f"--- Testing connection to: {MONGODB_URI.split('@')[-1]} ---")
    
    # 1. Initialize Client (Note: this doesn't connect immediately)
    client = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    
    try:
        # 2. Force connection with a ping
        await client.admin.command('ping')
        print("✅ SUCCESS: Connected and Pinged MongoDB successfully!")
        
        # 3. Verify Authentication/Server Info
        info = await client.server_info()
        print(f"✅ SUCCESS: Authenticated. Server version: {info.get('version')}")
        
        # 4. Test Write Permission
        db = client[MONGODB_DB_NAME]
        test_doc = {"test": "connection", "timestamp": "now"}
        result = await db.connection_test.insert_one(test_doc)
        print(f"✅ SUCCESS: Write permission verified. Inserted ID: {result.inserted_id}")
        
        # Cleanup test document
        await db.connection_test.delete_one({"_id": result.inserted_id})
        print("✅ SUCCESS: Cleanup completed.")

    except ServerSelectionTimeoutError:
        print("❌ ERROR: Could not connect to server. Check your URI/Whitelist/Network.")
    except OperationFailure as e:
        print(f"❌ ERROR: Authentication failed or insufficient permissions: {e}")
    except Exception as e:
        print(f"❌ ERROR: An unexpected error occurred: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    if not MONGODB_URI or MONGODB_URI == "your_mongodb_uri_here":
        print("❌ ERROR: MONGODB_URI is not set.")
    else:
        asyncio.run(verify_connection())
