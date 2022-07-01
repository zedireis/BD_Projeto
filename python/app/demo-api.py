##
# =============================================
# ============== Bases de Dados ===============
# ============== LEI  2020/2021 ===============
# =============================================
# ================= PROJETO ===================
# =============================================
# =============================================
# === Department of Informatics Engineering ===
# =========== University of Coimbra ===========
# =============================================
##
# Authors:
# José Reis - 2018285575
# Nuno Silva - 2018285621


from flask import Flask, jsonify, request
from datetime import datetime, timedelta
from functools import wraps
import logging
import psycopg2
import time
import jwt

app = Flask(__name__)

app.config['SECRET_KEY'] = 'Th1s1ss3cr3t'


@app.route('/dbproj/')
def hello():
    return """

    Hello World!  <br/>
    <br/>
    Check the sources for instructions on how to use the endpoints!<br/>
    <br/>
    BD 2021 Team<br/>
    <br/>
    """


def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):

        token = None

        if 'x-access-tokens' in request.headers:
            token = request.headers['x-access-tokens']

        if not token:
            return jsonify({'message': 'a valid token is missing'})

        conn = db_connection()
        cur = conn.cursor()

        result = ''

        try:
            data = jwt.decode(
                token, app.config['SECRET_KEY'], algorithms=["HS256"])

            current_user = data['id']
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error(error)
            return jsonify({'error': 'token is invalid or has expired'})
        finally:
            if conn is not None:
                conn.close()

        return f(current_user, *args, **kwargs)

    return decorator


##
# GET
##
# Obtain all leiloes, in JSON format
##
# To use it, access:
##
# http://localhost:8080/dbproj/leiloes/
##

@app.route("/dbproj/leiloes/", methods=['GET'], strict_slashes=True)
@token_required
def get_all_auctions(current_user):
    logger.info("###              DEMO: GET /leiloes              ###")

    conn = db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT l.id, v.descricao FROM leilao l, versao v WHERE v.id = l.last_version_id AND l.data_fim > NOW() ORDER BY l.id")
    rows = cur.fetchall()

    payload = []
    logger.debug("---- Leiloes  ----")
    for row in rows:
        logger.debug(row)
        content = {'leilaoId': int(row[0]), 'descricao': row[1]}
        payload.append(content)  # appending to the payload to be returned

    conn.close()
    return jsonify(payload)


##
# GET
##
# Obtain leilao with artigoId or by descricao
##
# To use it, access:
##
# http://localhost:8080/dbproj/leiloes/
##

@app.route("/dbproj/leiloes/<pesquisa>", methods=['GET'])
@token_required
def get_department(current_user, pesquisa):
    logger.info(
        "###              DEMO: GET /dbproj/leiloes/<pesquisa>              ###")

    logger.debug(f': {pesquisa}')

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("""(SELECT l.id, v.descricao 
                    FROM leilao l, versao v 
                    WHERE v.id = l.last_version_id AND l.artigo_id = %s AND l.data_fim > NOW() ORDER BY l.id)
            UNION       (SELECT l.id, v.descricao 
                        FROM leilao l, versao v 
                        WHERE v.id = l.last_version_id AND l.data_fim > NOW() AND UPPER(v.descricao) LIKE UPPER(%s) ORDER BY l.id)""", (pesquisa, '%'+pesquisa+'%',))
    rows = cur.fetchall()

    if (cur.rowcount == 0):
        content = {}
        return jsonify(content)
    
    logger.debug("---- Leiloes Encontrados  ----")
    
    hist = []
    for i in range(len(rows)):
        logger.debug(rows[i])
        hist.append({'leilaoId': int(rows[i][0]), 'descricao': rows[i][1]})

    
    content = hist

    conn.close()
    return jsonify(content)


