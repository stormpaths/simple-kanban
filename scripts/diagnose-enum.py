#!/usr/bin/env python3
"""
Diagnostic script to investigate the grouprole enum issue.

This script connects to the database and examines:
1. Enum type definitions
2. Existing user_groups data
3. Column constraints and types
"""
import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def diagnose_enum_issue():
    """Diagnose the grouprole enum issue."""
    
    # Get database URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return
    
    # Create async engine
    engine = create_async_engine(database_url, echo=False)
    
    try:
        async with engine.begin() as conn:
            print("🔍 Investigating grouprole enum issue...")
            print("=" * 50)
            
            # 1. Check if grouprole enum type exists
            print("\n1. Checking enum type existence:")
            enum_check = await conn.execute(text("""
                SELECT typname, oid 
                FROM pg_type 
                WHERE typname LIKE '%role%' OR typname LIKE '%group%'
                ORDER BY typname;
            """))
            
            enum_types = enum_check.fetchall()
            if enum_types:
                for enum_type in enum_types:
                    print(f"   Found type: {enum_type.typname} (OID: {enum_type.oid})")
            else:
                print("   ❌ No enum types found matching 'role' or 'group'")
            
            # 2. Check enum values for grouprole specifically
            print("\n2. Checking grouprole enum values:")
            enum_values = await conn.execute(text("""
                SELECT e.enumlabel, e.enumsortorder
                FROM pg_enum e
                JOIN pg_type t ON e.enumtypid = t.oid
                WHERE t.typname = 'grouprole'
                ORDER BY e.enumsortorder;
            """))
            
            values = enum_values.fetchall()
            if values:
                print("   Enum values:")
                for value in values:
                    print(f"     - '{value.enumlabel}' (order: {value.enumsortorder})")
            else:
                print("   ❌ No values found for 'grouprole' enum")
                
                # Check if it might be named differently
                print("\n   Checking all enum types and their values:")
                all_enums = await conn.execute(text("""
                    SELECT t.typname, e.enumlabel, e.enumsortorder
                    FROM pg_enum e
                    JOIN pg_type t ON e.enumtypid = t.oid
                    ORDER BY t.typname, e.enumsortorder;
                """))
                
                all_enum_data = all_enums.fetchall()
                current_type = None
                for row in all_enum_data:
                    if row.typname != current_type:
                        print(f"\n   Enum type: {row.typname}")
                        current_type = row.typname
                    print(f"     - '{row.enumlabel}'")
            
            # 3. Check user_groups table structure
            print("\n3. Checking user_groups table structure:")
            table_info = await conn.execute(text("""
                SELECT column_name, data_type, udt_name, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'user_groups'
                ORDER BY ordinal_position;
            """))
            
            columns = table_info.fetchall()
            if columns:
                print("   Columns:")
                for col in columns:
                    print(f"     - {col.column_name}: {col.data_type} ({col.udt_name}) nullable={col.is_nullable}")
            else:
                print("   ❌ user_groups table not found")
            
            # 4. Check existing data in user_groups
            print("\n4. Checking existing user_groups data:")
            existing_data = await conn.execute(text("""
                SELECT id, user_id, group_id, role, created_at
                FROM user_groups
                ORDER BY id
                LIMIT 5;
            """))
            
            rows = existing_data.fetchall()
            if rows:
                print("   Existing records:")
                for row in rows:
                    print(f"     - ID {row.id}: User {row.user_id} -> Group {row.group_id}, Role: '{row.role}'")
            else:
                print("   ℹ️  No existing records in user_groups table")
            
            # 5. Try to understand the constraint
            print("\n5. Checking constraints on role column:")
            constraints = await conn.execute(text("""
                SELECT 
                    tc.constraint_name,
                    tc.constraint_type,
                    cc.check_clause
                FROM information_schema.table_constraints tc
                LEFT JOIN information_schema.check_constraints cc 
                    ON tc.constraint_name = cc.constraint_name
                WHERE tc.table_name = 'user_groups' 
                AND tc.constraint_type IN ('CHECK', 'FOREIGN KEY');
            """))
            
            constraint_data = constraints.fetchall()
            if constraint_data:
                print("   Constraints:")
                for constraint in constraint_data:
                    print(f"     - {constraint.constraint_name} ({constraint.constraint_type})")
                    if constraint.check_clause:
                        print(f"       Check: {constraint.check_clause}")
            else:
                print("   ℹ️  No relevant constraints found")
                
    except Exception as e:
        print(f"❌ Error during diagnosis: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(diagnose_enum_issue())
