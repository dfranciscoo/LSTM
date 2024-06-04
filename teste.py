import pandas as pd

# Ler o arquivo CSV
df = pd.read_csv('diabetes_trans.csv')
df = df.head(100)
# Excluir a coluna 'outcome'
df.drop('Outcome', axis=1, inplace=True)
df.drop('Age', axis=1, inplace=True)
df.drop('Pregnancies', axis=1, inplace=True)

# Definir o intervalo de tempo em minutos
intervalo_minutos = 30

# Calcular o número de períodos
num_periodos = len(df)
# Criar uma série de datas com intervalos de 30 minutos
datas = pd.date_range(start='2024-05-09', periods=num_periodos, freq=f'{intervalo_minutos}T')

# Adicionar uma nova coluna 'data' com os valores sequenciais de datas
df['data'] = datas
print(df)
# Salvar o DataFrame resultante em um novo arquivo CSV
df.to_csv('novo_arquivo.csv', index=False)
