# Previsão de Vendas da Rede de Drogarias Rossmann

## Problema de Negócio

A Rossmann, uma das maiores redes de drogarias da Europa com mais de 3.000 lojas, enfrenta o desafio de prever com precisão suas vendas diárias com até seis semanas de antecedência. Atualmente, essa tarefa é delegada aos gerentes de cada loja, resultando em previsões com grande variação de acurácia, pois são baseadas em experiências empíricas e processos descentralizados.

O objetivo principal deste projeto é desenvolver uma solução centralizada e baseada em dados para **prever as vendas das lojas para as próximas seis semanas**, permitindo um planejamento mais eficiente da alocação de recursos para futuras reformas.

A solução proposta é um **sistema de previsão de vendas utilizando Machine Learning**, com as previsões acessíveis através de uma API REST e um bot no Telegram, garantindo que os stakeholders possam consultar os dados de qualquer lugar.

---

## Arquitetura da Solução

A solução foi desenhada para ser robusta, escalável e de fácil acesso para os usuários finais. O fluxo de dados e interações segue a arquitetura abaixo:

---

## Fluxo de Comunicação:

### Usuário → Bot do Telegram

- O usuário (um stakeholder, como um gerente de loja) envia uma mensagem para o seu bot no Telegram com o ID de uma loja. Exemplo: /24.

### Bot do Telegram → Seu Bot no Render (Webhook)

- O servidor do Telegram recebe essa mensagem e a encaminha imediatamente para a URL do seu bot que está rodando no Render (o "webhook" que foi configurado).

### Bot no Render → API de Previsão no Render

- O script rossmann-bot.py recebe a requisição.
- Ele extrai o ID da loja (24).
- Carrega os dados das próximas 6 semanas para essa loja a partir dos arquivos test.csv e store.csv.
- Converte esses dados em formato JSON.
- Envia uma requisição POST com esse JSON para o endpoint da API de previsão (/rossmann/predict), que também está rodando no Render.

### API de Previsão → Modelo de Machine Learning

- Seu script handler.py (a API) recebe os dados.
- A classe Rossmann realiza todo o pré-processamento necessário (limpeza, engenharia de atributos, encoding, etc.).
- Os dados preparados são passados para o modelo XGBoost, que gera as previsões de vendas.

### API de Previsão → Bot no Render

- A API retorna as previsões em formato JSON para o serviço do bot.

### Bot no Render → Usuário

- O script do bot recebe a resposta da API.
- Ele calcula o total das vendas previstas para as 6 semanas.
- Formata uma mensagem amigável e clara para o usuário (ex: "A loja 24 venderá R$ X nas próximas 6 semanas.").
- Envia essa mensagem final de volta para o usuário através da API do Telegram.

> **IMPORTANTE:** Essencialmente, o bot atua como um orquestrador inteligente: ele entende o pedido do usuário, busca os dados brutos necessários, solicita a "mágica" (a previsão) à API e, finalmente, traduz o resultado técnico em uma resposta de negócio útil.

---

## Demonstração em Funcionamento

Para facilitar o acesso às previsões, foi desenvolvido um bot no Telegram que serve como uma interface direta e amigável. Qualquer stakeholder pode solicitar a previsão de vendas para as próximas 6 semanas de uma loja específica simplesmente enviando o ID da loja para o bot.

A imagem abaixo demonstra a interação: o usuário envia o ID da loja (ex: `/24`) e o bot responde prontamente com o faturamento total previsto para o período.

<p align="center">
  <img title="Demonstração do Bot no Telegram" alt="Demonstração do Bot no Telegram" src="/images/bot-telegran.jpeg" width="400">
</p>

---

## Metodologia - CRISP-DM

O projeto foi estruturado seguindo o **CRISP-DM (Cross-Industry Standard Process for Data Mining)**, uma metodologia robusta e cíclica que garante que o projeto de ciência de dados esteja sempre alinhado com os objetivos de negócio.
<p align="center">
<img title="Metodologia CRIPS-DS" alt="Alt text" src="/images/crisp-dm.png" width="400">
</p>

