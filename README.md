# PV Performance Modeling in Practice

**Building, Validating, and Interpreting PV Models with Field Data**  
**CBENS 2026 — Tutorial interativo com Python e pvlib**

Este tutorial apresenta, de forma prática, a modelagem do desempenho de sistemas fotovoltaicos com [pvlib-python](https://pvlib-python.readthedocs.io/), desde os dados meteorológicos até a comparação com medições reais. Usaremos a usina **Simon Solar** como estudo de caso, explorando qualidade de dados, alinhamento temporal e validação de modelos.

**Não é necessário ter experiência prévia com Python nem instalar software.** Os notebooks podem ser executados diretamente no navegador pelo Google Colab ou pelo Binder.

## Acesse os notebooks

| Etapa | Atividade | Google Colab | Binder |
|---|---|---|---|
| **01 — Introdução** | Jupyter, pvlib, céu claro, dados meteorológicos, irradiância e temperatura | [Abrir no Colab](https://colab.research.google.com/github/PV-Tutorials/2026_pvlib-and-performance_CBENS/blob/main/01_introducao.ipynb) | [Abrir no Binder](https://mybinder.org/v2/gh/PV-Tutorials/2026_pvlib-and-performance_CBENS/main?urlpath=lab/tree/01_introducao.ipynb) |
| **02 — Desafio da manhã** | Modelagem do desempenho da usina Simon Solar | [Abrir no Colab](https://colab.research.google.com/github/PV-Tutorials/2026_pvlib-and-performance_CBENS/blob/main/02_morning_challenge.ipynb) | [Abrir no Binder](https://mybinder.org/v2/gh/PV-Tutorials/2026_pvlib-and-performance_CBENS/main?urlpath=lab/tree/02_morning_challenge.ipynb) |
| **03 — Atividades da tarde** | Exploração das medições de campo e comparação com o modelo | [Abrir no Colab](https://colab.research.google.com/github/PV-Tutorials/2026_pvlib-and-performance_CBENS/blob/main/03_afternoon.ipynb) | [Abrir no Binder](https://mybinder.org/v2/gh/PV-Tutorials/2026_pvlib-and-performance_CBENS/main?urlpath=lab/tree/03_afternoon.ipynb) |
| **04 — Desafio da tarde** | QA/QC, métricas de erro, investigação de discrepâncias e melhorias | [Abrir no Colab](https://colab.research.google.com/github/PV-Tutorials/2026_pvlib-and-performance_CBENS/blob/main/04_afternoon_challenge.ipynb) | [Abrir no Binder](https://mybinder.org/v2/gh/PV-Tutorials/2026_pvlib-and-performance_CBENS/main?urlpath=lab/tree/04_afternoon_challenge.ipynb) |

## Como executar

**Google Colab:** clique no link do notebook e execute as células com `Shift + Enter`. O Colab abre o notebook, mas **não disponibiliza automaticamente os demais arquivos do repositório**. Nas atividades que usam CSVs, execute a célula inicial de preparação dos dados para obter os arquivos necessários. Se essa célula não existir, baixe/clone o repositório antes de executar o notebook.

**Binder:** clique no link correspondente e aguarde a inicialização do JupyterLab. O Binder utiliza os arquivos do repositório (incluindo `weather_data/` e `field_data/`) e instala as dependências descritas em `requirements.txt`. O serviço é comunitário e pode demorar a iniciar.

**Jupyter local:** clone ou baixe o repositório, instale as dependências com `pip install -r requirements.txt` e abra os notebooks no JupyterLab.

**Importante:** sessões do Colab e do Binder não salvam automaticamente suas alterações no GitHub. Faça download do notebook ao final, se quiser conservar seu trabalho.

## Dados utilizados

- `weather_data/`: dados meteorológicos do NSRDB para Simon Solar.
- `field_data/`: medições reais da usina, incluindo potência AC e variáveis ambientais.

As atividades usam caminhos relativos. Mantenha a estrutura das pastas ao executar localmente.

## Recursos

- [Documentação do pvlib-python](https://pvlib-python.readthedocs.io/)
- [National Solar Radiation Database (NSRDB)](https://nsrdb.nrel.gov/)
- [Repositório no GitHub](https://github.com/PV-Tutorials/2026_pvlib-and-performance_CBENS)

---

**Nota para a organização (remover após a publicação):** os links acima usam os nomes solicitados `01_introducao.ipynb` e `04_afternoon_challenge.ipynb`. Na verificação de 24/10/2026, o repositório ainda apresentava `01_introduction.ipynb` e não listava `04_afternoon_challenge.ipynb`. Renomeie/envie esses arquivos antes de compartilhar os links com participantes.
