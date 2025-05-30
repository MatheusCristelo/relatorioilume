import streamlit as st
import pandas as pd
import numpy as np
import base64
from datetime import datetime, timedelta
import io
import matplotlib.pyplot as plt
import tempfile
import os

# Configuração da página Streamlit
st.set_page_config(
    page_title="Ilume - Relatórios Financeiros",
    page_icon="📊",
    layout="wide"
)

# Cores da identidade visual da Ilume
VIOLETA = "#6F387C"
AMARELO = "#F59D30"
BEGE = "#F7E8C9"

# Aplicar CSS personalizado
st.markdown(f"""
<style>
    .main .block-container {{
        padding-top: 2rem;
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: {VIOLETA};
    }}
    .stButton>button {{
        background-color: {VIOLETA};
        color: white;
    }}
    .stButton>button:hover {{
        background-color: {AMARELO};
        color: white;
    }}
    .highlight {{
        background-color: {BEGE};
        padding: 20px;
        border-radius: 5px;
        margin-bottom: 20px;
    }}
    .header-ilume {{
        background-color: {VIOLETA};
        padding: 1.5rem;
        color: white;
        text-align: center;
        border-radius: 5px;
        margin-bottom: 2rem;
    }}
</style>
""", unsafe_allow_html=True)

# Cabeçalho da aplicação
st.markdown(f"""
<div class="header-ilume">
    <h1>Ilume Finanças</h1>
    <p>Gerador de Relatórios Financeiros</p>
</div>
""", unsafe_allow_html=True)

# Função para processar o arquivo carregado
def processar_arquivo(uploaded_file):
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(uploaded_file)
    else:
        st.error("Formato de arquivo não suportado. Por favor, envie um arquivo .csv, .xls ou .xlsx")
        return None
    
    # Padronizar nomes das colunas (lowercase e sem espaços)
    df.columns = [col.lower().strip().replace(' ', '_') for col in df.columns]
    
    # Verificar e converter colunas de data
    date_columns = ['data', 'vencimento', 'data_vencimento', 'recebimento', 'data_recebimento']
    for col in date_columns:
        if col in df.columns:
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            except:
                pass
    
    # Verificar e converter colunas de valor
    value_columns = ['valor', 'valor_total', 'a_receber', 'valor_recebido']
    for col in value_columns:
        if col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            except:
                pass
    
    return df

