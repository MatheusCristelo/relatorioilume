import streamlit as st
import pandas as pd
import numpy as np
import base64
from datetime import datetime, timedelta
import io
from fpdf import FPDF
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
    .download-button {{
        display: inline-block;
        padding: 0.5rem 1rem;
        background-color: {VIOLETA};
        color: white;
        text-decoration: none;
        border-radius: 4px;
        font-weight: bold;
        margin-top: 1rem;
    }}
    .download-button:hover {{
        background-color: {AMARELO};
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

# Classe PDF personalizada usando FPDF
class PDF(FPDF):
    def __init__(self):
        super().__init__(orientation='L', unit='mm', format='A4')
        self.add_page()
        self.set_auto_page_break(auto=True, margin=15)
        
    def header(self):
        # Cabeçalho violeta
        self.set_fill_color(111, 56, 124)  # Violeta: #6F387C
        self.rect(0, 0, 297, 20, 'F')
        
        # Texto do cabeçalho
        self.set_font('Arial', 'B', 16)
        self.set_text_color(255, 255, 255)  # Branco
        self.cell(0, 15, 'Relatório de Contas a Receber', 0, 1, 'C')
        
        # Espaço após o cabeçalho
        self.ln(5)
        
    def footer(self):
        # Posição a 15mm do final
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Ilume Finanças - Relatório gerado em {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 0, 'C')
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'R')
        
    def add_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.set_text_color(111, 56, 124)  # Violeta
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(2)
        
    def add_subtitle(self, subtitle):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(111, 56, 124)  # Violeta
        self.cell(0, 8, subtitle, 0, 1, 'L')
        self.ln(2)
        
    def add_info_line(self, label, value):
        self.set_font('Arial', '', 10)
        self.set_text_color(0, 0, 0)
        self.cell(40, 6, label, 0, 0, 'L')
        self.cell(0, 6, value, 0, 1, 'L')
        
    def add_summary_box(self, resumo):
        # Bloco de resumo com fundo bege
        self.set_fill_color(247, 232, 201)  # Bege: #F7E8C9
        self.set_draw_color(200, 200, 200)  # Cinza claro para bordas
        
        # Calcular altura do bloco
        num_items = len(resumo)
        box_height = num_items * 8 + 10  # 8mm por item + margens
        
        # Desenhar retângulo de fundo
        start_y = self.get_y()
        self.rect(10, start_y, 277, box_height, 'DF')
        
        # Título do resumo
        self.set_xy(15, start_y + 5)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(111, 56, 124)  # Violeta
        self.cell(0, 8, 'Resumo Financeiro', 0, 1, 'L')
        
        # Itens do resumo
        self.set_font('Arial', '', 10)
        self.set_text_color(0, 0, 0)
        
        col_width = 130
        for i, (key, value) in enumerate(resumo.items()):
            self.set_xy(20, start_y + 15 + i * 8)
            self.cell(col_width, 8, key, 0, 0, 'L')
            self.cell(col_width, 8, value, 0, 0, 'R')
        
        # Avançar posição Y após o bloco
        self.set_y(start_y + box_height + 5)
        
    def add_table(self, headers, data):
        # Configurações da tabela
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(111, 56, 124)  # Violeta: #6F387C
        self.set_text_color(255, 255, 255)  # Branco
        
        # Calcular larguras das colunas
        page_width = 277  # A4 paisagem = 297mm - margens
        col_widths = []
        
        # Definir larguras específicas para certas colunas
        col_mapping = {
            'Descrição': 50,
            'Cliente': 40,
            'Valor (R$)': 25,
            'A Receber (R$)': 25,
            'Situação': 20
        }
        
        # Calcular larguras
        total_fixed_width = sum(col_mapping.get(h, 0) for h in headers)
        remaining_width = page_width - total_fixed_width
        default_width = remaining_width / (len(headers) - len([h for h in headers if h in col_mapping]))
        
        for header in headers:
            col_widths.append(col_mapping.get(header, default_width))
        
        # Cabeçalho da tabela
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 10, header, 1, 0, 'C', 1)
        self.ln()
        
        # Dados da tabela
        self.set_font('Arial', '', 9)
        self.set_text_color(0, 0, 0)
        
        # Alternar cores de fundo para linhas
        row_colors = [(255, 255, 255), (240, 240, 240)]
        
        for i, row in enumerate(data):
            # Definir cor de fundo para linha alternada
            if i % 2:
                self.set_fill_color(*row_colors[1])
            else:
                self.set_fill_color(*row_colors[0])
            
            # Verificar se precisa de nova página
            if self.get_y() + 6 > self.page_break_trigger:
                self.add_page()
                # Redesenhar cabeçalho da tabela
                self.set_font('Arial', 'B', 10)
                self.set_fill_color(111, 56, 124)  # Violeta
                self.set_text_color(255, 255, 255)  # Branco
                for j, header in enumerate(headers):
                    self.cell(col_widths[j], 10, header, 1, 0, 'C', 1)
                self.ln()
                self.set_font('Arial', '', 9)
                self.set_text_color(0, 0, 0)
            
            # Verificar coluna de situação para destacar "Em aberto"
            situacao_idx = -1
            if 'Situação' in headers:
                situacao_idx = headers.index('Situação')
            
            # Imprimir células da linha
            for j, cell in enumerate(row):
                # Verificar se é coluna de situação e valor é "Em aberto"
                if j == situacao_idx and cell.lower() == 'em aberto':
                    # Salvar cor de preenchimento atual
                    current_fill = self.fill_color
                    # Mudar para amarelo
                    self.set_fill_color(245, 157, 48)  # Amarelo: #F59D30
                    self.set_text_color(255, 255, 255)  # Texto branco
                    self.cell(col_widths[j], 6, cell, 1, 0, 'L', 1)
                    # Restaurar cor original
                    self.set_fill_color(*row_colors[i % 2])
                    self.set_text_color(0, 0, 0)
                else:
                    # Alinhar à direita valores monetários
                    align = 'R' if 'R$' in headers[j] else 'L'
                    self.cell(col_widths[j], 6, cell, 1, 0, align, 1)
            
            self.ln()

