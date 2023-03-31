import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
import re

st.set_page_config('Destino', 'https://controllab.com/wp-content/uploads/favicon-32x32-1.png')
ano = dt.datetime.now().year
mes = dt.datetime.now().month

def convert_num_to_text(datas):
    mes_text = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    nova_lista = list()
    padrao = re.compile('\d{1,2}\/')
    for data in datas:                
        mes = data.split('/')[0]
        nova_data = padrao.sub(f'{mes_text[int(mes)-1]}/', data)
        nova_lista.append(nova_data)
    return nova_lista

def datas_futuras(ano, mes):        
    range_ano =list()
    for i in range(1,13):
        mes += + 1
        if mes > 12:
            mes =1
            ano += 1
        texto = f'{mes}/{ano}'
        range_ano.append(texto)    
    range_ano = convert_num_to_text(range_ano)    
    return range_ano

range_ano = datas_futuras(ano, mes)






st.image('https://controllab.com/wp-content/uploads/logo_controllab_secundario_COR.png', width=200)
st.title('Formação de kit')

def pegar_itens(itens, df):
    cols = st.columns(itens+1)
    itens_list = [cols[i].selectbox(f'item {i+1}', 
                               options=list(df.lote)[:itens]+[''],
                               index=len(list(df.lote)[:itens]))for i in range(itens)]
    cols[itens].selectbox('Rodada', options=range_ano)


def formar_kits(tipo: str, itens: int, qtd: int, produto: str,dados):
    '''
    Tipo: EP ou CI
    Itens: Quantidade de itens para formação do Kit
    qtd: Quantos kits serão formados
    produto: Qual produto quer o kit
    dados: DataFrame para fazer o match
    '''
    texto = r'\space Sem \space Lote'
    if 'Kit_CI' == tipo:
        intermediario = dados.loc[(dados.Int_CI >= qtd) & (dados.produto == produto)]
        if len(intermediario)>=itens:
            intermediario.sort_values('Int_CI', inplace=True)
            
            texto = fr'''
Intermediário\space CI\space\to Kit \space CI
            '''
            df = intermediario.set_index('lote')[:itens]
            return df, texto

        else:   
            intermediario.sort_values('Int_CI', ascending=False,inplace=True)
            falta = itens - len(intermediario)
            lotes_direto = list(intermediario['lote'])[:]
            lotes_direto = ', '.join(lotes_direto)
            dados['quantidade_base'] = dados.Base + dados.Int_CI
            
            intermediario2 = dados.loc[(dados.quantidade_base >= qtd) & 
                                      (dados.produto == produto)]
            
            # intermediario2.Base = intermediario2.Base - intermediario2.Int_CI
            
            intermediario3 = pd.concat([intermediario, intermediario2[:falta]])
            intermediario3.drop(['produto', 'quantidade_base'], axis=1, inplace=True)
            lotes = list(intermediario3.lote)[:falta]
            lotes_base = ', '.join(lotes)
            

            if len(intermediario3)<itens:
                falta = itens - len(intermediario3)
                dados['quantidade_intep'] = dados.Int_EP + dados.Base + dados.Int_CI
                intermediario4= dados.loc[(dados.quantidade_intep >= qtd) &
                                           (dados.produto == produto) & 
                                           (~dados.lote.isin(list(intermediario3.lote)))]
                intermediario5 = pd.concat([intermediario3, intermediario4[:falta]])
                interep = pegar_lotes(falta, intermediario4)

                if len(intermediario5)<itens:
                    falta = itens - len(intermediario5)
                    dados['qtd_kit_ci'] = dados.Int_EP + dados.Base + \
                                            dados.Int_CI + dados.Kit_CI
                    intermediario6 = dados.loc[(dados.qtd_kit_ci >= qtd) &
                                           (dados.produto == produto) & 
                                           (~dados.lote.isin(list(intermediario5.lote)))]
                    intermediario7 = pd.concat([intermediario5, intermediario6[:falta]])
                    kitci = pegar_lotes(falta, intermediario7)

                    if len(intermediario7)<itens:
                        pass
                    else:
                        st.warning(f'Os lotes {interep} serão usados do Intermediário EP \n\nOs lotes {kitci} serão usados do Kit CI')
                        
                        texto = (fr'''\\
            Lote(s)\space | \space {lotes_direto}\\
            Intermediário\space CI\space\to Kit \space CI
            \\
            \\-------------------------------------\\
            Lote(s)\space | \space {lotes_base}\\
            Base\space\space\to\space Rotulagem\space\to\space Intermediário\space CI\space\to\space Kit\space CI\\
            \\-------------------------------------\\   
            Lote(s)\space | \space {interep}\\
            Intermediário\space EP\space\to Rotulagem \space\to\space Intermediário \space CI \space\to\space Kit\space CI
            \\-------------------------------------\\   
            Lote(s)\space | \space {kitci}\\
            Kit\space CI\space\to Desmonte \space\to\space Intermediário \space CI \space\to\space Kit\space CI
            \\
                        ''')
                        df =intermediario7.set_index('lote').drop(['produto', 'quantidade_base', 'quantidade_intep'], axis =1)
                        return df, texto

                else:            

                    st.warning(f'Os lotes {lotes_base} serão usados do lote do Base \n\nOs lotes {interep} serão usados do Intermediário EP')
                    
                    texto = (fr'''\\
        Lote(s)\space | \space {lotes_direto}\\
        Intermediário\space CI\space\to Kit \space CI
        \\
        \\-------------------------------------\\
        Lote(s)\space | \space {lotes_base}\\
        Base\space\space\to\space Rotulagem\space\to\space Intermediário\space CI\space\to\space Kit\space CI\\
        \\-------------------------------------\\   
        Lote(s)\space | \space {interep}\\
        Intermediário\space EP\space\to Rotulagem \space\to\space Intermediário \space CI \space\to\space Kit\space CI
                    ''')
                    df = intermediario5.set_index('lote').drop(['produto', 'quantidade_base', 'quantidade_intep'], axis =1)
                    return df, texto
            else:

                st.warning(f'Os lotes {lotes_base} serão usados do lote do Base')
                df = intermediario3.set_index('lote')[:itens]
                
                texto = (fr'''\\
    Lote(s)\space | \space {lotes_direto if ',' in lotes_direto else texto}\\
    Intermediário\space CI\space\to Kit \space CI
    \\-------------------------------------\\
    Lote(s)\space | \space {lotes_base}\\
    Base\space\space\to\space Rotulagem\space\to\space Intermediário CI\space\to\space Kit\space CI\\


                ''')
                return df, texto
    
    elif 'Kit_EP' == tipo:
        intermediario = dados.loc[(dados.Int_EP >= qtd) & (dados.produto == produto)]

    else:
        intermediario = dados
    
    return  intermediario

