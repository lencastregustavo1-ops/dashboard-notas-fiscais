import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard de Notas Fiscais", layout="wide")
st.title("Dashboard de Notas Fiscais - CAR SP")

# --- Função para carregar dados com cache ---
@st.cache_data(show_spinner="Carregando dados...")
def load_data(uploaded_file):
    try:
        df = pd.read_excel(
            uploaded_file,
            sheet_name="NF 22-25 CAR SP",
            skiprows=5,
            usecols="B:I",
            engine="openpyxl"
        )
        df.columns = [
            "Nota Fiscal", "Emissão", "Tomador", "Descrição",
            "Valor Bruto", "Recebimento", "Valor Líquido", "Invoice"
        ]
        for col in ["Nota Fiscal", "Emissão", "Tomador", "Descrição", "Valor Bruto", "Recebimento", "Valor Líquido"]:
            df[col] = df[col].ffill()
        df = df[df["Invoice"].notna()].copy()
        return df
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")
        return None

# --- Upload do arquivo ---
uploaded_file = st.file_uploader("Faça upload do arquivo Excel das notas fiscais", type=["xlsx"])

if uploaded_file:
    df_consolidado = load_data(uploaded_file)
    if df_consolidado is not None and not df_consolidado.empty:
        # Remover duplicatas para indicadores por nota fiscal
        df_unique_nf = df_consolidado.drop_duplicates(subset=["Nota Fiscal"]).copy()
        df_unique_nf["Status"] = df_unique_nf["Recebimento"].apply(lambda x: "Pago" if pd.notnull(x) else "Pendente")
        df_unique_nf["Mês"] = pd.to_datetime(df_unique_nf["Emissão"]).dt.to_period("M").astype(str)

        # --- Filtros interativos ---
        with st.sidebar:
            st.header("Filtros")
            clientes = sorted(df_unique_nf["Tomador"].dropna().unique())
            status_opcoes = ["Pago", "Pendente"]
            meses = sorted(df_unique_nf["Mês"].dropna().unique())

            cliente_filter = st.multiselect("Filtrar por Cliente", options=clientes)
            status_filter = st.multiselect("Filtrar por Status", options=status_opcoes)
            mes_filter = st.multiselect("Filtrar por Mês", options=meses)

        df_filtered = df_unique_nf.copy()
        if cliente_filter:
            df_filtered = df_filtered[df_filtered["Tomador"].isin(cliente_filter)]
        if status_filter:
            df_filtered = df_filtered[df_filtered["Status"].isin(status_filter)]
        if mes_filter:
            df_filtered = df_filtered[df_filtered["Mês"].isin(mes_filter)]

        # --- Indicadores principais ---
        st.subheader("📌 Indicadores Principais")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de Notas", df_filtered["Nota Fiscal"].nunique())
        col2.metric("Total de Invoices", df_consolidado["Invoice"].nunique())
        col3.metric("Valor Bruto Total", f"R$ {df_filtered['Valor Bruto'].sum():,.2f}")
        col4.metric("Valor Líquido Total", f"R$ {df_filtered['Valor Líquido'].sum():,.2f}")

        # --- Status de pagamento ---
        st.subheader("📊 Status de Pagamento")
        status_counts = df_filtered["Status"].value_counts()
        fig_status = px.pie(
            names=status_counts.index,
            values=status_counts.values,
            title="Distribuição de Pagamento"
        )
        st.plotly_chart(fig_status, use_container_width=True)

        # --- Evolução mensal do faturamento ---
        st.subheader("📈 Faturamento Mensal")
        monthly = df_filtered.groupby("Mês")[["Valor Bruto", "Valor Líquido"]].sum().reset_index()
        fig_monthly = px.line(
            monthly,
            x="Mês",
            y=["Valor Bruto", "Valor Líquido"],
            markers=True,
            title="Evolução Mensal do Faturamento"
        )
        st.plotly_chart(fig_monthly, use_container_width=True)

        # --- Top 10 clientes por valor bruto ---
        st.subheader("🏆 Top 10 Clientes por Valor Bruto")
        top_clientes = df_filtered.groupby("Tomador")["Valor Bruto"].sum().nlargest(10).reset_index()
        fig_top_clientes = px.bar(
            top_clientes,
            x="Tomador",
            y="Valor Bruto",
            title="Top 10 Clientes",
            text_auto=True
        )
        st.plotly_chart(fig_top_clientes, use_container_width=True)

        # --- Distribuição de notas por cliente ---
        st.subheader("📋 Distribuição de Notas por Cliente")
        notas_por_cliente = df_filtered["Tomador"].value_counts().reset_index()
        notas_por_cliente.columns = ["Tomador", "Quantidade"]
        fig_dist_clientes = px.bar(
            notas_por_cliente,
            x="Tomador",
            y="Quantidade",
            title="Quantidade de Notas por Cliente",
            text_auto=True
        )
        st.plotly_chart(fig_dist_clientes, use_container_width=True)

        # --- Tabela dinâmica filtrada ---
        with st.expander("📑 Tabela de Notas Fiscais (Filtrada)", expanded=False):
            st.dataframe(df_filtered)
