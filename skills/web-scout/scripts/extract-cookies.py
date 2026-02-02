#!/usr/bin/env python3
"""Extract and decrypt Chrome cookies for web-scout skill.

Usage: DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/1000/bus" python3 extract-cookies.py [domain_filter...]
Default filters: cryptoverse, logos.com
"""

import secretstorage, sqlite3, hashlib, json, sys, os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

CHROME_COOKIES_DB = os.path.expanduser('~/.config/google-chrome/Default/Cookies')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cookies')

DOMAIN_GROUPS = {
    'itc': '%cryptoverse%',
    'logos': '%logos.com%',
}


def get_chrome_key():
    """Get Chrome Safe Storage key from GNOME Keyring via D-Bus."""
    conn = secretstorage.dbus_init()
    collection = secretstorage.get_default_collection(conn)
    for item in collection.get_all_items():
        if item.get_label() == 'Chrome Safe Storage':
            return item.get_secret()
    raise RuntimeError('Chrome Safe Storage key not found in keyring')


def derive_key(raw_key):
    """Derive AES key using Chrome's PBKDF2 method."""
    return hashlib.pbkdf2_hmac('sha1', raw_key, b'saltysalt', 1, dklen=16)


def decrypt_v11(data, aes_key):
    """Decrypt v11 Chrome cookie.
    
    v11 on Linux: AES-128-CBC with PBKDF2-derived key.
    First 16 bytes of data after 'v11' prefix are a per-cookie nonce/IV-like block.
    Using space IV means first two blocks decrypt as garbage, real value starts at byte 32.
    For cookies where total ciphertext <= 32 bytes, the value is in the last block(s).
    """
    iv = b' ' * 16
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
    dec = cipher.decryptor()
    pt = dec.update(data) + dec.finalize()
    
    # Remove PKCS7 padding
    pad = pt[-1]
    if 1 <= pad <= 16 and all(b == pad for b in pt[-pad:]):
        pt = pt[:-pad]
    
    # Strip 32-byte corrupted prefix (2 CBC blocks from IV mismatch)
    if len(pt) > 32:
        pt = pt[32:]
    elif len(pt) > 16:
        pt = pt[16:]
    
    return pt.decode('utf-8', errors='replace')


def decrypt_cookie(enc_val, aes_key):
    """Decrypt a Chrome encrypted cookie value."""
    if not enc_val or len(enc_val) < 4:
        return ''
    
    prefix = enc_val[:3]
    data = enc_val[3:]
    
    if prefix == b'v11':
        return decrypt_v11(data, aes_key)
    elif prefix == b'v10':
        key10 = hashlib.pbkdf2_hmac('sha1', b'peanuts', b'saltysalt', 1, dklen=16)
        iv = b' ' * 16
        cipher = Cipher(algorithms.AES(key10), modes.CBC(iv), backend=default_backend())
        dec = cipher.decryptor()
        pt = dec.update(data) + dec.finalize()
        pad = pt[-1]
        if 1 <= pad <= 16:
            pt = pt[:-pad]
        return pt.decode('utf-8', errors='replace')
    else:
        return enc_val.decode('utf-8', errors='replace')


def extract_cookies(domain_pattern, aes_key):
    """Extract and decrypt cookies matching a domain pattern."""
    db = sqlite3.connect(CHROME_COOKIES_DB)
    cursor = db.cursor()
    cursor.execute("""
        SELECT host_key, name, encrypted_value, path, is_secure, is_httponly, 
               expires_utc, samesite
        FROM cookies WHERE host_key LIKE ?
    """, (domain_pattern,))
    
    cookies = []
    for host, name, enc_val, path, secure, httponly, expires, samesite in cursor.fetchall():
        try:
            value = decrypt_cookie(enc_val, aes_key)
        except Exception as e:
            print(f"  WARN: Failed to decrypt {name}@{host}: {e}", file=sys.stderr)
            continue
        
        # Chrome epoch (microseconds since 1601-01-01) to Unix epoch
        unix_expires = (expires / 1000000) - 11644473600 if expires else -1
        
        cookies.append({
            'name': name,
            'value': value,
            'domain': host if host.startswith('.') else host,
            'path': path,
            'secure': bool(secure),
            'httpOnly': bool(httponly),
            'expires': unix_expires if unix_expires > 0 else -1,
            'sameSite': ['None', 'Lax', 'Strict'][samesite] if samesite in (0, 1, 2) else 'Lax',
        })
    
    db.close()
    return cookies


def main():
    raw_key = get_chrome_key()
    aes_key = derive_key(raw_key)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    filters = sys.argv[1:] if len(sys.argv) > 1 else list(DOMAIN_GROUPS.keys())
    
    for group in filters:
        pattern = DOMAIN_GROUPS.get(group, f'%{group}%')
        cookies = extract_cookies(pattern, aes_key)
        
        outfile = os.path.join(OUTPUT_DIR, f'{group}-cookies.json')
        with open(outfile, 'w') as f:
            json.dump(cookies, f, indent=2)
        os.chmod(outfile, 0o600)
        
        print(f'{group}: {len(cookies)} cookies → {outfile}')
        for c in cookies[:3]:
            v = c['value'][:40] + '...' if len(c['value']) > 40 else c['value']
            print(f'  {c["name"]} = {v}')
        if len(cookies) > 3:
            print(f'  ... and {len(cookies) - 3} more')


if __name__ == '__main__':
    main()
