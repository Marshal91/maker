# Minimal Flask app for debugging 502 errors
import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS
import sqlite3
from contextlib import contextmanager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'debug-key')
app.config['DEBUG'] = False

# Database path
DATABASE_PATH = 'betting_analysis.db'

@contextmanager
def get_db():
    """Database connection context manager"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        yield conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        conn.close()

def init_db():
    """Initialize database with error handling"""
    try:
        with get_db() as conn:
            # Create tables if they don't exist
            conn.execute('''
                CREATE TABLE IF NOT EXISTS leagues (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    country TEXT NOT NULL
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS teams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    league_id INTEGER,
                    FOREIGN KEY (league_id) REFERENCES leagues (id)
                )
            ''')
            
            conn.commit()
            logger.info("Database initialized successfully")
            
            # Check if we need to populate data
            leagues_count = conn.execute('SELECT COUNT(*) FROM leagues').fetchone()[0]
            if leagues_count == 0:
                populate_basic_data(conn)
                
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        # Don't raise - let app start without DB if needed

def populate_basic_data(conn):
    """Populate minimal data set"""
    try:
        # Insert basic leagues
        leagues = [
            ('Premier League', 'England'),
            ('La Liga', 'Spain'),
            ('Serie A', 'Italy'),
            ('Bundesliga', 'Germany'),
            ('Champions League', 'Europe')
        ]
        
        for name, country in leagues:
            cursor = conn.execute(
                'INSERT INTO leagues (name, country) VALUES (?, ?)',
                (name, country)
            )
            league_id = cursor.lastrowid
            
            # Add a few teams per league
            if name == 'Premier League':
                teams = ['Arsenal', 'Manchester City', 'Liverpool', 'Chelsea']
            elif name == 'La Liga':
                teams = ['Real Madrid', 'Barcelona', 'Atletico Madrid', 'Sevilla']
            elif name == 'Serie A':
                teams = ['Inter Milan', 'AC Milan', 'Juventus', 'Napoli']
            elif name == 'Bundesliga':
                teams = ['Bayern Munich', 'Borussia Dortmund', 'RB Leipzig']
            else:
                teams = ['Team A', 'Team B', 'Team C']
            
            for team in teams:
                conn.execute(
                    'INSERT INTO teams (name, league_id) VALUES (?, ?)',
                    (team, league_id)
                )
        
        conn.commit()
        logger.info("Basic data populated successfully")
        
    except Exception as e:
        logger.error(f"Data population error: {e}")

# Initialize database on startup
try:
    init_db()
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")

# Basic health check route
@app.route('/')
def index():
    """Basic health check"""
    return jsonify({
        'status': 'healthy',
        'message': 'Football Betting Bot API is running',
        'version': '1.0.0'
    })

@app.route('/health')
def health_check():
    """Detailed health check"""
    try:
        # Test database connection
        with get_db() as conn:
            conn.execute('SELECT 1').fetchone()
        db_status = 'connected'
    except Exception as e:
        db_status = f'error: {str(e)}'
    
    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'python_version': sys.version,
        'environment': os.environ.get('ENVIRONMENT', 'development')
    })

@app.route('/api/leagues')
def get_leagues():
    """Get all leagues"""
    try:
        with get_db() as conn:
            leagues = conn.execute(
                'SELECT id, name, country FROM leagues ORDER BY name'
            ).fetchall()
            
            return jsonify({
                'success': True,
                'count': len(leagues),
                'leagues': [dict(league) for league in leagues]
            })
    except Exception as e:
        logger.error(f"Error fetching leagues: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/teams/<int:league_id>')
def get_teams_by_league(league_id):
    """Get teams for a specific league"""
    try:
        with get_db() as conn:
            teams = conn.execute(
                'SELECT id, name FROM teams WHERE league_id = ? ORDER BY name',
                (league_id,)
            ).fetchall()
            
            return jsonify({
                'success': True,
                'league_id': league_id,
                'count': len(teams),
                'teams': [dict(team) for team in teams]
            })
    except Exception as e:
        logger.error(f"Error fetching teams for league {league_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/matches/sample')
def get_sample_matches():
    """Get sample match data"""
    from datetime import datetime, timedelta
    import random
    
    matches = []
    base_time = datetime.now()
    
    sample_matches = [
        ('Arsenal', 'Manchester City', 'Premier League'),
        ('Real Madrid', 'Barcelona', 'La Liga'),
        ('Inter Milan', 'AC Milan', 'Serie A'),
        ('Bayern Munich', 'Borussia Dortmund', 'Bundesliga')
    ]
    
    for i, (home, away, league) in enumerate(sample_matches):
        match_time = base_time + timedelta(hours=i*2)
        matches.append({
            'id': f'sample_{i}',
            'homeTeam': home,
            'awayTeam': away,
            'league': league,
            'time': match_time.strftime('%H:%M'),
            'date': match_time.strftime('%Y-%m-%d'),
            'homeOdds': round(random.uniform(1.5, 3.5), 2),
            'drawOdds': round(random.uniform(3.0, 4.0), 2),
            'awayOdds': round(random.uniform(2.0, 4.5), 2)
        })
    
    return jsonify({
        'success': True,
        'count': len(matches),
        'matches': matches
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found', 'status': 404}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    return jsonify({'error': 'Internal server error', 'status': 500}), 500

@app.errorhandler(Exception)
def handle_exception(error):
    logger.error(f"Unhandled exception: {error}")
    return jsonify({
        'error': 'An unexpected error occurred',
        'message': str(error)
    }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    try:
        logger.info(f"Starting Flask app on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logger.error(f"Failed to start Flask app: {e}")
        sys.exit(1)