def pegar_lotes(falta, intermediario4):
    interep = list(intermediario4.lote)[:falta]
    interep = ', '.join(interep)
    return interep


dados = pd.read_csv('dados.csv')

cols = st.columns(4)

produto = cols[0].selectbox('Produto', options=list(dados.produto.unique())+ [''], index=len(dados.produto.unique()))

colunas = list(dados.columns) + ['']

colunas = [x for x in colunas if x not in ['produto', 'validade', 'lote']]

destino = cols[1].selectbox('Destino', options=['', 'Kit_CI', 'Kit_EP'],)
quantidade = cols[2].number_input('Quantidade de kits', min_value=1)
itens = cols[3].number_input('Quantidade de itens', min_value=1)
btn_destino = cols[0].button('Destinar', type='primary')
df, texto = formar_kits(destino, itens, quantidade, produto, dados)
pegar_itens(itens, df.reset_index())
if btn_destino:
    
    tabela = dados.drop('produto', axis=1).loc[dados.produto==produto]
    
    st.write(df)
    df.to_csv('intermediario.csv', index=False)
# try:
#     inte = pd.read_csv('intermediario.csv')
#     st.write(inte)
#     lotes = st.multiselect('Lotes:', options=inte.lote.unique(), max_selections=itens)
#     btn_confirmar = st.button('Confirmar', )
#     if btn_confirmar:
#         st.write(inte.loc[inte.isin(lotes)])
# except:
#     pass





# tabela = dados.drop('produto', axis=1).loc[dados.produto==produto]
# st.write(tabela if produto != '' else '') 





    # dados = [
    #     pd.DataFrame(dict(
    #     lote = [f'CO-{i}' for i in range(1,51)],
    #     validade = [dt.datetime(np.random.randint(2022,2025),np.random.randint(1,13), np.random.randint(1,25)) for i in range(50)],
    #     Base = np.random.randint(0, 60, 50),
    #     CP = np.random.randint(0, 20, 50),
    #     CQM = np.random.randint(0, 12, 50),
    #     Int_CI = np.random.randint(0, 60, 50),
    #     Int_EP = np.random.randint(0, 60, 50),
    #     Kit_CI = np.random.randint(0, 60, 50),
    #     Kit_EP = np.random.randint(0, 60, 50),
    #     produto = ['Coagulação']*50)),
    #     pd.DataFrame(dict(
    #     lote = [f'FE-{i}' for i in range(1,51)],
    #     validade = [dt.datetime(np.random.randint(2022,2025),np.random.randint(1,13), np.random.randint(1,25)) for i in range(50)],
    #     Base = np.random.randint(0, 60, 50),
    #     CP = np.random.randint(0, 20, 50),
    #     CQM = np.random.randint(0, 12, 50),
    #     Int_CI = np.random.randint(0, 60, 50),
    #     Int_EP = np.random.randint(0, 60, 50),
    #     Kit_CI = np.random.randint(0, 60, 50),
    #     Kit_EP = np.random.randint(0, 60, 50),
    #     produto = ['Anemia']*50)),
    #     pd.DataFrame(dict(
    #     lote = [f'GIH-{i}' for i in range(1,51)],
    #     validade = [dt.datetime(np.random.randint(2022,2025),np.random.randint(1,13), np.random.randint(1,25)) for i in range(50)],
    #     Base = np.random.randint(0, 60, 50),
    #     CP = np.random.randint(0, 20, 50),
    #     CQM = np.random.randint(0, 12, 50),
    #     Int_CI = np.random.randint(0, 60, 50),
    #     Int_EP = np.random.randint(0, 60, 50),
    #     Kit_CI = np.random.randint(0, 60, 50),
    #     Kit_EP = np.random.randint(0, 60, 50),
    #     produto = ['Bioquímica']*50)),
    #     pd.DataFrame(dict(
    #     lote = [f'DDI-{i}' for i in range(1,51)],
    #     validade = [dt.datetime(np.random.randint(2022,2025),np.random.randint(1,13), np.random.randint(1,25)) for i in range(50)],
    #     Base = np.random.randint(0, 60, 50),
    #     CP = np.random.randint(0, 20, 50),
    #     CQM = np.random.randint(0, 12, 50),
    #     Int_CI = np.random.randint(0, 60, 50),
    #     Int_EP = np.random.randint(0, 60, 50),
    #     Kit_CI = np.random.randint(0, 60, 50),
    #     Kit_EP = np.random.randint(0, 60, 50),
    #     produto = ['Dímero D']*50))
    #     ]
    # dados = pd.concat(dados, ignore_index=True)

    # dados.to_csv('dados.csv', index=False)



