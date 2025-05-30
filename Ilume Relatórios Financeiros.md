# Ilume Relatórios Financeiros

Ferramenta web para geração de relatórios financeiros com a identidade visual da Ilume.

## Funcionalidades

- Upload de arquivos Excel (.xlsx) ou CSV (.csv) com dados financeiros
- Filtros por intervalo de datas, cliente ou categoria
- Seleção de colunas para exibição no relatório
- Geração de relatório em PDF no formato paisagem (A4 horizontal)
- Layout profissional seguindo a identidade visual da Ilume

## Identidade Visual

- **Violeta**: #6F387C
- **Amarelo**: #F59D30
- **Bege**: #F7E8C9

## Tecnologias Utilizadas

- **Frontend**: Streamlit
- **Processamento de Dados**: Pandas
- **Geração de PDF**: ReportLab
- **Hospedagem**: Streamlit Cloud

## Como Usar

1. Acesse a aplicação através do link: [Ilume Relatórios no Streamlit Cloud](https://ilume-relatorios.streamlit.app/)
2. Faça upload do seu arquivo Excel ou CSV com dados financeiros
3. Utilize os filtros para selecionar o período, cliente ou categoria desejada
4. Escolha as colunas que deseja exibir no relatório
5. Clique em "Gerar Relatório PDF" para baixar o documento

## Estrutura do Relatório PDF

- **Formato**: A4 horizontal (modo paisagem)
- **Cabeçalho**: Faixa violeta com texto centralizado em branco
- **Bloco de Resumo**: Fundo bege com informações financeiras consolidadas
- **Tabela Detalhada**: Dados completos conforme filtros aplicados
- **Tipografia**: Lato (ou Arial como fallback)

## Desenvolvimento Local

Para executar este projeto localmente:

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/ilume-relatorios.git

# Entre no diretório
cd ilume-relatorios

# Instale as dependências
pip install -r requirements.txt

# Execute a aplicação
streamlit run app.py
```

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para mais detalhes.
