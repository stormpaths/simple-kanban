#!/usr/bin/env python3
"""
Debug script to check API key database status and authentication.
"""
import os
import sys
import hashlib
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Test API key provided by user
TEST_API_KEY = "sk_hQCaGq6Wbl1n-y48zI6hKwCmAGO0ISSYDFAM-KYUuyk"

async def debug_api_keys():
    """Debug API key database and authentication."""
    print("🔍 Debugging API Key System")
    print("=" * 50)
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return
    
    print(f"📊 Database URL: {database_url}")
    
    # Convert to async URL
    if database_url.startswith("postgresql://"):
        async_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    else:
        async_url = database_url
    
    try:
        engine = create_async_engine(async_url)
        async with engine.begin() as conn:
            # Check if api_keys table exists
            print("\n1️⃣ Checking if api_keys table exists...")
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'api_keys';
            """))
            table_exists = result.fetchone()
            
            if not table_exists:
                print("❌ api_keys table does not exist!")
                print("💡 The table needs to be created. This might be why API keys aren't working.")
                
                # Show all existing tables
                result = await conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name;
                """))
                tables = result.fetchall()
                print(f"\n📋 Existing tables ({len(tables)}):")
                for table in tables:
                    print(f"   - {table[0]}")
                return
            
            print("✅ api_keys table exists!")
            
            # Check table structure
            print("\n2️⃣ Checking api_keys table structure...")
            result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'api_keys' 
                ORDER BY ordinal_position;
            """))
            columns = result.fetchall()
            print("📋 Table columns:")
            for col in columns:
                print(f"   - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
            
            # Check number of API keys
            print("\n3️⃣ Checking API key count...")
            result = await conn.execute(text("SELECT COUNT(*) FROM api_keys;"))
            count = result.scalar()
            print(f"📊 Total API keys in database: {count}")
            
            if count == 0:
                print("❌ No API keys found in database!")
                print("💡 This explains why authentication is failing.")
                return
            
            # Show existing API keys (without sensitive data)
            print("\n4️⃣ Listing existing API keys...")
            result = await conn.execute(text("""
                SELECT id, name, key_prefix, is_active, user_id, expires_at, created_at
                FROM api_keys 
                ORDER BY created_at DESC 
                LIMIT 10;
            """))
            keys = result.fetchall()
            
            print("🔑 API Keys:")
            for key in keys:
                status = "🟢 Active" if key[3] else "🔴 Inactive"
                expires = key[5].strftime("%Y-%m-%d") if key[5] else "Never"
                print(f"   ID: {key[0]} | Name: {key[1]} | Prefix: {key[2]} | {status} | User: {key[4]} | Expires: {expires}")
            
            # Check if the provided API key exists
            print(f"\n5️⃣ Checking provided API key: {TEST_API_KEY[:20]}...")
            key_hash = hashlib.sha256(TEST_API_KEY.encode()).hexdigest()
            key_prefix = TEST_API_KEY[:8]
            
            print(f"🔐 Key hash: {key_hash}")
            print(f"🏷️  Key prefix: {key_prefix}")
            
            result = await conn.execute(text("""
                SELECT id, name, is_active, user_id, expires_at, scopes
                FROM api_keys 
                WHERE key_hash = :key_hash;
            """), {"key_hash": key_hash})
            
            matching_key = result.fetchone()
            
            if not matching_key:
                print("❌ Provided API key not found in database!")
                print("💡 The API key either doesn't exist or the hash doesn't match.")
                
                # Check if there's a key with matching prefix
                result = await conn.execute(text("""
                    SELECT id, name, key_prefix, is_active
                    FROM api_keys 
                    WHERE key_prefix = :key_prefix;
                """), {"key_prefix": key_prefix})
                
                prefix_match = result.fetchone()
                if prefix_match:
                    print(f"🔍 Found API key with matching prefix: ID {prefix_match[0]}, Name: {prefix_match[1]}")
                    print("💡 This suggests the key exists but the hash doesn't match (key might be different).")
                else:
                    print("🔍 No API key found with matching prefix either.")
                
                return
            
            print("✅ API key found in database!")
            print(f"   ID: {matching_key[0]}")
            print(f"   Name: {matching_key[1]}")
            print(f"   Active: {matching_key[2]}")
            print(f"   User ID: {matching_key[3]}")
            print(f"   Expires: {matching_key[4] if matching_key[4] else 'Never'}")
            print(f"   Scopes: {matching_key[5]}")
            
            # Check if key is valid
            if not matching_key[2]:
                print("❌ API key is inactive!")
                return
            
            if matching_key[4]:  # has expiration
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc)
                if now > matching_key[4]:
                    print("❌ API key has expired!")
                    return
            
            # Check if user exists and is active
            print(f"\n6️⃣ Checking user {matching_key[3]}...")
            result = await conn.execute(text("""
                SELECT id, username, is_active
                FROM users 
                WHERE id = :user_id;
            """), {"user_id": matching_key[3]})
            
            user = result.fetchone()
            if not user:
                print("❌ User associated with API key not found!")
                return
            
            if not user[2]:
                print("❌ User associated with API key is inactive!")
                return
            
            print("✅ User is active!")
            print(f"   User: {user[1]} (ID: {user[0]})")
            
            print("\n🎉 API key appears to be valid in database!")
            print("💡 The issue might be in the authentication middleware or request handling.")
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return

if __name__ == "__main__":
    asyncio.run(debug_api_keys())
