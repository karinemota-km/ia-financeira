import streamlit as st
import random
from supabase import create_client
from openai import OpenAI
import resend

# =============================
# CONFIG
# =============================
st.set_page_config(layout="wide")

st.markdown("""
<style>
body {background-color: #0e1117;}
h1, h2, h3 {color: white;}
.stButton>button {
    background: linear-gradient(90deg, #ff4b2b, #ff416c);
    color: white;
    border-radius: 10px;
    height: 3em;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# =============================
# SECRETS (SEGURO)
# =============================
def get_secret(name):
    try:
        return st.secrets[name]
    except:
        return None

SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_KEY = get_secret("SUPABASE_KEY")
OPENAI_KEY = get_secret("OPENAI_KEY")
RESEND_KEY = get_secret("RESEND_API_KEY")

# =============================
# CONEXÕES SEGURAS
# =============================
supabase = None
client = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except:
        pass

if OPENAI_KEY:
    try:
        client = OpenAI(api_key=OPENAI_KEY)
    except:
        pass

if RESEND_KEY:
    resend.api_key = RESEND_KEY

# =============================
# SESSION
# =============================
if "user" not in st.session_state:
    st.session_state.user = None

if "acesso" not in st.session_state:
    st.session_state.acesso = False

if "reset" not in st.session_state:
    st.session_state.reset = False

if "codigo" not in st.session_state:
    st.session_state.codigo = None

if "email_reset" not in st.session_state:
    st.session_state.email_reset = ""

# =============================
# TELA DE VENDA
# =============================
if not st.session_state.acesso:

    col1, col2 = st.columns(2)

    with col1:
        st.title("💰 Vida Financeira Blindada")

        st.markdown("""
        ### Saia do caos financeiro com inteligência

        ✔ Diagnóstico preciso  
        ✔ Plano estratégico  
        ✔ Clareza total  
        """)

        st.markdown(
    """
    <a href="SEU_LINK_KIWIFY" target="_blank">
        <button style="
            background-color:#00BFFF;
            color:white;
            padding:15px;
            border:none;
            border-radius:10px;
            width:100%;
            font-size:18px;
            font-weight:bold;
            cursor:pointer;
        ">
            🔥 Começar agora
        </button>
    </a>
    """,
    unsafe_allow_html=True
)

    with col2:
        st.markdown("""
        ### Você vai receber:

        📊 Análise completa  
        💡 Estratégia personalizada  
        🚀 Plano de ação  
        """)

        if st.button("Já tenho acesso", key="btn_acesso"):
            st.session_state.acesso = True
            st.rerun()

    st.stop()

# =============================
# LOGIN
# =============================
if not st.session_state.user:

    if st.button("⬅️ Voltar", key="voltar"):
        st.session_state.acesso = False
        st.rerun()

    st.subheader("Login")

    email = st.text_input("Email").lower()
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar", key="login"):

        if not supabase:
            st.error("Sistema temporariamente indisponível")
        else:
            try:
                res = supabase.table("usuarios").select("*").execute()
                usuarios = res.data or []

                user = next((u for u in usuarios if u["email"] == email), None)

                if user and user["senha"] == senha:
                    st.session_state.user = user
                    st.success("Login realizado")
                    st.rerun()

                elif user:
                    st.error("Senha incorreta")
                    st.session_state.reset = True
                    st.session_state.email_reset = email

                else:
                    st.error("Email não encontrado")

            except:
                st.error("Erro ao acessar banco")

# =============================
# RESET
# =============================
if st.session_state.reset:

    st.warning("Recuperar senha")

    if not st.session_state.codigo:

        if st.button("Enviar código"):

            codigo = str(random.randint(100000, 999999))
            st.session_state.codigo = codigo

            try:
                resend.Emails.send({
                    "from": "onboarding@resend.dev",
                    "to": [st.session_state.email_reset],
                    "subject": "Código",
                    "html": f"<h1>{codigo}</h1>"
                })
                st.success("Código enviado")
            except:
                st.info(f"Código (teste): {codigo}")

    else:

        cod = st.text_input("Código")
        nova = st.text_input("Nova senha", type="password")

        if st.button("Confirmar"):

            if cod == st.session_state.codigo:

                try:
                    supabase.table("usuarios").update({
                        "senha": nova
                    }).eq("email", st.session_state.email_reset).execute()

                    st.success("Senha atualizada")

                    st.session_state.reset = False
                    st.session_state.codigo = None

                except:
                    st.error("Erro ao atualizar")

            else:
                st.error("Código inválido")

# =============================
# IA
# =============================
if st.session_state.user:

    col1, col2 = st.columns([6,1])

    with col2:
        if st.button("Sair"):
            st.session_state.user = None
            st.session_state.acesso = False
            st.rerun()

    user = st.session_state.user
    uso = user.get("uso", 0)
    LIMITE = 5

    st.markdown(f"### Uso: {uso}/{LIMITE}")

    pergunta = st.text_area("Descreva sua situação")

    if st.button("Gerar plano"):

        if uso >= LIMITE:
            st.warning("Limite atingido")
        else:

            if not client:
                st.info("IA em modo demonstração")
                st.write("Organize gastos, corte excessos e priorize dívidas.")
            else:
                try:
                    r = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "Especialista financeiro"},
                            {"role": "user", "content": pergunta}
                        ]
                    )

                    resposta = r.choices[0].message.content
                    st.write(resposta)

                except:
                    st.warning("Erro na IA")

            # atualiza uso SEM quebrar
            try:
                novo = uso + 1
                supabase.table("usuarios").update({
                    "uso": novo
                }).eq("id", user["id"]).execute()

                st.session_state.user["uso"] = novo
            except:
                pass