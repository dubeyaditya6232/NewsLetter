import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import xml.etree.ElementTree as ET
import random
from faker import Faker
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import numpy as np
# Add new imports
import networkx as nx
from mlxtend.frequent_patterns import apriori
from mlxtend.frequent_patterns import association_rules
from scipy import stats
from lxml import etree

sns.set(style="whitegrid")

# Step 1: Generate synthetic XML data
fake = Faker()
def generate_fake_xml():
    num_actions = random.randint(1, 3)
    num_conditions = random.randint(1, 4)
    actions = ''.join([
        f"<RulesAction><ActionType>{random.choice(['EmailAlert', 'BlockTransaction', 'FlagTransaction'])}</ActionType><ActionValue>{fake.word()}</ActionValue></RulesAction>"
        for _ in range(num_actions)
    ])
    conditions = ''.join([
        f"<RulesCondition><ConditionField>{random.choice(['Amount', 'Location', 'UserType'])}</ConditionField><ConditionValue>{random.randint(1, 100)}</ConditionValue></RulesCondition>"
        for _ in range(num_conditions)
    ])
    return f"<Rule>{actions}{conditions}</Rule>"

def generate_fake_xml_with_timestamp():
    timestamp = fake.date_time_between(start_date='-1y', end_date='now')
    rule = generate_fake_xml().replace('</Rule>', f'<Timestamp>{timestamp}</Timestamp></Rule>')
    return rule, timestamp

# Update DataFrame creation to include timestamps
df = pd.DataFrame([generate_fake_xml_with_timestamp() for _ in range(1000)], 
                 columns=['xml_column', 'timestamp'])

# Step 2: Parse XML into structured columns
def parse_xml(xml_string):
    try:
        root = ET.fromstring(xml_string)
        actions, conditions = [], []
        for action in root.findall('.//RulesAction'):
            actions.append({elem.tag: elem.text for elem in action})
        for condition in root.findall('.//RulesCondition'):
            conditions.append({elem.tag: elem.text for elem in condition})
        return actions, conditions
    except Exception:
        return [], []

df['parsed'] = df['xml_column'].apply(parse_xml)
df['actions'] = df['parsed'].apply(lambda x: x[0])
df['conditions'] = df['parsed'].apply(lambda x: x[1])
df.drop(columns='parsed', inplace=True)

# Step 3: Flatten data
actions_df = pd.json_normalize(df.explode('actions')['actions'].dropna()).reset_index(drop=True)
conditions_df = pd.json_normalize(df.explode('conditions')['conditions'].dropna()).reset_index(drop=True)

df['num_actions'] = df['actions'].apply(len)
df['num_conditions'] = df['conditions'].apply(len)

# Step 4: Visualization
fig, axes = plt.subplots(3, 2, figsize=(16, 15))
sns.countplot(data=actions_df, x='ActionType', ax=axes[0, 0], order=actions_df['ActionType'].value_counts().index)
axes[0, 0].set_title('Distribution of Rule Actions')
axes[0, 0].tick_params(axis='x', rotation=45)

sns.countplot(data=conditions_df, x='ConditionField', ax=axes[0, 1], order=conditions_df['ConditionField'].value_counts().index)
axes[0, 1].set_title('Distribution of Rule Condition Fields')
axes[0, 1].tick_params(axis='x', rotation=45)

sns.histplot(df['num_actions'], bins=range(1, 6), kde=False, ax=axes[1, 0])
axes[1, 0].set_title('Number of Actions per Rule')

sns.histplot(df['num_conditions'], bins=range(1, 6), kde=False, ax=axes[1, 1])
axes[1, 1].set_title('Number of Conditions per Rule')

conditions_df['ConditionValue'] = conditions_df['ConditionValue'].astype(int)
sns.boxplot(data=conditions_df, x='ConditionField', y='ConditionValue', ax=axes[2, 0])
axes[2, 0].set_title('Condition Values by Field')

pivot = pd.merge(conditions_df, actions_df, left_index=True, right_index=True, how='inner')
pivot['ConditionValue'] = pivot['ConditionValue'].astype(int)
heatmap_data = pivot.pivot_table(index='ConditionField', columns='ActionType', values='ConditionValue', aggfunc='mean')
sns.heatmap(heatmap_data, annot=True, fmt=".1f", cmap='coolwarm', ax=axes[2, 1])
axes[2, 1].set_title('Avg. Condition Value per Field & Action Type')
plt.tight_layout()
plt.show()

