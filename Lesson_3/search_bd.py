import os
from pprint import pprint

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv("../.env")
MONGO_HOST = os.getenv("MONGO_HOST", None)
MONGO_PORT = int(os.getenv("MONGO_PORT", None))
MONGO_DB = os.getenv("MONGO_DB", None)
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", None)

def print_mongo_docs(cursor):
    for doc in cursor:
        pprint(doc)

def search_vacansy(search_val = 0, by_agreement = False):
    with MongoClient(MONGO_HOST, MONGO_PORT) as client:
        db = client[MONGO_DB]
        collection = db[MONGO_COLLECTION]

        if by_agreement == True:
            cursor = collection.find({
                'by_agreement': True
            })
            print_mongo_docs(cursor)
        else:
            cursor = collection.find({
                'salary_min': {'$gte': search_val}
            })
            print_mongo_docs(cursor)


if __name__ == '__main__':
    try:
        # by_agreement - флаг, который указывает на вакансии без указанной заработной платы
        by_agreement = input('Пожалуйста, набирите "1" - если хотите увидеть вакансии'
                                 ' без указаной заработной платы или оставьте поле пустым: ')
        if by_agreement == '1':
            by_agreement = True
            search_vacansy(by_agreement=by_agreement)
        else:
            search_val = int(input('Введите желаемую сумму заработной платы: '))
            search_vacansy(search_val=search_val)
    except ValueError:
        print('Сумму заработной платы - нужно водить только цифрами.')



