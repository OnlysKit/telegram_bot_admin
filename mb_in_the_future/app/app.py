import asyncio
import secrets
from fastapi import FastAPI, Request, Form, HTTPException, Depends, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import uvicorn
from modules.utils import db
from modules.configs.config import tariffs    

# Создаем экземпляр FastAPI приложения
app = FastAPI()

# Настраиваем шаблоны Jinja2
templates = Jinja2Templates(directory="templates")

# Настраиваем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

# Настройки аутентификации
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  # В реальном проекте используйте хеширование паролей
SECRET_KEY = "your-secret-key-change-in-production"

# Хранилище активных сессий (в реальном проекте используйте Redis или БД)
active_sessions = {}

def create_session():
    """Создает новую сессию"""
    session_id = secrets.token_urlsafe(32)
    active_sessions[session_id] = {"authenticated": True}
    return session_id

def verify_session(session_id: str = Cookie(None)):
    """Проверяет валидность сессии"""
    if not session_id or session_id not in active_sessions:
        return False
    return active_sessions[session_id].get("authenticated", False)

def require_auth(session_id: str = Cookie(None)):
    """Зависимость для проверки аутентификации"""
    if not verify_session(session_id):
        raise HTTPException(status_code=401, detail="Требуется аутентификация")
    return True

@app.get("/")
async def root(session_id: str = Cookie(None)):
    """Корневой эндпоинт"""
    # Проверяем, залогинен ли пользователь
    if verify_session(session_id):
        return RedirectResponse(url="/products")
    else:
        return RedirectResponse(url="/login")


@app.get("/login")
async def show_login_form(request: Request):
    """Отображает форму входа"""
    return templates.TemplateResponse("login.html", {
        "request": request
    })


