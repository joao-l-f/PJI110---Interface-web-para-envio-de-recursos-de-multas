# ========================
# MÓDULOS E BIBLIOTECAS
# ========================

import uuid
# UUID: Gera identificadores únicos universais (UUIDs), para criar IDs exclusivos para registros
import psycopg2
# PSYCOP2: Biblioteca para conectar e interagir com bancos de dados PostgreSQL em Python
import os
# OS: Fornece acesso a funcionalidades do sistema operacional
import smtplib
# SMTPLIB:Permite enviar e-mails usando o protocolo SMTP
import re
# RE: Usado para validação e manipulação de strings
from email.message import EmailMessage
# EMAIL.MESSAGE: Usado para construir e estruturar mensagens de e-mail
from flask import Flask, render_template, request, redirect, url_for, flash
# FLASK E DEMAIS MÓDULOS: Cria e gerencia requisições, templates e a navegação da aplicação web
from datetime import datetime
# DATETIME: Manipula datas e horários
import pytz
# PYTZ: Permite trabalhar com fusos horários,

# ========================
# INSTANCIAÇÃO DA APLICAÇÃO
# ========================

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# ========================
# LIMITES DE TAMANHO E EXTENSÃO DOS ANEXOS
# ========================

app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "docx"}


# ========================
# CONFIG EMAIL
# ========================

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# ========================
# VALIDAÇÃO DO E-MAIL DO REQUERENTE
# ========================

def email_valido(email):
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email)

# ========================
# CONEXÃO AO BD HOSPEDADO PELO RENDER
# CRIAÇÃO DA TABELA DE PROTOCOLOS (I.E, SE NÃO EXISTIR ANTES DA EXECUÇÃO DO CÓDIGO)
# ========================

