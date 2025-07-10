
import streamlit as st
import pandas as pd
import os
from datetime import date

# Configurações iniciais
st.set_page_config(page_title="Gestão Vinted", layout="wide")
data_file = "vinted_dados.csv"

# Verifica se o ficheiro CSV existe, caso contrário cria um
if not os.path.exists(data_file):
    df_init = pd.DataFrame(columns=[
        "Tipo", "Item", "Preco_Compra", "Preco_Proposto", "Preco_Venda",
        "Data_Anuncio", "Data_Venda", "Gastos", "Outros_Gastos", "Lucro"
    ])
    df_init.to_csv(data_file, index=False)

def carregar_dados():
    return pd.read_csv(data_file, parse_dates=["Data_Anuncio"], dayfirst=True)

def guardar_dados(df):
    df.to_csv(data_file, index=False)

def calcular_lucro(row):
    if pd.notnull(row["Preco_Venda"]):
        total_gastos = row["Preco_Compra"] + row.get("Gastos", 0) + row.get("Outros_Gastos", 0)
        return row["Preco_Venda"] - total_gastos
    return None

st.sidebar.title("Menu")
pagina = st.sidebar.selectbox("Escolhe a página:", [
    "Dashboard", "Adicionar Novo Item", "Inventário", "Análise Financeira"
])

df = carregar_dados()

# Converter Data_Venda explicitamente para datetime
df["Data_Venda"] = pd.to_datetime(df["Data_Venda"], errors="coerce")

if pagina == "Dashboard":
    st.title("Resumo de Vendas")

    total_vendas = df["Preco_Venda"].sum(skipna=True)
    total_gastos = df[["Preco_Compra", "Gastos", "Outros_Gastos"]].sum(skipna=True).sum()
    lucro_total = df.apply(calcular_lucro, axis=1).sum(skipna=True)
    vendidos = df["Preco_Venda"].notna().sum()
    ativos = df["Preco_Venda"].isna().sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Vendas (€)", f"{total_vendas:.2f}")
    col2.metric("Total de Gastos (€)", f"{total_gastos:.2f}")
    col3.metric("Lucro Total (€)", f"{lucro_total:.2f}")

    df_vendidos = df[df["Preco_Venda"].notna() & df["Data_Venda"].notna()]
    if not df_vendidos.empty:
        vendas_mensais = df_vendidos.groupby(df_vendidos["Data_Venda"].dt.to_period("M")).sum(numeric_only=True)["Preco_Venda"]
        st.bar_chart(vendas_mensais)
    else:
        st.info("Ainda não existem vendas com data registada para apresentar no gráfico.")

elif pagina == "Adicionar Novo Item":
    st.title("Adicionar Novo Item")
    with st.form("novo_item"):
        tipo = st.text_input("Tipo")
        item = st.text_input("Descrição do Item")
        preco_compra = st.number_input("Preço de Compra (€)", min_value=0.0, step=0.1)
        preco_proposto = st.number_input("Preço Proposto (€)", min_value=0.0, step=0.1)
        data_anuncio = st.date_input("Data de Anúncio", value=date.today())
        gastos = st.number_input("Gastos adicionais (€)", min_value=0.0, step=0.1)
        outros_gastos = st.number_input("Outros Gastos (€)", min_value=0.0, step=0.1)
        submitted = st.form_submit_button("Adicionar")

        if submitted:
            novo = pd.DataFrame([{
                "Tipo": tipo,
                "Item": item,
                "Preco_Compra": preco_compra,
                "Preco_Proposto": preco_proposto,
                "Preco_Venda": None,
                "Data_Anuncio": data_anuncio,
                "Data_Venda": None,
                "Gastos": gastos,
                "Outros_Gastos": outros_gastos,
                "Lucro": None
            }])
            df = pd.concat([df, novo], ignore_index=True)
            guardar_dados(df)
            st.success("Item adicionado com sucesso!")

elif pagina == "Inventário":
    st.title("Inventário de Itens")
    filtro_tipo = st.selectbox("Filtrar por tipo:", ["Todos"] + df["Tipo"].dropna().unique().tolist())

    if filtro_tipo != "Todos":
        df_filtrado = df[df["Tipo"] == filtro_tipo]
    else:
        df_filtrado = df

    st.dataframe(df_filtrado)

elif pagina == "Análise Financeira":
    st.title("Análise Financeira")

    df["Lucro"] = df.apply(calcular_lucro, axis=1)
    lucro_medio_tipo = df.groupby("Tipo")["Lucro"].mean().dropna()
    custo_medio = df.groupby("Tipo")["Preco_Compra"].mean().dropna()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Lucro Médio por Tipo")
        st.bar_chart(lucro_medio_tipo)
    with col2:
        st.subheader("Preço de Compra Médio por Tipo")
        st.bar_chart(custo_medio)

    st.write("Tabela de Lucros por Item")
    st.dataframe(df[["Tipo", "Item", "Lucro"]].dropna())
