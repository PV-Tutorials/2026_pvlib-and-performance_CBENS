#!/usr/bin/env python
# coding: utf-8

# ![Tutorial_banner](images/cbens_2026_performancetutorial_logo.jpg)
# 
# # Tutorial complementar — PVCaptest and RdTools
# 
# Este apêndice documenta um fluxo de pesquisa com dados PVDAQ de Simon Solar, análises de capacidade com **PVCaptest**, comparação posterior com **SAM**, análise de degradação e disponibilidade com **RdTools** e cálculo do **Performance Ratio (PR)**.
# 
# ### Fonte e referência
# 
# Este material foi desenvolvido a partir de análises de desempenho e confiabilidade de sistemas fotovoltaicos, incluindo testes de capacidade, degradação e disponibilidade operacional.
# 
# O código e os estudos relacionados estão disponíveis no repositório:
# 
# **[PV Repowering — Modeling Aging Systems and Lifecycle Decisions](https://github.com/NatLabRockies/pv_repowering/tree/main/Studies/EUPVSEC%202026%20-%20Modeling%20Aging%20Systems%20and%20Lifecycle%20Decisions)**
# 
# **Publicação relacionada:**  
# Ovaitt et al. *Modeling Aging Systems and Lifecycle Decisions*. Proceedings of the 43rd European Photovoltaic Solar Energy Conference and Exhibition (EU PVSEC), 2026.
# 
# Este notebook é disponibilizado como material complementar ao tutorial **PV Performance Modeling in Practice — CBENS 2026**, ilustrando aplicações mais avançadas de análise de dados de campo, testes de capacidade e avaliação de desempenho ao longo do tempo.
# 
# 
# **Como ler:** as seções explicam o propósito de cada etapa; os códigos e parâmetros originais foram preservados, inclusive testes exploratórios e células que dependem de arquivos intermediários. Trata-se de material de referência, **não de um notebook simplificado para execução direta em Colab/Binder**. Os arquivos do estudo (como `data/9069_subset.csv`, parquet meteorológico e saídas SAM) e as bibliotecas adicionais são necessários.
# 
# **Cuidados de interpretação:** horários, seleção de sensores, perdas de dados, clipping e definição dos denominadores influenciam as métricas. Estimativas de degradação aparente não são necessariamente degradação física isolada.
# 

# ## 1. Preparação do ambiente
# 
# Importação das bibliotecas e configuração inicial dos gráficos. Este apêndice preserva o código da análise original; algumas células dependem de arquivos locais e das versões das bibliotecas usadas na pesquisa.

# In[ ]:


import pandas as pd
import matplotlib.pyplot as plt
import pvlib
import numpy as np
import os
from pathlib import Path
from datetime import datetime


# In[ ]:


plt.rcParams.update({'font.size': 22})
plt.rcParams['figure.figsize'] = (12, 4)


# In[ ]:


# import captest as pvc
import captest as ct
import importlib.metadata
print(importlib.metadata.version('captest'))

#from captest import capdata as pvc
from bokeh.io import output_notebook, show

# uncomment below two lines to use cptest.scatter_hv in notebook
import holoviews as hv
from holoviews import opts
hv.extension('bokeh')

#if working offline with the CapData.plot() method may fail
#run 'export BOKEH_RESOURCES=inline' at the command line before
#running the jupyter notebook

output_notebook()


# ## 2. Teste de capacidade — dados de campo
# 
# Carregamos os dados PVDAQ 9069 da Simon Solar no PVCaptest e agregamos os canais de medição.

# In[ ]:


# Dados Simon Solar preparados anteriormente em Analysis_9069.py

# Iniciar análise com PVCaptest

# Criar objeto CapData para armazenar os dados de campo.
das = ct.load_data('./data/9069_subset.csv')


# In[ ]:


# Agregar os sensores antes da seleção temporal (alguns filtros redefinem o estado).
das.reset_filter()
das.agg_sensors(agg_map={'_inv_':'sum', 'irr_poa_':'median', 'temp_amb_':'median', 'wind__':'median'})


# ## Seleção do período de teste
# 
# O período de fevereiro a março de 2022 foi escolhido por sua melhor cobertura de dados. As observações do código original registram redução da potência do medidor M2 após maio de 2022 e indisponibilidade do vento a partir de março.

# In[ ]:


# Janela de dados utilizável: 01/02/2022 a 10/03/2022.
# Observou-se queda no canal meter_2_ac_power_kw a partir de 15/05/2022.
# poa_irradiance_02b apresenta melhor disponibilidade neste intervalo.
# O canal de velocidade do vento deixa de apresentar dados a partir de 11/03/2022.

start_date = pd.to_datetime('2022-02-01 6:0:0-05:00')
end_date = pd.to_datetime('2022-03-10 20:0:0-05:00') 

#das.filter_time(start=start_date, end=end_date)
das.data = das.data[(das.data.index >= start_date) & (das.data.index <= end_date)]


# In[ ]:


print([k for k in das.column_groups])
print(das.column_groups._mtr_)
print(das.column_groups.irr_poa_)
print(das.column_groups.temp_amb_)
print(das.column_groups.wind__)
print([k for k in das.column_groups._inv_])


# In[ ]:


# Explorar os diferentes canais de medição.
#combine = {'inv_sum_mtr_pwr': ['mtr', 'inv.*agg'], 'irr_all':['irr_poa', 'irr_ghi'], 'temp_all':['temp_amb', 'temp_mod']}
combine = {'irr_all':['poa_irr', 'ghi_irr'], 'temp_all':['ambient_temp', 'module_temp']}
default_groups = ['inv_sum_mtr_pwr', 'irr_all', 'temp_all']
das.plot(combine=combine, default_groups=default_groups, width=900)


# ## Regressão de capacidade
# 
# A regressão relaciona a potência AC com a irradiância POA e a temperatura. **A variável `t_amb` recebe temperatura do módulo** nesta análise, apesar do nome do argumento. O termo de vento foi retirado da fórmula.

# In[ ]:


