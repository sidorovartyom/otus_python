// Тестовый JavaScript файл для проверки MIME типа application/javascript

console.log('✅ JavaScript файл загружен успешно!');
console.log('MIME тип должен быть: application/javascript');

// Простая функция для демонстрации
function testFunction() {
    alert('Если вы видите это сообщение, значит JS работает правильно!');
}

// Если этот файл отображается как обычный текст в браузере,
// значит MIME тип установлен неправильно

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM загружен, JavaScript работает корректно');
}); 