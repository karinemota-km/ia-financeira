import streamlit as st
import random
import resend
from supabase import create_client
from openai import OpenAI

# =============================
# 🎨 CONFIG + ESTILO PREMIUM
# =============================
st.set_page_config(layout="wide")

st.markdown("""
<style>
body {background-color: #0e1117;}
h1, h2, h3, h4 {color: white;}
.stButton>button {
    background: linear-gradient(90deg, #ff4b2b, #ff416c);
    color: white;
    border-radius: 8px;
    height: 3em;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# =============================
# 🔐 SECRETS
# =============================
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    OPENAI_KEY = st.secrets["OPENAI_KEY"]
    RESEND_API_KEY = st.secrets["RESEND_API_KEY"]
except:
    st.error("Configure os Secrets no Streamlit")
    st.stop()

resend.api_key = RESEND_API_KEY

# =============================
# 🔌 CONEXÕES
# =============================
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
client = OpenAI(api_key=OPENAI_KEY)

# =============================
# 🔐 SESSION
# =============================
if "user" not in st.session_state:
    st.session_state.user = None

if "acesso_liberado" not in st.session_state:
    st.session_state.acesso_liberado = False

if "reset_mode" not in st.session_state:
    st.session_state.reset_mode = False

if "codigo_reset" not in st.session_state:
    st.session_state.codigo_reset = None

if "email_reset" not in st.session_state:
    st.session_state.email_reset = ""

# =============================
# 🎯 TELA DE VENDA
# =============================
if not st.session_state.acesso_liberado:

    col1, col2 = st.columns([1,1])

    with col1:
        st.title("💰 Vida Financeira Blindada")

        st.markdown("""
        ### Pare de viver no sufoco financeiro

        ✔ Diagnóstico completo  
        ✔ Plano estratégico  
        ✔ Clareza total  

        🔒 Acesso exclusivo
        """)
        if st.button("[Já tenho acesso](SEU_LINK_KIWIFY)"):
            st.session_state.acesso_liberado = True
            st.rerun()    
        st.markdown("[🔥 QUERO ACESSAR AGORA](SEU_LINK_KIWIFY)")

    with col2:
        st.markdown("""
        ### O que você recebe:

        📊 Análise financeira  
        💡 Estratégia personalizada  
        🚀 Plano de ação imediato  
        """)

        if st.button("Já tenho acesso"):
            st.session_state.acesso_liberado = True
            st.rerun()

    st.stop()

# =============================
# 🔐 LOGIN
# =============================
if not st.session_state.user:

    if st.button("⬅️ Voltar"):
        st.session_state.acesso_liberado = False
        st.rerun()

    st.subheader("Acesse sua conta")

    email = st.text_input("Email").strip().lower()
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):

        resposta = supabase.table("usuarios").select("*").execute()
        usuarios = resposta.data

        usuario = next((u for u in usuarios if u["email"].strip().lower() == email), None)

        if usuario and usuario["senha"] == senha:
            st.session_state.user = usuario
            st.success("Login realizado")
            st.rerun()

        elif usuario:
            st.error("Senha incorreta")
            st.session_state.reset_mode = True
            st.session_state.email_reset = email

        else:
            st.error("Email não encontrado")

# =============================
# 🔑 RECUPERAÇÃO
# =============================
if st.session_state.reset_mode:

    st.warning("🔑 Recuperação de senha")

    if st.session_state.codigo_reset is None:

        if st.button("Enviar código"):

            codigo = str(random.randint(100000, 999999))
            st.session_state.codigo_reset = codigo

            try:
                resend.Emails.send({
                    "from": "onboarding@resend.dev",
                    "to": [st.session_state.email_reset],
                    "subject": "Recuperação de senha",
                    "html": f"<h1>{codigo}</h1>"
                })
                st.success("Código enviado para o email!")

            except:
                st.warning("Modo teste ativo")
                st.info(f"Código: {codigo}")

    else:

        codigo_digitado = st.text_input("Digite o código")
        nova_senha = st.text_input("Nova senha", type="password")

        if st.button("Confirmar nova senha"):

            if codigo_digitado == st.session_state.codigo_reset:

                supabase.table("usuarios").update({
                    "senha": nova_senha
                }).eq("email", st.session_state.email_reset).execute()

                st.success("Senha redefinida!")

                st.session_state.reset_mode = False
                st.session_state.codigo_reset = None
                st.session_state.email_reset = ""

            else:
                st.error("Código inválido")

# =============================
# 🤖 IA
# =============================
if st.session_state.user:

    col1, col2 = st.columns([6,1])

    with col2:
        if st.button("🚪 Sair"):
            st.session_state.user = None
            st.session_state.acesso_liberado = False
            st.rerun()

    user = st.session_state.user
    uso = user["uso"]
    LIMITE = 5

    st.markdown(f"### 📊 Uso: {uso}/{LIMITE}")

    pergunta = st.text_area("Descreva sua situação financeira:")

    if st.button("Gerar plano financeiro"):

        if uso < LIMITE:

            if not OPENAI_KEY:
                st.warning("IA indisponível no momento")

            else:
                try:
                    resposta = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {
                                "role": "system",
                                "content": "Você é especialista em reeducação financeira. Responda com diagnóstico, plano e ação."
                            },
                            {"role": "user", "content": pergunta}
                        ]
                    )

                    st.success("Plano gerado com sucesso!")
                    st.write(resposta.choices[0].message.content)

                    novo_uso = uso + 1

                    supabase.table("usuarios").update({
                        "uso": novo_uso
                    }).eq("id", user["id"]).execute()

                    st.session_state.user["uso"] = novo_uso

                except Exception as e:
                    st.error(f"Erro: {e}")

        else:
            st.warning("🚫 Limite atingido")