# Função para gerar relatório HTML
def gerar_relatorio_html(df, filtros, colunas_selecionadas):
    # Criar HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Relatório Financeiro Ilume</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
            }}
            .header {{
                background-color: {VIOLETA};
                color: white;
                padding: 20px;
                text-align: center;
            }}
            .container {{
                padding: 20px;
            }}
            .summary {{
                background-color: {BEGE};
                padding: 15px;
                margin-bottom: 20px;
                border-radius: 5px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            th {{
                background-color: {VIOLETA};
                color: white;
                padding: 10px;
                text-align: left;
            }}
            td {{
                padding: 8px;
                border-bottom: 1px solid #ddd;
            }}
            tr:nth-child(even) {{
                background-color: #f2f2f2;
            }}
            .em-aberto {{
                background-color: {AMARELO};
                color: white;
                padding: 5px;
                border-radius: 3px;
            }}
            .filters {{
                margin-bottom: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Relatório de Contas a Receber</h1>
        </div>
        <div class="container">
    """
    
    # Adicionar informações de filtro
    if filtros['data_inicio'] or filtros['data_fim'] or filtros['cliente'] or filtros['categoria']:
        html += '<div class="filters"><h2>Filtros aplicados</h2><ul>'
        if filtros['data_inicio'] and filtros['data_fim']:
            html += f'<li>Período: {filtros["data_inicio"].strftime("%d/%m/%Y")} a {filtros["data_fim"].strftime("%d/%m/%Y")}</li>'
        if filtros['cliente']:
            html += f'<li>Cliente: {filtros["cliente"]}</li>'
        if filtros['categoria']:
            html += f'<li>Categoria: {filtros["categoria"]}</li>'
        html += '</ul></div>'
    
    # Calcular resumo financeiro
    resumo = {}
    
    # Verificar se as colunas necessárias existem
    valor_col = next((col for col in ['valor', 'valor_total', 'a_receber'] if col in df.columns), None)
    data_col = next((col for col in ['data', 'vencimento', 'data_vencimento'] if col in df.columns), None)
    
    if valor_col and data_col:
        # Converter para datetime se necessário
        if not pd.api.types.is_datetime64_dtype(df[data_col]):
            df[data_col] = pd.to_datetime(df[data_col], errors='coerce')
        
        hoje = datetime.now().date()
        
        # Calcular valores para o resumo
        vencidos = df[df[data_col].dt.date < hoje][valor_col].sum()
        vencem_hoje = df[df[data_col].dt.date == hoje][valor_col].sum()
        a_vencer = df[df[data_col].dt.date > hoje][valor_col].sum()
        
        # Verificar se existe coluna de recebimento
        recebimento_col = next((col for col in ['recebimento', 'data_recebimento'] if col in df.columns), None)
        if recebimento_col:
            recebidos = df[~df[recebimento_col].isna()][valor_col].sum()
        else:
            recebidos = 0
            
        total = df[valor_col].sum()
        
        resumo = {
            'Vencidos (R$)': f"R$ {vencidos:,.2f}".replace(',', '.').replace('.', ',', 1),
            'Vencem hoje (R$)': f"R$ {vencem_hoje:,.2f}".replace(',', '.').replace('.', ',', 1),
            'A vencer (R$)': f"R$ {a_vencer:,.2f}".replace(',', '.').replace('.', ',', 1),
            'Recebidos (R$)': f"R$ {recebidos:,.2f}".replace(',', '.').replace('.', ',', 1),
            'Total do Período (R$)': f"R$ {total:,.2f}".replace(',', '.').replace('.', ',', 1)
        }
    
    # Adicionar bloco de resumo
    if resumo:
        html += '<div class="summary"><h2>Resumo Financeiro</h2><table>'
        for k, v in resumo.items():
            html += f'<tr><td><strong>{k}</strong></td><td>{v}</td></tr>'
        html += '</table></div>'
    
    # Adicionar tabela de dados
    html += '<h2>Detalhamento</h2>'
    
    # Preparar dados para a tabela
    if not colunas_selecionadas:
        colunas_selecionadas = df.columns.tolist()
    
    # Mapear nomes de colunas para exibição mais amigável
    mapeamento_colunas = {
        'data': 'Data',
        'data_vencimento': 'Vencimento',
        'vencimento': 'Vencimento',
        'data_recebimento': 'Recebimento',
        'recebimento': 'Recebimento',
        'descricao': 'Descrição',
        'cliente': 'Cliente',
        'categoria': 'Categoria',
        'valor': 'Valor (R$)',
        'valor_total': 'Valor Total (R$)',
        'a_receber': 'A Receber (R$)',
        'situacao': 'Situação'
    }
    
    # Cabeçalho da tabela
    headers = [mapeamento_colunas.get(col, col.replace('_', ' ').title()) for col in colunas_selecionadas]
    
    html += '<table><tr>'
    for header in headers:
        html += f'<th>{header}</th>'
    html += '</tr>'
    
    # Dados da tabela
    for _, row in df.iterrows():
        html += '<tr>'
        for col in colunas_selecionadas:
            value = row.get(col, '')
            
            # Formatar datas
            if pd.api.types.is_datetime64_dtype(type(value)):
                if not pd.isna(value):
                    value = value.strftime('%d/%m/%Y')
                else:
                    value = ''
            
            # Formatar valores monetários
            elif col in ['valor', 'valor_total', 'a_receber']:
                if pd.notna(value):
                    value = f"R$ {value:,.2f}".replace(',', '.').replace('.', ',', 1)
                else:
                    value = ''
            
            # Converter para string
            if pd.isna(value):
                value = ''
            else:
                value = str(value)
            
            # Destacar "Em aberto"
            if col == 'situacao' and value.lower() == 'em aberto':
                html += f'<td><span class="em-aberto">{value}</span></td>'
            else:
                html += f'<td>{value}</td>'
        
        html += '</tr>'
    
    html += '</table>'
    
    # Fechar HTML
    html += """
        </div>
    </body>
    </html>
    """
    
    return html

# Função para criar um link de download para HTML
def get_download_link_html(html_content, filename):
    b64 = base64.b64encode(html_content.encode()).decode()
    href = f'<a href="data:text/html;base64,{b64}" download="{filename}" style="display: inline-block; padding: 0.5rem 1rem; background-color: {VIOLETA}; color: white; text-decoration: none; border-radius: 4px; font-weight: bold; margin-top: 1rem;">📥 Baixar Relatório HTML</a>'
    return href

# Interface principal
st.markdown('<div class="highlight">', unsafe_allow_html=True)
st.write("### Upload de Arquivo")
st.write("Faça upload do seu arquivo Excel (.xlsx) ou CSV (.csv) com dados financeiros.")
uploaded_file = st.file_uploader("Escolha um arquivo", type=['csv', 'xlsx', 'xls'])
st.markdown('</div>', unsafe_allow_html=True)

# Se um arquivo foi carregado
if uploaded_file is not None:
    # Processar o arquivo
    df = processar_arquivo(uploaded_file)
    
    if df is not None:
        st.success(f"Arquivo carregado com sucesso! {len(df)} registros encontrados.")
        
        # Exibir as primeiras linhas
        st.write("### Visualização dos Dados")
        st.dataframe(df.head())
        
        # Sidebar para filtros
        st.sidebar.title("Filtros")
        
        # Filtro de data
        st.sidebar.subheader("Período")
        
        # Identificar coluna de data
        data_col = next((col for col in ['data', 'vencimento', 'data_vencimento'] if col in df.columns), None)
        
        data_inicio = None
        data_fim = None
        
        if data_col:
            # Converter para datetime se necessário
            if not pd.api.types.is_datetime64_dtype(df[data_col]):
                df[data_col] = pd.to_datetime(df[data_col], errors='coerce')
            
            # Obter datas mínima e máxima
            min_date = df[data_col].min().date()
            max_date = df[data_col].max().date()
            
            # Definir datas padrão (último mês)
            default_start = max_date - timedelta(days=30)
            
            # Widgets de seleção de data
            data_inicio = st.sidebar.date_input("Data Inicial", value=default_start, min_value=min_date, max_value=max_date)
            data_fim = st.sidebar.date_input("Data Final", value=max_date, min_value=min_date, max_value=max_date)
            
            # Validar intervalo de datas
            if data_inicio > data_fim:
                st.sidebar.error("Data inicial deve ser anterior à data final")
                data_inicio = data_fim
        
        # Filtro de cliente
        cliente_col = next((col for col in ['cliente', 'nome_cliente'] if col in df.columns), None)
        cliente_selecionado = None
        
        if cliente_col:
            clientes = ['Todos'] + sorted(df[cliente_col].dropna().unique().tolist())
            cliente_selecionado = st.sidebar.selectbox("Cliente", clientes)
            
            if cliente_selecionado == 'Todos':
                cliente_selecionado = None
        
        # Filtro de categoria
        categoria_col = next((col for col in ['categoria', 'tipo', 'classificacao'] if col in df.columns), None)
        categoria_selecionada = None
        
        if categoria_col:
            categorias = ['Todas'] + sorted(df[categoria_col].dropna().unique().tolist())
            categoria_selecionada = st.sidebar.selectbox("Categoria", categorias)
            
            if categoria_selecionada == 'Todas':
                categoria_selecionada = None
        
        # Aplicar filtros
        df_filtrado = df.copy()
        
        if data_col and data_inicio and data_fim:
            df_filtrado = df_filtrado[(df_filtrado[data_col].dt.date >= data_inicio) & 
                                     (df_filtrado[data_col].dt.date <= data_fim)]
        
        if cliente_col and cliente_selecionado:
            df_filtrado = df_filtrado[df_filtrado[cliente_col] == cliente_selecionado]
        
        if categoria_col and categoria_selecionada:
            df_filtrado = df_filtrado[df_filtrado[categoria_col] == categoria_selecionada]
        
        # Exibir contagem após filtros
        st.write(f"**Registros após filtros:** {len(df_filtrado)}")
        
        # Seleção de colunas
        st.sidebar.subheader("Colunas do Relatório")
        
        # Colunas padrão recomendadas
        colunas_padrao = ['vencimento', 'recebimento', 'descricao', 'cliente', 'categoria', 'valor', 'situacao']
        colunas_disponiveis = df.columns.tolist()
        
        # Mapear colunas disponíveis para nomes mais amigáveis
        mapeamento_colunas = {
            'data': 'Data',
            'data_vencimento': 'Vencimento',
            'vencimento': 'Vencimento',
            'data_recebimento': 'Recebimento',
            'recebimento': 'Recebimento',
            'descricao': 'Descrição',
            'cliente': 'Cliente',
            'categoria': 'Categoria',
            'valor': 'Valor',
            'valor_total': 'Valor Total',
            'a_receber': 'A Receber',
            'situacao': 'Situação'
        }
        
        # Criar opções de seleção com nomes amigáveis
        opcoes_colunas = {col: mapeamento_colunas.get(col, col.replace('_', ' ').title()) for col in colunas_disponiveis}
        
        # Pré-selecionar colunas padrão se disponíveis
        colunas_pre_selecionadas = [col for col in colunas_padrao if col in colunas_disponiveis]
        if not colunas_pre_selecionadas:
            colunas_pre_selecionadas = colunas_disponiveis[:min(8, len(colunas_disponiveis))]
        
        # Widget de seleção de colunas
        colunas_selecionadas = st.sidebar.multiselect(
            "Selecione as colunas para o relatório",
            options=colunas_disponiveis,
            default=colunas_pre_selecionadas,
            format_func=lambda x: opcoes_colunas.get(x, x)
        )
        
        # Botão para gerar relatório
        st.markdown('<div class="highlight">', unsafe_allow_html=True)
        st.write("### Geração de Relatório")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write("Clique no botão ao lado para gerar o relatório com os filtros aplicados.")
        
        with col2:
            gerar_relatorio = st.button("Gerar Relatório")
        
        # Gerar relatório quando solicitado
        if gerar_relatorio:
            if len(df_filtrado) > 0:
                with st.spinner('Gerando relatório...'):
                    # Preparar filtros para o relatório
                    filtros = {
                        'data_inicio': data_inicio if data_inicio else None,
                        'data_fim': data_fim if data_fim else None,
                        'cliente': cliente_selecionado,
                        'categoria': categoria_selecionada
                    }
                    
                    # Gerar o relatório HTML
                    html_content = gerar_relatorio_html(df_filtrado, filtros, colunas_selecionadas)
                    
                    # Nome do arquivo
                    now = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"Relatorio_Ilume_{now}.html"
                    
                    # Criar link de download
                    st.markdown(get_download_link_html(html_content, filename), unsafe_allow_html=True)
                    st.success("Relatório gerado com sucesso!")
                    
                    # Mostrar prévia do relatório
                    st.write("### Prévia do Relatório")
                    st.components.v1.html(html_content, height=600, scrolling=True)
            else:
                st.error("Não há dados para gerar o relatório. Verifique os filtros aplicados.")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Exibir dados filtrados
        st.write("### Dados Filtrados")
        st.dataframe(df_filtrado)

else:
    # Instruções iniciais
    st.info("👆 Faça upload de um arquivo Excel ou CSV para começar.")
    
    # Exemplo de estrutura esperada
    st.write("### Estrutura de Dados Esperada")
    st.write("""
    O arquivo deve conter colunas como:
    - **Vencimento** ou **Data**: Data de vencimento da conta
    - **Recebimento**: Data de recebimento (se houver)
    - **Descrição**: Descrição da transação
    - **Cliente**: Nome do cliente
    - **Categoria**: Categoria da transação
    - **Valor**: Valor da transação
    - **Situação**: Status da transação (ex: "Em aberto", "Pago")
    """)
    
    # Mostrar exemplo
    st.write("### Exemplo de Dados")
    
    # Criar DataFrame de exemplo
    exemplo = pd.DataFrame({
        'vencimento': pd.date_range(start='2025-05-01', periods=5),
        'recebimento': [pd.NaT, pd.NaT, '2025-05-03', pd.NaT, pd.NaT],
        'descricao': ['Serviço de Consultoria', 'Venda de Produto', 'Manutenção', 'Assinatura Mensal', 'Projeto Especial'],
        'cliente': ['Empresa ABC', 'Cliente XYZ', 'Empresa 123', 'Cliente 456', 'Empresa DEF'],
        'categoria': ['Serviços', 'Produtos', 'Manutenção', 'Assinatura', 'Projetos'],
        'valor': [1500.00, 2750.50, 850.00, 199.90, 3200.00],
        'situacao': ['Em aberto', 'Em aberto', 'Pago', 'Em aberto', 'Em aberto']
    })
    
    # Converter para datetime
    exemplo['recebimento'] = pd.to_datetime(exemplo['recebimento'], errors='coerce')
    
    # Exibir exemplo
    st.dataframe(exemplo)

# Rodapé
st.markdown("""
---
Desenvolvido para Ilume Finanças | 2025
""")
