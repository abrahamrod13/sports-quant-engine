import json

# Ruta a tu archivo credentials.json
with open('credentials.json', 'r') as f:
    creds = json.load(f)

# Convertir a string JSON con escapes
creds_str = json.dumps(creds)

# Imprimir para copiar
print('service_account = "' + creds_str + '"')