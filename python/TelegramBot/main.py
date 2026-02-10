import pandas as pd
import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import time
# передаём значение переменной с кодом экземпляру бота
from telebot import types # для определения типов
import spacy
import ru_core_news_sm
from keybert import KeyBERT
import sqlite3


#класс парсинга сайта с текстами песен
class MyParsing:
    #открываем сессию, создаем агента для открытия
    session = requests.session()
    ua = UserAgent()
    headers = {'User-Agent': ua.random}
    #создаем списки название групп
    list_group_name = []
    #ссылка на страницу группы
    list_group_link = []
    #имя сайта
    url = "https://www.beesona.pro"
    #список первых букв для страниц со списками исполнителей
    letters = ['a', 'b', 'v', 'g', 'd','e', '', 'z', 'z', 'i', '', 'k', 'l', 'm', 'n', 'o', 'p', 'r', 's', 't', 'u', 'f', 'h', 't', 'c', 's', 'e',  'y', 'y']
    #загружаем языковую модель
    nlp = spacy.load("ru_core_news_sm")
    nlp = ru_core_news_sm.load()
    #создаем модель для определения ключевых слов
    kw_model = KeyBERT()

    #парсим страницу с названиями исполнителей, аргумент - номер страницы
    def parse_page(self, page_number):
        try:
            #получаем адрес и текст
            namestr = self.url + '/songs/?first_letter=' + str(page_number)
            print(namestr)
            response = self.session.get(namestr, headers=self.headers)
        except Exception as e:
            print(e)
            return False
        txt = response.text
        #разбираем html текст
        soup = BeautifulSoup(txt, 'html.parser')

        #находим ссылки на странице
        for post in soup.find_all('a', )[:1000]:
            #если есть атрибут ссылки и определенный текст - это ссылка на страницу исполнителя
            if 'href' in post.attrs:
                href = post.attrs['href']
                if '?first_letter' in href:
                    continue
                #ищем ссылки с песнями с началом на определенную букву
                if 'songs/' + self.letters[page_number - 1] in href:
                    #добавляем имя и ссылку на исполнителя в список
                    self.list_group_name.append(post.text)
                    self.list_group_link.append(href)

        return True

    #парсим страницы исполнителей
    def parse_songs(self):

        #получаем ссылки страницы групп из файла
        df = pd.read_csv('qw/data.csv')
        #создаем пустые списки на ссылки
        lgroup = []
        lsong = []

        #перебираем датафрейм ссылок
        for index, row in df.iterrows():

            #получаем содержимое страницы
            try:
                response = self.session.get(self.url + row['Link'], headers=self.headers)
            except Exception as e:
                print(e)  #
            txt = response.text
            #парсим страницу
            soup = BeautifulSoup(txt, 'html.parser')
            #определяем сслыки на песни, добавляем в список
            for post in soup.find_all('a', {'class': 'blueBig'})[:1000]:
                if 'href' in post.attrs:
                    href = post.attrs['href']
                    lgroup.append(row['Name'])
                    lsong.append(href)
            print(lgroup)
            print(lsong)
            time.sleep(1)
            #сохраняем песни в файл
            data = {'Name': lgroup, 'Link': lsong}
            df = pd.DataFrame(data)
            df.to_csv("data_song_names.csv", sep=',', index=False, encoding='utf-8')
        return True

    #создание списка на ссылки исполнителей
    def create_list_group(self):

        #перебираем страницы со списками исполнителей
        for i in range(1, 30):
            self.parse_page(i)
        #сохраняем данные в файл
        data = {'Name': self.list_group_name, 'Link': self.list_group_link}
        df = pd.DataFrame(data)
        df.to_csv("data.csv", sep=',', index=False, encoding='utf-8')

    #парсинг страниц с текстами песен
    def parse_text(self):
        #получаем датафрейм с ссылками на страницы
        df = pd.read_csv('qw/data_song_names.csv')
        #перебираем датафрейм
        for index, row in df.iterrows():

            #получаем содержимое страницы с песней
            try:
                response = self.session.get(self.url + row['Link'], headers=self.headers)
            except Exception as e:
                print("Ошибка")
                print(e)
            txt = response.text
            #парсим
            soup = BeautifulSoup(txt, 'html.parser')
            songname = ''
            #находим контейнер с тектом
            for post in soup.find_all('div', {'class': 'copys'})[:1000]:
                #внутри контейнера находим текст
                for s in post.children:
                    soup1 = BeautifulSoup(str(s), 'html.parser')
                    for post1 in soup1.find_all('b', {'class': 'm153'})[:1000]:
                        #print('*'*10)
                        songname = post1.text
                        #print('*' * 10)

            #преобразуем текст в строку с разделителями
            stext = ''
            for post in soup.find_all('div', {'class': 'm207'})[:1000]:
                for s in post.children:
                    if s.text and not '@' in s.text:
                        qw = 0
                        stext = stext + s.text + '\n'

            #получаем лемматиризованный текст песни
            ltext = ''
            doc = self.nlp(stext)
            for w in doc:
                if w.lemma_ == '-':
                    continue
                temp = str(w.pos_)
                if  temp !='SPACE' and temp != 'PUNCT':
                    ltext = ltext + w.lemma_ + ' '
            #print(stext)
            #print(ltext)

            #получаем лемматизированное название песни
            lsongname = ''
            doc = self.nlp(songname)
            for w in doc:
                if w.lemma_ == '-':
                    continue
                temp = str(w.pos_)
                if temp != 'SPACE' and temp != 'PUNCT':
                    lsongname = lsongname + w.lemma_ + ' '
            #print(lsongname)

            #находим ключевые слова из текста песни
            ktext = ''
            for d in (self.kw_model.extract_keywords(ltext)):
                ktext += d[0] + ' '

            #создаем строку запрос для добавления в БД
            strsql = "INSERT INTO Main (singer, song, lemmasong, text, lemmatext, keywords) VALUES ('{singer}','{song}','{lemmasong}', '{text}', '{lemmatext}', '{keywords}')".format(
                    singer = row['Name'],
                    song = songname,
                    lemmasong = lsongname,
                    text = stext,
                    lemmatext = ltext,
                    keywords = ktext
                    )

            #добавляем строку в таблицу БД
            con = sqlite3.connect("pp.db")
            cursor = con.cursor()
            try:
                cursor.execute(strsql)
            except Exception as e:
                print("Ошибка")
                print(e)
            con.commit()
            #делаем паузу, чтобы не забанили на сайте
            time.sleep(0.5)