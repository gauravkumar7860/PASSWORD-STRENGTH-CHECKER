from flask import Flask, render_template, request
import re, math, random, string

app = Flask(__name__)

common_passwords = ["password", "123456", "qwerty", "admin", "letmein", "welcome"]

def check_password_strength(password):
    feedback = []
    score = 0

    # Basic checks
    length_error = len(password) < 8
    lowercase_error = re.search(r"[a-z]", password) is None
    uppercase_error = re.search(r"[A-Z]", password) is None
    digit_error = re.search(r"\d", password) is None
    special_char_error = re.search(r"[!@#$%^&*(),.?\":{}|<>]", password) is None
    repeated_error = re.search(r"(.)\1\1", password) is not None
    common_error = password.lower() in common_passwords

    errors = [length_error, lowercase_error, uppercase_error, digit_error, special_char_error, repeated_error, common_error]
    score = 7 - sum(errors)

    # Feedback messages
    if length_error:
        feedback.append("Use at least 8 characters")
    if lowercase_error:
        feedback.append("Include a lowercase letter")
    if uppercase_error:
        feedback.append("Include an uppercase letter")
    if digit_error:
        feedback.append("Include a number")
    if special_char_error:
        feedback.append("Include a special character (!@#$...)")
    if repeated_error:
        feedback.append("Avoid repeated characters")
    if common_error:
        feedback.append("Avoid common passwords")

    # Strength messages
    if score >= 6:
        strength = "Very Strong 💪"
        color = "green"
    elif score >= 5:
        strength = "Strong 👍"
        color = "limegreen"
    elif score >= 4:
        strength = "Moderate 😐"
        color = "orange"
    elif score >= 3:
        strength = "Weak ⚠️"
        color = "orangered"
    else:
        strength = "Very Weak ❌"
        color = "red"

    # Entropy calculation
    pool = 0
    if re.search(r"[a-z]", password): pool += 26
    if re.search(r"[A-Z]", password): pool += 26
    if re.search(r"\d", password): pool += 10
    if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password): pool += 32
    entropy = round(len(password) * math.log2(pool), 2) if pool > 0 else 0

    return strength, color, feedback, entropy

def generate_password(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(random.choice(chars) for _ in range(length))

@app.route("/", methods=["GET", "POST"])
def index():
    password = ""
    strength = ""
    color = ""
    feedback = []
    entropy = 0
    suggested_password = ""

    if request.method == "POST":
        password = request.form.get("password")
        if "check" in request.form:
            strength, color, feedback, entropy = check_password_strength(password)
        elif "generate" in request.form:
            suggested_password = generate_password()
            password = suggested_password
            strength, color, feedback, entropy = check_password_strength(password)

    return render_template("index.html",
                           password=password,
                           strength=strength,
                           color=color,
                           feedback=feedback,
                           entropy=entropy,
                           suggested_password=suggested_password)

if __name__ == "__main__":
    app.run(debug=True)