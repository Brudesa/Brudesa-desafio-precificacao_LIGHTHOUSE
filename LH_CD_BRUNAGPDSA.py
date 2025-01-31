# Importação das bibliotecas necessárias para análise, visualização e modelagem
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import joblib

# Definição do caminho do arquivo (ajuste conforme necessário)
caminho_arquivo = r'C:\Projetos\DesafioBruna\teste_indicium_precificacao.csv'

# Carregamento do dataset
df = pd.read_csv(caminho_arquivo)

# Ajustando nomes de colunas para melhor compreensão
df.rename(columns={
    'id': 'id',
    'nome': 'nome',
    'host_id': 'id_host',
    'host_name': 'nome_host',
    'bairro_group': 'grupo_bairro',
    'bairro': 'bairro',
    'latitude': 'latitude',
    'longitude': 'longitude',
    'room_type': 'tipo_quarto',
    'price': 'preco',
    'minimum_nights': 'minimo_noites',  # Nome corrigido
    'number_of_reviews': 'numero_de_reviews',
    'last_review': 'ultima_review',
    'reviews_per_month': 'reviews_por_mes',
    'calculated_host_listings_count': 'calculado_host_listings_count',
    'availability_365': 'disponibilidade_365'
}, inplace=True)

# Visualização inicial dos dados
print("\nAmostra dos dados após renomeação:")
print(df.head())

# Analisando valores ausentes
print("\nValores ausentes por coluna:")
print(df.isnull().sum())

# Preenchendo valores ausentes de forma estratégica
df['reviews_por_mes'].fillna(df['reviews_por_mes'].median(), inplace=True)

# Criando novas variáveis para enriquecer a análise
df['tem_reviews'] = df['numero_de_reviews'] > 0

# Correção: Fechamento correto da lambda function para evitar erro de sintaxe
df['ano_recente'] = df['ultima_review'].apply(lambda x: 1 if pd.notna(x) and '2019' in str(x) else 0)

# Removendo preços extremamente baixos ou altos (prováveis erros de cadastro)
limite_inferior = df['preco'].quantile(0.05)  # Considerando apenas a partir do percentil 5%
limite_superior = df['preco'].quantile(0.95)  # Limitando ao percentil 95% para evitar distorções
df = df[(df['preco'] >= limite_inferior) & (df['preco'] <= limite_superior)]

# Estatísticas gerais sobre os preços ajustados
print("\nEstatísticas sobre a distribuição de preços após tratamento:")
print(df['preco'].describe())

# Visualizando a distribuição dos preços ajustados
plt.figure(figsize=(10, 6))
sns.histplot(df["preco"], bins=50, kde=True)
plt.title("Distribuição dos Preços Ajustada")
plt.xlabel("Preço")
plt.ylabel("Frequência")
plt.show()

# Scatter plot para explorar relação entre preço e número de reviews
plt.figure(figsize=(10, 6))
sns.scatterplot(x=df["numero_de_reviews"], y=df["preco"], alpha=0.5)
plt.title("Relação entre Preço e Número de Reviews")
plt.xlabel("Número de Reviews")
plt.ylabel("Preço")
plt.show()

# Nuvem de palavras dos anúncios mais caros (top 10% em preço)
top_10_percent = df[df["preco"] > df["preco"].quantile(0.9)]
text_nomes = " ".join(top_10_percent["nome"].dropna())

wordcloud = WordCloud(width=800, height=400, background_color="white").generate(text_nomes)

plt.figure(figsize=(12, 6))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis("off")
plt.title("Palavras mais frequentes em Nomes de Propriedades Caras")
plt.show()

# --- MODELAGEM PREDITIVA ---

# Seleção das variáveis relevantes
features = ['grupo_bairro', 'tipo_quarto', 'latitude', 'longitude', 'minimo_noites',
            'numero_de_reviews', 'reviews_por_mes', 'calculado_host_listings_count', 'disponibilidade_365',
            'tem_reviews', 'ano_recente']
target = 'preco'

# Separação entre variáveis numéricas e categóricas
num_vars = ['latitude', 'longitude', 'minimo_noites', 'numero_de_reviews', 
            'reviews_por_mes', 'calculado_host_listings_count', 'disponibilidade_365', 'ano_recente']
cat_vars = ['grupo_bairro', 'tipo_quarto', 'tem_reviews']

# Criando pipelines para transformação dos dados
num_transformer = SimpleImputer(strategy='median')  # Mediana é menos sensível a outliers
cat_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='most_frequent')),
    ('onehot', OneHotEncoder(handle_unknown='ignore'))  # Evitar erro com categorias desconhecidas
])

# Combinando transformações
preprocessor = ColumnTransformer([
    ('num', num_transformer, num_vars),
    ('cat', cat_transformer, cat_vars)
])

# Preparando os dados para modelagem
X = preprocessor.fit_transform(df)
y = df[target]

# Divisão em treino e teste
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

# Definição dos modelos
modelo_lr = LinearRegression()
modelo_rf = RandomForestRegressor(n_estimators=150, max_depth=10, random_state=42)  # Ajuste fino para melhor desempenho

# Treinamento dos modelos
modelo_lr.fit(X_train, y_train)
modelo_rf.fit(X_train, y_train)

# Previsões
y_pred_lr = modelo_lr.predict(X_test)
y_pred_rf = modelo_rf.predict(X_test)

# Avaliação dos modelos
mse_lr, r2_lr = mean_squared_error(y_test, y_pred_lr), r2_score(y_test, y_pred_lr)
mse_rf, r2_rf = mean_squared_error(y_test, y_pred_rf), r2_score(y_test, y_pred_rf)

print(f"\nResultados da Regressão Linear - MSE: {mse_lr:.2f}, R²: {r2_lr:.2f}")
print(f"Resultados do Random Forest - MSE: {mse_rf:.2f}, R²: {r2_rf:.2f}")

# Salvando o modelo Random Forest para futuras previsões
joblib.dump(modelo_rf, 'modelo_precificacao_rf.pkl')

# Testando uma previsão com um exemplo realista
exemplo = pd.DataFrame({
    'latitude': [40.7128], 'longitude': [-74.0060], 'minimo_noites': [2],  # Nome atualizado corretamente
    'numero_de_reviews': [50], 'reviews_por_mes': [1.2], 'calculado_host_listings_count': [5],
    'disponibilidade_365': [180], 'tem_reviews': [1], 'ano_recente': [1],
    'grupo_bairro': ['Manhattan'], 'tipo_quarto': ['Entire home/apt']
})

# Transformação e previsão
exemplo_transformado = preprocessor.transform(exemplo)
previsao_preco = modelo_rf.predict(exemplo_transformado)

print(f"\nPreço previsto para o exemplo: ${previsao_preco[0]:.2f}")
