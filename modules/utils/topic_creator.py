from modules.bot.bot import bot
from modules.utils import db
from modules.configs.config import SUPER_GROUP_ID, USE_SUPER_GROUP


async def create_topic(user_id):
    
    if USE_SUPER_GROUP:
        
        try:
            
            user_data = await db.get_one_generic_async(table='users', user_id=user_id)
            topic_id = user_data['topic_id']
            
            if not topic_id:
                
                full_name = (
                    user_data['first_name'] or
                    user_data['username'] or
                    f'{user_id}'
                )
                
                topic_name = f'{full_name} [ID: {user_id}]'
                
                # Создаём новую тему
                created_topic = await bot.create_forum_topic(
                    chat_id=SUPER_GROUP_ID,
                    name=topic_name
                )
                
                topic_id = created_topic.message_thread_id
                
                await db.update_generic_async(columns=['topic_id'], values=[topic_id], table='users', user_id=user_id)
        
        except Exception as e:
            print(f"Ошибка при создании темы для пользователя {user_id}: {e}")
        
    