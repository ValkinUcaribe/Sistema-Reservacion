document.addEventListener('DOMContentLoaded', () => {
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm-password');
    const togglePassword = document.getElementById('toggle-password');
    const passwordForm = document.getElementById('password-form');
    const responseMessage = document.getElementById('response-message');
    let isPasswordVisible = false;

    const rules = {
        length: document.getElementById('length-rule'),
        uppercase: document.getElementById('uppercase-rule'),
        lowercase: document.getElementById('lowercase-rule'),
        special: document.getElementById('special-rule')
    };

    // Validar la contraseña mientras el usuario escribe
    passwordInput.addEventListener('input', () => {
        validatePassword(passwordInput.value);
    });

    // Alternar visibilidad de la contraseña
    togglePassword.addEventListener('click', () => {
        isPasswordVisible = !isPasswordVisible;
        passwordInput.type = isPasswordVisible ? 'text' : 'password';
        confirmPasswordInput.type = isPasswordVisible ? 'text' : 'password';
    });

    // Validar reglas visualmente
    function validatePassword(value) {
        rules.length.style.color = value.length >= 8 ? 'green' : 'red';
        rules.uppercase.style.color = /[A-Z]/.test(value) ? 'green' : 'red';
        rules.lowercase.style.color = /[a-z]/.test(value) ? 'green' : 'red';
        rules.special.style.color = /[!@#$%^&*(),.?":{}|<>]/.test(value) ? 'green' : 'red';
    }

    // Envío del formulario
    passwordForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const passwordValue = passwordInput.value;
        const confirmValue = confirmPasswordInput.value;

        if (passwordValue !== confirmValue) {
            showMessage('Las contraseñas no coinciden', 'red');
            return;
        }

        const lengthValid = passwordValue.length >= 8;
        const hasUppercase = /[A-Z]/.test(passwordValue);
        const hasLowercase = /[a-z]/.test(passwordValue);
        const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(passwordValue);

        if (!lengthValid) {
            showMessage('La contraseña debe tener al menos 8 caracteres', 'red');
            return;
        }
        if (!hasUppercase) {
            showMessage('La contraseña debe contener al menos una letra mayúscula', 'red');
            return;
        }
        if (!hasLowercase) {
            showMessage('La contraseña debe contener al menos una letra minúscula', 'red');
            return;
        }
        if (!hasSpecialChar) {
            showMessage('La contraseña debe contener al menos un carácter especial', 'red');
            return;
        }

        // Si todo está bien, enviar los datos
        const formData = new FormData(passwordForm);
        try {
            const response = await fetch(passwordForm.action, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorMessage = await response.text();
                showMessage(errorMessage || 'Error al procesar la solicitud.', 'red');
            } else {
                showMessage('Contraseña actualizada con éxito', 'green');
                setTimeout(() => window.location.href = '/', 2000);
            }
        } catch (error) {
            showMessage('Error al procesar la solicitud.', 'red');
        }
    });

    function showMessage(message, color) {
        responseMessage.style.display = 'block';
        responseMessage.style.backgroundColor = color;
        responseMessage.style.color = 'white';
        responseMessage.textContent = message;
    }
});
