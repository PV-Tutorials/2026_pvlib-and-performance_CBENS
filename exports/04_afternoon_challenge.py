#!/usr/bin/env python
# coding: utf-8

# ![Tutorial_banner](images/cbens_2026_performancetutorial_logo.jpg)
# 
# # Tutorial 4 — Desafio: Investigando o desempenho da Simon Solar
# 
# **PV Performance Modeling in Practice — CBENS 2026**
# 
# ## Objetivo
# 
# Nos tutoriais anteriores, construímos um modelo de desempenho fotovoltaico com pvlib, exploramos dados reais de operação da usina Simon Solar e identificamos desafios de qualidade e alinhamento temporal.
# 
# Agora é a vez de vocês!
# 
# Neste desafio, cada equipe deverá **investigar as diferenças entre o desempenho medido e modelado**, identificar possíveis causas e propor melhorias na análise ou na simulação.
# 
# ### Arquivos necessários
# 
# - `results/Simon_Solar_modeled_2016_2023.csv` — resultados da simulação fotovoltaica realizada no Tutorial 3.
# - `results/Simon_Solar_field_aligned_2016_2023.csv` — dados operacionais do PVDAQ com timestamps alinhados.
# 
# ### Possíveis investigações
# 
# 1. **QA/QC:** identificar valores anômalos, dados ausentes e problemas de qualidade das medições.
# 2. **Métricas de desempenho:** calcular MBE, MAE, RMSE e erros normalizados.
# 3. **Análise de discrepâncias:** investigar diferenças por ano, estação, irradiância ou temperatura.
# 4. **Melhorias do modelo:** explorar perdas, disponibilidade, degradação e outras hipóteses.
# 5. **Sensibilidade e incertezas:** avaliar como mudanças nos parâmetros afetam os resultados.
# 6. Outras?
# 
# ### Entrega do desafio
# 
# Cada equipe deverá apresentar **pelo menos uma figura, seus principais resultados e uma conclusão**.
# 
# Não existe uma única resposta correta. O objetivo é formular hipóteses, testar ideias e interpretar os resultados com base nos dados.
# 
# **Importante:** os arquivos de resultados serão carregados diretamente neste notebook, sem necessidade de repetir toda a simulação do Tutorial 3. Caso necessário, utilizaremos os arquivos de referência disponibilizados no repositório do curso.

# In[ ]:


from pathlib import Path
import subprocess
import shutil
import importlib.util

if importlib.util.find_spec("pvlib") is None:
    get_ipython().run_line_magic('pip', 'install -q pvlib ipywidgets')

REPO_URL = "https://github.com/PV-Tutorials/2026_pvlib-and-performance_CBENS.git"

# No Colab, os arquivos do repositório não são baixados automaticamente.
if Path("/content").exists():
    repo_dir = Path("/content/2026_pvlib-and-performance_CBENS")

    if not repo_dir.exists():
        subprocess.run(
            ["git", "clone", "--depth", "1", REPO_URL, str(repo_dir)],
            check=True
        )

    # Disponibilizar as pastas no diretório de trabalho do notebook
    for folder in ["weather_data", "field_data", "results"]:
        source = repo_dir / folder
        destination = Path.cwd() / folder

        if source.exists() and not destination.exists():
            shutil.copytree(source, destination)

# Verificar os arquivos disponíveis
for folder in ["weather_data", "field_data", "results"]:
    path = Path(folder)
    files = list(path.glob("*.csv")) if path.exists() else []
    print(f"{folder}: {len(files)} arquivos CSV")


# In[7]:


from pathlib import Path
import pandas as pd

modeled = pd.read_csv(
    "results/Simon_Solar_modeled_2016_2023.csv",
    index_col="timestamp", parse_dates=True
)

field = pd.read_csv(
    "results/Simon_Solar_field_aligned_2016_2023.csv",
    index_col="timestamp", parse_dates=True
)

modeled.keys()


# In[10]:


comparison = pd.concat([
    (modeled["ac_power_kw"] / 1000).rename("Modelado (MW)"),
    (field["meter_ac_power_kw"] / 1000).rename("Medido (MW)")
], axis=1).dropna().sort_index()

display(comparison.head())
print("Horas com dados coincidentes:", len(comparison))


# In[ ]:





# In[ ]:





# In[ ]:




