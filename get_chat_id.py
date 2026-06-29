import requests

token = "7442502216:AAGvBUH02GqqkpArydFKs3Z18xM8p5nzhLc"
url = f"https://api.telegram.org/bot{token}/getUpdates"
resp = requests.get(url, timeout=10)
data = resp.json()

if data.get("result"):
    for u in data["result"]:
        msg = u.get("message", {})
        chat = msg.get("chat", {})
        chat_id = chat.get("id")
        name = chat.get("first_name", "?")
        text = msg.get("text", "")
        print(f"Chat ID: {chat_id}  Name: {name}  Text: {text}")
else:
    print("No messages found. Send a message to the bot first.")
