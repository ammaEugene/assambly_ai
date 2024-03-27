import os
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import storage
from openai import OpenAI
import openpyxl
from collections import Counter
from datetime import datetime

API_KEY = ''

# Функции для транскрибирования и анализа аудио
def transcribe_and_analyze(audio_uri, sample_rate_hertz, prompts):
    transcripts = transcribe_audio(audio_uri, sample_rate_hertz)
    dialog = ' '.join(transcripts)
    print(f"Транскрибированный диалог: {dialog}")
    analyzed_result = analyze_dialog(dialog, prompts)
    print(f"Результат анализа: {analyzed_result}")
    return analyzed_result, dialog

def analyze_dialog(dialog, prompts):
    client = OpenAI(api_key=API_KEY)

    messages = [{"role": "user", "content": dialog}]
    for prompt in prompts:
        messages.append({"role": "assistant", "content": prompt})

    chat_completion = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        max_tokens=100
    )

    return chat_completion.choices[0].message.content.strip()

def transcribe_audio(audio_uri, sample_rate_hertz):
    try:
        client = speech.SpeechClient()
    except exceptions.DefaultCredentialsError as e:
        print("Ошибка авторизации. Убедитесь, что переменная среды GOOGLE_APPLICATION_CREDENTIALS указывает на корректный файл ключа JSON.")
        raise e

    audio = speech.RecognitionAudio(uri=audio_uri)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=sample_rate_hertz,
        language_code="uk-UA",
    )

    operation = client.long_running_recognize(config=config, audio=audio)
    response = operation.result()
    transcripts = []
    for result in response.results:
        transcripts.append(result.alternatives[0].transcript)

    return transcripts

def get_sample_rate(audio_uri):
    return 8000

# Переменные среды
bucket_name = "own_audio_bucket"
audio_directory = "oprosnik"

# Получение списка аудиофайлов в бакете
storage_client = storage.Client()
bucket = storage_client.get_bucket(bucket_name)
blob_list = bucket.list_blobs(prefix=audio_directory)
audio_files = []
for blob in blob_list:
    if blob.name.endswith(".WAV"):
        audio_files.append("gs://" + bucket_name + "/" + blob.name)

# Создаем новую книгу Excel
now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
workbook_name = f"results_{now}.xlsx"
workbook = openpyxl.Workbook()
worksheet = workbook.active

# Добавляем заголовки столбцов
worksheet['A1'] = 'Аудиофайл'
worksheet['B1'] = 'Транскрибированный диалог'
worksheet['C1'] = 'Результат анализа'

# Счетчик для номера строки
row_num = 2

# Словарь для хранения источников информации
info_sources = Counter()

# Промпты, основанные на возможных источниках информации о компании
prompts = [
    "По вашему ответу, абонент мог узнать о компании Triolan из наклеек в доме.",
    "По вашему ответу, абонент мог узнать о компании Triolan из бумажного буклета в доме.",
    "По вашему ответу, абонент мог узнать о компании Triolan из табличек на подъездах.",
    "По вашему ответу, абонент мог узнать о компании Triolan с билборда на улице.",
    "По вашему ответу, абонент мог узнать о компании Triolan из рекламы на YouTube.",
    "По вашему ответу, абонент мог узнать о компании Triolan с авто сотрудника на улице.",
    "По вашемему ответу, абонент мог узнать о компании Triolan по форме сотрудника на улице.",
    "По вашему ответу, абонент мог узнать о компании Triolan из окружного ТГ канала.",
    "По вашему ответу, абонент мог узнать о компании Triolan из ФБ.",
    "По вашему ответу, абонент мог узнать о компании Triolan из бумажного буклета на улице."
]

print(f"Найдено {len(audio_files)} аудиофайлов для обработки.")

for i, audio_file in enumerate(audio_files, start=1):
    sample_rate = get_sample_rate(audio_file)
    analyzed_result, dialog = transcribe_and_analyze(audio_file, sample_rate, prompts)

    # Запись результатов в таблицу Excel
    worksheet[f'A{row_num}'] = audio_file
    worksheet[f'B{row_num}'] = dialog
    worksheet[f'C{row_num}'] = analyzed_result

    # Извлечение источника информации из результата анализа
    for source in prompts:
        if source in analyzed_result:
            info_source = source.split(',')[0].split('По вашему ответу, абонент мог узнать о компании Triolan из')[-1].strip()
            worksheet[f'D{row_num}'] = info_source
            info_sources[info_source] += 1
            break
    else:
        worksheet[f'D{row_num}'] = 'Неизвестно'
        info_sources['Неизвестно'] += 1

    row_num += 1

# Сохранение книги Excel
workbook.save(workbook_name)
print(f"Результаты сохранены в файл: {workbook_name}")

# Вывод статистики источников информации
print("\nСтатистика источников информации:")
for source, count in info_sources.items():
    print(f"{source}: {count}")
    