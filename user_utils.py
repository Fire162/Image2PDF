import requests

def upload_file(file_path):
    url = "https://file.io/"

    try:
        with open(file_path, "rb") as file:
            files = {"file": file}
            response = requests.post(url, files=files)
            if response.status_code == 200:
                return response.json()["link"]
            else:
                return None
    except Exception as e:
        return None
def check_user(channel_array, user_id,bot):
    joined = True
#    return True
    for chat_id in channel_array:
        try:
            i = bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        except:
            bot.send_message(chat_id=5797764799, text=f'Bot is not Admin in {chat_id}')
            joined = False
            break
        if i.status in ['kicked', 'left']:
            joined = False
            break
    return joined
