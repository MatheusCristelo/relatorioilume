import streamlit as st
import pandas as pd
import numpy as np
import base64
from datetime import datetime, timedelta
import io
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

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

# Função para gerar o PDF
def gerar_pdf(df, filtros, colunas_selecionadas):
    buffer = io.BytesIO()
    
    # Configurar o documento PDF em modo paisagem
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=landscape(A4),
        rightMargin=72, 
        leftMargin=72,
        topMargin=72, 
        bottomMargin=72
    )
    
    # Registrar fonte Lato se disponível, senão usar Arial
    try:
        pdfmetrics.registerFont(TTFont('Lato', '/usr/share/fonts/truetype/lato/Lato-Regular.ttf'))
        pdfmetrics.registerFont(TTFont('Lato-Bold', '/usr/share/fonts/truetype/lato/Lato-Bold.ttf'))
        font_name = 'Lato'
        font_bold = 'Lato-Bold'
    except:
        # Fallback para Arial
        font_name = 'Helvetica'
        font_bold = 'Helvetica-Bold'
    
    # Estilos de parágrafo
    styles = getSampleStyleSheet()
    
    # Estilo para título
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName=font_bold,
        fontSize=16,
        textColor=colors.white,
        alignment=1,  # Centralizado
        spaceAfter=12
    )
    
    # Estilo para subtítulo
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Heading2'],
        fontName=font_bold,
        fontSize=14,
        textColor=colors.HexColor(VIOLETA),
        alignment=0,  # Esquerda
        spaceAfter=6
    )
    
    # Estilo para texto normal
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        textColor=colors.black,
        alignment=0  # Esquerda
    )
    
    # Lista de elementos para o PDF
    elements = []
    
    # Função para criar o cabeçalho
    def header_footer(canvas, doc):
        canvas.saveState()
        
        # Cabeçalho
        canvas.setFillColor(colors.HexColor(VIOLETA))
        canvas.rect(0, doc.height + doc.topMargin - 0.5*inch, doc.width + doc.leftMargin + doc.rightMargin, 1*inch, fill=True, stroke=False)
        
        canvas.setFont(font_bold, 16)
        canvas.setFillColor(colors.white)
        canvas.drawCentredString(doc.width/2 + doc.leftMargin, doc.height + doc.topMargin + 0.2*inch, "Relatório de Contas a Receber")
        
        # Rodapé
        canvas.setFont(font_name, 8)
        canvas.setFillColor(colors.black)
        canvas.drawCentredString(doc.width/2 + doc.leftMargin, doc.bottomMargin - 0.2*inch, f"Ilume Finanças - Relatório gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        canvas.restoreState()
    
    # Adicionar informações de filtro
    filtro_texto = []
    if filtros['data_inicio'] and filtros['data_fim']:
        filtro_texto.append(f"Período: {filtros['data_inicio'].strftime('%d/%m/%Y')} a {filtros['data_fim'].strftime('%d/%m/%Y')}")
    if filtros['cliente']:
        filtro_texto.append(f"Cliente: {filtros['cliente']}")
    if filtros['categoria']:
        filtro_texto.append(f"Categoria: {filtros['categoria']}")
    
    if filtro_texto:
        elements.append(Paragraph("Filtros aplicados:", subtitle_style))
        for texto in filtro_texto:
            elements.append(Paragraph(f"• {texto}", normal_style))
        elements.append(Spacer(1, 0.2*inch))
    
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
            'Vencidos (R$)': vencidos,
            'Vencem hoje (R$)': vencem_hoje,
            'A vencer (R$)': a_vencer,
            'Recebidos (R$)': recebidos,
            'Total do Período (R$)': total
        }
    
    # Adicionar bloco de resumo
    if resumo:
        elements.append(Paragraph("Resumo Financeiro", subtitle_style))
        
        # Criar tabela de resumo
        resumo_data = [[k, f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')] for k, v in resumo.items()]
        resumo_table = Table(resumo_data, colWidths=[3*inch, 1.5*inch])
        
        # Estilo da tabela de resumo
        resumo_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(BEGE)),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ])
        
        resumo_table.setStyle(resumo_style)
        elements.append(resumo_table)
        elements.append(Spacer(1, 0.3*inch))
    
    # Adicionar tabela de dados
    elements.append(Paragraph("Detalhamento", subtitle_style))
    
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
    table_data = [headers]
    
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
    
    # Criar tabela
    if len(table_data) > 1:  # Se houver dados além do cabeçalho
        col_widths = [1.2*inch] * len(headers)  # Largura padrão para todas as colunas
        
        # Ajustar larguras específicas
        for i, header in enumerate(headers):
            if header in ['Descrição', 'Cliente']:
                col_widths[i] = 2*inch
            elif header in ['Valor (R$)', 'A Receber (R$)']:
                col_widths[i] = 1.5*inch
            elif header == 'Situação':
                col_widths[i] = 1*inch
        
        table = Table(table_data, colWidths=col_widths)
        
        # Estilo da tabela
        table_style = TableStyle([
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(VIOLETA)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), font_bold),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            
            # Corpo da tabela
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Alinhar valores monetários à direita
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            
            # Bordas e espaçamento
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ])
        
        # Identificar índice da coluna "Situação"
        situacao_idx = -1
        for i, header in enumerate(headers):
            if header == 'Situação':
                situacao_idx = i
                break
        
        # Colorir células da coluna "Situação" se existir
        if situacao_idx >= 0:
            for i in range(1, len(table_data)):
                if table_data[i][situacao_idx].lower() == 'em aberto':
                    table_style.add('BACKGROUND', (situacao_idx, i), (situacao_idx, i), colors.HexColor(AMARELO))
                    table_style.add('TEXTCOLOR', (situacao_idx, i), (situacao_idx, i), colors.white)
        
        # Aplicar estilo à tabela
        table.setStyle(table_style)
        elements.append(table)
    else:
        elements.append(Paragraph("Nenhum dado disponível para exibição.", normal_style))
    
    # Construir o PDF
    doc.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)
    
    # Retornar o buffer
    buffer.seek(0)
    return buffer

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
