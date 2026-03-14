from flask import Flask, render_template, request, jsonify
import re
import secrets
import string
import math
from collections import Counter
import requests

app = Flask(__name__)

# Common passwords dictionary (top 1000 for demo)
COMMON_PASSWORDS = [
    'password', '123456', '123456789', 'guest', 'qwerty', '12345678', '111111', 
    '12345', '123123', 'abc123', 'Password1', 'admin', 'letmein', 'welcome',
    'monkey', 'dragon', 'master', 'hello', 'freedom', 'whatever', 'qazwsx',
    'trustno1', 'ninja', 'abcde', '000000', 'password1', 'iloveyou', 'welcome1'
]

def check_length(password):
    return len(password) >= 8

def check_uppercase(password):
    return bool(re.search(r'[A-Z]', password))

def check_lowercase(password):
    return bool(re.search(r'[a-z]', password))

def check_digit(password):
    return bool(re.search(r'\d', password))

def check_special(password):
    special_chars = r'[!@#$%^&*(),.?":{}|<>]'
    return bool(re.search(special_chars, password))

def check_dictionary(password):
    password_lower = password.lower()
    return password_lower in [pw.lower() for pw in COMMON_PASSWORDS]

def check_repeated_chars(password):
    char_count = Counter(password)
    for count in char_count.values():
        if count > 2:
            return False
    return True

def check_patterns(password):
    # Check for sequential patterns
    seq_patterns = [
        r'123456', r'abcdef', r'qwerty', r'1qaz2wsx',
        r'abcdefghijklmnopqrstuvwxyz', r'0123456789'
    ]
    password_lower = password.lower()
    for pattern in seq_patterns:
        if re.search(pattern, password_lower):
            return False
    return True

def calculate_entropy(password):
    charset_sizes = {
        'lower': 26, 'upper': 26, 'digits': 10, 'special': 32
    }
    
    charset = 0
    if check_lowercase(password): charset += charset_sizes['lower']
    if check_uppercase(password): charset += charset_sizes['upper']
    if check_digit(password): charset += charset_sizes['digits']
    if check_special(password): charset += charset_sizes['special']
    
    length = len(password)
    if charset == 0 or length == 0:
        return 0
    
    entropy = length * math.log2(charset)
    strength_score = min(100, (entropy / 60) * 100)  # Scale to 100
    return round(entropy, 2), round(strength_score, 2)

def generate_strong_password(length=16):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(chars) for _ in range(length))

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
    
    passed = sum(checks.values())
    total = len(checks)
    
    if passed == total:
        strength = "Very Strong"
        score = 100
    elif passed >= total * 0.8:
        strength = "Strong"
        score = 80
    elif passed >= total * 0.6:
        strength = "Good"
        score = 60
    elif passed >= total * 0.4:
        strength = "Weak"
        score = 40
    else:
        strength = "Very Weak"
        score = 20
    
    entropy, entropy_score = calculate_entropy(password)
    
    return {
        'strength': strength,
        'score': score,
        'entropy': entropy,
        'entropy_score': entropy_score,
        'checks': checks,
        'suggestions': get_suggestions(checks)
    }

def get_suggestions(checks):
    suggestions = []
    if not checks['length']:
        suggestions.append("Use at least 8 characters")
    if not checks['uppercase']:
        suggestions.append("Add uppercase letters")
    if not checks['lowercase']:
        suggestions.append("Add lowercase letters")
    if not checks['digit']:
        suggestions.append("Add numbers")
    if not checks['special']:
        suggestions.append("Add special characters (!@#$%)")
    if not checks['dictionary']:
        suggestions.append("Avoid common words")
    if not checks['repeated']:
        suggestions.append("Avoid repeated characters")
    if not checks['patterns']:
        suggestions.append("Avoid keyboard patterns")
    return suggestions

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check', methods=['POST'])
def check_password():
    data = request.json
    password = data.get('password', '')
    
    if not password:
        return jsonify({'error': 'Please enter a password'})
    
    result = get_password_strength(password)
    result['strong_password'] = generate_strong_password()
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)