---

## Tecnologias Utilizadas

Este projeto foi desenvolvido utilizando o ecossistema Python, com as seguintes bibliotecas e frameworks principais:

-   **Análise e Manipulação de Dados:** `pandas`, `numpy`
-   **Visualização de Dados:** `matplotlib`, `seaborn`
-   **Modelagem de Machine Learning:** `scikit-learn`, `xgboost`, `Boruta`
-   **API e Deploy:** `Flask`, `python-dotenv`
-   **Utilitários:** `inflection`, `requests`, `pickle`

---

## Estrutura do Projeto

O repositório está organizado da seguinte forma para garantir a modularidade e a clareza:

```
.
├── api/                  # Contém o código da API Flask (handler.py) e a classe de pré-processamento (Rossmann.py).
├── bot/                  # Contém o código do bot do Telegram e suas dependências.
├── data/                 # Armazena os dados brutos, limpos e transformados.
├── images/               # Imagens e diagramas utilizados na documentação.
├── model/                # Modelos serializados (.pkl) e objetos de pré-processamento.
├── notebooks/            # Jupyter Notebooks com todo o processo de desenvolvimento.
├── README.md             # Este arquivo.
└── requirements.txt      # Dependências Python para a API.
```

---

## Instalação e Como Executar

Para executar este projeto localmente, siga os passos abaixo. Recomenda-se o uso de ambientes virtuais (`venv`) para isolar as dependências.

### Pré-requisitos

-   Python 3.9 ou superior

### Clonando o Repositório

```bash
git clone https://github.com/seu-usuario/rossmann-sales-forecast.git
cd rossmann-sales-forecast
```

### Executando a API de Previsão

A API é o núcleo do projeto, responsável por receber os dados, processá-los e retornar as previsões.

1.  **Navegue até a pasta da API:**
    ```bash
    cd api
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # No Linux/macOS
    # venv\Scripts\activate   # No Windows
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Inicie o servidor Flask:**
    ```bash
    python handler.py
    ```
    A API estará rodando em `http://127.0.0.1:5001`.

### Executando o Bot do Telegram

O bot serve como uma interface amigável para consultar as previsões da API.

1.  **Abra um novo terminal e navegue até a pasta do bot:**
    ```bash
    cd bot
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # No Linux/macOS
    # venv\Scripts\activate   # No Windows
    ```

3.  **Instale as dependências do bot:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as Variáveis de Ambiente:**
    Crie um arquivo chamado `.env` dentro da pasta `bot/` e adicione as seguintes variáveis:
    ```bash
    TELEGRAM_BOT_TOKEN="SEU_TOKEN_AQUI"
    API_URL="http://127.0.0.1:5001/rossmann/predict"
    ```
    > **IMPORTANTE:** Adicione o arquivo `.env` ao seu `.gitignore` para não expor seu token.

5.  **Inicie o bot:**
    ```bash
    python rossmann-bot.py
    ```
    O bot agora está online. Envie o ID de uma loja (ex: `/10`) para receber a previsão de vendas.

---


## Deploy e Manutenção

Os serviços da API e do Bot foram implantados na plataforma **Render**. Como o plano gratuito do Render suspende os serviços após 15 minutos de inatividade, foi configurado um workflow do **GitHub Actions** (`.github/workflows/keep-alive.yml`) para enviar requisições a cada 10 minutos, mantendo os serviços sempre ativos e responsivos.


## Análise Exploratória - Principais Insights

A análise exploratória de dados (EDA) foi fundamental para entender a dinâmica das vendas e validar hipóteses de negócio. Abaixo estão os principais insights obtidos:

| Hipótese | Conclusão | Relevância | Insight Principal |
| :--- | :--- | :--- | :--- |
| **Competidores Próximos** | Inválida | Alta | Lojas com competidores mais próximos **vendem mais**, sugerindo que a concorrência se concentra em áreas de alta demanda. |
| **Promoções Prolongadas** | Inválida | Alta | Promoções contínuas (`Promo2`) **não garantem vendas maiores**; o efeito promocional parece diminuir com o tempo. |
| **Feriado de Natal** | Válida | Alta | Lojas que permanecem abertas durante o Natal apresentam uma **mediana de vendas significativamente maior**. |
| **Férias Escolares** | Válida | Alta | As vendas são consistentemente **menores durante os períodos de férias escolares**. |
| **Finais de Semana** | Parcialmente Válida | Média | O volume total de vendas cai nos finais de semana. No entanto, as poucas lojas que abrem aos domingos possuem uma **média de vendas elevada**. |


---

## Preparação dos Dados e Engenharia de Atributos

O processo de preparação dos dados foi encapsulado na classe `Rossmann` e envolveu as seguintes etapas:

1.  **Limpeza de Dados:** Tratamento de valores ausentes com estratégias específicas (ex: `CompetitionDistance` preenchido com um valor alto), padronização dos nomes das colunas para `snake_case` e conversão de tipos de dados.
2.  **Engenharia de Atributos:** Extração de features a partir da data (`ano`, `mês`, `dia`, `semana_do_ano`) e criação de variáveis de negócio, como o tempo em meses desde a abertura de um concorrente (`CompetitionTimeMonth`) e o tempo em semanas desde o início de uma promoção (`PromoTimeWeek`).
3.  **Transformação de Dados:**
    -   **Rescalonamento:** Variáveis numéricas como `CompetitionDistance` e `Year` foram normalizadas para que o modelo não seja enviesado por diferentes escalas.
    -   **Encoding:** Variáveis categóricas foram transformadas em representações numéricas (`One-Hot Encoding` para `StateHoliday`, `Label Encoding` para `StoreType` e `Ordinal Encoding` para `Assortment`).
    -   **Transformação Cíclica:** Features temporais como `DayOfWeek` e `Month` foram transformadas em componentes seno e cosseno para que o modelo entenda sua natureza cíclica.


---

## Modelagem e Resultados

Foram testados múltiplos algoritmos de regressão (Regressão Linear, Lasso, Random Forest, XGBoost). Os modelos não lineares apresentaram performance superior, e o **XGBoost Regressor** foi selecionado como o modelo final devido ao seu excelente equilíbrio entre performance e custo computacional. A avaliação foi realizada utilizando **Validação Cruzada para Séries Temporais**, garantindo uma estimativa robusta do erro em dados não vistos.

Após a tunagem de hiperparâmetros, os resultados finais do modelo no conjunto de teste foram:

| Métrica | Valor | Descrição |
| :--- | :--- | :--- |
| **MAE** (Mean Absolute Error) | 679.33 | Média do erro absoluto entre o previsto e o real. |
| **MAPE** (Mean Absolute Percentage Error) | 9.92% | Média do erro percentual absoluto. |
| **RMSE** (Root Mean Squared Error) | 995.73 | Raiz do erro quadrático médio, que penaliza mais os erros grandes. |


---

## Análise de Negócio e Financeira

O desempenho do modelo foi traduzido em impacto de negócio, fornecendo uma visão clara do seu valor financeiro.

-   **Previsão de Faturamento Total:** O modelo prevê um faturamento total de **R$ 283.76 milhões** para as próximas 6 semanas, considerando todas as lojas.
-   **Cenários de Risco:** Para auxiliar na tomada de decisão, foram calculados o melhor e o pior cenário, que estimam um faturamento entre **R$ 283.00 milhões** e **R$ 284.52 milhões**.


---

## Próximos Passos

-   **Engenharia de Features Avançada:** Explorar a criação de novas variáveis e interações entre elas para capturar padrões mais complexos.
-   **Monitoramento e Atualização Contínua:** Estabelecer rotinas de monitoramento do desempenho do modelo em produção e definir critérios para re-treinamento periódico.
-   **Documentação e Reprodutibilidade:** Manter a documentação de todas as etapas do pipeline atualizada para garantir a reprodutibilidade e facilitar futuras manutenções.