function resetTelegramId(type, productId) {
    if (confirm(`Вы уверены, что хотите сбросить Telegram ${type} ID?`)) {
        console.log(`Сброс Telegram ${type} ID для продукта ${productId}`);
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/products/${productId}/reset-telegram-${type}`;
        document.body.appendChild(form);
        form.submit();
    }
}
