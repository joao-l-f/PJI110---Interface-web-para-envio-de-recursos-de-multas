import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

# =============================================
# CONFIGURAÇÕES DO BANCO
# =============================================

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD'),
    'database': 'postgres'  # Banco do sistema para criar o banco
}

DB_NAME = os.getenv('DB_NAME', 'sistema_protocolos')

# =============================================
# FUNÇÕES
# =============================================

def criar_banco_dados():
    """Cria o banco de dados se não existir"""
    try:
        # Conecta ao PostgreSQL 
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Verifica se o banco já existe
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
        existe = cursor.fetchone()
        
        if not existe:
            # Cria o banco de dados
            cursor.execute(f"""
                CREATE DATABASE {DB_NAME}
                ENCODING 'UTF8'
                LC_COLLATE 'pt_BR.UTF-8'
                LC_CTYPE 'pt_BR.UTF-8'
                TEMPLATE template0
            """)
            print(f" Banco de dados '{DB_NAME}' criado com sucesso!")
        else:
            print(f"  Banco de dados '{DB_NAME}' já existe")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f" Erro ao criar banco de dados: {e}")
        return False

def criar_tabela_protocolo():
    """Cria a tabela protocolo e seus objetos"""
    try:
        # Conecta ao banco recém-criado
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_NAME
        )
        cursor = conn.cursor()
        
        # SQL para criar a tabela protocolo (singular)
        sql_tabela = """
        CREATE TABLE IF NOT EXISTS protocolo (
            id SERIAL PRIMARY KEY,
            placa_veiculo VARCHAR(8) NOT NULL,
            instancia_processo VARCHAR(50) NOT NULL,
            nome_requerente VARCHAR(200) NOT NULL,
            numero_protocolo VARCHAR(30) NOT NULL UNIQUE,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # SQL para criar índices
        sql_indices = [
            "CREATE INDEX IF NOT EXISTS idx_protocolo_placa ON protocolo(placa_veiculo);",
            "CREATE INDEX IF NOT EXISTS idx_protocolo_numero ON protocolo(numero_protocolo);",
            "CREATE INDEX IF NOT EXISTS idx_protocolo_requerente ON protocolo(nome_requerente);"
        ]
        
        # SQL para criar função de atualização
        sql_funcao = """
        CREATE OR REPLACE FUNCTION atualizar_data_atualizacao()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.data_atualizacao = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        """
        
        # SQL para criar trigger (agora na tabela protocolo)
        sql_trigger = """
        DROP TRIGGER IF EXISTS trigger_atualizar_data_atualizacao ON protocolo;
        CREATE TRIGGER trigger_atualizar_data_atualizacao
            BEFORE UPDATE ON protocolo
            FOR EACH ROW
            EXECUTE FUNCTION atualizar_data_atualizacao();
        """
        
        # Executa a criação da tabela
        cursor.execute(sql_tabela)
        print("✅ Tabela 'protocolo' criada/verificada")
        
        # Executa a criação dos índices
        for idx in sql_indices:
            cursor.execute(idx)
        print("✅ Índices criados/verificados")
        
        # Executa a criação da função
        cursor.execute(sql_funcao)
        print("✅ Função 'atualizar_data_atualizacao' criada/verificada")
        
        # Executa a criação do trigger
        cursor.execute(sql_trigger)
        print("✅ Trigger criado/verificado")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f" Erro ao criar tabela: {e}")
        return False

def verificar_estrutura():
    """Verifica se a tabela foi criada corretamente"""
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_NAME
        )
        cursor = conn.cursor()
        
        # Verifica colunas da tabela
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'protocolo'
            ORDER BY ordinal_position
        """)
        
        colunas = cursor.fetchall()
        
        print("\n Estrutura da tabela 'protocolo':")
        print("-" * 50)
        for coluna in colunas:
            print(f"  • {coluna[0]}: {coluna[1]} (nullable: {coluna[2]})")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f" Erro ao verificar estrutura: {e}")
        return False

# =============================================
# EXECUÇÃO PRINCIPAL
# =============================================

if __name__ == "__main__":
    print("\n" + "="*50)
    print(" SCRIPT DE CRIAÇÃO DO BANCO DE DADOS")
    print("="*50 + "\n")
    
    # Verifica se a senha foi configurada
    if not DB_CONFIG['password']:
        print("⚠️  ATENÇÃO: Senha do PostgreSQL não configurada!")
        print("   Crie um arquivo .env com: DB_PASSWORD=sua_senha")
        print("\n   Ou configure a variável de ambiente DB_PASSWORD")
        exit(1)
    
    # Passo 1: Criar banco de dados
    print(" Passo 1: Criando banco de dados...")
    if not criar_banco_dados():
        exit(1)
    
    # Passo 2: Criar tabela protocolo
    print("\n Passo 2: Criando tabela protocolo...")
    if not criar_tabela_protocolo():
        exit(1)
    
    # Passo 3: Verificar estrutura
    print("\n Passo 3: Verificando estrutura...")
    verificar_estrutura()
    
    print("\n" + "="*50)
    print("🎉 BANCO DE DADOS CRIADO COM SUCESSO!")
    print("="*50)
    print(f"\n Informações:")
    print(f"   Banco: {DB_NAME}")
    print(f"   Tabela: protocolo")
    print(f"   Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"   Usuário: {DB_CONFIG['user']}")
    print("\n Pronto para usar!")