#das.regression_formula = 'power ~ poa + I(poa * poa) + I(poa * t_amb) + I(poa * w_vel) - 1'
das.regression_formula = 'power ~ poa + I(poa * poa) + I(poa * t_amb)  - 1'  # Usa temperatura do módulo no argumento t_amb.


# In[ ]:


# Definir as colunas usadas na regressão.
#das.set_regression_cols(power='inverter_07_ac_power_(kw)', poa='poa_irradiance_02b', 
#                        t_amb='ambient_temperature_median', w_vel='wind_speed_ms')
das.reset_filter()

das.data_filtered = das.data_filtered[(das.data_filtered['_inv__sum_agg'].notna())&(das.data_filtered['poa_irradiance_02b'].notna())
                    &(das.data_filtered['module_temperature_median'].notna())&(das.data_filtered['wind_speed_ms'].notna())]

das.set_regression_cols(power='_inv__sum_agg', poa='poa_irradiance_02b', 
                        t_amb='module_temperature_median', w_vel='wind_speed_ms') #t_amb='ambient_temperature_median', w_vel='wind_speed_ms'


das.filter_irr(200, 2000)

#das.filter_sensors() # removes almost everything for some reason...
#das.filter_custom(pd.DataFrame.dropna) # removes all data for some reason...
das.filter_outliers() # 

das.fit_regression(filter=True, summary=False)


# ## Condições de referência e qualidade do ajuste
# 
# O PVCaptest estima condições de referência e permite aplicar filtros, examinar observações e ajustar a regressão.

# In[ ]:


das.rep_cond()
print(das.rc)


# In[ ]:


das.filter_irr(0.5, 1.5, ref_val=das.rc['poa'][0])


# In[ ]:


das.scatter_hv()


# In[ ]:


das.fit_regression(summary=False)


# In[ ]:


print(das.regression_results.summary())


# In[ ]:


# Calcular a potência prevista nas condições de referência.
a = list(das.regression_results.params)
r = [das.rc.poa.iloc[0], das.rc.t_amb.iloc[0]]
power_predict = r[0]*(a[0] + a[1]*r[0] )
print(f'Predicted power: {power_predict:.1f} kW')


# In[ ]:


das.rc


# In[ ]:


#!pip install selenium
#!conda install -c conda-forge firefox geckodriver


# ## 3. Teste de capacidade dos 40 inversores
# 
# Aplicamos a mesma metodologia aos canais de cada inversor. O objetivo é comparar as **capacidades estimadas a partir dos dados de campo**, nas mesmas condições de referência.

# In[ ]:


## Aplicar o procedimento de teste de capacidade a todos os inversores.

def process_inverter_channel(das, power_col, rc=None):
    das.reset_filter()
    das.data_filtered = das.data_filtered[(das.data_filtered[power_col].notna()) &
                                          (das.data_filtered['poa_irradiance_02b'].notna()) &
                                          (das.data_filtered['module_temperature_median'].notna()) &
                                          (das.data_filtered['wind_speed_ms'].notna())]
    das.set_regression_cols(power=power_col, poa='poa_irradiance_02b',
                            t_amb='module_temperature_median', w_vel='wind_speed_ms')
    das.filter_irr(200, 2000)
    das.filter_outliers()
    das.fit_regression(filter=True, summary=False)
    if rc is None:
        das.rep_cond()
        print(das.rc)
    else:
        das.rc = rc
    das.filter_irr(0.5, 1.5, ref_val=das.rc['poa'][0])
    das.filter_irr(200, 900) # some clipping happening at high irradiance at 33MWac.
    das.fit_regression(summary=False)
    return das

def regression_predict(das):
    # Calcular a potência prevista nas condições de referência.
    a = list(das.regression_results.params)
    r = [das.rc.poa.iloc[0], das.rc.t_amb.iloc[0], das.rc.w_vel.iloc[0]]
    power_predict = r[0]*(a[0] + a[1]*r[0] + a[2]*r[1])
    print(f'Predicted power: {power_predict:.1f} kW')
    return power_predict


# ## Condições de referência escolhidas
# 
# Definimos 800 W/m² de POA, 20 °C de temperatura associada ao argumento `t_amb` (aqui, temperatura do módulo) e 1 m/s de vento. O vento consta da estrutura das condições, mas não da regressão selecionada.

# In[ ]:


rc = pd.DataFrame({'poa':[800], 't_amb':[20], 'w_vel':[1]})
print(rc)


# ## Exemplo: inversor 29
# 
# Gráfico do teste de capacidade de um inversor, com o ponto estimado nas condições de referência.

# In[ ]:


# Executar a análise do inversor 29 e preparar a figura.
mult = 1  # change this multiplier to scale the figure size and font size for publication. Holoviews is dumb and can't do dpi=300
das_29 = process_inverter_channel(das, 'inverter_29_ac_power_(kw)', rc=rc)
power_predict_29 = regression_predict(das_29)
das_29_scatter = das_29.scatter_filters()
das_29_scatter.opts(opts.Scatter( size=5*mult))
# add a star point to the predicted power plot at x=800, y=power_predict_29
das_29_annotation = hv.Scatter([(800, power_predict_29)], label='RC')
das_29_annotation.opts(color='orangered', size=20*mult, marker='star')
combined_plot = das_29_scatter * das_29_annotation
combined_plot.opts(title="", xlabel="POA Irradiance (W/m²)", ylabel="AC Power (kW)", 
                    width=600*mult, height=500*mult, legend_position='bottom_right', 
                    fontsize={'title': 16*mult, 'labels': 14*mult, 'xticks': 12*mult, 
                              'yticks': 12*mult, 'legend': 12*mult},
                    )


# In[ ]:


hv.save(combined_plot,'inverter_29_ac_power_vs_poa_1x.png',dpi=2000)


# ## Capacidade estimada para cada inversor
# 
# A rotina percorre os 40 canais, executa filtragem e regressão e salva as estimativas de capacidade.

# In[ ]:


# Tabela para armazenar as capacidades estimadas de cada inversor.
power_predict_df = pd.DataFrame(columns=das.column_groups._inv_ + ['_inv__sum_agg'], index=['power_predict'])


# Repetir o teste de capacidade para todos os canais de inversores.
#for power_col in ([das.column_groups._inv_[30]] ):
for power_col in (das.column_groups._inv_):
    print(f'Processing {power_col}...')
    das = process_inverter_channel(das, power_col, rc=rc)
    power_predict_df[power_col] = regression_predict(das)
    das_scatter = das.scatter_filters()
    hv.save(das_scatter, f'.\plots\{power_col}.html')
    hv.save(das_scatter, f'.\plots\{power_col}.png')


# In[ ]:


das.scatter_hv()


# In[ ]:


power_predict_df.to_csv(r'.\data\9069_Feb_March_2022_800poa20tmod.csv')


# ## Distribuição das capacidades medidas — boxplot dos 40 inversores
# 
# **Este boxplot é resultado do teste de capacidade dos inversores**, antes de qualquer comparação com o modelo SAM. Ele ilustra a dispersão entre os 40 equipamentos.

# In[ ]:


power_predict_df = pd.read_csv(r'.\data\9069_Feb_March_2022_800poa20tmod.csv', index_col=0)
labels =  [col.split('_')[1] for col in power_predict_df.columns[:-1]] + ['total']

# Boxplot da distribuição das capacidades estimadas a partir dos dados de campo.
random = np.random.normal(1, 0.04, size=power_predict_df.T.shape) # add some random noise to the x values for better visualization
plt.figure(figsize=(5,4),)
plt.scatter(random[:-1], power_predict_df.T[:-1], alpha=0.5)
plt.boxplot(power_predict_df.T,  showfliers=False)
#plt.xticks(rotation=45)
plt.ylabel('Inverter PTC power (kW)', size=14)
# change the xtick labels to just be one tick with the label 'Inverter channel'
plt.xticks([1], ['Inverter channels 1-40'], size=14)


# ## 4. Comparação posterior com SAM
# 
# Somente agora carregamos a simulação SAM de referência. Ajustamos uma regressão compatível para comparar as estimativas nas mesmas condições de referência.

# In[ ]:


# Carregar a simulação SAM de referência para um inversor.
# initial try: 900kWdc, 700kWac, 1.286 DC/AC ratio
#df_temp = pd.read_csv('./data/9069_SAM_750AC_965DC.csv', index_col=0, parse_dates=True)
#df_temp.to_csv(r'.\data\9069_SAM_750AC_965DC_edited.csv')

sim = ct.load_data('./data/9069_SAM_825AC_965DC_edited.csv')


# In[ ]:


sim.column_groups


# In[ ]:


# Write over cptest.flt_sim dataframe with a copy of the original unfiltered dataframe
sim.reset_filter()
sim.set_regression_cols(power='_inv_', poa='irr_poa_', t_amb='temp_mod_', w_vel='wind__')
sim.regression_formula = 'power ~ poa + I(poa * poa) + I(poa * t_amb)  - 1'  # Usa temperatura do módulo no argumento t_amb.
sim.reset_filter()
sim.filter_time(test_date='2/11/2022', days=60)
sim.scatter_hv()


# In[ ]:


sim.filter_irr(0.5, 1.5, ref_val=das.rc['poa'][0])
sim.fit_regression()


# In[ ]:


das.rc = rc
sim.rc = rc


# In[ ]:


SAM_val = regression_predict(sim)


# ## Boxplot dos inversores com referência do SAM
# 
# Reapresentamos a distribuição do teste de capacidade, **agora acrescentando a estimativa do SAM** como uma linha horizontal. Não confundir a dispersão entre inversores com o desvio em relação ao SAM.

# In[ ]:


# Repetir o boxplot dos testes de capacidade, acrescentando a referência SAM.
plt.figure(figsize=(5,4),)
plt.scatter(random[:-1], power_predict_df.T[:-1], alpha=0.5)
plt.boxplot(power_predict_df.T,  showfliers=False)
# add a horizontal line for the SAM prediction
plt.axhline(y=SAM_val, color='r', linestyle='--', label='SAM prediction')
# add annotation for the SAM line
plt.text(1.05, SAM_val-3.5, 't0 Modeled', color='r', va='center')
#plt.ylim(610, 700)
#plt.xticks(rotation=45)
plt.ylabel('Inverter PTC power (kW)', size=14)
# change the xtick labels to just be one tick with the label 'Inverter channel'
plt.xticks([1], ['Inverter channels 1-40'], size=14)


# In[ ]:


SAM_val


# ## Diferença aparente de capacidade
# 
# A comparação com o valor de referência é usada para uma estimativa exploratória de perda aparente. **Não interpretar automaticamente como taxa de degradação medida**: os períodos e pressupostos devem ser avaliados.

# In[ ]:


# Estimativa exploratória de perda aparente em relação à referência SAM.
p_mean = power_predict_df.T[:-1].mean()
print(f'Apparent degradation rate: -{(SAM_val - p_mean.iloc[0])/SAM_val/6*100:.2f}% per year median')
print(f'Apparent degradation: -{(SAM_val - p_mean.iloc[0])/SAM_val*100:.2f}% total')


# ## 5. Consistência dos sensores de irradiância
# 
# Comparamos o canal de referência de célula com o canal POA 02b; o código registra um possível desvio aditivo. A regressão aqui é uma comparação empírica, não uma calibração rastreável do sensor.

# In[ ]:


# Comparação entre sensores: desvio observado entre POA 02b e referência de célula.
fit = np.polyfit(das.data_filtered['reference_cell_poa_median'],das.data_filtered['poa_irradiance_02b'] , 1)
plt.figure(figsize=(5,4),)
plt.scatter(das.data_filtered['reference_cell_poa_median'], das.data_filtered['poa_irradiance_02b'], alpha=0.5)
plt.plot(das.data_filtered['reference_cell_poa_median'], fit[0]*das.data_filtered['reference_cell_poa_median'] + fit[1], color='r', label='Fit line')
plt.ylabel('POA Irradiance 02b')
plt.xlabel('RefCell Median')
plt.title(f'POA vs RefCell, fit line y={fit[0]:.4f}x + {fit[1]:.1f}')