@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Обрабатывает вход в систему"""
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session_id = create_session()
        response = RedirectResponse(url="/products", status_code=303)
        response.set_cookie(key="session_id", value=session_id, httponly=True, secure=False)
        return response
    else:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Неверное имя пользователя или пароль"
        })


@app.get("/logout")
async def logout():
    """Выход из системы"""
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="session_id")
    return response




@app.get("/products")
async def show_products(request: Request, bot_id: str = None, session_id: str = Cookie(None)):
    """Отображает страницу с продуктами из базы данных"""
    
    # Получаем все продукты из таблицы products
    if bot_id and bot_id != "all":
        products = await db.get_all_generic_async("products", product_bot=bot_id)
    else:
        products = await db.get_all_generic_async("products")
    
    products_list = []
    
    # Получаем список ботов для сопоставления
    bots = await db.get_all_generic_async("bots")
    bots_dict = {str(bot['bot_id']): bot for bot in bots}
    
    for product in products:
        product_id = product['id']
        title = product['title']
        description = product.get('description') or ''
        image = product.get('image') or ''
        video = product.get('video') or ''
        is_free = product.get('is_free') or 0
        price = product.get('price') or 0
        discount = product.get('discount') or 0
        file_type = product.get('file_type') or ''
        product_bot_id = product.get('product_bot') or ''
        path = product.get('path') or ''
        
        # Находим информацию о боте
        bot_info = bots_dict.get(str(product_bot_id), {})
        bot_title = bot_info.get('title', '')
        bot_username = bot_info.get('bot_username', '')
        
        link = product.get('link') or ''
        
        products_list.append({
            'id': product_id,
            'title': title,
            'description': description,
            'image': image,
            'video': video,
            'is_free': is_free,
            'price': price,
            'discount': discount,
            'file_type': file_type,
            'product_bot_id': product_bot_id,
            'bot_title': bot_title,
            'bot_username': bot_username,
            'path': path,
            'link': link
        })
    
    return templates.TemplateResponse("products.html", {
        "request": request,
        "products": products_list,
        "bots": bots,
        "selected_bot_id": bot_id,
        "is_authenticated": verify_session(session_id)
    })


@app.get("/add-product")
async def show_add_product_form(request: Request, auth: bool = Depends(require_auth)):
    """Отображает форму для добавления нового продукта"""
    # Получаем список ботов из базы данных
    bots = await db.get_all_generic_async("bots")
    
    return templates.TemplateResponse("add_product.html", {
        "request": request,
        "bots": bots
    })


@app.post("/add-product")
async def add_product(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    image: str = Form(""),
    video: str = Form(""),
    is_free: str = Form("0"),
    price: int = Form(0),
    discount: int = Form(0),
    file_type: str = Form(""),
    bot_id: str = Form(""),
    path: str = Form(""),
    link: str = Form(""),
    auth: bool = Depends(require_auth)
):
    """Добавляет новый продукт в базу данных"""
    
    try:
        # Обрабатываем пустые поля - заменяем на None
        def process_field(value):
            return None if not value or value.strip() == "" else value
        
        # Вставляем продукт в базу данных
        columns = ["title", "description", "image", "video", "is_free", "price", "discount", "file_type", "product_bot", "path", "link"]
        values = [
            title, 
            process_field(description), 
            process_field(image), 
            process_field(video), 
            is_free, 
            price, 
            discount, 
            process_field(file_type), 
            process_field(bot_id), 
            process_field(path), 
            process_field(link)
        ]
        await db.insert_async(columns, values, "products")
        
        # Перенаправляем на страницу со списком продуктов
        return RedirectResponse(url="/products", status_code=303)
        
    except Exception as e:
        # В случае ошибки возвращаем форму с сообщением об ошибке
        bots = await db.get_all_generic_async("bots")
        return templates.TemplateResponse("add_product.html", {
            "request": request,
            "bots": bots,
            "error": f"Ошибка при добавлении продукта: {str(e)}"
        })


@app.get("/delete-product/{product_id}")
async def delete_product(product_id: int, auth: bool = Depends(require_auth)):
    """Удаляет продукт по ID"""
    try:
        await db.delete_generic_async("products", id=product_id)
        return RedirectResponse(url="/products", status_code=303)
    except Exception as e:
        return {"error": f"Ошибка при удалении продукта: {str(e)}"}


@app.get("/edit-product/{product_id}")
async def show_edit_product_form(request: Request, product_id: int, auth: bool = Depends(require_auth)):
    """Отображает форму для редактирования продукта"""
    try:
        # Получаем продукт по ID
        product = await db.get_one_generic_async("products", id=product_id)
        if not product:
            return RedirectResponse(url="/products", status_code=303)
        
        # Получаем список ботов
        bots = await db.get_all_generic_async("bots")
        
        return templates.TemplateResponse("add_product.html", {
            "request": request,
            "bots": bots,
            "product": product,
            "is_edit": True
        })
    except Exception as e:
        return RedirectResponse(url="/products", status_code=303)


@app.post("/edit-product/{product_id}")
async def update_product(
    request: Request,
    product_id: int,
    title: str = Form(...),
    description: str = Form(""),
    image: str = Form(""),
    video: str = Form(""),
    is_free: str = Form("0"),
    price: int = Form(0),
    discount: int = Form(0),
    file_type: str = Form(""),
    bot_id: str = Form(""),
    path: str = Form(""),
    link: str = Form(""),
    auth: bool = Depends(require_auth)
):
    """Обновляет продукт в базе данных"""
    
    # Обрабатываем пустые поля - заменяем на None
    def process_field(value):
        return None if not value or value.strip() == "" else value
    
    # Подготавливаем данные для обновления
    product_data = {
        'title': title,
        'description': process_field(description),
        'image': process_field(image),
        'video': process_field(video),
        'is_free': 1 if is_free == "1" else 0,
        'price': price,
        'discount': discount,
        'file_type': process_field(file_type),
        'product_bot': process_field(bot_id),
        'path': process_field(path),
        'link': process_field(link)
    }
    
    try:
        # Обновляем продукт в базе данных
        columns = list(product_data.keys())
        values = list(product_data.values())
        await db.update_generic_async("products", columns, values, id=product_id)
        
        # Перенаправляем на страницу со списком продуктов
        return RedirectResponse(url="/products", status_code=303)
        
    except Exception as e:
        # В случае ошибки возвращаем форму с сообщением об ошибке
        bots = await db.get_all_generic_async("bots")
        product = await db.get_one_generic_async("products", id=product_id)
        return templates.TemplateResponse("add_product.html", {
            "request": request,
            "bots": bots,
            "product": product,
            "is_edit": True,
            "error": f"Ошибка при обновлении продукта: {str(e)}"
        })


@app.get("/add-bot")
async def show_add_bot_form(request: Request, auth: bool = Depends(require_auth)):
    """Отображает форму для добавления нового бота"""
    return templates.TemplateResponse("add_bot.html", {
        "request": request
    })


@app.post("/add-bot")
async def add_bot(
    request: Request,
    title: str = Form(...),
    bot_id: int = Form(...),
    bot_token: str = Form(...),
    bot_username: str = Form(...),
    auth: bool = Depends(require_auth)
):
    """Добавляет нового бота в базу данных"""
    
    try:
        # Обрабатываем пустые поля - заменяем на None
        def process_field(value):
            return None if not value or value.strip() == "" else value
        
        await db.insert_async(
            ["title", "bot_id", "bot_token", "bot_username"], 
            [process_field(title), bot_id, process_field(bot_token), process_field(bot_username)], 
            table='bots'
        )
        return RedirectResponse(url="/products", status_code=303)
    except Exception as e:
        return templates.TemplateResponse("add_bot.html", {
            "request": request,
            "error": f"Ошибка при добавлении бота: {str(e)}"
        })


@app.get("/users")
async def show_users(request: Request, bot_id: str = None, session_id: str = Cookie(None)):
    """Отображает страницу с пользователями"""
    auth = verify_session(session_id)
    
    # Получаем всех пользователей
    if bot_id and bot_id != "all":
        users = await db.get_all_generic_async("users", bot_id=bot_id)
    else:
        users = await db.get_all_generic_async("users")
    
    # Получаем список ботов для фильтрации
    bots = await db.get_all_generic_async("bots")
    
    return templates.TemplateResponse("users.html", {
        "request": request,
        "users": users,
        "bots": bots,
        "tariffs": tariffs,
        "selected_bot_id": bot_id,
        "is_authenticated": auth
    })


@app.post("/users/{user_id}/ban")
async def ban_user(user_id: int, auth: bool = Depends(require_auth)):
    """Блокирует/разблокирует пользователя"""
    try:
        # Получаем текущее состояние пользователя
        user = await db.get_one_generic_async("users", user_id=user_id)
        if not user:
            return {"error": "Пользователь не найден"}
        
        # Переключаем статус бана
        new_banned_status = 0 if user.get('banned', 0) == 1 else 1
        await db.update_generic_async("users", ["banned"], [new_banned_status], user_id=user_id)
        
        return RedirectResponse(url="/users", status_code=303)
    except Exception as e:
        return {"error": f"Ошибка при изменении статуса пользователя: {str(e)}"}


@app.post("/users/{user_id}/role")
async def change_user_role(user_id: int, role: str = Form(...), auth: bool = Depends(require_auth)):
    """Изменяет роль пользователя"""
    try:
        user = await db.get_one_generic_async("users", user_id=user_id)
        if not user:
            return {"error": "Пользователь не найден"}
        
        # Сбрасываем все роли
        await db.update_generic_async("users", ["is_admin", "is_moderator"], [0, 0], user_id=user_id)
        
        # Устанавливаем новую роль
        if role == "admin":
            await db.update_generic_async("users", ["is_admin"], [1], user_id=user_id)
        elif role == "moderator":
            await db.update_generic_async("users", ["is_moderator"], [1], user_id=user_id)
        # Если role == "user", роли остаются сброшенными
        
        return RedirectResponse(url="/users", status_code=303)
    except Exception as e:
        return {"error": f"Ошибка при изменении роли пользователя: {str(e)}"}


@app.post("/users/{user_id}/tariff")
async def change_user_tariff(user_id: int, tariff: str = Form(""), auth: bool = Depends(require_auth)):
    """Изменяет тариф пользователя"""
    try:
        user = await db.get_one_generic_async("users", user_id=user_id)
        if not user:
            return {"error": "Пользователь не найден"}
        
        # Если тариф пустой, устанавливаем NULL
        tariff_value = tariff if tariff else None
        await db.update_generic_async("users", ["tariff"], [tariff_value], user_id=user_id)
        return RedirectResponse(url="/users", status_code=303)
    except Exception as e:
        return {"error": f"Ошибка при изменении тарифа пользователя: {str(e)}"}


@app.post("/users/{user_id}/bot")
async def change_user_bot(user_id: int, bot_id: str = Form(""), auth: bool = Depends(require_auth)):
    """Изменяет бота пользователя"""
    try:
        user = await db.get_one_generic_async("users", user_id=user_id)
        if not user:
            return {"error": "Пользователь не найден"}
        
        if bot_id:
            # Получаем информацию о боте
            bot = await db.get_one_generic_async("bots", bot_id=int(bot_id))
            bot_username = bot.get('bot_username', '') if bot else ''
            await db.update_generic_async("users", ["bot_id", "bot_username"], [int(bot_id), bot_username], user_id=user_id)
        else:
            # Если бот не выбран, очищаем поля
            await db.update_generic_async("users", ["bot_id", "bot_username"], [None, None], user_id=user_id)
        
        return RedirectResponse(url="/users", status_code=303)
    except Exception as e:
        return {"error": f"Ошибка при изменении бота пользователя: {str(e)}"}


@app.post("/users/{user_id}/source")
async def change_user_source(user_id: int, source: str = Form(""), auth: bool = Depends(require_auth)):
    """Изменяет источник пользователя"""
    try:
        user = await db.get_one_generic_async("users", user_id=user_id)
        if not user:
            return {"error": "Пользователь не найден"}
        
        # Если источник пустой, устанавливаем NULL
        source_value = source if source else None
        await db.update_generic_async("users", ["source"], [source_value], user_id=user_id)
        return RedirectResponse(url="/users", status_code=303)
    except Exception as e:
        return {"error": f"Ошибка при изменении источника пользователя: {str(e)}"}


@app.get("/users/{user_id}/delete")
async def delete_user(user_id: int, auth: bool = Depends(require_auth)):
    """Удаляет пользователя"""
    try:
        await db.delete_generic_async("users", user_id=user_id)
        return RedirectResponse(url="/users", status_code=303)
    except Exception as e:
        return {"error": f"Ошибка при удалении пользователя: {str(e)}"}


@app.post("/products/{product_id}/reset-telegram-file")
async def reset_telegram_file_id(product_id: int, auth: bool = Depends(require_auth)):
    """Сбрасывает Telegram File ID продукта"""
    try:
        await db.update_generic_async("products", ["telegram_file_id"], [None], id=product_id)
        return RedirectResponse(url=f"/edit-product/{product_id}", status_code=303)
    except Exception as e:
        return {"error": f"Ошибка при сбросе Telegram File ID: {str(e)}"}


@app.post("/products/{product_id}/reset-telegram-video")
async def reset_telegram_video_id(product_id: int, auth: bool = Depends(require_auth)):
    """Сбрасывает Telegram Video ID продукта"""
    try:
        await db.update_generic_async("products", ["telegram_video_id"], [None], id=product_id)
        return RedirectResponse(url=f"/edit-product/{product_id}", status_code=303)
    except Exception as e:
        return {"error": f"Ошибка при сбросе Telegram Video ID: {str(e)}"}


@app.post("/products/{product_id}/reset-telegram-image")
async def reset_telegram_image_id(product_id: int, auth: bool = Depends(require_auth)):
    """Сбрасывает Telegram Image ID продукта"""
    try:
        await db.update_generic_async("products", ["telegram_image_id"], [None], id=product_id)
        return RedirectResponse(url=f"/edit-product/{product_id}", status_code=303)
    except Exception as e:
        return {"error": f"Ошибка при сбросе Telegram Image ID: {str(e)}"}


async def create_tables():
    await db.creator(table='products', column_types={'title': 'TEXT', 'description': 'TEXT', 'image': 'TEXT', 'video': 'TEXT', 'is_free': 'INTEGER',
                                               'price': 'INTEGER', 'discount': 'INTEGER', 'file_type': 'TEXT', 'product_bot': 'TEXT', 'path': 'TEXT', 'link': 'TEXT',
                                               'telegram_file_id': 'TEXT', 'telegram_video_id': 'TEXT', 'telegram_image_id': 'TEXT', 'unique_product_id': 'TEXT'})
    await db.creator(table='bots', column_types={'title': 'TEXT', 'bot_id': 'INTEGER', 'bot_token': 'TEXT', 'bot_username': 'TEXT'})
    await db.creator(table='users', column_types={'user_id': 'INTEGER', 'topic_id': 'INTEGER', 'username': 'TEXT',
                                               'first_name': 'TEXT', 'last_name': 'TEXT', 'source': 'TEXT', 
                                               'is_admin': 'INTEGER', 'is_moderator': 'INTEGER', 'banned': 'INTEGER',
                                               'tariff': 'TEXT', 'bot_username': 'TEXT', 'bot_id': 'INTEGER'})

if __name__ == "__main__":
    asyncio.run(create_tables())
    uvicorn.run(app, host="0.0.0.0", port=8010)