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

# Step 3: Modified Flatten data logic
def flatten_dict_list(dict_list):
    flattened = []
    for d in dict_list:
        if d:  # Only process non-empty dictionaries
            for key, value in d.items():
                flattened.append({'action_type': key, 'action_value': value})
    return flattened

def flatten_condition_dict_list(dict_list):
    flattened = []
    for d in dict_list:
        if d:  # Only process non-empty dictionaries
            for key, value in d.items():
                flattened.append({'condition_field': key, 'condition_value': value})
    return flattened

# Create flattened DataFrames
actions_df = pd.DataFrame([item for sublist in df['actions'].apply(flatten_dict_list) for item in sublist])
conditions_df = pd.DataFrame([item for sublist in df['conditions'].apply(flatten_condition_dict_list) for item in sublist])

# Update column references throughout the code
df['num_actions'] = df['actions'].apply(lambda x: len([d for d in x if d]))
df['num_conditions'] = df['conditions'].apply(lambda x: len([d for d in x if d]))

# Update visualization code
fig, axes = plt.subplots(3, 2, figsize=(16, 15))
sns.countplot(data=actions_df, x='action_type', ax=axes[0, 0], 
              order=actions_df['action_type'].value_counts().index)
axes[0, 0].set_title('Distribution of Rule Actions')
axes[0, 0].tick_params(axis='x', rotation=45)

sns.countplot(data=conditions_df, x='condition_field', ax=axes[0, 1], 
              order=conditions_df['condition_field'].value_counts().index)
axes[0, 1].set_title('Distribution of Rule Condition Fields')
axes[0, 1].tick_params(axis='x', rotation=45)

sns.histplot(df['num_actions'], bins=range(1, 6), kde=False, ax=axes[1, 0])
axes[1, 0].set_title('Number of Actions per Rule')

sns.histplot(df['num_conditions'], bins=range(1, 6), kde=False, ax=axes[1, 1])
axes[1, 1].set_title('Number of Conditions per Rule')

conditions_df['condition_value'] = pd.to_numeric(conditions_df['condition_value'], errors='coerce')
sns.boxplot(data=conditions_df, x='condition_field', y='condition_value', ax=axes[2, 0])
axes[2, 0].set_title('Condition Values by Field')

# Update pivot table creation
pivot = pd.merge(conditions_df, actions_df, left_index=True, right_index=True, how='inner')
heatmap_data = pivot.pivot_table(
    index='condition_field', 
    columns='action_type', 
    values='condition_value', 
    aggfunc='mean'
)
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

# Add after existing visualizations but before pattern mining

# Calculate and print key insights
print("\nKey Rule System Insights:")

# 1. Rule Complexity Distribution
print("\n1. Rule Complexity:")
print(f"Average rule complexity: {df['rule_complexity'].mean():.2f}")
print(f"Most common complexity range: {df['rule_complexity'].mode()[0]:.2f}")
print(f"Complexity variation (std): {df['rule_complexity'].std():.2f}")

# 2. Action Type Analysis
print("\n2. Action Distribution:")
action_dist = actions_df['action_type'].value_counts(normalize=True) * 100
for action, pct in action_dist.items():
    print(f"{action}: {pct:.1f}%")
print(f"Most common action: {action_dist.index[0]}")

# 3. Condition Analysis
print("\n3. Condition Field Usage:")
cond_dist = conditions_df['condition_field'].value_counts(normalize=True) * 100
for field, pct in cond_dist.items():
    print(f"{field}: {pct:.1f}%")

# 4. Rule Structure
print("\n4. Rule Structure:")
print(f"Average actions per rule: {df['num_actions'].mean():.2f}")
print(f"Average conditions per rule: {df['num_conditions'].mean():.2f}")
print(f"Most complex rule has {df['num_actions'].max()} actions and {df['num_conditions'].max()} conditions")

# 5. Redundancy Analysis
print("\n5. Redundancy Analysis:")
print(f"Exact duplicate rules: {(1 - len(df['rule_signature'].unique()) / len(df)) * 100:.1f}%")
print(f"Action pattern redundancy: {(1 - len(df['action_keys'].unique()) / len(df)) * 100:.1f}%")
print(f"Condition pattern redundancy: {(1 - len(df['condition_keys'].unique()) / len(df)) * 100:.1f}%")

# 6. Temporal Analysis
print("\n6. Temporal Analysis:")
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['month'] = df['timestamp'].dt.month
monthly_rules = df['month'].value_counts().sort_index()
peak_month = monthly_rules.idxmax()
print(f"Peak rule creation month: {peak_month}")
print(f"Rules per month variation (std): {monthly_rules.std():.2f}")

# 7. Field Value Distribution
print("\n7. Condition Value Distribution:")
for field in conditions_df['condition_field'].unique():
    field_values = conditions_df[conditions_df['condition_field'] == field]['condition_value']
    print(f"\n{field}:")
    print(f"  Mean: {field_values.mean():.2f}")
    print(f"  Median: {field_values.median():.2f}")
    print(f"  Std: {field_values.std():.2f}")

