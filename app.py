st.set_page_config(layout="wide")
st.markdown("""<style>
button { width: 100%; }
</style>""", unsafe_allow_html=True)

import streamlit as st
import random
import resend
import os
from supabase import create_client
from openai import OpenAI

# =============================
# 🔧 CONFIGURAÇÃO DA PÁGINA
# =============================
st.set_page_config(layout="wide")

# =============================
# 🔐 KEYS 
# =============================

import os

OPENAI_KEY = os.getenv("OPENAI_KEY")

import streamlit as st

SUPABASE_URL = st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY")

st.write("DEBUG URL:", SUPABASE_URL)
st.write("KEY:", SUPABASE_KEY)

resend.api_key = os.getenv("RESEND_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
client = OpenAI(api_key=OPENAI_KEY)

# 🔐 SESSION STATE
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
        ### Você não precisa mais viver no sufoco financeiro

        ✔ Diagnóstico completo  
        ✔ Plano personalizado  
        ✔ Clareza financeira  

        🔒 Acesso exclusivo para usuários
        """)

        if st.button("🔥 Quero organizar minha vida agora", key="btn_pagamento"):
            st.markdown("[PAGAR AGORA](SEU_LINK_KIWIFY)")

    with col2:
        st.markdown("""
        ### O que você vai receber:

        📊 Análise financeira completa  
        💡 Estratégia personalizada  
        🚀 Plano de ação  

        ---
        """)

        if st.button("Já tenho acesso", key="btn_ir_login"):
            st.session_state.acesso_liberado = True
            st.rerun()

    st.stop()

# =============================
# 🔐 LOGIN
# =============================
st.markdown("""
        ### A sua melhor decisão 🚀
        """)
if not st.session_state.user:

    if st.button("⬅️ Voltar", key="btn_voltar"):
     st.session_state.acesso_liberado = False
    st.rerun()

    st.subheader("Login")

    email = st.text_input("Email").strip().lower()
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar", key="btn_login"):

        resposta = supabase.table("usuarios").select("*").execute()
        usuarios = resposta.data

        usuario = next((u for u in usuarios if u["email"].strip().lower() == email), None)

        if usuario:

            if usuario["senha"] == senha:
                st.session_state.user = usuario
                st.success("Login realizado")
                st.rerun()

            else:
                st.error("Senha incorreta")
                st.session_state.reset_mode = True
                st.session_state.email_reset = email

        else:
            st.error("Email não encontrado")

# =============================
# 🔑 RECUPERAÇÃO DE SENHA
# =============================
if st.session_state.reset_mode:

    st.warning("🔑 Recuperação de senha")

    if st.session_state.codigo_reset is None:

        if st.button("Enviar código", key="btn_enviar_codigo"):

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

            except Exception as e:
                st.error("Erro ao enviar email")
                st.write(e)

    else:

        codigo_digitado = st.text_input("Digite o código")
        nova_senha = st.text_input("Nova senha", type="password")

        if st.button("Confirmar nova senha", key="btn_confirmar_reset"):

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
# 🤖 ÁREA DA IA
# =============================
if st.session_state.user:

    col1, col2 = st.columns([6,1])

    with col2:
        if st.button("🚪 Sair", key="btn_logout"):
            st.session_state.user = None
            st.session_state.acesso_liberado = False
            st.rerun()

    user = st.session_state.user
    uso = user["uso"]
    LIMITE = 5

    st.write(f"Uso: {uso}/{LIMITE}")

    pergunta = st.text_area("Descreva sua situação financeira:")

    if st.button("Analisar", key="btn_analise"):

        if uso < LIMITE:

            try:
                resposta = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Você é especialista em finanças."},
                        {"role": "user", "content": pergunta}
                    ]
                )

                st.write(resposta.choices[0].message.content)

                novo_uso = uso + 1

                supabase.table("usuarios").update({
                    "uso": novo_uso
                }).eq("id", user["id"]).execute()

                st.session_state.user["uso"] = novo_uso

            except Exception as e:
                st.error(f"Erro: {e}")

        else:
            st.warning("Limite atingido")