##
# POST
##
# Add a new user in a JSON payload
##
# To use it, you need to use postman or curl:
##
# curl -X POST http://localhost:8080/dbproj/user/ -H "Content-Type: application/json" -d '{"username": "username","password": "password","email": "email","nome": "nome","morada": "morada"}'
##


@app.route("/dbproj/user", methods=['POST'])
def add_user():
    logger.info("###              POST /dbproj/user              ###")
    payload = request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    if "nome" not in payload or "email" not in payload or "username" not in payload or "password" not in payload or "morada" not in payload:
        return {'error':'Parameters for user creation are missing. Please check again!'}

    logger.info("---- New User  ----")
    logger.debug(f'payload: {payload}')

    # parameterized queries, good for security and performance
    statement = """
                  INSERT INTO pessoa (nome, email, username, password, morada)
                          VALUES ( %s, %s, %s, %s, %s ) RETURNING id"""

    values = (payload["nome"], payload["email"],
              payload["username"], payload["password"], payload["morada"])

    try:
        cur.execute(statement, values)
        userid = cur.fetchone()[0]
        cur.execute("commit")

        result = {'userId':userid}
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        result = {'error':'Failed to insert user!'}
    finally:
        if conn is not None:
            conn.close()

    return jsonify(result)


##
# POST
##
# Add a new leilao in a JSON payload
##
# To use it, you need to use postman or curl:
##
# curl -X POST http://localhost:8080/dbproj/leilao -H "Content-Type: application/json" -d '{"artigoId": "artigo","precoMinimo" : 999,"titulo" : "Leilao1","descricao" : "LeilaoTeste","dataFim" : "DD/MM/AAAA HH:MM"}'
##


@app.route("/dbproj/leilao", methods=['POST'])
@token_required
def new_leilao(current_user):
    logger.info("###              POST /dbproj/leilao              ###")
    payload = request.get_json()

    conn = db_connection()
    cur = conn.cursor()
    
    if "titulo" not in payload or "descricao" not in payload or "dataFim" not in payload or "precoMinimo" not in payload or "artigoId" not in payload:
        return {'error':'Parameters for user creation are missing. Please check again!'}

    logger.info("---- New Auction  ----")
    logger.debug(f'payload: {payload}')

    # parameterized queries, good for security and performance                                                      #ESTE AINDA NAO ESTA A FUNCIONAR

    datetime_dataFim = datetime.strptime(payload["dataFim"], '%d/%m/%Y %H:%M')

    statement1 = """
                  INSERT INTO leilao (preco_min, data_fim, pessoa_id, artigo_id)
                          VALUES ( %s,   %s , %s,  %s ) RETURNING id"""
    values1 = (payload["precoMinimo"], datetime_dataFim,
               current_user, payload["artigoId"])
    statement2 = """
                  INSERT INTO versao (titulo, descricao, leilao_id) 
                          VALUES ( %s,   %s ,   %s )"""

    try:
        cur.execute(statement1, values1)
        leilaoid = cur.fetchone()[0]

        values2 = (payload["titulo"], payload["descricao"], leilaoid)

        cur.execute(statement2, values2)

        cur.execute("commit")

        result ={'leilaoId':leilaoid}
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        result = {'error':'Failed to insert!'}
    finally:
        if conn is not None:
            conn.close()

    return jsonify(result)


##
# PUT
##
# Login a user based on the a JSON payload
##
# To use it, you need to use postman or curl:
##
# curl -X PUT http://localhost:8080/dbproj/user -H "Content-Type: application/json" -d '{"ndep": 69, "localidade": "Porto"}'
##