# Step 5: Extended EDA
plt.figure(figsize=(8, 5))
sns.scatterplot(data=df, x='num_conditions', y='num_actions', alpha=0.5)
plt.title('Rule Complexity: Number of Conditions vs Actions')
plt.xlabel('Number of Conditions')
plt.ylabel('Number of Actions')
plt.tight_layout()
plt.show()

# Duplicates
df['action_keys'] = df['actions'].apply(lambda x: tuple(sorted(f"{i.get('ActionType')}:{i.get('ActionValue')}" for i in x)))
df['condition_keys'] = df['conditions'].apply(lambda x: tuple(sorted(f"{i.get('ConditionField')}:{i.get('ConditionValue')}" for i in x)))
df['rule_signature'] = df.apply(lambda row: (row['action_keys'], row['condition_keys']), axis=1)
duplicate_rules = df['rule_signature'].value_counts()

# Add after the duplicate_rules calculation

# Enhanced Redundancy Analysis
def analyze_redundancies(df):
    # 1. Exact duplicates
    exact_duplicates = df['rule_signature'].value_counts()
    
    # 2. Action pattern redundancy
    action_patterns = df['action_keys'].value_counts()
    
    # 3. Condition pattern redundancy
    condition_patterns = df['condition_keys'].value_counts()
    
    # 4. Semantic redundancy (similar rules with different values)
    def get_semantic_pattern(row):
        actions = tuple(sorted(a['ActionType'] for a in row['actions']))
        conditions = tuple(sorted(c['ConditionField'] for c in row['conditions']))
        return (actions, conditions)
    
    df['semantic_pattern'] = df.apply(get_semantic_pattern, axis=1)
    semantic_duplicates = df['semantic_pattern'].value_counts()
    
    return {
        'exact_duplicates': exact_duplicates,
        'action_patterns': action_patterns,
        'condition_patterns': condition_patterns,
        'semantic_duplicates': semantic_duplicates
    }

redundancy_analysis = analyze_redundancies(df)

# Visualize redundancy metrics
fig, axes = plt.subplots(2, 2, figsize=(15, 12))

# Plot top 10 exact duplicates
redundancy_analysis['exact_duplicates'].head(10).plot(kind='bar', ax=axes[0,0])
axes[0,0].set_title('Top 10 Exact Rule Duplicates')
axes[0,0].tick_params(axis='x', rotation=45)

# Plot top 10 action patterns
redundancy_analysis['action_patterns'].head(10).plot(kind='bar', ax=axes[0,1])
axes[0,1].set_title('Top 10 Action Patterns')
axes[0,1].tick_params(axis='x', rotation=45)

# Plot top 10 condition patterns
redundancy_analysis['condition_patterns'].head(10).plot(kind='bar', ax=axes[1,0])
axes[1,0].set_title('Top 10 Condition Patterns')
axes[1,0].tick_params(axis='x', rotation=45)

# Plot top 10 semantic duplicates
redundancy_analysis['semantic_duplicates'].head(10).plot(kind='bar', ax=axes[1,1])
axes[1,1].set_title('Top 10 Semantic Duplicates')
axes[1,1].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.show()

# Calculate redundancy metrics
print("\nRedundancy Metrics:")
print(f"Total unique rules: {len(df)}")
print(f"Unique exact rules: {len(redundancy_analysis['exact_duplicates'])}")
print(f"Unique action patterns: {len(redundancy_analysis['action_patterns'])}")
print(f"Unique condition patterns: {len(redundancy_analysis['condition_patterns'])}")
print(f"Unique semantic patterns: {len(redundancy_analysis['semantic_duplicates'])}")

# Calculate redundancy percentages
total_rules = len(df)
redundancy_percentages = {
    'Exact Duplicates': (1 - len(redundancy_analysis['exact_duplicates'])/total_rules) * 100,
    'Action Pattern': (1 - len(redundancy_analysis['action_patterns'])/total_rules) * 100,
    'Condition Pattern': (1 - len(redundancy_analysis['condition_patterns'])/total_rules) * 100,
    'Semantic': (1 - len(redundancy_analysis['semantic_duplicates'])/total_rules) * 100
}

# Plot redundancy percentages
plt.figure(figsize=(10, 6))
plt.bar(redundancy_percentages.keys(), redundancy_percentages.values())
plt.title('Rule Redundancy Percentages')
plt.ylabel('Redundancy %')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# Field importance
field_importance = conditions_df['ConditionField'].value_counts()

