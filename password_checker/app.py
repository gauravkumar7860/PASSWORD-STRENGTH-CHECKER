import os
from flask import Flask, render_template, request, jsonify
import re
import secrets
import string
import math
from collections import Counter

app = Flask(__name__)

# Production config
port = int(os.environ.get('PORT', 5000))
host = os.environ.get('HOST', '0.0.0.0')

# Common passwords
COMMON_PASSWORDS = ['password', '123456', 'qwerty', 'admin', 'letmein', 'welcome', 'monkey', '123456789', 'password1', 'iloveyou']

def check_length(password): return len(password) >= 8
def check_uppercase(password): return bool(re.search(r'[A-Z]', password))
def check_lowercase(password): return bool(re.search(r'[a-z]', password))
def check_digit(password): return bool(re.search(r'\d', password))
def check_special(password): return bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
def check_dictionary(password): return password.lower() in [pw.lower() for pw in COMMON_PASSWORDS]
def check_repeated_chars(password): return all(count <= 2 for count in Counter(password).values())
def check_patterns(password): 
    patterns = [r'123456', r'abcdef', r'qwerty']
    return not any(re.search(p, password.lower()) for p in patterns)

def calculate_entropy(password):
    charset = 0
    if check_lowercase(password): charset += 26
    if check_uppercase(password): charset += 26
    if check_digit(password): charset += 10
    if check_special(password): charset += 32
    length = len(password)
    return round(length * math.log2(max(charset, 1)), 2) if length else 0

def generate_strong_password(): 
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(chars) for _ in range(16))

def get_password_strength(password):
    checks = {
        'length': check_length(password),
        'uppercase': check_uppercase(password),
        'lowercase': check_lowercase(password),
        'digit': check_digit(password),
        'special': check_special(password),
        'dictionary': not check_dictionary(password),
        'repeated': check_repeated_chars(password),
        'patterns': check_patterns(password)
    }
    
    score = sum(checks.values()) / len(checks) * 100
    strength = ["Very Weak", "Weak", "Good", "Strong", "Very Strong"][min(4, int(score/25))]
    entropy = calculate_entropy(password)
    
    suggestions = []
    if not checks['length']: suggestions.append("Use 8+ characters")
    if not checks['uppercase']: suggestions.append("Add uppercase letters")
    if not checks['special']: suggestions.append("Add special chars")
    
    return {
        'strength': strength,
        'score': round(score),
        'entropy': entropy,
        'checks': checks,
        'suggestions': suggestions,
        'strong_password': generate_strong_password()
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check', methods=['POST'])
def check_password():
    password = request.json.get('password', '')
    return jsonify(get_password_strength(password) if password else {'error': 'Enter password'})

if __name__ == '__main__':
    app.run(host=host, port=port, debug=False)
