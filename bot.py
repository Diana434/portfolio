#!pip install spacy    
import spacy
import gensim
from sympy.physics.units import current
from songbase import WorkSQL
import urllib.request
urllib.request.urlretrieve('https://vectors.nlpl.eu/repository/20/180.zip', 'ruscorpora_upos_cbow_300_20_2019.zip')
import zipfile
import re

#загружаем векторную модель
src = 'ruscorpora_upos_cbow_300_20_2019.zip'
with zipfile.ZipFile(src, 'r') as zip_ref:
    zip_ref.extractall('.')
m = 'model.bin'

#0 - ждем запрос на песни
#1 - есть список песен
#2 - ждем ввода исполнителя
#3 - ждем ввода названия песни
#4 - ждем ввода текста

#класс, который определяет профиль текущего чата
class Chat_profile:

    #статус
    Status = 0
    #список найденных песен и исполнителей
    songlist = []
    #список песен в текстовом виде
    current_songs = 'Пустой список'
    #имя нового исполнителя
    newsinger = ''
    #имя новой песни
    newsong = ''
    #текст новой песни
    newtxt = ''


#класс, который определяет работу с чатами разных пользователей
class Chat:
    #словарь чатов, для каждого нового чата тут будет профиль и айди
    chat_list = {}

    #получить профиль чата по айди
    def get_prof(self, id):
        try:
            prof = self.chat_list[id]
        except KeyError:
            prof = Chat_profile()
            pass
        return prof

    #установить новый статус и обновить кнопки
    def setstatus(self, id, status):

        #получаем профиль, меняем статус в профиле
        prof = self.get_prof(id)
        prof.Status = status
        self.chat_list[id] = prof

        #обновляем кнопки в соответствии со статусом
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True) #клавиатура с кнопками
        start_button = types.KeyboardButton("Помощь")
        action_button = types.KeyboardButton("Список песен")
        add_button = types.KeyboardButton("Добавить песню")
        cancel_button = types.KeyboardButton("Отменить")
        if status == 0:
            markup.add(start_button, add_button)
        elif  status == 1:
            markup.add(start_button, action_button, add_button)
        elif status == 2 or status == 3 or status == 4:
            markup.add(cancel_button)
        return markup

    #получаем статус
    def getstatus(self, id):
        prof = self.get_prof(id)
        return prof.Status

    #устанавливаем для профиля список песен в списке и в текстовом виде
    def setsonglist(self, id, songlist, current_songs):
        prof = self.get_prof(id)
        prof.songlist = songlist
        prof.current_songs = current_songs
        self.chat_list[id] = prof

    #сохраняем ввод нового исполнителя
    def setnewsinger(self, id, newsinger):
        prof = self.get_prof(id)
        prof.newsinger = newsinger
        self.chat_list[id] = prof

    #сохраняем ввод новой песни
    def setnewsong(self, id, newsong):
        prof = self.get_prof(id)
        prof.newsong = newsong
        self.chat_list[id] = prof

    #получаем профиль
    def getprof(self, id):
        prof = self.get_prof(id)
        return prof

    #получаем список песен в текстовом виде
    def getcurrentsongs(self, id):
        prof = self.get_prof(id)
        return prof.current_songs

    #получем список исполнителей и песен
    def getsonglist(self, id):
        prof = self.get_prof(id)
        return prof.songlist


#загружаем векторную модель
rus_model = gensim.models.KeyedVectors.load_word2vec_format(m, binary=True)
#загружаем языковую модель
nlp = spacy.load("ru_core_news_sm")
#создаем переменную класса работы с базой
wsql = WorkSQL()
#содаем переменную работы с чатом
chat = Chat()

#находим похожие слова в модели
def similarity (mood, deep):
    sim_mood = []
    for w in mood:
        l = [(w, 10)]
        doc = nlp(w)
        #токенизируем слово, т.к. нам нужно слово с частью речи
        for token in doc:
            w1 = token.lemma_ + '_' + token.pos_
            w1 = w1.replace("ё", "е")
        if w1 in rus_model.index_to_key:
            for i in rus_model.most_similar(w1, topn=deep):
                #добавляем пять слов входящих в пять популярных в готовой модели
                l.append((i[0][:i[0].find("_")], i[1]))
        sim_mood.append(l)

    return sim_mood

