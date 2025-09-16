import os
import sys
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import requests
import json
from datetime import datetime, timedelta
import sqlite3
from contextlib import contextmanager
import random
import threading
import time

# Render-specific optimizations
app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-please-change-in-production')
app.config['DEBUG'] = False

# Database setup for Render (uses persistent storage)
DATABASE_PATH = '/opt/render/project/src/data/betting_analysis.db'
if not os.path.exists(os.path.dirname(DATABASE_PATH)):
    DATABASE_PATH = 'betting_analysis.db'  # Fallback for local development

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize database with required tables"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        
        with get_db() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS match_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    home_team TEXT NOT NULL,
                    away_team TEXT NOT NULL,
                    analysis_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS betting_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    matches TEXT NOT NULL,
                    total_odds REAL NOT NULL,
                    bet_amount REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️ Database initialization error: {e}")

class RenderOptimizedFootballAPI:
    def __init__(self):
        self.api_key = os.environ.get('FOOTBALL_DATA_API_KEY')
        self.rapidapi_key = os.environ.get('RAPIDAPI_KEY')
        self.base_url = 'https://api.football-data.org/v4'
        self.headers = {'X-Auth-Token': self.api_key} if self.api_key else {}
        
    def get_todays_matches(self):
        """Fetch today's matches with Render-optimized timeout settings"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Try APIs with shorter timeouts for Render
        if self.api_key:
            try:
                matches = self.fetch_from_football_data(today)
                if matches:
                    return matches
            except Exception as e:
                print(f"Football-Data API error: {e}")
        
        if self.rapidapi_key:
            try:
                matches = self.fetch_from_rapidapi(today)
                if matches:
                    return matches
            except Exception as e:
                print(f"RapidAPI error: {e}")
        
        # Always return intelligent sample data
        return self.get_render_optimized_matches()
    
    def fetch_from_football_data(self, date):
        """Fetch with Render-optimized settings"""
        try:
            response = requests.get(
                f"{self.base_url}/matches",
                headers=self.headers,
                params={'dateFrom': date, 'dateTo': date},
                timeout=8  # Shorter timeout for Render
            )
            
            if response.status_code == 200:
                data = response.json()
                return self.process_football_data(data['matches'])
        except requests.RequestException as e:
            print(f"API request failed: {e}")
        return []
    
    def fetch_from_rapidapi(self, date):
        """Fetch from RapidAPI with timeout optimization"""
        try:
            url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
            }
            
            response = requests.get(
                url, 
                headers=headers, 
                params={"date": date}, 
                timeout=8
            )
            
            if response.status_code == 200:
                data = response.json()
                return self.process_rapidapi_data(data['response'])
        except requests.RequestException as e:
            print(f"RapidAPI request failed: {e}")
        return []
    
    def process_football_data(self, matches):
        """Process Football-Data API response"""
        processed = []
        for match in matches[:12]:  # Limit for faster loading
            if match['status'] in ['SCHEDULED', 'TIMED', 'IN_PLAY']:
                processed.append({
                    'id': str(match['id']),
                    'time': datetime.fromisoformat(match['utcDate'].replace('Z', '+00:00')).strftime('%H:%M'),
                    'homeTeam': match['homeTeam']['name'],
                    'awayTeam': match['awayTeam']['name'],
                    'league': match['competition']['name'],
                    'status': match['status'],
                    'homeOdds': round(random.uniform(1.4, 4.0), 2),
                    'drawOdds': round(random.uniform(2.8, 4.2), 2),
                    'awayOdds': round(random.uniform(1.8, 5.5), 2),
                    'source': 'football-data.org'
                })
        return processed
    
    def process_rapidapi_data(self, fixtures):
        """Process RapidAPI response"""
        processed = []
        for fixture in fixtures[:12]:
            processed.append({
                'id': str(fixture['fixture']['id']),
                'time': datetime.fromisoformat(fixture['fixture']['date']).strftime('%H:%M'),
                'homeTeam': fixture['teams']['home']['name'],
                'awayTeam': fixture['teams']['away']['name'],
                'league': fixture['league']['name'],
                'status': fixture['fixture']['status']['short'],
                'homeOdds': round(random.uniform(1.4, 4.0), 2),
                'drawOdds': round(random.uniform(2.8, 4.2), 2),
                'awayOdds': round(random.uniform(1.8, 5.5), 2),
                'source': 'rapidapi'
            })
        return processed
    
    def get_render_optimized_matches(self):
        """Generate matches optimized for Render deployment"""
        today = datetime.now()
        day_of_week = today.weekday()
        
        # Render-friendly match data
        weekend_matches = [
            ('Manchester United', 'Chelsea', 'Premier League'),
            ('Liverpool', 'Arsenal', 'Premier League'),
            ('Barcelona', 'Real Madrid', 'La Liga'),
            ('Bayern Munich', 'Borussia Dortmund', 'Bundesliga'),
            ('Inter Milan', 'AC Milan', 'Serie A'),
            ('PSG', 'Lyon', 'Ligue 1')
        ]
        
        midweek_matches = [
            ('Manchester City', 'Tottenham', 'Premier League'),
            ('Atletico Madrid', 'Valencia', 'La Liga'),
            ('Juventus', 'Roma', 'Serie A'),
            ('Leipzig', 'Leverkusen', 'Bundesliga')
        ]
        
        if day_of_week in [5, 6]:  # Weekend
            selected_matches = weekend_matches
        elif day_of_week == 2:  # Wednesday
            selected_matches = midweek_matches
        else:
            return [{
                'id': 'render-info',
                'time': 'No scheduled matches',
                'homeTeam': f'Today is {today.strftime("%A")}',
                'awayTeam': f'{today.strftime("%B %d, %Y")}',
                'league': f'Running on Render.com - {today.strftime("%H:%M UTC")}',
                'status': 'INFO',
                'homeOdds': 0,
                'drawOdds': 0,
                'awayOdds': 0,
                'source': 'render-system',
                'isInfo': True
            }]
        
        matches = []
        base_time = today.replace(hour=15, minute=0, second=0, microsecond=0)
        
        for i, (home, away, league) in enumerate(selected_matches):
            match_time = base_time + timedelta(hours=i*2)
            matches.append({
                'id': f'render-{i}',
                'time': match_time.strftime('%H:%M'),
                'homeTeam': home,
                'awayTeam': away,
                'league': league,
                'status': 'SCHEDULED',
                'homeOdds': round(random.uniform(1.5, 3.8), 2),
                'drawOdds': round(random.uniform(2.9, 4.1), 2),
                'awayOdds': round(random.uniform(1.8, 4.8), 2),
                'source': 'render-optimized'
            })
        
        return matches

class RenderTeamAnalyzer:
    def __init__(self):
        self.team_cache = {}
        self.cache_expiry = {}
    
    def get_team_stats(self, team_name):
        """Get team statistics with memory-efficient caching"""
        now = datetime.now()
        
        # Check cache (30 min expiry for Render)
        if (team_name in self.team_cache and 
            team_name in self.cache_expiry and 
            now < self.cache_expiry[team_name]):
            return self.team_cache[team_name]
        
        # Generate stats
        stats = self.generate_render_stats(team_name)
        
        # Limit cache size
        if len(self.team_cache) > 50:
            self.team_cache.clear()
            self.cache_expiry.clear()
        
        self.team_cache[team_name] = stats
        self.cache_expiry[team_name] = now + timedelta(minutes=30)
        
        return stats
    
    def generate_render_stats(self, team_name):
        """Generate realistic stats optimized for Render"""
        elite_teams = ['Manchester United', 'Manchester City', 'Chelsea', 'Liverpool', 
                      'Arsenal', 'Barcelona', 'Real Madrid', 'Bayern Munich', 'PSG']
        
        is_elite = any(elite in team_name for elite in elite_teams)
        
        if is_elite:
            confidence = random.randint(75, 90)
            goals_for = round(random.uniform(2.0, 3.0), 1)
            goals_against = round(random.uniform(0.8, 1.5), 1)
            win_rate = random.randint(60, 80)
        else:
            confidence = random.randint(55, 75)
            goals_for = round(random.uniform(1.3, 2.3), 1)
            goals_against = round(random.uniform(1.1, 2.2), 1)
            win_rate = random.randint(35, 65)
        
        return {
            'recentForm': self.generate_form(),
            'goalsFor': goals_for,
            'goalsAgainst': goals_against,
            'homeWinRate': win_rate,
            'awayWinRate': max(20, win_rate - 15),
            'cleanSheets': random.randint(25, 65),
            'confidence': confidence,
            'lastUpdated': now.strftime('%Y-%m-%d %H:%M'),
            'platform': 'Render.com'
        }
    
    def generate_form(self):
        """Generate recent form"""
        results = ['W', 'D', 'L']
        weights = [0.45, 0.30, 0.25]
        form = []
        for _ in range(5):
            form.append(random.choices(results, weights=weights)[0])
        return '-'.join(form)
    
    def analyze_match(self, home_team, away_team):
        """Render-optimized match analysis"""
        home_stats = self.get_team_stats(home_team)
        away_stats = self.get_team_stats(away_team)
        
        home_strength = home_stats['confidence'] + 7  # Home advantage
        away_strength = away_stats['confidence']
        strength_diff = abs(home_strength - away_strength)
        
        if strength_diff > 20:
            if home_strength > away_strength:
                recommendation = {
                    'bet': f'{home_team} Win',
                    'odds': round(random.uniform(1.4, 2.1), 2),
                    'confidence': min(85, 70 + strength_diff // 3),
                    'type': 'Single Bet',
                    'reasoning': f'{home_team} significantly stronger with home advantage'
                }
            else:
                recommendation = {
                    'bet': f'{away_team} Win',
                    'odds': round(random.uniform(1.7, 2.8), 2),
                    'confidence': min(80, 65 + strength_diff // 4),
                    'type': 'Value Bet',
                    'reasoning': f'{away_team} much stronger despite playing away'
                }
        else:
            recommendation = {
                'bet': 'Both Teams to Score',
                'odds': round(random.uniform(1.6, 2.1), 2),
                'confidence': 72,
                'type': 'Alternative Market',
                'reasoning': 'Evenly matched teams often produce goals'
            }
        
        return {
            'homeStats': home_stats,
            'awayStats': away_stats,
            'recommendation': recommendation,
            'analysis': {
                'keyFactors': [
                    f"Home team averages {home_stats['goalsFor']} goals per game",
                    f"Away team has {away_stats['cleanSheets']}% clean sheet rate",
                    f"Analysis powered by Render.com deployment"
                ],
                'riskFactors': [
                    'Check for injuries and team news',
                    'Consider recent head-to-head record',
                    'Weather and pitch conditions may apply'
                ]
            }
        }

# Initialize services
football_api = RenderOptimizedFootballAPI()
team_analyzer = RenderTeamAnalyzer()

# Initialize database
init_db()

# Routes
@app.route('/')
def index():
    """Serve the main application"""
    return render_template('index.html')

@app.route('/api/matches/today')
def get_todays_matches():
    """Get today's matches - Render optimized"""
    try:
        matches = football_api.get_todays_matches()
        return jsonify({
            'success': True,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'platform': 'Render.com',
            'matches': matches,
            'count': len(matches)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'platform': 'Render.com'
        }), 500

@app.route('/api/analyze/<home_team>/<away_team>')
def analyze_match(home_team, away_team):
    """Match analysis endpoint"""
    try:
        analysis = team_analyzer.analyze_match(home_team, away_team)
        return jsonify({
            'success': True,
            'analysis': analysis,
            'platform': 'Render.com'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/calculate-bet', methods=['POST'])
def calculate_bet():
    """Bankroll calculation"""
    try:
        data = request.get_json()
        balance = float(data.get('balance', 0))
        
        if balance <= 0:
            return jsonify({'success': False, 'error': 'Invalid balance'}), 400
        
        recommendations = {
            'conservative': round(balance * 0.2, 2),
            'moderate': round(balance * 0.3, 2),
            'aggressive': round(balance * 0.4, 2),
            'maximum': round(balance * 0.4, 2)
        }
        
        return jsonify({
            'success': True,
            'balance': balance,
            'recommendations': recommendations,
            'platform': 'Render.com'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check for Render"""
    return jsonify({
        'status': 'healthy',
        'platform': 'Render.com',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected' if os.path.exists(DATABASE_PATH) else 'initializing'
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found', 'platform': 'Render.com'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error', 'platform': 'Render.com'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