@app.route("/dbproj/user", methods=['PUT'])
def login_user():
    logger.info("###              LOGIN: PUT /dbproj/user              ###")
    content = request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    # if content["ndep"] is None or content["nome"] is None :
    #    return 'ndep and nome are required to update'

    if "username" not in content or "password" not in content:
        return 'user and password are required to login'

    logger.info("---- Login User ----")
    logger.info(f'content: {content}')

    statement1 = """SELECT id, username, password FROM pessoa WHERE username = %s AND password = %s"""

    values1 = (content["username"], content["password"])

    try:
        res = cur.execute(statement1, values1)
        match = f'Matches: {cur.rowcount}'
        if match == 0:
            result = 'User or Password does not match'
            if conn is not None:
                conn.close()
            return jsonify(result)
        else:
            rows = cur.fetchall()
            row = rows[0]
            userId = int(row[0])

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        result = 'Failed!'
        if conn is not None:
            conn.close()
        return jsonify(result)

    token = jwt.encode({'id': userId, 'exp': datetime.utcnow(
    ) + timedelta(minutes=30)}, app.config['SECRET_KEY'], algorithm="HS256")

    if conn is not None:
        conn.close()
    return jsonify({'token': token})

##
# GET
##
# Obtain detalhes leilao by leilaoId
##
# To use it, access:
##
# http://localhost:8080/dbproj/leilao/{leilaoId}
##


@app.route("/dbproj/leilao/<leilaoId>", methods=['GET'])
@token_required
def get_leilaodetails(current_user,leilaoId):
    logger.info(
        "###              DEMO: GET /dbproj/leilao/<leilaoId>              ###")

    logger.debug(f': {leilaoId}')

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("""SELECT lei.id, ver.titulo, ver.descricao, lei.data_fim, pes.nome
                    FROM leilao as lei, versao as ver, pessoa as pes
                    WHERE (ver.id = lei.last_version_id) AND 
                        (lei.id = %s) AND
                        (pes.id = lei.pessoa_id)
    """, leilaoId)
    rows = cur.fetchall()

    # Lista com os dados do leilao
    row = rows[0]

    cur.execute("""SELECT preco, nome
                FROM licitacao, pessoa
                WHERE (pessoa_id = pessoa.id) AND
                (leilao_id = %s)
                ORDER BY preco DESC
    """, leilaoId)
    rows = cur.fetchall()

    # Criar Lista com o historico de licitacoes
    hist = []
    for i in range(len(rows)):
        hist.append({'preco': str(rows[i][0]) + '€', 'licitador': rows[i][1]})

    cur.execute("""SELECT texto, data, nome
                FROM mensagem, pessoa
                WHERE pessoa_id = pessoa.id AND leilao_id = %s
                ORDER BY DATA DESC
    """, leilaoId)
    rows = cur.fetchall()

    # Criar Lista de dicionarios com o mural de mensagens
    mural = []
    for i in range(len(rows)):
        mural.append(
            {'mensagem': rows[i][0], 'data': rows[i][1], 'autor': rows[i][2]})

    logger.debug("---- Leilao Selecionado  ----")
    logger.debug(row)
    logger.debug(hist)
    logger.debug(mural)
    content = {'leilaoId': int(row[0]), 'titulo': row[1], 'descricao': row[2],
               'data_fim': row[3], 'vendedor': row[4], 'licitacoes': hist, 'mural de mensagens': mural}

    conn.close()
    return jsonify(content)

##
# GET
##
# Obtain detalhes leilao from current user
##
# To use it, access:
##
# http://localhost:8080/dbproj/leilao/
##


