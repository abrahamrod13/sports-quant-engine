from sqlalchemy import create_engine, text
import os

DATABASE_URL = "sqlite:///database/sports.db"
os.makedirs('database', exist_ok=True)
engine = create_engine(DATABASE_URL)

def init_database():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS nba_games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                home_team TEXT,
                away_team TEXT,
                home_probability REAL,
                volatility REAL,
                edge REAL,
                odds REAL,
                approved INTEGER,
                result TEXT
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS soccer_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                league TEXT,
                home_team TEXT,
                away_team TEXT,
                home_probability REAL,
                volatility REAL,
                edge REAL,
                odds REAL,
                approved INTEGER,
                result TEXT
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS daily_setups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                sport TEXT,
                match_name TEXT,
                probability REAL,
                volatility REAL,
                edge REAL,
                odds REAL,
                confidence TEXT
            )
        """))
        
        conn.commit()
        print("✅ Base de datos inicializada correctamente")

if __name__ == "__main__":
    init_database()