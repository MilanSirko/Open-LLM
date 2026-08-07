import os
from supabase import create_client
from dotenv import load_dotenv
from secretapi import encrypt_value, decrypt_value

load_dotenv()
supabase=create_client(os.getenv('supabase_url'), os.getenv('supabase_key'))

def create_api_key(key: str, email: str | None = None):
    db_email = email
    if email:
        try:
            res = supabase.table('api_keys').select('email').like('email', f"{email}%").execute()
            existing_emails = {item['email'] for item in res.data if item['email'] == email or item['email'].startswith(f"{email}#")}
            if email in existing_emails:
                db_email = f"{email}#2"
        except Exception as e:
            print(f"Hiba az e-mail ellenőrzésekor: {e}")
            
    supabase.table('api_keys').insert({
        'api_key': key,
        'email': db_email,
        'active': True,
    }).execute()

def verify_key(key: str) -> bool:
    result = supabase.table('api_keys').select('*').eq('api_key', key).eq('active', True).execute()
    return len(result.data) > 0

def add_token_usage(key: str, tokens_count: int):
    try:
        res = supabase.table('api_keys').select('used_tokens').eq('api_key', key).execute()
        if res.data:
            current_tokens = res.data[0].get('used_tokens') or 0
            new_total = current_tokens + tokens_count
            supabase.table('api_keys').update({'used_tokens': new_total}).eq('api_key', key).execute()
    except Exception as e:
        print(f"Hiba a tokenek mentésekor: {e}")

def get_usage_by_key(key: str) -> int:
    res = supabase.table('api_keys').select('used_tokens').eq('api_key', key).execute()
    if res.data:
        return res.data[0].get('used_tokens') or 0
    return 0

def get_user_keys_info(email: str | None = None) -> list[dict]:
    try:
        query = supabase.table('api_keys').select('api_key, created_at, used_tokens, email')
        
        if email:
            query = query.like('email', f"{email}%")
            
        res = query.execute()
        
        keys_list = []
        for item in res.data:
            item_email = item.get('email') or ""
            if not email or item_email == email or item_email.startswith(f"{email}#"):
                keys_list.append({
                    "api_key": item.get('api_key'),
                    "created_at": item.get('created_at'),
                    "used_tokens": item.get('used_tokens') or 0
                })
        return keys_list
    except Exception as e:
        print(f"Hiba a kulcsok lekérésekor: {e}")
        return []

def revoke_api_key(email: str, key_to_revoke: str) -> bool:
    try:
        if "..." in key_to_revoke:
            res = supabase.table('api_keys').select('api_key, email').like('email', f"{email}%").execute()
            for item in res.data:
                raw_key = item['api_key']
                item_email = item.get('email') or ""
                if item_email == email or item_email.startswith(f"{email}#"):
                    masked = f"{raw_key[:6]}...{raw_key[-4:]}" if len(raw_key) > 10 else raw_key
                    if masked == key_to_revoke:
                        res_del = supabase.table('api_keys').delete().eq('api_key', raw_key).execute()
                        if res_del.data and len(res_del.data) > 0:
                            return True
            return False
            
        res = supabase.table('api_keys').select('email').eq('api_key', key_to_revoke).execute()
        if not res.data:
            return False
        item_email = res.data[0].get('email') or ""
        if item_email == email or item_email.startswith(f"{email}#"):
            res_del = supabase.table('api_keys').delete().eq('api_key', key_to_revoke).execute()
            if res_del.data and len(res_del.data) > 0:
                return True
        return False
    except Exception as e:
        print(f"Hiba a kulcs visszavonásakor: {e}")
        return False

def count_user_keys(email: str) -> int:
    try:
        res = supabase.table('api_keys').select('email').like('email', f"{email}%").eq('active', True).execute()
        count = 0
        for item in res.data:
            item_email = item.get('email') or ""
            if item_email == email or item_email.startswith(f"{email}#"):
                count += 1
        return count
    except Exception as e:
        print(f"Hiba a kulcsok számlálásánál: {e}")
        return 0

def save_provider_key(apikey: str, provider: str, provider_key: str):
    encrypted = encrypt_value(provider_key)
    supabase.table('user_provider_keys').upsert({
        'api_key': apikey,
        'provider': provider,
        'provider_key_encrypted': encrypted,
    }, on_conflict='api_key,provider').execute()

def get_provider_key(apikey: str, provider: str) -> str | None:
    result = supabase.table('user_provider_keys').select('provider_key_encrypted').eq('api_key', apikey).eq('provider', provider).execute()
    if result.data:
        return decrypt_value(result.data[0]['provider_key_encrypted'])
    return None

def list_provider_keys(apikey: str) -> list[dict]:
    result = supabase.table('user_provider_keys').select('provider, provider_key_encrypted').eq('api_key', apikey).execute()
    return result.data

def delete_provider_key(apikey: str, provider: str):
    supabase.table('user_provider_keys').delete().eq('api_key', apikey).eq('provider', provider).execute()