#берем список слов, находим похожие, получаем список песен в базе
def gettext(txt):
    #создаем список слов
    mood = txt.split(' ')
    #устанавливаем глубину похожих 10
    deep = 10 #мб пять поставить
    #mood_n = []
    #for i in mood:
    #    mood_n.append(i)

    #находим похожие
    siml = similarity(mood, deep)

    #превращаем список похожих в текст для вывода
    resl = []
    for sl in siml: #берём каждый список для каждого слова
        tempstr = '' 
        for s in sl: #берём по одному слову среди похожих для одного слова
            tempstr += s[0] + ' ' #s[0] - исходное слово, s[1] - его часть речи
        resl.append(tempstr) #список из двух элементов, где просто длинные строки 

    #temps = wsql.songs(siml) # функция выдаёт список песен

    return resl, wsql.songs(siml)

# передаём значение переменной с кодом экземпляру бота
import telebot # импортируем telebot
from telebot import types # для определения типов
from keyboa import Keyboa

import random # для выбора случайного комплимента
# передаём значение переменной с кодом экземпляру бота
token = ('7296256234:AAEYZBPWaf-e2vl-8UlFuP89_Y5EPyf6mNw')
bot = telebot.TeleBot(token)



#создаем кнопки выбора песни
@bot.message_handler(commands=['set'])
def send_buttons(message: types.Message):
    #проверяем список
    bb = []
    #создаем список кнопок
    songlist = chat.getsonglist(message.chat.id)
    for i in range(len(songlist)):
        bb.append(str(i + 1))
    if len(bb) == 0:
        print('Список кнопок пустой')
        return
    #создаем клавиатуру
    kb = Keyboa(items=bb, copy_text_to_callback=True, items_in_row=4, alignment=False)
    #выводим
    bot.send_message(
        chat_id=message.chat.id, reply_markup=kb(),
        text="Выберете текст песни")

#показать текст песни по номеру
def show_song_text(chat, message, number1):
    #получаем список песен из  профиля
    songlist = chat.getsonglist(message.chat.id)
    number = int(number1) - 1

    #проверяем на корректность списка
    if number < 0 or number >= len(songlist):
        bot.send_message(message.chat.id, text="Некорректный номер песни")
        return '', '', "Не могу найти"
    if len(songlist) == 0:
        return '', '', "Список песен пустой"

    #получаем из списка исполнителя и песню
    singer = songlist[number][0]
    song = songlist[number][1]

    #делаем запрос в базу на текст песни
    txt = wsql.getsong(singer, song)
    #если песня найдена - выводим
    if message.text == '':
        bot.send_message(message.chat.id, 'Песня в списке найденных')
    else:
        bot.send_message(message.chat.id, text='<b>' + singer + '\n' + song + '</b>' + '\n' + txt, parse_mode="HTML")

#отрабатываем нажатие кнопки выбора песни
@bot.callback_query_handler(func=lambda call: call.data.isdigit())
def save_btn(call):
    message = call.message
    show_song_text(chat, message, int(call.data))


# хендлер и функция для обработки команды /start
@bot.message_handler(commands=['start'])
def start_message(message):
    markup = chat.setstatus(message.chat.id, 0)
    bot.send_message(message.chat.id, text="Привет, {0.first_name}!💘\nЭтот бот - твой помощник в составлении плейлиста, соответствующего твоему настроению.\
    Со мной ты получишь подходящий плейлист, а также сможешь добавлять в базу данных новые песни, чтобы я мог развиваться.\
    \nЧерез пробел введи несколько слов, описывающих твоё настроение, а я найду подходящие песни!".format(message.from_user), reply_markup=markup)

#включение статуса ввода песни
@bot.message_handler(commands=['add'])
def add_song(message):
    #ставим статус
    markup = chat.setstatus(message.chat.id, 2) #делает кнопки, единственная - отменить
    #выводим подсказки
    bot.send_message(message.chat.id, text="Добавление новую песню в базу", reply_markup=markup)
    bot.send_message(message.chat.id, text="Введи исполнителя", reply_markup=markup)

def mes_is_ok(message):
    print("luuuuu")
    if not message:
        return False
    message = str(message)
    return bool(re.fullmatch(r'^[a-zA-Zа-яА-Я0-9 ]+$', message))