# ## 6. Evolução das estimativas de capacidade ao longo dos anos
# 
# Repetimos testes de capacidade em janelas selecionadas e com condições de referência comparáveis. O código original inclui anos de 2016, 2017, 2018, 2021 e 2022.

# In[ ]:


# Repetir o teste de capacidade em diferentes janelas temporais.
# start by re-loading all data, then just do time filter and regression fit for the combined inverter channel, then predict power at the reference conditions for each time period to see how it changes over time.
# startdate: 2016-02-17.   enddate: 2022-03-10 (data availability is limited after 3/10/22)
das_time = ct.load_data('./data/9069_subset.csv')

das_time.agg_sensors(agg_map={'_inv_':'sum', 'irr_poa_':'median', 'temp_amb_':'median', 'wind__':'median'})
#das_time.regression_formula = 'power ~ poa + I(poa * poa) + I(poa * t_amb) + I(poa * w_vel) - 1'
das_time.regression_formula = 'power ~ poa + I(poa * poa) + I(poa * t_amb)  - 1'  # Usa temperatura do módulo no argumento t_amb.
das_time.data['refcell_adj'] = das_time.data['reference_cell_poa_median']*fit[0] + fit[1]  # apply above adjustment y = 0.9997x+49.8 to match refcell to POA


# In[ ]:


das_time.plot()


# In[ ]:


# Janelas disponíveis identificadas no estudo (a lista abaixo inclui cinco janelas).

start_dates = pd.to_datetime(['2016-02-17 6:0:0-05:00', '2017-01-01 6:0:0-05:00', '2018-01-15 6:0:0-05:00',
               '2021-01-10 6:0:0-05:00', '2022-02-01 6:0:0-05:00'])
end_dates = pd.to_datetime(['2016-02-28 20:0:0-05:00', '2017-02-28 20:0:0-05:00', '2018-01-28 20:0:0-05:00',
             '2021-02-28 20:0:0-05:00', '2022-03-10 20:0:0-05:00'])


# In[ ]:


def process_inverter_channel_time(das_time, power_col, start, end):
    das_time.reset_filter()
    das_time.filter_time(start=start, end=end)
    das_time.set_regression_cols(power=power_col, poa='refcell_adj', 
                            t_amb='module_temperature_median', w_vel='wind_speed_ms')
    das_time.filter_irr(200, 2000)
    das_time.filter_outliers()
    das_time.fit_regression(filter=True, summary=False)
    das_time.rc = rc
    das_time.filter_irr(0.5, 1.5, ref_val=rc['poa'][0])
    das_time.filter_irr(200, 950) # some clipping happening at high irradiance at 33MWac.
    das_time.fit_regression(summary=False)
    if power_col == '_inv__sum_agg':
        return regression_predict(das_time) / 40
    else:
        return regression_predict(das_time)


# In[ ]:


power_predict_time = pd.DataFrame(columns=['power_predict'], index=start_dates.date)
for i in range(len(start_dates)):
    power_predict_time.iloc[i] = process_inverter_channel_time(das_time, '_inv__sum_agg', 
                                                         start_dates[i], end_dates[i]) 


# ## Análise detalhada por inversor — rotina opcional
# 
# A rotina de todas as janelas e inversores estava desativada no código original por exigir tempo de processamento elevado.

# In[ ]:


# Rotina demorada; os resultados foram salvos para reutilização.
"""
for i in range(len(start_dates)):

    power_predict_time_df = pd.DataFrame(columns=das_time.column_groups._inv_ + ['_inv__sum_agg'], index=['power_predict'])

    # Repetir o teste de capacidade para todos os canais de inversores.
    #for power_col in ([das.column_groups._inv_[30]] ):
    for power_col in (das_time.column_groups._inv_):
        print(f'Processing {start_dates[i].date().strftime("%Y-%m-%d")}_{power_col}...')
        power_predict_time_df[power_col] = process_inverter_channel_time(das_time, power_col, start_dates[i], end_dates[i])
        das_scatter = das_time.scatter_filters()
        #hv.save(das_scatter, f'.\plots\{power_col}.html')
        hv.save(das_scatter, f'.\plots\{start_dates[i].date().strftime("%Y-%m-%d")}_{power_col}.png')

    power_predict_time_df.to_csv(f'.\data\{start_dates[i].date().strftime("%Y-%m-%d")}_800poa20tmod.csv')

"""


# In[ ]:


SAM_val


# In[ ]:


fig = plt.figure(figsize=(10,6))
plt.axhline(y=SAM_val, color='r', linestyle='--', label='SAM prediction')
plt.plot(power_predict_time, marker='o')
# add annotation for the SAM line
plt.text(power_predict_time.index[2], SAM_val-3.5, 't0 Modeled', color='r', va='center')
plt.ylabel('Inverter-level PTC power (kW)')
fig.autofmt_xdate()


# In[ ]:


# Estimar a variação aparente entre janelas de teste.
p_start = power_predict_time.iloc[0,0]
p_end = power_predict_time.iloc[-1,0]
print(f'Apparent degradation rate: {(p_end - p_start)/p_end/6*100:.2f}% per year median')
print(f'Apparent degradation: {(p_end - p_start)/p_end*100:.2f}% total')
print(f'Initial prediction: {p_start:.1f} kW, Final prediction: {p_end:.1f} kW')


# In[ ]:


i=0
scatter_dates = [start_dates[i] + pd.Timedelta(days=int(t*7)) for t in random[:-1]]


# ## Distribuições de capacidade em diferentes anos
# 
# Os boxplots desta etapa mostram a variação **das estimativas de capacidade dos inversores ao longo dos períodos de teste**.

# In[ ]:


# Recarregar as capacidades anuais e visualizar a distribuição por inversor.
import matplotlib.dates as mdates

fig = plt.figure(figsize=(7,4))
#plt.plot(power_predict_time, marker='o')

