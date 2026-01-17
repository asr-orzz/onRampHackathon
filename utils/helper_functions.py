import os
import json
import requests

session_token = None
def get_session_token():
    global session_token
    return session_token
def set_session_token(token):
    global session_token
    session_token = token

import os, json

def register_merchant(account_address, name, business_type, description, kyc_info=None):
    """
    Registers a new merchant in Data/merchants.json if the name is unique.
    Supports both list and dict formats, but saves in list format for compatibility.
    """
    # Basic validation
    if not isinstance(account_address, str) or not account_address.strip():
        return {"success": False, "error": "Invalid account_address."}
    if not isinstance(name, str) or not name.strip():
        return {"success": False, "error": "Invalid name."}
    if not isinstance(business_type, str) or not business_type.strip():
        return {"success": False, "error": "Invalid business_type."}
    if not isinstance(description, str):
        return {"success": False, "error": "Invalid description."}
    if kyc_info is not None and not isinstance(kyc_info, dict):
        return {"success": False, "error": "kyc_info must be a dict if provided."}

    merchants_path = os.path.join("Data", "merchants.json")

    # Load existing merchants
    merchants_list = []
    if os.path.exists(merchants_path):
        try:
            with open(merchants_path, "r") as f:
                merchants_data = json.load(f)

            if isinstance(merchants_data, list):
                merchants_list = merchants_data
            elif isinstance(merchants_data, dict):
                # Convert dict format to list format (preserve extra keys if possible)
                merchants_list = []
                for key, value in merchants_data.items():
                    value = value if isinstance(value, dict) else {}
                    merchants_list.append({
                        "name": key,
                        "description": value.get("description", ""),
                        "receiver_address": value.get("receiver_address", value.get("wallet_address", "")),
                        "business_type": value.get("business_type", ""),
                        "kyc_info": value.get("kyc_info", {})
                    })
        except (json.JSONDecodeError, OSError):
            merchants_list = []

    # Name uniqueness check (case-insensitive)
    name_lower = name.strip().lower()
    for merchant in merchants_list:
        merchant_name = merchant.get("name", "")
        if isinstance(merchant_name, str) and merchant_name.strip().lower() == name_lower:
            return {"success": False, "error": "Merchant name already exists. Please choose a unique name."}

    merchant_entry = {
        "name": name.strip(),
        "description": description.strip(),
        "receiver_address": account_address.strip(),
        "business_type": business_type.strip(),
        "kyc_info": kyc_info or {}
    }

    merchants_list.append(merchant_entry)

    try:
        os.makedirs(os.path.dirname(merchants_path), exist_ok=True)
        with open(merchants_path, "w") as f:
            json.dump(merchants_list, f, indent=2)
    except Exception as e:
        return {"success": False, "error": str(e)}

    return {"success": True, "merchant": merchant_entry}



def pay(api_endpoint, receiver_address, amount):
    """
    Pays a merchant via the restricted payment rail.
    
    This function:
    1. Calls frontend /api/register-token to request authorization (triggers UI)
    2. Waits for user to authorize with fingerprint
    3. Calls frontend /agent/pay with session token to execute payment
    4. Returns transaction hash or error
    
    Args:
        receiver_address (str): The receiver's wallet address on Sepolia
        amount (float): Amount to send in ETH
    
    Returns:
        dict: Result of payment with tx_hash or error
    """
    frontend_url = os.getenv("FRONTEND_URL", "https://on-ramp-hackathon.vercel.app/")
    
    session_token = get_session_token()
    
    try:
        if not session_token:   
            # Step 1: Request authorization token from frontend
            register_response = requests.post(
                f"{frontend_url}/api/register-token",
                json={},
                timeout=300  # 5 minute timeout for user authorization
            )
            
            if register_response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Failed to register token: {register_response.text}"
                }
            
            register_data = register_response.json()
            if not register_data.get("success"):
                return {
                    "success": False,
                    "error": register_data.get("error", "Authorization failed")
                }   
            session_token = register_data.get("token")
            set_session_token(session_token)
            
        print(f"\n\n###Session token: {session_token}")
        
        # Step 2: Make payment with session token
        pay_payload = {
            "receiver": receiver_address,
            "amount": amount,
            "sessionToken": session_token
        }
        
        pay_response = requests.post(
            f"{frontend_url}/api/agent/pay",
            json=pay_payload,
            timeout=60
        )
        
        pay_data = pay_response.json()
        print(f"\n\n###Pay data: {pay_data}")
        if pay_response.status_code == 200 and pay_data.get("success"):
            return {
                "success": True,
                "tx_hash": pay_data.get("tx_hash"),
                "status": "Settled autonomously"
            }
        else:
            return {
                "success": False,
                "error": pay_data.get("error", "Payment failed")
            }
            
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Authorization timeout - user did not respond in time"
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": f"Could not connect to frontend at {frontend_url}. Make sure the frontend server is running."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def register_user(username,upi_id, wallet_address):
    """
    Registers a new user in Data/users.json if the username is unique.
    Args:
        username (str): Unique username.
        upi_id (str): Unique UPI ID.
        wallet_address (str): User's wallet address.
    Returns:
        dict: Result of registration, or reason for failure.
    """
    users_path = os.path.join("Data", "users.json")
    if not os.path.exists(users_path):
        users_list = []
    else:
        with open(users_path, "r") as f:
            try:
                users_data = json.load(f)
                if isinstance(users_data, list):
                    users_list = users_data
                else:
                    users_list = []
            except json.JSONDecodeError:
                users_list = []
    # Username uniqueness check (case-insensitive)  
    username_lower = username.lower()
    for user in users_list:
        user_name = user.get("name", "")
        if isinstance(user_name, str) and user_name.lower() == username_lower:
            return {"success": False, "error": "Username already exists. Please choose a unique username."}
    # Build user data object (list format for compatibility with agent_service)
    user_entry = {
        "name": username,
        "upi_id": upi_id,
        "wallet_address": wallet_address,
    }
    # Add new user to list
    users_list.append(user_entry)
    try:
        os.makedirs(os.path.dirname(users_path), exist_ok=True)
        with open(users_path, "w") as f:
            json.dump(users_list, f, indent=2)
        return {"success": True, "user": user_entry}
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def get_user(wallet_address):
    """
    Gets a user from Data/users.json by wallet address.
    Args:
        wallet_address (str): User's wallet address.
    Returns:
        dict: User data, or None if not found.
    """
    users_path = os.path.join("Data", "users.json")
    if not os.path.exists(users_path):
        return None
    with open(users_path, "r") as f:
        try:
            users_data = json.load(f)
            if isinstance(users_data, list):
                for user in users_data:
                    if user.get("wallet_address", "") == wallet_address:
                        return user
        except json.JSONDecodeError:
            return None
    return None

def get_user_by_upi_id(upi_id):
    """
    Gets a user from Data/users.json by UPI ID.
    Args:
        upi_id (str): User's UPI ID.
    Returns:
        dict: User data, or None if not found.
    """
    users_path = os.path.join("Data", "users.json")
    if not os.path.exists(users_path):
        return None
    with open(users_path, "r") as f:
        try:
            users_data = json.load(f)
            if isinstance(users_data, list):
                for user in users_data:
                    if user.get("upi_id", "") == upi_id:
                        return user
        except json.JSONDecodeError:
            return None
    return None