@app.route("/dbproj/leilao/", methods=['GET'])
@token_required
def get_leilao_details_from_current_user(current_user):
    logger.info(
        "###              DEMO: GET /dbproj/leilao/              ###")

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("""SELECT DISTINCT id
                FROM leilao
                WHERE pessoa_id = %s
                UNION
                SELECT DISTINCT leilao_id
                FROM licitacao
                WHERE pessoa_id = %s
    """, (current_user, current_user))
    leilaoIds = cur.fetchall()
    result = []

    for i in range(len(leilaoIds)):
        leilaoId = leilaoIds[i]

        cur.execute("""SELECT lei.id, ver.titulo, ver.descricao, lei.data_fim, pes.nome
                        FROM leilao as lei, versao as ver, pessoa as pes
                        WHERE (ver.id = lei.last_version_id) AND 
                            (lei.id = %s) AND
                            (pes.id = lei.pessoa_id)
        """, leilaoId)
        rows = cur.fetchall()

        # Lista com os dados do leilao
        row = rows[0]

        cur.execute("""SELECT preco, nome
                    FROM licitacao, pessoa
                    WHERE (pessoa_id = pessoa.id) AND
                    (leilao_id = %s)
                    ORDER BY preco DESC
        """, leilaoId)
        rows = cur.fetchall()

        # Criar Lista com o historico de licitacoes
        hist = []
        for i in range(len(rows)):
            hist.append(
                {'preco': str(rows[i][0]) + '€', 'licitador': rows[i][1]})

        cur.execute("""SELECT texto, data, nome
                    FROM mensagem, pessoa
                    WHERE pessoa_id = pessoa.id AND leilao_id = %s
                    ORDER BY DATA DESC
        """, leilaoId)
        rows = cur.fetchall()

        # Criar Lista de dicionarios com o mural de mensagens
        mural = []
        for i in range(len(rows)):
            mural.append(
                {'mensagem': rows[i][0], 'data': rows[i][1], 'autor': rows[i][2]})

        logger.debug("---- Leilao Selecionado  ----")
        logger.debug(row)
        logger.debug(hist)
        logger.debug(mural)
        content = {'leilaoId': int(row[0]), 'titulo': row[1], 'descricao': row[2],
                   'data_fim': row[3], 'vendedor': row[4], 'licitacoes': hist, 'mural de mensagens': mural}
        result.append(content)

    conn.close()
    return jsonify(result)

##
# GET
##
# Make a bid in a auction
##
# To use it, access:
##
# http://localhost:8080/dbproj/licitar/{leilaoId}/{licitacao}
##


@app.route("/dbproj/licitar/<leilaoId>/<licitacao>", methods=['GET'])
@token_required
def new_licitacao(current_user, leilaoId, licitacao):
    logger.info(
        "###              DEMO: GET /dbproj/licitar/<leilaoId>/<licitacao>              ###")

    logger.debug(f': {leilaoId, licitacao}')

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("""SELECT *
                    FROM insert_new_licitation(%s, %s, %s);
    """, (leilaoId, licitacao, current_user))
    content = cur.fetchall()[0][0]

    logger.debug("---- Nova licitacao  ----")
    logger.debug(content)

    result = {}
    if content == 1:
        result = {'licitacao': 'Sucesso'}
    elif content == 0:
        result = {'erro': 'Erro 2 -> Valor de licitacao demasiado baixo'}
    else:
        result = {'erro': 'Erro 3 -> Leilao ja acabou'}

    conn.commit()
    conn.close()
    return result


##
#   PUT
##
# Update textual info of an auction from a JSON payload
##
# To use it, you need to use postman or curl:
##
# curl -X PUT http://localhost:8080/dbproj/leilao -H "Content-Type: application/json" -d '{"titulo": "Novo titulo", "descricao": "Nova descricao"}'
##


