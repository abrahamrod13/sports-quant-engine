import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os
import csv

def main():
    # Obtener credenciales del secreto
    creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    if not creds_json:
        print("❌ GOOGLE_CREDENTIALS no encontrado")
        return
    
    creds_dict = json.loads(creds_json)
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # Abrir Google Sheet
        sheet = client.open('Sports Quant Picks').worksheet('Picks')
        data = sheet.get_all_values()
        
        if not data or len(data) < 2:
            print("⚠️ No hay datos en Google Sheets")
            return
        
        # Crear directorio si no existe
        os.makedirs('data', exist_ok=True)
        
        # Guardar como CSV
        with open('data/picks_tracker.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(data)
        
        print(f"✅ Sincronizado: {len(data)-1} picks")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()