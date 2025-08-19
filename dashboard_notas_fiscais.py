### Aqui está o script completo para você usar e adaptar:
!pip install streamlit

import pandas as pd
import streamlit as st
import plotly.express as px

# Título do dashboard
st.title("Dashboard de Notas Fiscais - CAR SP")

# --- Upload do arquivo ---
uploaded_file = st.file_uploader("Faça upload do arquivo Excel das notas fiscais", type=["xlsx"])

if uploaded_file is not None:
    # --- Carregar dados ---
    # Lê a aba correta, pulando as 5 primeiras linhas e pegando apenas as colunas B até I
    df_raw = pd.read_excel(
        uploaded_file,
        sheet_name="NF 22-25 CAR SP",
        skiprows=5,
        usecols="B:I",
        engine="openpyxl"
    )
    # Renomeia as colunas para facilitar o tratamento
    df_raw.columns = [
        "Nota Fiscal", "Emissão", "Tomador", "Descrição",
        "Valor Bruto", "Recebimento", "Valor Líquido", "Invoice"
    ]

    # Consolidar dados
    for col in ["Nota Fiscal", "Emissão", "Tomador", "Descrição", "Valor Bruto", "Recebimento", "Valor Líquido"]:
        df_raw[col] = df_raw[col].ffill()

    # Remover linhas sem invoice
    df_consolidado = df_raw[df_raw["Invoice"].notna()].copy()

    # Remover duplicatas para indicadores por nota fiscal
    df_unique_nf = df_consolidado.drop_duplicates(subset=["Nota Fiscal"])

    # Status de pagamento
    df_unique_nf["Status"] = df_unique_nf["Recebimento"].apply(lambda x: "Pago" if pd.notnull(x) else "Pendente")

    # Mês para agrupamento
    df_unique_nf["Mês"] = pd.to_datetime(df_unique_nf["Emissão"]).dt.to_period("M").astype(str)


    # Aqui você pode seguir com o processamento e visualização
    st.write(df_raw.head())

    # Streamlit layout
    st.title("Dashboard de Notas Fiscais - CAR SP")

    # Indicadores principais
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Notas", df_unique_nf["Nota Fiscal"].nunique())
    col2.metric("Valor Bruto Total", f"R$ {df_unique_nf['Valor Bruto'].sum():,.2f}")
    col3.metric("Valor Líquido Total", f"R$ {df_unique_nf['Valor Líquido'].sum():,.2f}")

    # Status de pagamento
    status_counts = df_unique_nf["Status"].value_counts()
    fig_status = px.pie(names=status_counts.index, values=status_counts.values, title="Status de Pagamento")
    st.plotly_chart(fig_status)

    # Evolução mensal do faturamento
    monthly = df_unique_nf.groupby("Mês")[["Valor Bruto", "Valor Líquido"]].sum().reset_index()
    fig_monthly = px.line(monthly, x="Mês", y=["Valor Bruto", "Valor Líquido"], title="Faturamento Mensal")
    st.plotly_chart(fig_monthly)

    # Top 10 clientes por valor bruto
    top_clientes = df_unique_nf.groupby("Tomador")["Valor Bruto"].sum().nlargest(10).reset_index()
    fig_top_clientes = px.bar(top_clientes, x="Tomador", y="Valor Bruto", title="Top 10 Clientes por Valor Bruto")
    st.plotly_chart(fig_top_clientes)

    # Distribuição de notas por cliente
    notas_por_cliente = df_unique_nf["Tomador"].value_counts().reset_index()
    notas_por_cliente.columns = ["Tomador", "Quantidade"]
    fig_dist_clientes = px.bar(notas_por_cliente, x="Tomador", y="Quantidade", title="Distribuição de Notas por Cliente")
    st.plotly_chart(fig_dist_clientes)

    # Filtros interativos
    st.sidebar.header("Filtros")
    cliente_filter = st.sidebar.multiselect("Filtrar por Cliente", options=df_unique_nf["Tomador"].unique())
    status_filter = st.sidebar.multiselect("Filtrar por Status", options=["Pago", "Pendente"])
    mes_filter = st.sidebar.multiselect("Filtrar por Mês", options=df_unique_nf["Mês"].unique())

    df_filtered = df_unique_nf.copy()
    if cliente_filter:
        df_filtered = df_filtered[df_filtered["Tomador"].isin(cliente_filter)]
    if status_filter:
        df_filtered = df_filtered[df_filtered["Status"].isin(status_filter)]
    if mes_filter:
        df_filtered = df_filtered[df_filtered["Mês"].isin(mes_filter)]

    st.subheader("Tabela de Notas Fiscais (Filtrada)")
    st.dataframe(df_filtered)

    # Barra de pesquisa
    st.subheader("🔍 Pesquisa por qualquer campo")
    search_term = st.text_input("Digite um termo para buscar")
    if search_term:
        mask = df_consolidado.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)
        df_search = df_consolidado[mask]
        # Agrupar por nota fiscal para mostrar resultado unificado (sem duplicatas de nota)
        df_search_grouped = df_search.groupby("Nota Fiscal").first().reset_index()
        st.write(f"Resultados encontrados para: {search_term}")
        st.dataframe(df_search_grouped)

else:
    st.warning("Por favor, faça upload do arquivo Excel para visualizar o dashboard.")