# Action-Condition Linkage Matrix
mlb_conditions = MultiLabelBinarizer()
mlb_actions = MultiLabelBinarizer()
condition_matrix = mlb_conditions.fit_transform(df['condition_keys'])
action_matrix = mlb_actions.fit_transform(df['action_keys'])
condition_df = pd.DataFrame(condition_matrix, columns=mlb_conditions.classes_)
action_df = pd.DataFrame(action_matrix, columns=mlb_actions.classes_)
linkage_matrix = pd.DataFrame(np.dot(condition_df.T, action_df), index=condition_df.columns, columns=action_df.columns)

plt.figure(figsize=(10, 6))
sns.heatmap(linkage_matrix, annot=True, fmt='d', cmap='YlGnBu')
plt.title('Action-Condition Field Linkage Matrix')
plt.tight_layout()
plt.show()

# Outliers
plt.figure(figsize=(8, 5))
sns.boxplot(data=conditions_df, x='ConditionField', y='ConditionValue')
plt.title('Outliers in Condition Values')
plt.tight_layout()
plt.show()

# Clustering
rule_vectors = np.hstack([condition_matrix, action_matrix])
inertia = []
sil_scores = []
K_range = range(2, 7)
for k in K_range:
    km = KMeans(n_clusters=k, random_state=42)
    labels = km.fit_predict(rule_vectors)
    inertia.append(km.inertia_)
    sil_scores.append(silhouette_score(rule_vectors, labels))

plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
plt.plot(K_range, inertia, marker='o')
plt.title('KMeans Inertia vs K')
plt.xlabel('K')
plt.ylabel('Inertia')

plt.subplot(1, 2, 2)
plt.plot(K_range, sil_scores, marker='o')
plt.title('Silhouette Score vs K')
plt.xlabel('K')
plt.ylabel('Silhouette Score')
plt.tight_layout()
plt.show()

# Add Rule Complexity Analysis
def calculate_rule_complexity(row):
    action_weight = 1.5
    condition_weight = 1.0
    
    complexity = (row['num_actions'] * action_weight + 
                 row['num_conditions'] * condition_weight)
    
    unique_actions = len(set(a['ActionType'] for a in row['actions']))
    unique_conditions = len(set(c['ConditionField'] for c in row['conditions']))
    
    return complexity * (1 + (unique_actions + unique_conditions) / 10)

df['rule_complexity'] = df.apply(calculate_rule_complexity, axis=1)

# Visualize complexity distribution
plt.figure(figsize=(10, 6))
sns.histplot(data=df, x='rule_complexity', bins=30)
plt.title('Distribution of Rule Complexity')
plt.show()

# Network Analysis
def create_rule_network(actions_df, conditions_df):
    G = nx.Graph()
    for _, condition in conditions_df.iterrows():
        for _, action in actions_df.iterrows():
            G.add_edge(f"C:{condition['ConditionField']}", 
                      f"A:{action['ActionType']}", 
                      weight=1)
    return G

plt.figure(figsize=(12, 8))
G = create_rule_network(actions_df, conditions_df)
pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_color='lightblue', 
        node_size=1500, font_size=8)
plt.title('Rule Components Network')
plt.show()

# Pattern Mining
def mine_rule_patterns(df):
    pattern_df = pd.DataFrame()
    
    for action in df['actions']:
        for a in action:
            col_name = f"action_{a['ActionType']}"
            pattern_df[col_name] = 1
            
    for condition in df['conditions']:
        for c in condition:
            col_name = f"condition_{c['ConditionField']}"
            pattern_df[col_name] = 1
    
    frequent_patterns = apriori(pattern_df, min_support=0.1, use_colnames=True)
    rules = association_rules(frequent_patterns, metric="confidence", min_threshold=0.5)
    return rules

pattern_rules = mine_rule_patterns(df)
print("\nTop 5 Rule Patterns:")
print(pattern_rules.head())

# Statistical Analysis
chi2, p_value = stats.chi2_contingency(
    pd.crosstab(conditions_df['ConditionField'], actions_df['ActionType'])
)
print(f"\nChi-square test p-value: {p_value:.4f}")

# Rule Validation
def validate_rule_structure(xml_string):
    try:
        etree.fromstring(xml_string)
        return True
    except etree.XMLSyntaxError:
        return False

df['is_valid'] = df['xml_column'].apply(validate_rule_structure)
print(f"\nValid Rules: {df['is_valid'].mean()*100:.2f}%")

#pip install mlxtend networkx lxml