# Manter a cor de cada inversor consistente entre os anos.
df_ref = pd.read_csv(f'.\\data\\{start_dates[0].date().strftime("%Y-%m-%d")}_800poa20tmod.csv', index_col=0)
ref_vals = df_ref.T.iloc[:-1, 0].astype(float)
ref_rank = ref_vals.rank(method='first')
ref_rank_norm = ((ref_rank - 1) / (len(ref_rank) - 1)).to_dict()

for i in range(len(start_dates)):
    scatter_dates = [start_dates[i] + pd.Timedelta(days=int(t*10)) for t in random[:-1]]
    df_temp = pd.read_csv(f'.\\data\\{start_dates[i].date().strftime("%Y-%m-%d")}_800poa20tmod.csv', index_col=0)

    vals = df_temp.T.iloc[:-1, 0].astype(float)
    point_colors = vals.index.to_series().map(ref_rank_norm).to_numpy()
    plt.scatter(scatter_dates, vals.to_numpy(), c=point_colors, cmap='coolwarm', vmin=0, vmax=1, alpha=0.8)

    # Boxplot positions must be numeric for matplotlib; convert datetime to date number.
    xpos = mdates.date2num(start_dates[i].to_pydatetime())
    box_data = vals.dropna().values
    plt.boxplot([box_data], positions=[xpos], widths=100, showfliers=False, manage_ticks=False)

#plt.axhline(y=SAM_val, color='r', linestyle='--', label='SAM prediction')
# add annotation for the SAM line
#plt.text(power_predict_time.index[2]+pd.Timedelta(days=200), SAM_val+8, 't0 Modeled', color='r', va='center')
plt.ylabel('Inverter-level power (kW) at RC')
plt.gca().xaxis_date()
fig.autofmt_xdate()


# In[ ]:


df_temp.median(axis=1)


# ## RdTools analysis - merge DAS data with NSRDB satellite data. Run inverter-level clearsky degradation 


# ## 7. Degradação com RdTools e meteorologia NSRDB
# 
# Iniciamos outra abordagem: normalização da potência por condições ambientais, filtragem e estimativa de tendências de degradação com RdTools.

# In[ ]:


import rdtools
print(rdtools.__version__)


# In[ ]:


df0 = pd.read_csv('./data/9069_subset.csv', index_col = 0, parse_dates=True)
print([k for k in df0.columns])


# ## Diagnóstico de timestamps — ajuste exploratório
# 
# O código original documenta uma discrepância entre a interpretação dos horários PVDAQ e NSRDB. Remove o fuso horário, localiza em `America/New_York` e acrescenta 5 horas. **Essa transformação foi aplicada no estudo; não deve ser considerada uma correção universal sem verificação dos timestamps originais.**

# In[ ]:


df = df0.copy()

#df = df.tz_convert('UTC')
# Interpretação temporal testada no estudo: remover fuso e localizar em America/New_York.
df.index = df.index.tz_localize(None).tz_localize('America/New_York', ambiguous='NaT', nonexistent='shift_forward')
df.index = df.index + pd.Timedelta(hours=5)  # reverse ETC/GMT+5 to UTC correction...


# In[ ]:


df.head()  # first datapoint should be 2016-02-17 18:05:00-05:00


# ## Dados meteorológicos PSM4
# 
# Carregamos o arquivo parquet preparado previamente e calculamos a irradiância no plano dos módulos e de céu claro.

# In[ ]:


# load NSRDB data in parquet format: 9069_PSM4.parquet.  2016-2023. Social Circle GA, 30025
import pyarrow.parquet as pq
psm4 = pq.read_table('./data/9069_PSM4.parquet').to_pandas()
psm4.head()


# In[ ]:


# Specify the Metadata
meta = {"latitude": 33.6762, 
        "longitude": -83.676,
        "timezone": 'America/New_York',
        "gamma_pdc": -0.0034,  # Temperature coefficient for modern silicon PV modules (1/K)
        "azimuth": 180,
        "tilt": 20,
        "power_dc_rated": 680,
        "temp_model_params":'open_rack_glass_polymer'}

# Set the pvlib location
loc = pvlib.location.Location(meta['latitude'], meta['longitude'], tz = meta['timezone'])
solar_position = loc.get_solarposition(times=psm4.index)

nsrdb_poa = pvlib.irradiance.get_total_irradiance(
    surface_tilt=meta['tilt'],
    surface_azimuth=meta['azimuth'],
    dni=psm4['dni'],
    ghi=psm4['ghi'],
    dhi=psm4['dhi'],
    solar_zenith=solar_position['apparent_zenith'],
    solar_azimuth=solar_position['azimuth'])

nsrdb_clear = pvlib.irradiance.get_total_irradiance(
    surface_tilt=meta['tilt'],
    surface_azimuth=meta['azimuth'],
    dni=psm4['dni_clear'],
    ghi=psm4['ghi_clear'],
    dhi=psm4['dhi_clear'],
    solar_zenith=solar_position['apparent_zenith'],
    solar_azimuth=solar_position['azimuth'])

nsrdb_poa = nsrdb_poa.dropna()
nsrdb_clear = nsrdb_clear.dropna()
nsrdb_clear.rename(columns={'poa_global':'clearsky_poa'}, inplace=True)


# ## Médias horárias e convenção HH:30
# 
# Após a agregação para valores horários, acrescentamos 30 minutos ao rótulo do intervalo para corresponder à convenção central dos dados NSRDB. Este ajuste de **meia hora** é distinto da questão de fuso horário.

# In[ ]:


# Agregar as medidas para resolução horária e alinhar aos timestamps do NSRDB.
# Mudar rótulo de início de hora para centro da hora (HH:30).
df_hourly = df.resample('h',origin=pd.to_datetime('2016-02-17 18:00:00+0'), label='left').mean()
df_hourly.index = df_hourly.index + pd.Timedelta(minutes=30)


# In[ ]:


df_hourly.columns


# In[ ]:


# Simplificar os nomes dos canais de potência dos inversores.
inv_cols = [col for col in df_hourly.columns if 'inverter_' in col and 'ac_power_(kw)' in col]
inv_cols_rename = {col: f'inv_{i+1}_kw' for i, col in enumerate(inv_cols)}
df_hourly.rename(columns=inv_cols_rename, inplace=True)


# In[ ]:


inv_cols_rename


# ## Junção de medições com meteorologia
# 
# Associamos aos horários de campo a POA calculada, temperatura do ar, vento e POA de céu claro.

# In[ ]:


# Combinar dados de campo e meteorologia NSRDB.
df_join = df_hourly.join(nsrdb_poa[['poa_global']], how='left')
df_join = df_join.join(psm4[['temp_air', 'wind_speed']], how='left')
df_join = df_join.join(nsrdb_clear[['clearsky_poa']], how='left')

#df_join = df_join.dropna()
print(df_join.__len__())
df_join = df_join.rename(columns = {
    'poa_global': 'poa',
    'temp_air': 'Tamb',
})
df_join['power'] = df_join['inv_4_kw']


# ## Modelagem esperada e filtros para RdTools
# 
# Estimamos a temperatura de célula e a potência DC esperada, normalizamos a produção e aplicamos filtros de irradiância, temperatura, clipping e céu claro.

# In[ ]:


# Normalização exploratória da potência esperada após investigar o alinhamento temporal.


params = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_polymer']

df_join = rdtools.interpolate(df_join, 'h')
df_join['Tcell'] = pvlib.temperature.sapm_cell(df_join.poa, df_join.Tamb,
                                                df_join.wind_speed, **params)
modeled_power = pvlib.pvsystem.pvwatts_dc(df_join['poa'], df_join['Tcell'], meta['power_dc_rated'],
                                          meta['gamma_pdc'], 25.0 )

# Calcular a série normalizada e a insolação correspondente.
# each point in the normalized PV energy timeseries
normalized, insolation = rdtools.normalize_with_expected_power(df_join['power'],
                                                               modeled_power,
                                                               df_join['poa'])

df_join['normalized'] = normalized
df_join['insolation'] = insolation


normalized_mask = rdtools.normalized_filter(df_join['normalized'])
poa_mask = rdtools.poa_filter(df_join['poa'])
tcell_mask = rdtools.tcell_filter(df_join['Tcell'])
# Note: This clipping mask may be disabled when you are sure the system is not
# experiencing clipping due to high DC/AC ratio
clip_mask = rdtools.clip_filter(df_join['power'])
clearsky_mask = rdtools.clearsky_filter(df_join['poa'], df_join['clearsky_poa'], model='csi')

# filter the time series and keep only the columns needed for the**meta['temp_model_params']
# remaining steps
filtered = df_join[normalized_mask & poa_mask & tcell_mask & clip_mask & clearsky_mask]
#filtered = filtered[['insolation', 'normalized']]
print(filtered.__len__())


# In[ ]:


#  plot to show raw power and poa irradiance and clearsky irradiance for timestamp alignment check
plt.rcParams.update({'font.size': 12})
subset = df_join.loc['2019-1-01 06:00:00-05:00':'2019-1-08 20:00:00-05:00']
fig = plt.figure()
plt.plot(subset.index, subset['power'], label='Power (kW)')
plt.plot(subset.index, subset['poa'], label='POA Irradiance (W/m^2)')
plt.plot(subset.index, subset['clearsky_poa'], label='Clearsky POA Irradiance (W/m^2)')
plt.legend()
fig.autofmt_xdate()


# In[ ]:


import plotly.graph_objects as go

#subset = df_join.loc['2019-12-01 06:00:00-05:00':'2019-12-08 20:00:00-05:00']
#modeled_subset = modeled_power.loc['2019-12-01 06:00:00-05:00':'2019-12-08 20:00:00-05:00']

fig = go.Figure()
fig.add_trace(go.Scatter(x=df_hourly.index, y=df_hourly['inv_5_kw'], name='Power (kW)'))
fig.add_trace(go.Scatter(x=modeled_power.index, y=modeled_power, name='Modeled Power (kW)'))
fig.update_layout(font=dict(size=12), xaxis_title='Date', legend=dict(orientation='h'))
fig.show()


# ## Tendência ano a ano (YoY)
# 
# O RdTools estima a tendência e o intervalo de confiança da taxa de degradação aparente com os dados filtrados.

# In[ ]:


ta = rdtools.TrendAnalysis(df_join['power'], df_join['poa'],
                           temperature_ambient=df_join['Tamb'],
                           gamma_pdc=meta['gamma_pdc'],
                           interp_freq='h',
                           windspeed=df_join['wind_speed'],
                           temperature_model=meta['temp_model_params'],
                           power_dc_rated=meta['power_dc_rated'],)

ta.set_clearsky(pvlib_location=loc, pv_tilt=meta['tilt'], pv_azimuth=meta['azimuth'], albedo=0.25)
ta.filter_params['sensor_clearsky_filter'] = {'window_length':180}
ta.filter_params['poa_filter'] = {'poa_global_low':500}
ta.filter_params['normalized_filter'] = {'energy_normalized_low':0.5, 'energy_normalized_high':1.4}
ta.filter_params_aggregated['hampel_filter'] = {}
ta.filter_params_aggregated['insolation_filter'] = {}
ta.sensor_analysis(analyses=['yoy_degradation'])


# In[ ]:


yoy_results = ta.results['sensor']['yoy_degradation']
# Print the sensor-based analysis p50 degradation rate and confidence interval
print(np.round(yoy_results['p50_rd'], 3))
print(np.round(yoy_results['rd_confidence_interval'], 3))


# In[ ]:


# Plot the sensor based degradation results
plt.rcParams.update({'font.size': 12})
fig = ta.plot_degradation_summary('sensor', summary_title='Sensor-based degradation results',
                                  scatter_ymin=0.5, scatter_ymax=1.25,
                                  hist_xmin=-50, hist_xmax=60, bins=100)
plt.show()


# In[ ]:


yoy_results['rd_confidence_interval'][0]


# ## Análises individuais dos inversores
# 
# Função para repetir o fluxo de degradação para cada canal de potência.

# In[ ]:


def run_degradation(label, power, poa, tamb, windspeed):
    ta = rdtools.TrendAnalysis(power, poa,
                           temperature_ambient=tamb,
                           gamma_pdc=meta['gamma_pdc'],
                           interp_freq='h',
                           windspeed=windspeed,
                           temperature_model=meta['temp_model_params'],
                           power_dc_rated=meta['power_dc_rated'],)

    ta.set_clearsky(pvlib_location=loc, pv_tilt=meta['tilt'], pv_azimuth=meta['azimuth'], albedo=0.25)
    ta.filter_params['sensor_clearsky_filter'] = {'window_length':180}
    ta.filter_params['poa_filter'] = {'poa_global_low':500}
    ta.filter_params['normalized_filter'] = {'energy_normalized_low':0.5, 'energy_normalized_high':1.4}
    ta.filter_params_aggregated['hampel_filter'] = {}
    ta.filter_params_aggregated['insolation_filter'] = {}
    try:
        ta.sensor_analysis(analyses=['yoy_degradation'])
    except ValueError as e:
        print(f'Error in sensor_analysis for {label}: {e}')
        return None, None
    yoy_results = ta.results['sensor']['yoy_degradation']
    # Print the sensor-based analysis p50 degradation rate and confidence interval
    print(f'Inverter {label}: {np.round(yoy_results["p50_rd"], 3)}')
    print(f'Inverter {label} confidence interval: {np.round(yoy_results["rd_confidence_interval"], 3)}')

    # Plot the sensor based degradation results
    # Plot the sensor based degradation results
    plt.rcParams.update({'font.size': 12})
    fig = ta.plot_degradation_summary('sensor', summary_title='Sensor-based degradation results',
                                    scatter_ymin=0.5, scatter_ymax=1.25,
                                    hist_xmin=-50, hist_xmax=60, bins=100)
    fig.suptitle(f'Inverter {label} degradation results', fontsize=16)
    fig.savefig(f'./plots/rdtools/Inverter_{label}_degradation_results.png', dpi=300)
    return yoy_results['p50_rd'], yoy_results['rd_confidence_interval'][0], yoy_results['rd_confidence_interval'][1]


# In[ ]:


# loop over all inverters in df_join and run the degradation analysis. store results in a dataframe with 'p50_rd' and 'rd_confidence_interval' columns, indexed by inverter label.
degradation_results = pd.DataFrame(columns=['p50_rd', 'ci_low', 'ci_high'], index=[col for col in df_join.columns if 'inv_' in col])
for col in degradation_results.index:
    p50_rd, ci_low, ci_high = run_degradation(col, df_join[col], df_join['poa'], df_join['Tamb'], df_join['wind_speed'])
    degradation_results.loc[col] = [p50_rd, ci_low, ci_high]


# In[ ]:


degradation_results.to_csv('9069_rdtools_degradation_results.csv')


# In[ ]:


df_join.tail(30)


# ## Testes de agregação dos inversores
# 
# Foram exploradas maneiras diferentes de agregar os canais; soma e média após remover zeros não são equivalentes, especialmente com falhas de aquisição.

# In[ ]:


# sum all AC power together and run analysis.  First set all AC power values = 0 to NaN to not affect the mean calculation.
ac_power_sum = df_join[[col for col in df_join.columns if 'inv_' in col]].sum(axis=1)

p50_rd, ci_low, ci_high = run_degradation('ac_power_sum', ac_power_sum/40, df_join['poa'], df_join['Tamb'], df_join['wind_speed'])


# In[ ]:


# sum all AC power together and run analysis.  First set all AC power values = 0 to NaN to not affect the mean calculation.
ac_power_sum = df_join[[col for col in df_join.columns if 'inv_' in col]].replace(0, np.nan).mean(axis=1)

p50_rd, ci_low, ci_high = run_degradation('ac_power_sum', ac_power_sum, df_join['poa'], df_join['Tamb'], df_join['wind_speed'])


# In[ ]:


degradation_results.loc['ac_power_sum'] = [p50_rd, ci_low, ci_high]


# ### Análise de disponibilidade e falhas dos inversores
# 


# In[ ]:


df_join.columns


# ## 8. Medidor agregado e disponibilidade
# 
# Os medidores M1 e M2 cobrem intervalos distintos. O código original substitui valores ausentes por zero antes de somá-los, o que pode mascarar lacunas. Interpretar os resultados de disponibilidade com essa ressalva.

# In[ ]:


df_join['meter_power'] = df_join['meter_1_ac_power_kw'].replace( np.nan, 0) + df_join['meter_2_ac_power_kw'].replace( np.nan, 0) 


# In[ ]:


plt.plot(df_join.meter_power, 'b.', alpha=0.3, label='Meter Power')
plt.plot(ac_power_sum*40, 'r.', alpha=0.3, label='Inverter Power Sum')
plt.plot(modeled_power*45, 'g.', alpha=0.3, label='Modeled Power Sum')
plt.ylim(0,45000)
plt.legend()


# In[ ]:


# create cumulative sum of meter_power and ac_power_sum*40 and plot them on the same graph 
ac_power_daily = (ac_power_sum*40).groupby(df_join.index.date).sum()
daily_avg = ac_power_daily.mean()
ac_power_daily.index = pd.to_datetime(ac_power_daily.index).tz_localize(df_join.index.tz)
ac_power_daily = ac_power_daily.replace(0, daily_avg).resample('h').interpolate('linear').reindex(df_join.index, method='nearest')/24


cumsum_meter = df_join.meter_power.cumsum()
cumsum_ac_power = ac_power_daily.cumsum()
cumsum_modeled = modeled_power.cumsum()*45

