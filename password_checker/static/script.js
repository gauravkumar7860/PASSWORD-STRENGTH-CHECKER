const passwordInput = document.getElementById("passwordInput");
const showHideBtn = document.getElementById("showHideBtn");
const eyeIcon = document.getElementById("eyeIcon");

const strengthCircle = document.getElementById("strengthCircle");
const strengthScore = document.getElementById("strengthScore");
const strengthText = document.getElementById("strengthText");
const entropyValue = document.getElementById("entropyValue");
const checklist = document.getElementById("checklist");
const suggestions = document.getElementById("suggestions");

const generateBtn = document.getElementById("generateBtn");
const generatedPassword = document.getElementById("generatedPassword");
const copyBtn = document.getElementById("copyBtn");

// Toggle password visibility
showHideBtn.addEventListener("click", () => {
    if (passwordInput.type === "password") {
        passwordInput.type = "text";
        eyeIcon.classList.remove("fa-eye");
        eyeIcon.classList.add("fa-eye-slash");
    } else {
        passwordInput.type = "password";
        eyeIcon.classList.remove("fa-eye-slash");
        eyeIcon.classList.add("fa-eye");
    }
});

// Check password on input
passwordInput.addEventListener("input", () => {
    const password = passwordInput.value.trim();
    if (!password) return resetDisplay();

    fetch("/check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password })
    })
        .then(res => res.json())
        .then(data => updateDisplay(data))
        .catch(err => console.error(err));
});

// Generate strong password
generateBtn.addEventListener("click", () => {
    fetch("/check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password: "" })
    })
        .then(res => res.json())
        .then(data => {
            passwordInput.value = data.strong_password;
            generatedPassword.textContent = data.strong_password;
            copyBtn.style.display = "inline-block";
            updateDisplay(data);
        })
        .catch(err => console.error(err));
});

// Copy password
copyBtn.addEventListener("click", () => {
    navigator.clipboard.writeText(passwordInput.value);
    alert("Password copied to clipboard!");
});

// Update UI
function updateDisplay(data) {
    if (data.error) {
        strengthScore.textContent = 0;
        strengthText.textContent = "Enter a password";
        entropyValue.textContent = 0;
        checklist.innerHTML = "";
        suggestions.innerHTML = "";
        return;
    }

    // Strength
    strengthScore.textContent = data.score;
    strengthText.textContent = data.strength;
    entropyValue.textContent = data.entropy;

    // Checklist
    checklist.innerHTML = "";
    for (const [key, passed] of Object.entries(data.checks)) {
        const div = document.createElement("div");
        div.textContent = `${key}: ${passed ? "✔" : "❌"}`;
        checklist.appendChild(div);
    }

    // Suggestions
    suggestions.innerHTML = "";
    data.suggestions.forEach(s => {
        const div = document.createElement("div");
        div.textContent = `💡 ${s}`;
        suggestions.appendChild(div);
    });
}

// Reset UI
function resetDisplay() {
    strengthScore.textContent = 0;
    strengthText.textContent = "Enter a password";
    entropyValue.textContent = 0;
    checklist.innerHTML = "";
    suggestions.innerHTML = "";
}