def get_db():
    conn = psycopg2.connect(
        os.getenv("DATABASE_URL"),
        sslmode="require"
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SET TIME ZONE 'America/Sao_Paulo';")
    return conn

def create_table():
    try:
        with get_db() as conn:
            with conn.cursor() as cur:

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS protocolos (
                        id SERIAL PRIMARY KEY,
                        nome VARCHAR(200) NOT NULL,
                        placa VARCHAR(8) NOT NULL,
                        tipo TEXT NOT NULL,
                        requerente TEXT NOT NULL,
                        protocolo TEXT NOT NULL UNIQUE,
                        data_envio TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        data_atualizacao TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # ÍNDICES 
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_nome ON protocolos(nome);
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_placa ON protocolos(placa);
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_protocolo ON protocolos(protocolo);
                """)

                # FUNÇÃO 
                cur.execute("""
                    CREATE OR REPLACE FUNCTION atualizar_data_atualizacao()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        NEW.data_atualizacao = CURRENT_TIMESTAMP;
                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql;
                """)

                # TRIGGER
                cur.execute("""
                    DROP TRIGGER IF EXISTS trigger_update ON protocolos;
                    CREATE TRIGGER trigger_update
                    BEFORE UPDATE ON protocolos
                    FOR EACH ROW
                    EXECUTE FUNCTION atualizar_data_atualizacao();
                """)

        print("✅ Estrutura do banco pronta")

    except Exception as e:
        print("❌ Erro ao criar estrutura:", e)

# ========================
# PREPARAÇÃO DO ENVIO DO FORMULÁRIO AO EMAIL DO DESTINATÁRIO
# ========================

def enviar_email(dados, protocolo, arquivos):
    try:
        msg = EmailMessage()
        msg["Subject"] = f"Novo protocolo {protocolo}"
        msg["From"] = EMAIL_USER
        msg["To"] = EMAIL_USER

        # CORPO DO E-MAIL
        corpo = f"""
Novo envio recebido:

Protocolo: {protocolo}
Nome: {dados['nome']}
CPF: {dados['cpf']}
Placa: {dados['placa']}
Tipo: {dados['tipo']}
Requerente: {dados['requerente']}
Email: {dados['email']}
Telefone: {dados['telefone']}

Endereço: 
Rua: {dados['rua']} Bairro: {dados['bairro']} Número: {dados['numero']}
Município: {dados['cidade']} Estado: {dados['estado']}

Descrição:
{dados['descricao']}
"""
        msg.set_content(corpo)

        # DATA (FUSO HORÁRIO ADAPTADO PARA A REGIÃO DE SÃO PAULO)
        tz = pytz.timezone("America/Sao_Paulo")
        data_envio = datetime.now(tz).strftime("%d/%m/%Y %H:%M")

        # ESTRUTURA HTML DA APRESNTAÇÃO GRÁFICA  DO E-MAIL
        html = f"""
        <body style="margin:0; padding:0; background-color:#D3DAFB; font-family: Arial;">
          <table width="100%" style="padding:20px;">
            <tr><td align="center">

              <table width="600" style="background:#fff; border-radius:10px; overflow:hidden;">

                <tr>
                  <td style="background:#195FAE; padding:20px; text-align:center; color:white;">
                    <h1>RECURSOS DE MULTA</h1>
                    <p>SMTTU/DETRASMA</p>
                  </td>
                </tr>

                <tr>
                  <td style="padding:30px;">
                    <h2 style="color:#195FAE;">Novo Protocolo</h2>

                    <p><strong>Protocolo:</strong> {protocolo}</p>
                    <p><strong>Nome:</strong> {dados['nome']}</p>
                    <p><strong>CPF:</strong> {dados['cpf']}</p>
                    <p><strong>Placa:</strong> {dados['placa']}</p>
                    <p><strong>Tipo:</strong> {dados['tipo']}</p>
                    <p><strong>Requerente:</strong> {dados['requerente']}</p>
                    <p><strong>Data:</strong> {data_envio}</p>
                    <p><strong>E-mail:</strong> {dados['email']}</p>
                    <p><strong>Telefone:</strong> {dados['telefone']}</p>
                    <br>
                    <p><strong>Endereço:</strong></p>
                    <p><strong>Rua:</strong> {dados['rua']} <strong>Bairro:</strong> {dados['bairro']} <strong>Número:</strong> {dados['numero']} </p>
                    <p><strong>Município:</strong> {dados['cidade']} <strong>Estado:</strong> {dados['estado']}</p>
                    <br>
                    <p><strong>Descrição:</strong><br>
                    {dados['descricao']}</p>
                  </td>
                </tr>

                <tr>
                  <td style="background:#195FAE; color:white; text-align:center; padding:15px;">
                    SMTTU - São Miguel Arcanjo/SP
                  </td>
                </tr>

              </table>

            </td></tr>
          </table>
        </body>
        """

        msg.add_alternative(html, subtype="html")

        # ANEXOS DO FORMULÁRIO
        for key, file in arquivos:
            filename, filedata, mimetype = file

            maintype, subtype = (
                mimetype.split("/", 1) if mimetype else ("application", "octet-stream")
            )

            msg.add_attachment(
                filedata,
                maintype=maintype,
                subtype=subtype,
                filename=filename
            )


        # CONFIGURAÇÃO DO SERVIDOR SMTP
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)

        print("EMAIL ENVIADO ✅")

    except Exception as e:
        print("ERRO EMAIL:", e)
        raise

# ========================
# ENVIO DE E-MAIL DE CONFIRMAÇÃO DO PROTOCOLO AO REQUERENTE
# ========================


def enviar_confirmacao(dados, protocolo):
    try:
        msg = EmailMessage()
        msg["Subject"] = f"Confirmação de protocolo {protocolo}"
        msg["From"] = EMAIL_USER
        msg["To"] = dados["email"]

        tz = pytz.timezone("America/Sao_Paulo")
        data_envio = datetime.now(tz).strftime("%d/%m/%Y %H:%M")

        # TEXTO SIMPLES
        msg.set_content(f"""
Olá, {dados['nome']}!

Recebemos sua solicitação com sucesso.

Protocolo: {protocolo}
Data: {data_envio}
Instância: {dados['tipo']}


Atenciosamente,
SMTTU - São Miguel Arcanjo/SP
""")

        # HTML 
        html = f"""
<body style="margin:0; padding:0; background-color:#D3DAFB; font-family: Arial;">
  <table width="100%" style="padding:20px;">
    <tr>
      <td align="center">

        <table width="600" style="background:#fff; border-radius:10px; overflow:hidden;">

          <tr>
            <td style="background:#195FAE; padding:20px; text-align:center; color:white;">
              <h1>RECURSOS DE MULTA</h1>
              <p>SMTTU/DETRASMA</p>
            </td>
          </tr>

          <tr>
            <td style="padding:30px;">
              
              <h2 style="color:#195FAE;">Confirmação de Envio</h2>

              <p>Olá, <strong>{dados['nome']}</strong>!</p>

              <p>Seu protocolo foi recebido com sucesso.</p>

              <p><strong>Protocolo:</strong> {protocolo}</p>
              <p><strong>Data:</strong> {data_envio}</p>
              <p><strong>Instância:</strong> {dados['tipo']}</p>

              <hr>

              <p style="font-size:12px; color:gray;">
                SMTTU - São Miguel Arcanjo/SP
              </p>

            </td>
          </tr>

        </table>

      </td>
    </tr>
  </table>
</body>
"""

        msg.add_alternative(html, subtype="html")

        # ENVIO
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)

        print("CONFIRMAÇÃO ENVIADA ✅")

    except Exception as e:
        print("ERRO CONFIRMAÇÃO:", e)

# ========================
# ROTAS 
# ========================

#PÁGINA DE ENVIO DE RECURSOS
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/enviar", methods=["POST"])
def enviar():
    try:
        # DADOS
        dados = {
            # DADOS DE IDENTIFICAÇÃO DO REQUERENTE 
            "nome": request.form.get("nome", "").strip(),
            "cpf": request.form.get("cpf", "").replace(".", "").replace("-", ""),
            "telefone": request.form.get("telefone"),
            "email": request.form.get("email", "").strip(),
            "placa": request.form.get("placa", "").upper().strip(),
            "tipo": request.form.get("tipo"),
            "requerente": request.form.get("requerente"),
            # ENDEREÇO DO REQUERENTE
            "rua": request.form.get("rua"),
            "bairro": request.form.get("bairro"),
            "numero": request.form.get("numero"),
            "cidade": request.form.get("cidade"),
            "estado": request.form.get("estado"),
            # DESCRIÇÃO DA SOLICITAÇÃO
            "descricao": request.form.get("descricao")
        }

        # VALIDAÇÃO DOS CAMPOS OBRIGATÓRIOS DO FORMULÁRIO
        if not dados["nome"]:
            return "Nome é obrigatório", 400

        if not dados["email"] or not email_valido(dados["email"]):
            return "Email inválido", 400

        # GERAÇÃO DE PROTOCOLO
        protocolo = uuid.uuid4().hex

        # INCLUSÃO DOS DADOS *MINIMIZADOS* NA TABELA "PROTOCOLOS"
        try:
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO protocolos (
                            nome, placa, tipo, requerente, protocolo
                        ) VALUES (%s,%s,%s,%s,%s)
                    """, (
                        dados["nome"],
                        dados["placa"],
                        dados["tipo"],
                        dados["requerente"],
                        protocolo
                    ))
        except Exception as e:
            print("ERRO AO SALVAR:", e)

        # ENVIO E VERIFICAÇÃO DOS ANEXOS
        ALLOWED_MIME_TYPES = {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }

        arquivos = []
        def arquivo_permitido(filename):
            return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
        for key, file in request.files.items():
            if file and file.filename:

                if not arquivo_permitido(file.filename):
                    return f"Extensão não permitida: {file.filename}", 400

                if file.mimetype not in ALLOWED_MIME_TYPES:
                    return f"Tipo inválido: {file.filename}", 400

                arquivos.append(
                    (key, (file.filename, file.read(), file.mimetype))
        )

        # ENVIO DO EMAIL
        enviar_email(dados, protocolo, arquivos)
        enviar_confirmacao(dados, protocolo)
        flash(f"Enviado com sucesso! Protocolo: {protocolo}")
        return redirect(url_for("index"))

    except Exception as e:
        print("ERRO GERAL:", e)
        return f"Erro interno: {e}", 500

# BUSCA DE PROTOCOLOS

@app.route("/buscar", methods=["GET", "POST"])
def buscar():
    if request.method == "GET":
        return render_template("search.html")

    try:
        nome = request.form.get("nome", "")
        protocolo = request.form.get("protocolo", "")
        placa = request.form.get("placa", "").upper().strip()
        
        nome_like = f"%{nome}%"

        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT nome, placa, tipo, protocolo, requerente, data_envio
                    FROM protocolos
                    WHERE 
                        (%s = '' OR LOWER(nome) LIKE LOWER(%s))
                        AND (%s = '' OR protocolo = %s)
                        AND (%s = '' OR placa = %s)
                    ORDER BY data_envio DESC
                    LIMIT 1
                """, (
                    nome, nome_like,
                    protocolo, protocolo,
                    placa, placa
                ))

                resultado = cur.fetchone()


        tz = pytz.timezone("America/Sao_Paulo")

        if resultado:
            data_utc = resultado[5]

            # GARANTE O AJUSTE DE TIMEZONE
            if data_utc.tzinfo is None:
                data_utc = pytz.utc.localize(data_utc)

            data_br = data_utc.astimezone(tz)

            # DICIONÁRIO DE DADOS PARA EXIBIÇÃO 
            dados = {
                "nome": resultado[0],
                "placa": resultado[1],
                "tipo": resultado[2],
                "protocolo": resultado[3],
                "requerente": resultado[4],
                "data_envio": data_br.strftime("%d/%m/%Y %H:%M")
            }  
                
                
        
            return render_template("search.html", resultado=dados)

        return render_template("search.html", erro="Nenhum registro encontrado.")

    except Exception as e:
        print("Erro na busca:", e)
        return f"Erro na busca: {e}", 500


# ========================
# TESTE DE CONEXÃO COM O DB
# ========================

@app.route("/teste-db")
def teste_db():
    try:
        with get_db():
            pass
        return "Banco conectado!"
    except Exception as e:
        return str(e)

# ========================
# INIT
# ========================

create_table()

# ========================
# RUN
# ========================

if __name__ == "__main__":
    app.run(debug=True)