fig, ax1 = plt.subplots()
ax1.plot(cumsum_meter, 'b-', alpha=0.3, label='Cumulative Meter Power')
ax1.set_ylabel('Cumulative Meter Power', color='b')
ax1.plot(cumsum_ac_power, 'r-', alpha=0.3, label='Simulated Inverter Power Sum')
ax1.plot(cumsum_modeled, 'g-', alpha=0.3, label='Cumulative Modeled Power Sum')
ax1.set_ylabel('Cumulative Inverter Power Sum', color='r')
plt.legend()
plt.show()


# In[ ]:


label='meter_power'
power = df_join['meter_power'].replace(0, np.nan)
poa = df_join['poa']
tamb = df_join['Tamb']
windspeed = df_join['wind_speed']

ta = rdtools.TrendAnalysis(power, poa,
                        temperature_ambient=tamb,
                        gamma_pdc=meta['gamma_pdc'],
                        interp_freq='h',
                        windspeed=windspeed,
                        temperature_model=meta['temp_model_params'],
                        power_dc_rated=meta['power_dc_rated']*40,
                        max_timedelta=pd.Timedelta('365d'),
                        )

ta.set_clearsky(pvlib_location=loc, pv_tilt=meta['tilt'], pv_azimuth=meta['azimuth'], albedo=0.25)
ta.filter_params['sensor_clearsky_filter'] = {'window_length':180}
ta.filter_params['poa_filter'] = {'poa_global_low':500}
ta.filter_params['normalized_filter'] = {'energy_normalized_low':0.5, 'energy_normalized_high':1.4}
ta.filter_params_aggregated['hampel_filter'] = {}
ta.filter_params_aggregated['insolation_filter'] = {}


# In[ ]:


try:
    ta.sensor_analysis(analyses=['yoy_degradation'])
except ValueError as e:
    print(f'Error in sensor_analysis for {label}: {e}')
    #return None, None
yoy_results = ta.results['sensor']['yoy_degradation']
# Print the sensor-based analysis p50 degradation rate and confidence interval
print(f'Inverter {label}: {np.round(yoy_results["p50_rd"], 3)}')
print(f'Inverter {label} confidence interval: {np.round(yoy_results["rd_confidence_interval"], 3)}')

# Plot the sensor based degradation results
# Plot the sensor based degradation results
plt.rcParams.update({'font.size': 12})
fig = ta.plot_degradation_summary('sensor', summary_title='Sensor-based degradation results',
                                scatter_ymin=0.5, scatter_ymax=1.25,
                                hist_xmin=-50, hist_xmax=60, bins=100)
fig.suptitle(f'Site meter degradation results', fontsize=16)
fig.savefig(f'./plots/rdtools/Site_meter_degradation_results.png', dpi=300)
#return yoy_results['p50_rd'], yoy_results['rd_confidence_interval'][0], yoy_results['rd_confidence_interval'][1]


# In[ ]:


# Visualizar a evolução temporal da degradação estimada.
ta.plot_degradation_timeseries(case='sensor', rolling_days=365, center=True, min_periods_divisor=12)


# ## Análise de disponibilidade com RdTools
# 
# Comparamos potência do sistema, subsistemas e potência esperada para avaliar períodos de indisponibilidade dos inversores.

# In[ ]:


columns = [col for col in df_join.columns if 'inv_' in col]
from rdtools.availability import AvailabilityAnalysis
aa = AvailabilityAnalysis(
    power_system=df_join['meter_power'].where(df_join['meter_power'].between(0, 50000)).replace(0, np.nan),
    power_subsystem=df_join[columns],
    energy_cumulative=cumsum_ac_power,
    power_expected=modeled_power*45,
)
# identify and classify outages, rolling up to daily metrics for this short dataset:
aa.run(rollup_period='D')


# In[ ]:


fig = aa.plot()
fig.set_size_inches(16, 7)
fig.axes[1].legend(loc='upper left')
plt.show()


# In[ ]:


import pprint


# In[ ]:


results = aa.results
fig = plt.figure(figsize=(6,4))
plt.plot(results['availability'].resample('30D').mean(), label='Availability')
plt.ylabel('Monthly inverter availability')
fig.savefig(f'./plots/rdtools/Availability_results.png', dpi=300)

print('Yearly availability:')
print(results['availability'].resample('YE', ).mean().index)
print(results['availability'].resample('YE', ).mean().values)


# In[ ]:


temp = results['availability'].resample('YE', ).mean()


# In[ ]:


results.to_csv('9069_rdtools_availability_results.csv')


# ## 9. Performance Ratio (PR) mensal
# 
# Calculamos um PR exploratório a partir de energia AC e irradiação POA para períodos filtrados. A agregação pressupõe consistência dos intervalos temporais e das medições.

# In[ ]:


# Calcular e representar o Performance Ratio mensal.
pr_calc = df_join[['meter_power', 'poa']]
pr_calc = pr_calc[(pr_calc['meter_power'].between(0,50000)) & (pr_calc['poa'].between(0,2000))]
pr_calc['yf'] = pr_calc['meter_power'] / (38600)
pr_calc['yr'] = pr_calc['poa'] / (1000)
pr_calc['sequential_month'] = pr_calc.index.to_period('M').to_timestamp()

pr_monthly = pr_calc.groupby('sequential_month').sum()
pr_monthly['PR'] = pr_monthly['yf'] / pr_monthly['yr']
plt.figure(figsize=(6,4))
plt.bar(pr_monthly.index, pr_monthly['PR'], width=30, align='center')
plt.ylabel('Monthly Site PR')
plt.title(f'Site PR. Yr1: {pr_monthly.iloc[:12].PR.mean():.3f}')


# ## Resumo estatístico do PR
# 
# As estatísticas impressas precisam ser interpretadas considerando os meses incompletos e os filtros aplicados.

# In[ ]:


print(f'Yr1 average PR: {pr_monthly.iloc[:12].PR.mean():.3f}')
print(f'Excluding low (<0.4) Months: {pr_monthly[pr_monthly.PR>0.4].PR.mean():.3f}')
print(f'Median PR: {pr_monthly.PR.median():.3f}')
print(f'Mean PR: {pr_monthly.PR.mean():.3f}')

