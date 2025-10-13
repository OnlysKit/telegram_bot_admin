function filterByBot() {
    const select = document.getElementById('bot-filter');
    const selectedBotId = select.value;
    
    // Перенаправляем на ту же страницу с параметром bot_id
    if (selectedBotId === 'all') {
        window.location.href = '/products';
    } else {
        window.location.href = '/products?bot_id=' + selectedBotId;
    }
}
