"""
Password Hashing Utility
Generate bcrypt password hashes for creating users in the database
"""

import bcrypt
import sys

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def main():
    print("=" * 60)
    print("PASSWORD HASHING UTILITY")
    print("=" * 60)
    print()
    
    if len(sys.argv) > 1:
        # Hash password from command line argument
        password = sys.argv[1]
        hashed = hash_password(password)
        print(f"Password: {password}")
        print(f"Hash:     {hashed}")
        print()
        print("Copy this hash to your users.csv or INSERT statement.")
        
    else:
        # Interactive mode
        print("This utility helps you create bcrypt password hashes")
        print("for adding users to the database.")
        print()
        
        while True:
            password = input("\nEnter password to hash (or 'quit' to exit): ")
            
            if password.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
                
            if not password:
                print("❌ Password cannot be empty")
                continue
                
            if len(password) < 4:
                print("⚠️  Warning: Password is very short")
                
            hashed = hash_password(password)
            
            print()
            print(f"✅ Password: {password}")
            print(f"✅ Hash:     {hashed}")
            print()
            print("SQL INSERT example:")
            print("-" * 60)
            print(f"""INSERT INTO users (username, email, password_hash, full_name, role)
VALUES ('username', 'user@example.com', '{hashed}', 'Full Name', 'user');""")
            print("-" * 60)
            
            # Verify it works
            verify = input("\nVerify password? (y/n): ")
            if verify.lower() == 'y':
                test_password = input("Enter password to verify: ")
                if verify_password(test_password, hashed):
                    print("✅ Password verification successful!")
                else:
                    print("❌ Password verification failed!")

if __name__ == "__main__":
    main()
