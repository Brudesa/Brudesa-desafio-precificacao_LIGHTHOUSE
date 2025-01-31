import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np
import joblib

# Definir o caminho do arquivo
df = pd.read_csv (r'C:\Projetos\DesafioBruna\teste_indicium_precificacao.csv')

# Renomear colunas para português
colunas_renomeadas = {
    'id': 'id', 'nome': 'nome', 'host_id': 'id_host', 'host_name': 'nome_host',
    'bairro_group': 'grupo_bairro', 'bairro': 'bairro', 'latitude': 'latitude', 'longitude': 'longitude',
    'room_type': 'tipo_quarto', 'price': 'preco', 'minimo_noites': 'noites_minimas',
    'numero_de_reviews': 'numero_de_reviews', 'ultima_review': 'ultima_review',
    'reviews_por_mes': 'reviews_por_mes', 'calculado_host_listings_count': 'contagem_ofertas',
    'disponibilidade_365': 'disponibilidade_365'
}
df.rename(columns=colunas_renomeadas, inplace=True)

# Remover outliers do preço
df = df[(df['preco'] > 20) & (df['preco'] < 1000)]

# Preencher valores ausentes
df['reviews_por_mes'] = df['reviews_por_mes'].fillna(df['reviews_por_mes'].median())

# Criar novas variáveis
df['tem_reviews'] = df['numero_de_reviews'] > 0
df['ano_recente'] = df['ultima_review'].apply(lambda x: 1 if pd.notna(x) and '2019' in str(x) else 0)

# Separar variáveis para modelagem
features = ['grupo_bairro', 'tipo_quarto', 'latitude', 'longitude', 'noites_minimas',
            'numero_de_reviews', 'reviews_por_mes', 'contagem_ofertas', 'disponibilidade_365',
            'tem_reviews', 'ano_recente']
target = 'preco'

# Separar colunas numéricas e categóricas
numeric_features = ['latitude', 'longitude', 'noites_minimas', 'numero_de_reviews',
                    'reviews_por_mes', 'contagem_ofertas', 'disponibilidade_365', 'ano_recente']
categorical_features = ['grupo_bairro', 'tipo_quarto', 'tem_reviews']

# Criar pipeline de pré-processamento
numeric_transformer = SimpleImputer(strategy='mean')
categorical_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='most_frequent')),
    ('onehot', OneHotEncoder(drop='first'))
])
preprocessor = ColumnTransformer([
    ('num', numeric_transformer, numeric_features),
    ('cat', categorical_transformer, categorical_features)
])

# Aplicar transformação aos dados
X = preprocessor.fit_transform(df)
y = df[target]

# Dividir os dados em treino e teste
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Criar e treinar os modelos
modelo_lr = LinearRegression()
modelo_rf = RandomForestRegressor(n_estimators=100, random_state=42)
modelo_lr.fit(X_train, y_train)
modelo_rf.fit(X_train, y_train)

# Fazer previsões
y_pred_lr = modelo_lr.predict(X_test)
y_pred_rf = modelo_rf.predict(X_test)

# Avaliação dos modelos
mse_lr = mean_squared_error(y_test, y_pred_lr)
r2_lr = r2_score(y_test, y_pred_lr)
mse_rf = mean_squared_error(y_test, y_pred_rf)
r2_rf = r2_score(y_test, y_pred_rf)

print(f'Regressão Linear - MSE: {mse_lr:.2f}, R² Score: {r2_lr:.2f}')
print(f'Random Forest - MSE: {mse_rf:.2f}, R² Score: {r2_rf:.2f}')

# Salvar o modelo Random Forest
joblib.dump(modelo_rf, 'modelo_precificacao.pkl')

# Exemplo de previsão
exemplo = pd.DataFrame({
    'latitude': [40.75362], 'longitude': [-73.98377], 'noites_minimas': [1],
    'numero_de_reviews': [45], 'reviews_por_mes': [0.38], 'contagem_ofertas': [2],
    'disponibilidade_365': [355], 'tem_reviews': [1], 'ano_recente': [1],
    'grupo_bairro': ['Manhattan'], 'tipo_quarto': ['Entire home/apt']
})
exemplo_transf = preprocessor.transform(exemplo)
previsao_preco = modelo_rf.predict(exemplo_transf)
print(f'Preço previsto: ${previsao_preco[0]:.2f}')
