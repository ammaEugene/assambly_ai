import os
from openai import OpenAI
from gtts import gTTS
import pygame

openai_api_key = ""

# Инициализируем клиент OpenAI
client = OpenAI(api_key=openai_api_key)

# Инициализируем pygame для воспроизведения аудио
pygame.mixer.init()

# Системные сообщения
system_prompt_1 = """
Ты консультант компании интернет-провайдера Триолан.
Действуй как профессионал, будь вежливым.
Отвечай кратко и веди себя как человек. Не задавай более одного вопроса за раз!
Ты звонишь людям с опросом о продвижении рекламной продукции.
Сначала представься (имя придумай самостоятельно) и назови цель своего звонка.
Ты должен выяснить, видел ли клиент нашу рекламу, и если видел, то где.
Места, где потенциально могла быть реклама: билборды, в почтовом ящике, в подъезде на оборудовании Триолан, в интернете.
Не называй места, где потенциально может быть реклама, пока клиент этого не попросит.
После того, как ты узнал, где клиент видел нашу рекламу, вежливо попрощайся.
"""

system_prompt_2 = """
Ты клиентка компании Триолан, тебе позвонили спросить, где ты видела рекламу компании в последний месяц. Места, где ты потенциально мог видеть рекламу: билборды, в своем почтовом ящике, в подъезде на оборудовании Триолан, в интернете или нигде не видел. Отвечай на вопросы четко и кратко.
НЕ ПРИВЕТСТВУЙ, ПОТОМУ ЧТО ТЫ УЖЕ ЭТО СДЕЛАЛ, НО НЕ ПОМНИШЬ ЭТОГО!
"""

farewell_phrases = ["до свидания", "спасибо за ответ", "всего доброго", "спасибо за информацию"]

def contains_farewell(text):
    return any(phrase.lower() in text.lower() for phrase in farewell_phrases)

def dialog():
    current_prompt = system_prompt_1
    user_response_text = ""
    while True:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": current_prompt},
                {"role": "user", "content": user_response_text}
            ],
            model="gpt-3.5-turbo",
        )
        system_response_text = response.choices[0].message.content.strip()

        print(f"Модель 1: {system_response_text}")
        tts = gTTS(text=system_response_text, lang='ru')
        tts.save("model_1.mp3")
        pygame.mixer.music.load("model_1.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            continue

        if contains_farewell(system_response_text):
            print("Диалог завершен.")
            break

        current_prompt = system_prompt_2 if current_prompt == system_prompt_1 else system_prompt_1
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": current_prompt},
                {"role": "user", "content": system_response_text}
            ],
            model="gpt-3.5-turbo",
        )
        user_response_text = response.choices[0].message.content.strip()

        print(f"Модель 2: {user_response_text}")
        tts = gTTS(text=user_response_text, lang='ru')
        tts.save("model_2.mp3")
        pygame.mixer.music.load("model_2.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            continue

        if contains_farewell(user_response_text):
            print("Диалог завершен.")
            break

if __name__ == "__main__":
    dialog()