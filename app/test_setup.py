from app.models import User, Thread, ChatMessage
from app.crud import create_user, create_thread, create_message, get_thread_history

user = create_user(User(username="test_user"))
print("Created user:", user)

thread = create_thread(Thread(user_id=user.id, title="Test Chat"))
print("Created thread:", thread)

create_message(ChatMessage(thread_id=thread.id, sender="user", content="my name is Rania"))
create_message(ChatMessage(thread_id=thread.id, sender="bot", content="Nice to meet you, Rania!"))

history = get_thread_history(thread.id)
print("History:", history)