@app.route("/dbproj/leilao/<leilaoId>", methods=['PUT'])
@token_required
def update_leilao(current_user, leilaoId):
    logger.info("###               PUT /dbproj/leilao              ###")
    logger.debug(f': {leilaoId}')

    content = request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    # if content["ndep"] is None or content["nome"] is None :
    #    return 'ndep and nome are required to update'

    if "titulo" not in content or "descricao" not in content:
        return 'titulo and descricao are required to update'

    logger.info("---- Update Leilao  ----")
    logger.info(f'content: {content}')

    cur.execute("""SELECT lei.pessoa_id, lei.preco_min, lei.data_fim
                    FROM leilao as lei
                    WHERE (lei.id = %s)
    """, leilaoId)
    rows = cur.fetchall()

    # Lista com os detalhes do leilao
    row = rows[0]

    if(current_user != row[0]):
        if conn is not None:
            conn.close()
        return jsonify({"erro": 'Este leilão não pertence ao user'})

    # parameterized queries, good for security and performance
    statement = """
                  INSERT INTO versao (titulo, descricao, leilao_id) 
                          VALUES ( %s,   %s ,   %s )"""

    values = (content["titulo"], content["descricao"], leilaoId)

    try:
        res = cur.execute(statement, values)
        result = {'leilaoId': leilaoId, 'titulo': content["titulo"], 'descricao': content["descricao"], 'precoMinimo': str(
            row[1]), 'dataFim': row[2]}
        cur.execute("commit")
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        result = {'erro': 'Erro a atualizar'}
    finally:
        if conn is not None:
            conn.close()
    return jsonify(result)


##
# POST
##
# Add a new user in a JSON payload
##
# To use it, you need to use postman or curl:
##
# curl -X POST http://localhost:8080/dbproj/user/ -H "Content-Type: application/json" -d '{"username": "username","password": "password","email": "email","nome": "nome","morada": "morada"}'
##


@app.route("/dbproj/message/<leilaoId>", methods=['POST'])
@token_required
def add_mensagem(current_user, leilaoId):
    logger.info("###              POST /dbproj/mensagem              ###")
    payload = request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    if "texto" not in payload:
        return 'Message cannot be empty'

    logger.info("---- New User  ----")
    logger.debug(f'payload: {payload}')

    # parameterized queries, good for security and performance
    statement = """
                  INSERT INTO mensagem (texto, data, pessoa_id, leilao_id)
                          VALUES ( %s, %s, %s, %s )"""

    values = (payload["texto"], datetime.now()+timedelta(hours=+1),
              current_user, leilaoId)

    try:
        cur.execute(statement, values)
        cur.execute("commit")

        result = {'Success':'Created new message'}
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        result = {'Error':'Failed to create message'}
    finally:
        if conn is not None:
            conn.close()

    return jsonify(result)

##
# GET
##
# Obtain notificacoes for current user and current leilao
##
# To use it, access:
##
# http://localhost:8080/dbproj/message/
##


@app.route("/dbproj/message/<leilaoId>", methods=['GET'])
@token_required
def get_notificacoes(current_user, leilaoId):
    logger.info(
        "###              : GET /dbproj/message/              ###")

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("""SELECT texto, data, nome
                    FROM notificacao, pessoa
                    WHERE notificacao.pessoa_id = %s AND pessoa.id = from_id AND leilao_id = %s
                    ORDER BY DATA DESC
    """, (current_user,leilaoId,))
    rows = cur.fetchall()

    # Criar Lista de dicionarios com o mural de notificacoes
    mural = []
    for i in range(len(rows)):
        mural.append(
            {'notificacao': rows[i][0], 'data': rows[i][1], 'autor': rows[i][2]})

    logger.debug("---- Leilao Selecionado  ----")
    logger.debug(mural)
    content = {'notificacoes': mural}

    conn.close()
    return jsonify(content)

##########################################################
# DATABASE ACCESS
##########################################################

def db_connection():
    db = psycopg2.connect(user="aulaspl",
                          password="aulaspl",
                          host="db",
                          port="5432",
                          database="projeto")
    return db


##########################################################
# MAIN
##########################################################
if __name__ == "__main__":

    # Set up the logging
    logging.basicConfig(filename="logs/log_file.log")
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s',
                                  '%H:%M:%S')
    # "%Y-%m-%d %H:%M:%S") # not using DATE to simplify
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    time.sleep(1)  # just to let the DB start before this print :-)

    logger.info("\n---------------------------------------------------------------\n" +
                "API v1.0 online: http://localhost:8080/departments/\n\n")

    app.run(host="0.0.0.0", debug=True, threaded=True)