#отработка ввода текста
@bot.message_handler(content_types=['text'])
def process_text(message):
    #получаем статус профиля
    status = chat.getstatus(message.chat.id)
    #если один из статусов - ввод добавления - отрабатываем ввод
    if status == 2 or status == 3 or status == 4:
        #если нажали кнопку отменить - возвращаем статус поиска песен
        if message.text == 'Отменить':
            markup = chat.setstatus(message.chat.id, 0)
            bot.send_message(message.chat.id, text='Ввод песни отменён. Если ты хочешь добавить песню, введи команду /add\nЕсли ты хочешь получить список песен, то через пробел введи несколько слов, описывающих твоё настроение', reply_markup=markup)
        #если введен текст
        else:
            #если был статус - ввод исполнителя
            if status == 2:
                #меняем статус на ввод названия
                chat.setstatus(message.chat.id, 3)
                #запоминаем исполнителя,
                chat.setnewsinger(message.chat.id, message.text)
                bot.send_message(message.chat.id, text='Введи название песни')
                # ставим статус ввода названия
                chat.setstatus(message.chat.id, 3)
            #статус - ввод названия
            if status == 3:
                #запоминаем название
                chat.setnewsong(message.chat.id, message.text)
                # меняем статус на ввод текста
                bot.send_message(message.chat.id, text='Введи текст песни')
                chat.setstatus(message.chat.id, 4)
            # статус - ввод текста
            if status == 4:
                #ставим статус - поиск песен
                markup = chat.setstatus(message.chat.id, 0)
                #добавляем запись в базу данных
                prof = chat.getprof(message.chat.id)
                if wsql.add_song(prof.newsinger, prof.newsong, message.text):
                    bot.send_message(message.chat.id, text='Песня успешно добавлена в базу', reply_markup=markup)
                else:
                    bot.send_message(message.chat.id, text='Ошибка добавления в базу, возможно эта песня уже существует', reply_markup=markup)
#исполнитель и названия уникальны, мы не можем вводить одно и то же несколько раз


    #если статус - поиск песен
    if status == 0 or status == 1:
        #проверим, что в сообщении пользователя есть только буквы, цифры и пробелы
        if not mes_is_ok(message.text):
            bot.send_message(message.chat.id, text="Пожалуйста, вводи только буквы и цифры.")
            return
        #отрабатываем запрос о помощи
        if (message.text == "Помощь"):
            #chat.setstatus(message.chat.id, 0)
            bot.send_message(message.chat.id, text="/start для перезапуска бота\n/add для добавления новой песни")
        #запрос списка
        elif (message.text == "Список песен"):
            if chat.getstatus(message.chat.id) == 1:
#если пользователь забыл какие у него песни
                bot.send_message(message.chat.id, text = chat.getcurrentsongs(message.chat.id))
                send_buttons(message)
            else:
                bot.send_message(message.chat.id, text="Список песен не сформирован, введите пару слов, описывающих ваше настроение, и я подберу плейлист!")
        #переводим в режим добавления песни
        elif (message.text == "Добавить песню"):
            add_song(message)
        #отрабатываем режим отмены
        elif (message.text == "Отмена"):
            add_song(message)
        #отрабатываем нажатие цифры, которое будет выбором песни из списка найденных
        elif message.text.isdigit(): #если сообщение - цифра
            if chat.getstatus(message.chat.id) == 1:
                show_song_text(chat, message, message.text)
            else:
                bot.send_message(message.chat.id, text="Список песен не сформирован")
        #отрабатываем ввод текст, по нему будем искать список песен
        else:
            #находим список песен и служебной информации
            markup = chat.setstatus(message.chat.id, 1)
            lwords, lsongs = gettext(message.text)
            bot.send_message(message.chat.id, text="Списки похожих слов, по которым я более точно нахожу песни:", reply_markup=markup)

            for txt in lwords:
                if txt != '':
                    bot.send_message(message.chat.id, text=txt, reply_markup=markup)

            #если список не пустой - формируем список песен
            if len(lsongs) != 0:
                bot.send_message(message.chat.id, text=f"Я упорядочил песни по убыванию их рейтинга, оценивающего соответствие введённым словам\n{lsongs}", reply_markup=markup)
                print(wsql.songlist)
                chat.setsonglist(message.chat.id, wsql.songlist, wsql.current_songs)
                # рисуем кнопки
                send_buttons(message)
            else:
                markup = chat.setstatus(message.chat.id, 0)
                bot.send_message(message.chat.id, text="Я не смог найти песни по данным словам ((", reply_markup=markup)

#запускаем бот
print("start")
bot.polling(none_stop=True, interval=0)