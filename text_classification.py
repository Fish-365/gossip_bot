import asyncio
import os
import torch.nn.functional as F

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
from transformers import BertTokenizer, BertForSequenceClassification

async def classify_text(text):
    """
    Асинхронная функция для классификации текста.

    Аргументы:
    text (str): Текст для классификации.

    Возвращает:
    float: Вероятность токсичности текста.
    """
    # загрузка токенизатора и весов модели
    tokenizer = BertTokenizer.from_pretrained('s-nlp/russian_toxicity_classifier')
    model = BertForSequenceClassification.from_pretrained('s-nlp/russian_toxicity_classifier')

    # подготовка входных данных
    batch = tokenizer.encode(text, return_tensors='pt')

    # инференс
    outputs = model(batch)
    logits = outputs.logits

    # преобразование логитов в вероятности
    probs = F.softmax(logits, dim=-1)

    # возвращение результата
    return probs[0][1].item()