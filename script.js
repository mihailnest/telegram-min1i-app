\document.addEventListener('DOMContentLoaded', () => {
    const codeScreen = document.getElementById('code-screen');
    const gameScreen = document.getElementById('game-screen');
    const resultScreen = document.getElementById('result-screen');
    const codeInput = document.getElementById('code-input');
    const submitBtn = document.getElementById('submit-btn');
    const errorMsg = document.getElementById('error-msg');
    const winAmount = document.getElementById('win-amount');
    const coins = document.querySelectorAll('.coin');
    
    let currentCode = '';
    let winValue = 0;
    
    // Функция проверки кода через API бота
    async function checkCode(code) {
        try {
            const response = await fetch(`https://mihailnest.github.io/telegram-mini-app/}`);
            const data = await response.json();
            
            if (data.valid) {
                winValue = data.amount;
                return true;
            }
            return false;
        } catch (error) {
            console.error('Ошибка при проверке кода:', error);
            errorMsg.textContent = "Ошибка соединения с сервером";
            return false;
        }
    }
    
    // Функция записи победы
    async function recordWin(code, amount) {
        try {
            const userId = Telegram.WebApp.initDataUnsafe.user?.id;
            if (!userId) {
                console.error('User ID не найден');
                return false;
            }
            
            await fetch('https://mihailnest.github.io/telegram-mini-app/n', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    user_id: userId,
                    code: code,
                    amount: amount
                })
            });
            return true;
        } catch (error) {
            console.error('Ошибка при записи победы:', error);
            return false;
        }
    }
    
    // Обработка ввода кода
    submitBtn.addEventListener('click', async () => {
        const code = codeInput.value.trim();
        if (code.length !== 4 || !/^\d+$/.test(code)) {
            errorMsg.textContent = "Введите 4-значный код";
            return;
        }
        
        errorMsg.textContent = "Проверка кода...";
        const isValid = await checkCode(code);
        
        if (isValid) {
            currentCode = code;
            codeScreen.style.display = 'none';
            gameScreen.style.display = 'block';
            errorMsg.textContent = "";
        } else {
            errorMsg.textContent = "Неверный код или неактивный";
        }
    });
    
    // Обработка клика по монетам
    coins.forEach(coin => {
        coin.addEventListener('click', async () => {
            // Остановка анимации
            coins.forEach(c => c.style.animation = 'none');
            
            // Показ результата
            gameScreen.style.display = 'none';
            winAmount.textContent = `${winValue}₽`;
            resultScreen.style.display = 'block';
            
            // Отправка данных на сервер
            const success = await recordWin(currentCode, winValue);
            if (!success) {
                alert("Ошибка при сохранении результата!");
            }
        });
    });
    
    // Инициализация Telegram WebApp
    Telegram.WebApp.ready();
    Telegram.WebApp.expand();
});