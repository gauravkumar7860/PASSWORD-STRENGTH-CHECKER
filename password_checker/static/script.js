document.addEventListener('DOMContentLoaded', function() {
    const passwordInput = document.getElementById('passwordInput');
    const showHideBtn = document.getElementById('showHideBtn');
    const eyeIcon = document.getElementById('eyeIcon');
    const strengthDisplay = document.getElementById('strengthDisplay');
    const strengthCircle = document.getElementById('strengthCircle');
    const strengthScore = document.getElementById('strengthScore');
    const strengthText = document.getElementById('strengthText');
    const entropyValue = document.getElementById('entropyValue');
    const checklistSection = document.getElementById('checklistSection');
    const checklist = document.getElementById('checklist');
    const suggestionsSection = document.getElementById('suggestionsSection');
    const suggestions = document.getElementById('suggestions');
    const generateBtn = document.getElementById('generateBtn');
    const generatedPassword = document.getElementById('generatedPassword');
    const copyBtn = document.getElementById('copyBtn');

    let isPasswordVisible = false;

    // Toggle password visibility
    showHideBtn.addEventListener('click', function() {
        isPasswordVisible = !isPasswordVisible;
        passwordInput.type = isPasswordVisible ? 'text' : 'password';
        eyeIcon.className = isPasswordVisible ? 'fas fa-eye-slash' : 'fas fa-eye';
    });

    // Real-time password checking
    passwordInput.addEventListener('input', debounce(checkPassword, 300));

    // Generate strong password
    generateBtn.addEventListener('click', generateStrongPassword);

    // Copy password
    copyBtn.addEventListener('click', copyToClipboard);

    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    async function checkPassword() {
        const password = passwordInput.value;
        
        if (password.length === 0) {
            hideResults();
            return;
        }

        try {
            const response = await fetch('/check