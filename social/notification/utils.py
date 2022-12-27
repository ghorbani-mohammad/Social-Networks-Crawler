import requests


def telegram_text_purify(text: str):
    return text.replace("#", "-").replace("&", "-")


def telegram_bot_send_text(token, chat_id, message):
    send_text = (
        "https://api.telegram.org/bot"
        + token
        + "/sendMessage?chat_id="
        + chat_id
        + "&text="
        + message
        + "&parse_mode=html"
    )
    response = requests.get(send_text)
    return response.json()
