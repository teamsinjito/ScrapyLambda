# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import psycopg2
from PIL import Image
from io import BytesIO
import urllib.request
import base64
import requests
import boto3
import re
from janome.tokenizer import Tokenizer

class SinjitopicsScrapyPipeline:
    
    ############################################################################
    ###
    ###記事の独自タブIDを返却
    ###
    ############################################################################        
    def getTabId(tabName):
        if tabName == "国内":
            return 1
        elif tabName == "国際":
            return 2
        elif tabName == "経済":
            return 3
        elif tabName == "IT":
            return 4
        elif tabName == "スポーツ":
            return 5
        elif tabName == "エンタメ":
            return 6
        else:
            return 0


    ############################################################################
    ###
    ###記事本文の配列を連結
    ###
    ############################################################################             
    def linkingText(ary):
        print('記事本文の配列を連結開始')
        mojiretu = ''
        for val in ary:
            if val != '\n':
                mojiretu += val
                
        mojiretu.replace('\u3000', ' ')
        return mojiretu  

    

    ############################################################################
    ###
    ###記事に画像が存在していない場合,""を返す
    ###
    ############################################################################    
    def checkExistImage(img):
        
        if img is None:
            return ""
        else:
            #Base64型で返す
            file = base64.b64encode(requests.get(img).content).decode('utf-8')
            bmg = 'data:image/jpeg;base64,' + str(file)
            return bmg


    ############################################################################
    ###
    ###画像サイズからサムネイルIDを取得
    ###
    ############################################################################      
    def setThumbnailGid(img):
        
        #画像があるかどうか
        if img is None:
            return 4
        else:
            file = BytesIO(urllib.request.urlopen(img).read())
            im = Image.open(file)
            width = im.width
            height = im.height
            
            #縦幅、横幅からサムネイルIDを決定
            if height >= width:
                return 3
            elif width / height >= 2:
                return 2
            else:
                return 1


    ############################################################################
    ###
    ###アニメーションIDを取得
    ###
    ############################################################################           
    def setAnimationGid():
        return 1 


    ############################################################################
    ###
    ###取得した配信日を
    ###
    ############################################################################    
    def setUploadDateTime(dt):
        upload = ''
        for d in dt:
            upload += d
        upload += ' 配信'
        
        return upload
      
     
    ############################################################################
    ###
    ###DBへ保存
    ###
    ############################################################################    
    def saveDataBase(item):
        
        print('DBへ保存開始')
        connection = psycopg2.connect(
            host = "sinjitopics-db.cacctcmaatmb.ap-northeast-1.rds.amazonaws.com",
            port = "5432",
            dbname = "postgres",
            user = "posgres",
            password = "password"
        )
        cur = connection.cursor()
        
        #DBに登録されていれば保存処理は行わない
        cur.execute("select count(id) from topics where id ='" + item['id'] + "'")
        
        #DBに登録されていなければ保存
        for row in cur:
            exts = row[0]
        if exts == 0:
    
            cur.execute(
               'INSERT INTO topics (id,tab_id,title,text,owner,url,image,thumbnail_gid,animation_gid,music_gid,upload,created_at,updated_at)'+ 
               'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', 
               (
                    item['id'],
                    item['tab_id'],
                    item['title'],
                    item['text'],
                    item['owner'],
                    item['url'],
                    item['image'],
                    item['thumbnail_gid'],
                    item['animation_gid'],
                    item['music_gid'],
                    item['upload'],
                    item['created_at'],
                    item['updated_at']
                )
            )
            
            connection.commit()
        connection.close()
        
        return item
    
        
    ############################################################################
    ###
    ###2日前の記事をDBから削除
    ###
    ############################################################################    
    def deleteDatabase(preDate):
        
        connection = psycopg2.connect(
            host = "sinjitopics-db.cacctcmaatmb.ap-northeast-1.rds.amazonaws.com",
            port = "5432",
            dbname = "postgres",
            user = "posgres",
            password = "password"
        )
        cur = connection.cursor()
        
        cur.execute("DELETE FROM topics where created_at < '" + preDate + "'")
        connection.commit()
        connection.close()

    ############################################################################
    ###
    ###記事本文から音楽IDを取得
    ###
    ############################################################################          
    def setMusicGid(text):
        
        s3 = boto3.client('s3')
        AWS_S3_BUCKET_NAME = 'sinjito-bucket'
        GET_OBJECT_KEY_NAME = 'semantic_orientations_of_words.txt'
        object = s3.get_object(Bucket=AWS_S3_BUCKET_NAME, Key=GET_OBJECT_KEY_NAME)
        lines = object['Body'].read().decode('utf-8').splitlines()
        
        dic_pn = {}
        for line in lines:
            columns = line.split(':')
            dic_pn[columns[0]] = float(columns[3])
        
    
        
        #セパレータを「。」とする。
        seperator = "。"

        text = re.sub("[｜ 　「」\n]", "", text) # | と全角半角スペース、「」と改行の削除
        
        text_list = text.split(seperator)  # セパレーターを使って文章をリストに分割する
        text_list = [x+seperator for x in text_list]  # 文章の最後に。を追加  
        
        #この時点でデータの準備が終わりです
        #ここから形態素分析に入ります
        t = Tokenizer()

        semantic_value = 0
        semantic_count = 0
        
        for sentence in text_list:
            tokens = t.tokenize(sentence)
            for token in tokens:
                partOfSpeech = token.part_of_speech.split(',')[0]
    
                #感情分析(感情極性実数値より)
                if( partOfSpeech in ['動詞','名詞', '形容詞', '副詞']):
                    if(token.surface in dic_pn):
                        data = token.surface + ":" + str(dic_pn[token.surface])
                        print(data)
                        semantic_value = dic_pn[token.surface] + semantic_value
                        semantic_count = semantic_count + 1
        data = semantic_value / semantic_count
        print(data)
        #分析結果から音楽IDを振り分ける
        if data > -0.42:
            return 1
        elif data > -0.44:
            return 2
        elif data > -0.46:
            return 3
        elif data > -0.48:
            return 4
        elif data > -0.55:
            return 5
        elif data > -0.60:
            return 6
        elif data > -0.65:
            return 7
        elif data > -0.70:
            return 8
        else:
            return 9
            
        
 