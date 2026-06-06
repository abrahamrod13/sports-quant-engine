import json

with open('credentials.json', 'r') as f:
    creds = json.load(f)

# Escapar private_key correctamente
if 'private_key' in creds:
    creds['private_key'] = creds['private_key'].replace('\n', '\\n')

# Convertir a string JSON
creds_str = json.dumps(creds, indent=None, separators=(',', ':'))

# Formato TOML para Streamlit
print("[gcp]")
print(f'service_account = """{creds_str}"""')