# Função para gerar o PDF
def gerar_pdf(df, filtros, colunas_selecionadas):
    # Criar PDF
    pdf = PDF()
    
    # Adicionar informações de filtro
    filtro_texto = []
    if filtros['data_inicio'] and filtros['data_fim']:
        filtro_texto.append(f"Período: {filtros['data_inicio'].strftime('%d/%m/%Y')} a {filtros['data_fim'].strftime('%d/%m/%Y')}")
    if filtros['cliente']:
        filtro_texto.append(f"Cliente: {filtros['cliente']}")
    if filtros['categoria']:
        filtro_texto.append(f"Categoria: {filtros['categoria']}")
    
    if filtro_texto:
        pdf.add_title("Filtros aplicados:")
        for texto in filtro_texto:
            pdf.add_info_line("•", texto)
        pdf.ln(5)
    
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
            'Vencidos (R$)': f"R$ {vencidos:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            'Vencem hoje (R$)': f"R$ {vencem_hoje:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            'A vencer (R$)': f"R$ {a_vencer:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            'Recebidos (R$)': f"R$ {recebidos:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            'Total do Período (R$)': f"R$ {total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        }
    
    # Adicionar bloco de resumo
    if resumo:
        pdf.add_summary_box(resumo)
        pdf.ln(5)
    
    # Adicionar tabela de dados
    pdf.add_title("Detalhamento")
    
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
    
    # Dados da tabela
    table_data = []
    
    # Formatar dados para a tabela
    for _, row in df.iterrows():
        table_row = []
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
                    value = f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                else:
                    value = ''
            
            # Converter para string
            if pd.isna(value):
                value = ''
            else:
                value = str(value)
                
            table_row.append(value)
        
        table_data.append(table_row)
    
    # Adicionar tabela ao PDF
    if table_data:
        pdf.add_table(headers, table_data)
    else:
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 10, "Nenhum dado disponível para exibição.", 0, 1, 'L')
    
    # Salvar PDF em um buffer
    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    
    return pdf_buffer

# Função para criar um link de download
def get_download_link(buffer, filename):
    b64 = base64.b64encode(buffer.getvalue()).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}" class="download-button">📥 Clique aqui para baixar o PDF</a>'
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
        
        # Botão para gerar PDF
        st.markdown('<div class="highlight">', unsafe_allow_html=True)
        st.write("### Geração de Relatório")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write("Clique no botão ao lado para gerar o relatório em PDF com os filtros aplicados.")
        
        with col2:
            gerar_relatorio = st.button("Gerar Relatório PDF")
        
        # Gerar PDF quando solicitado
        if gerar_relatorio:
            if len(df_filtrado) > 0:
                with st.spinner('Gerando relatório PDF...'):
                    # Preparar filtros para o PDF
                    filtros = {
                        'data_inicio': data_inicio if data_inicio else None,
                        'data_fim': data_fim if data_fim else None,
                        'cliente': cliente_selecionado,
                        'categoria': categoria_selecionada
                    }
                    
                    # Gerar o PDF
                    pdf_buffer = gerar_pdf(df_filtrado, filtros, colunas_selecionadas)
                    
                    # Nome do arquivo
                    now = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"Relatorio_Ilume_{now}.pdf"
                    
                    # Criar link de download
                    st.markdown(get_download_link(pdf_buffer, filename), unsafe_allow_html=True)
                    st.success("Relatório gerado com sucesso!")
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
