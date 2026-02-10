import sqlite3
from spacy.lang.en.tokenizer_exceptions import string
#from tabulate import tabulate
import pandas as pd
import spacy
import ru_core_news_sm
from keybert import KeyBERT


class WorkSQL:

    songlist = []
    current_songs = 'Пустой список'

    def query(self, cur, lwords):

        tempdf = pd.DataFrame(columns=['Group', 'Name', 'Text', 'Rate'])

        #qtxt = "SELECT Singer, Song, Keywords, LemmaSong, Text, LemmaText from main WHERE (1=1)"
        qtxt = "SELECT Singer, Song, LemmaText, Keywords, LemmaSong from main WHERE (1=2)"

        for lword in lwords:
            w1 = '% ' + lword[0] + ' %'
            w2 = lword[0] + ' %'
            w3 = '% ' + lword[0]
            w4 = lword[0]
            qtxt += " or (LemmaSong Like '{w1}') or (LemmaSong Like '{w2}') or (LemmaSong Like '{w3}') or (LemmaSong = 'w4')".format(w1=w1, w2=w2, w3=w3, w4=w4)
            qtxt += " or (Keywords Like '{w1}') or (Keywords Like '{w2}') or (Keywords Like '{w3}') or (Keywords = 'w4')".format(w1=w1, w2=w2, w3=w3, w4=w4)
            qtxt += " or (LemmaText Like '{w1}') or (LemmaText Like '{w2}') or (LemmaText Like '{w3}') or (LemmaText = 'w4')".format(w1=w1, w2=w2, w3=w3, w4=w4)
        cur.execute(qtxt)
        for ll in cur.fetchall():
            rating = 0
            for lword in lwords:
                ww = lword[0]
                rr = lword[1]
                temp = str(ll[2]).count(ww)*rr + str(ll[3]).count(ww) * 5 * rr + str(ll[4]).count(ww) * 10 * rr
        #сколько раз встречается в лем. тексте + сколько раз встречается в ключ. словах * 5 + сколько встречается в названии * 10        
                rating += temp #общий рейтинг песни по всем введённым словам

            rating = round(rating, 2)
            new_row = {'Group': ll[0],'Name': ll[1],'Text': ll[2],'Rate': rating}
            tempdf.loc[len(tempdf)] = new_row
        tempdf.sort_values(by=['Rate'], ascending=False, inplace=True)
        tempdf = tempdf[:500]
        tempdf = tempdf.drop("Text", axis=1)


        return tempdf

    def songs(self, ls):


        con = sqlite3.connect('pp.db')  # подключение
        cur = con.cursor()  # курсор

        df = pd.DataFrame(columns=['Group', 'Name', 'Text', 'Rate'])
        for l1 in ls:
            df1 = self.query(cur, l1)
            if ls.index(l1) == 0:
                df = df1
            else:
                df = df.merge(df1, on=None, how='inner', left_on=['Group', 'Name'], right_on=['Group', 'Name'], sort=True)
        con.close()

        templ = []

        for index, row in df.iterrows():
            r = 0
            for i in range(2, len(row)):
                r += row.iloc[i]
            templ.append(r)
        df['Rating'] = templ

        #str = ta bulate(df, headers='keys', tablefmt='plain', showindex=False)
        #print(str)
        df.sort_values(by=['Rating'], ascending=False, inplace=True)

        self.songlist = []

        ct = 1
        str1 = ''
        for index, row in df[:20].iterrows():
            str1 += str(ct) + ' ' +  row['Group']+ '; ' + row['Name'] + ': ' + str(int(row['Rating'])) + '\n'
            self.songlist.append((row['Group'], row['Name']))
            ct += 1
        #str = tabulate(df[:20], headers='keys', tablefmt='plain', showindex=False)

        self.current_songs = str1

        return str1

    def getsong(self, singer, song):

        con = sqlite3.connect('pp.db')  # подключение
        cur = con.cursor()  # курсор

        qtxt = "SELECT Text FROM Main WHERE Singer LIKE '{w1}' and Song LIKE '{w2}'".format(w1 = singer, w2 = song)
        cur.execute(qtxt)
        res = str(cur.fetchone()[0])
        con.close()
        return res

    def add_song(self, singer, songname, stext):

        # загружаем языковую модель
        nlp = spacy.load("ru_core_news_sm")
        nlp = ru_core_news_sm.load()
        # создаем модель для определения ключевых слов
        kw_model = KeyBERT()

        # получаем лемматиризованный текст песни
        ltext = ''
        doc = nlp(stext)
        for w in doc:
            if w.lemma_ == '-':
                continue
            temp = str(w.pos_)
            if temp != 'SPACE' and temp != 'PUNCT':
                ltext = ltext + w.lemma_ + ' '

        # получаем лемматизированное название песни
        lsongname = ''
        doc = nlp(songname)
        for w in doc:
            if w.lemma_ == '-':
                continue
            temp = str(w.pos_)
            if temp != 'SPACE' and temp != 'PUNCT':
                lsongname = lsongname + w.lemma_ + ' '

                # находим ключевые слова из текста песни
        ktext = ''
        for d in (kw_model.extract_keywords(ltext)):
            ktext += d[0] + ' '

        # создаем строку запрос для добавления в БД
        strsql = "INSERT INTO Main (singer, song, lemmasong, text, lemmatext, keywords) VALUES ('{singer}','{song}','{lemmasong}', '{text}', '{lemmatext}', '{keywords}')".format(
            singer=singer,
            song=songname,
            lemmasong=lsongname,
            text=stext,
            lemmatext=ltext,
            keywords=ktext
        )


        # добавляем строку в таблицу БД
        con = sqlite3.connect("pp.db")
        cursor = con.cursor()
        try:
            cursor.execute(strsql)
        except Exception as e:
            print("Ошибка")
            print(e)
            return False
        con.commit()
        return True
    
    def delete_song(self, singer, song):
        con = sqlite3.connect("pp.db")  # Подключаемся к базе данных
        cursor = con.cursor()

        try:
            # SQL-запрос для удаления песни
            query = "DELETE FROM Main WHERE Singer = ? AND Song = ?"
            cursor.execute(query, (singer, song))
            con.commit()  # Сохраняем изменения
            print(f"Песня '{song}' исполнителя '{singer}' удалена.")
            return True
        except Exception as e:
            print(f"Ошибка при удалении песни: {e}")
            return False
        finally:
            con.close()