# 8. Action-Condition Relationships
print("\n8. Action-Condition Relationships:")
pivot_counts = pd.crosstab(conditions_df['condition_field'], actions_df['action_type'])
strongest_pairs = []
for condition in pivot_counts.index:
    max_action = pivot_counts.loc[condition].idxmax()
    max_count = pivot_counts.loc[condition, max_action]
    strongest_pairs.append((condition, max_action, max_count))

for condition, action, count in sorted(strongest_pairs, key=lambda x: x[2], reverse=True):
    print(f"{condition} → {action}: {count} occurrences")

# Duplicates
df['action_keys'] = df['actions'].apply(
    lambda x: tuple(sorted(f"{k}:{v}" for d in x for k, v in d.items() if d))
)
df['condition_keys'] = df['conditions'].apply(
    lambda x: tuple(sorted(f"{k}:{v}" for d in x for k, v in d.items() if d))
)
df['rule_signature'] = df.apply(lambda row: (row['action_keys'], row['condition_keys']), axis=1)
duplicate_rules = df['rule_signature'].value_counts()

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
        actions = tuple(sorted(k for d in row['actions'] for k in d.keys() if d))
        conditions = tuple(sorted(k for d in row['conditions'] for k in d.keys() if d))
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
field_importance = conditions_df['condition_field'].value_counts()

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
sns.boxplot(data=conditions_df, x='condition_field', y='condition_value')
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
    
    unique_actions = len(set(a['action_type'] for a in row['actions']))
    unique_conditions = len(set(c['condition_field'] for c in row['conditions']))
    
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
            G.add_edge(f"C:{condition['condition_field']}", 
                      f"A:{action['action_type']}", 
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
    
    for idx, row in df.iterrows():
        for action_dict in row['actions']:
            if action_dict:
                for action_type in action_dict.keys():
                    col_name = f"action_{action_type}"
                    pattern_df.at[idx, col_name] = 1
                    
        for condition_dict in row['conditions']:
            if condition_dict:
                for condition_field in condition_dict.keys():
                    col_name = f"condition_{condition_field}"
                    pattern_df.at[idx, col_name] = 1
    
    pattern_df = pattern_df.fillna(0)
    frequent_patterns = apriori(pattern_df, min_support=0.1, use_colnames=True)
    rules = association_rules(frequent_patterns, metric="confidence", min_threshold=0.5)
    return rules

pattern_rules = mine_rule_patterns(df)
print("\nTop 5 Rule Patterns:")
print(pattern_rules.head())

# Statistical Analysis
chi2, p_value = stats.chi2_contingency(
    pd.crosstab(conditions_df['condition_field'], actions_df['action_type'])
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


def parse_xml_rule(xml_file):
    # Parse the XML file
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # Extract rule information
    rule_name = root.get('name')
    rule_id = root.get('internalID')
    
    print(f"Processing rule: {rule_name} (ID: {rule_id})")
    
    # Parse rule conditions
    conditions = []
    rule_condition = root.find('.//ruleCondition')
    if rule_condition:
        sql_condition = parse_condition_node(rule_condition)
        conditions.append(sql_condition)
    
    # Return the SQL-like condition
    return " ".join(conditions)

def parse_condition_node(condition_node, indent=""):
    result = []
    
    # Get condition attributes
    condition_id = condition_node.get('identifier')
    
    # Check for operator
    operator_node = condition_node.find('./operator')
    operator_type = operator_node.get('id') if operator_node is not None else None
    
    # Process children conditions
    children_node = condition_node.find('./children')
    if children_node is not None:
        child_conditions = []
        for child in children_node.findall('./condition'):
            child_result = parse_condition_node(child, indent + "  ")
            if child_result:
                child_conditions.append(child_result)
        
        # Process expression terms
        for expr in children_node.findall('./expressionTerm'):
            expr_id = expr.get('identifier')
            expression = expr.get('expression')
            if expression and expr_id:
                child_conditions.append(f"{expression}")
        
        # Process value terms
        for val in children_node.findall('./valueTerm'):
            val_id = val.get('identifier')
            value = val.get('value')
            if value and val_id:
                # If previous was an expression, this is likely a comparison
                if len(child_conditions) > 0 and "expression" in locals():
                    child_conditions[-1] = f"{child_conditions[-1]} = '{value}'"
                else:
                    child_conditions.append(f"'{value}'")
        
        # Process field terms
        for field in children_node.findall('./fieldTerm'):
            field_id = field.get('id')
            if field_id:
                child_conditions.append(f"{field_id}")
        
        # Join child conditions based on operator
        operator = operator_type if operator_type else " "
        result.append(f"({operator.join(child_conditions)})")
    
    return " ".join(result)

