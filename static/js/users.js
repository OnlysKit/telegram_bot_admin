function filterByBot() {
    const select = document.getElementById('bot-filter');
    const selectedBotId = select.value;
    
    if (selectedBotId === 'all') {
        window.location.href = '/users';
    } else {
        window.location.href = '/users?bot_id=' + selectedBotId;
    }
}

function changeRole(userId, role) {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/users/' + userId + '/role';
    
    const roleInput = document.createElement('input');
    roleInput.type = 'hidden';
    roleInput.name = 'role';
    roleInput.value = role;
    
    form.appendChild(roleInput);
    document.body.appendChild(form);
    form.submit();
}

function changeTariff(userId, tariff) {
    if (!tariff) return; // Не отправляем пустые значения
    
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/users/' + userId + '/tariff';
    
    const tariffInput = document.createElement('input');
    tariffInput.type = 'hidden';
    tariffInput.name = 'tariff';
    tariffInput.value = tariff;
    
    form.appendChild(tariffInput);
    document.body.appendChild(form);
    form.submit();
}

function changeBot(userId, botId) {
    if (!botId) return; // Не отправляем пустые значения
    
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/users/' + userId + '/bot';
    
    const botInput = document.createElement('input');
    botInput.type = 'hidden';
    botInput.name = 'bot_id';
    botInput.value = botId;
    
    form.appendChild(botInput);
    document.body.appendChild(form);
    form.submit();
}

let currentUserId = null;

function openSourceModal(userId, currentSource) {
    currentUserId = userId;
    document.getElementById('sourceInput').value = currentSource;
    document.getElementById('sourceModal').style.display = 'block';
}

function closeSourceModal() {
    document.getElementById('sourceModal').style.display = 'none';
    currentUserId = null;
}

function saveSource() {
    if (!currentUserId) return;
    
    const source = document.getElementById('sourceInput').value;
    
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/users/' + currentUserId + '/source';
    
    const sourceInput = document.createElement('input');
    sourceInput.type = 'hidden';
    sourceInput.name = 'source';
    sourceInput.value = source;
    
    form.appendChild(sourceInput);
    document.body.appendChild(form);
    form.submit();
}

// Закрытие модального окна при клике вне его
window.onclick = function(event) {
    const modal = document.getElementById('sourceModal');
    if (event.target == modal) {
        closeSourceModal();
    }
}
