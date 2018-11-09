import psycopg2
import time
from threading import Thread
import subprocess
from difflib import SequenceMatcher

class Database():
    def __init__(self, banco, usuario, senha):
        try:
            self.connection = psycopg2.connect(
                "dbname='%s' user='%s' host='localhost' password='%s' port='5432'" % (banco, usuario, senha))
            self.connection.autocommit = True
            self.cursor = self.connection.cursor()
            print("Conexão com o banco de dados efetuada com sucesso!")
        except:
            print("Erro ao conectar no database!")

    def query(self, sql):
        self.cursor.execute(sql)
        registros = self.cursor.fetchall()
        return registros

    def execute(self, sql):
        self.cursor.execute(sql)

fila_submissoes = []
banco     = input("Informe o nome do banco de dados: ")
usuario   = input("Informe o nome do usuário para logar no database: ")
senha     = input("Informe sua senha para logar no database: ")
database  = Database(banco, usuario, senha)
DIRETORIO = "/home/vinicius/Documentos/Python/compilador-multilinguagens/arquivos/"


def BuscarSubmissoes():
    global fila_submissoes, database

    while True:
        time.sleep(3)

        fila_submissoes = database.query("SELECT ID, STATUS, LINGUAGEM_ID, PROBLEMA_ID FROM SUBMISSAO WHERE STATUS = 'PROCESSANDO' ORDER BY ID")

        if len(fila_submissoes) > 0:
            print(fila_submissoes)
            AtualizarStatusCompilando()

def AtualizarStatusCompilando():
    global fila_submissoes, database

    for i in fila_submissoes:
        sql = "UPDATE SUBMISSAO SET STATUS = 'COMPILANDO' WHERE ID = %s" %i[0]
        database.execute(sql)

def AtualizarStatus(id, status):
    sql = "UPDATE SUBMISSAO SET STATUS = '%s' WHERE ID = %s" % (status, id)
    database.execute(sql)

def AtualizarResposta(id, resposta):
    sql = "UPDATE SUBMISSAO SET RESPOSTA = '%s' WHERE ID = %s" % (resposta, id)
    database.execute(sql)

def Compilando():
    # O nome do arquivo será o ID do registro
    while True:
        time.sleep(3)
        for i in fila_submissoes:
            # print("ID: " + str(i[0]) + " | Linguagem: " + str(i[2]))
            Script(i[0], i[2], i[3])

def Script(arquivo, linguagem, problema):

    # Linguagens
    # 1 - C++
    # 2 - Kotlin
    # 3 - Java
    # 4 - Python

    entrada_1001 = '%sentradas/1001.in' % DIRETORIO
    entrada_1002 = '%sentradas/1002.in' % DIRETORIO
    entrada_1003 = '%sentradas/1003.in' % DIRETORIO
    saida_1001   = '%ssaidas/1001.out' % DIRETORIO
    saida_1002   = '%ssaidas/1002.out' % DIRETORIO
    saida_1003   = '%ssaidas/1003.out' % DIRETORIO

    if problema == 1001:
        entrada = entrada_1001
        saida = saida_1001
    elif problema == 1002:
        entrada = entrada_1002
        saida = saida_1002
    elif problema == 1003:
        entrada = entrada_1003
        saida = saida_1003

    if linguagem == 1:
        compilar = "g++ %sfile%s.cpp -o %scompilacoes/file%s 2> " \
                       "%serros/erros_file%s.txt && echo 'Compilado com sucesso!' || cat %serros/erros_file%s.txt" \
                   % (DIRETORIO, arquivo, DIRETORIO, arquivo, DIRETORIO, arquivo, DIRETORIO, arquivo)

        executar = "cd %scompilacoes/ && ./file%s < %s " \
                   "> %scompilacoes/file%s.txt" % (DIRETORIO, arquivo, entrada, DIRETORIO, arquivo)

    elif linguagem == 2:
        compilar = "kotlinc ../arquivos/%s.kt -include-runtime -d ../arquivos/compilacoes/%s.jar 2> " \
                   "../arquivos/erros/erros_%s.txt && echo 'Compilado com sucesso!' || cat ../arquivos/erros/erros_%s.txt" % (
                       arquivo, arquivo, arquivo, arquivo)
    elif linguagem == 3:
        compilar = "javac ../arquivos/file%s.java 2> " \
                   "../arquivos/erros/erros_file%s.txt && echo 'Compilado com sucesso!' || " \
                   "cat ../arquivos/erros/erros_file%s.txt" % (arquivo, arquivo, arquivo)

        executar = "cd ../arquivos/ && java file%s" % arquivo

    elif linguagem == 4:
        compilar = "python -m py_compile ../arquivos/file%s.py 2> " \
                   "../arquivos/erros/erros_file%s.txt && echo 'Compilado com sucesso!' || " \
                   "cat ../arquivos/erros/erros_file%s.txt" % (arquivo, arquivo, arquivo)

        executar = "python3 ../arquivos/__pycache__/file%s.cpython-35.pyc" % arquivo

    elif linguagem == 5:
        pass

    compilacao = subprocess.check_output(compilar, shell=True)

    if compilacao.decode().strip() == 'Compilado com sucesso!':
        print("Compilado com sucesso: file%s" % arquivo)

        subprocess.check_output(executar, shell=True)

        resposta = CalcularPercentualDeErro("%scompilacoes/file%s.txt" % (DIRETORIO, arquivo), saida)
        if float(resposta) <= 0:
            print("Resposta correta: file%s" % arquivo)
            AtualizarStatus(arquivo, "Correta")
            AtualizarResposta(arquivo, "Solução compilada e executada com sucesso!")
        else:
            print("Resposta %s incorreta: file%s" % (resposta, arquivo))
            AtualizarStatus(arquivo, "Incorreta")
            AtualizarResposta(arquivo, "Solução incorreta: %s" % resposta + "%")

    else:
        print("Erro ao compilar: file%s" % arquivo)
        compilacao_frmt = compilacao.decode()
        AtualizarResposta(arquivo, compilacao_frmt.replace("'", "´"))
        AtualizarStatus(arquivo, "Erro de compilação")

def CalcularPercentualDeErro(arquivo, saida):
    compilacao     = open(arquivo).read()
    saida_esperada = open(saida).read()
    percent        = SequenceMatcher(None, compilacao, saida_esperada)
    resposta       = percent.ratio() * 100
    erro           = "%.2f" % (100.0 - resposta)
    return erro

def Main():

    buscar_submissoes = Thread(target=BuscarSubmissoes)
    buscar_submissoes.start()

    compilando = Thread(target=Compilando)
    compilando.start()

Main()