import pandas as pd
import xml.etree.ElementTree as ET
from collections import Counter

# Assuming df contains your Excel data with XML in a column named 'xml_column'
def parse_rule(xml_str):
    try:
        root = ET.fromstring(xml_str)
        rule_data = {
            'rule_id': root.attrib.get('internalID'),
            'rule_name': root.attrib.get('name'),
            'rule_identifier': root.attrib.get('identifier'),
            'num_actions': len(root.findall('./ruleActions/action')),
            'num_conditions': len(root.findall('.//condition')),
            'actions': [a.attrib.get('identifier') for a in root.findall('./ruleActions/action')],
            'action_values': [a.attrib.get('value') for a in root.findall('./ruleActions/action')],
            'operators': [op.attrib.get('id') for op in root.findall('.//operator')],
            'expressions': [exp.attrib.get('expression') for exp in root.findall('.//expressionTerm')]
        }
        return rule_data
    except Exception as e:
        return None

# Apply parsing to all rows
df['parsed'] = df['xml_column'].apply(parse_rule)


# 1)Rule Complexity Distribution:
# Create histogram of number of actions and conditions
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
df['parsed'].apply(lambda x: x['num_actions']).hist()
plt.title('Distribution of Actions per Rule')

plt.subplot(1, 2, 2)
df['parsed'].apply(lambda x: x['num_conditions']).hist()
plt.title('Distribution of Conditions per Rule')
plt.tight_layout()


# 2)Action Types analysis
# Flatten all actions and count frequencies
all_actions = []
for p in df['parsed']:
    if p:
        all_actions.extend(p['actions'])

action_counts = Counter(all_actions)
pd.Series(action_counts).sort_values(ascending=False).plot(kind='bar', figsize=(12, 6))
plt.title('Most Common Action Types')

#3)Operator Usage:

# Count operator frequencies
all_operators = []
for p in df['parsed']:
    if p:
        all_operators.extend(p['operators'])

operator_counts = Counter(all_operators)
pd.Series(operator_counts).plot(kind='pie', figsize=(10, 10), autopct='%1.1f%%')
plt.title('Operator Distribution')


# 4)Expression Pattern Analysis:

# Extract common patterns from expressions
import re

def extract_pattern(expr):
    if not expr:
        return None
    # Extract function names or list references
    matches = re.findall(r'\[([^\]]+)\]|(\w+)\s*\(', expr)
    return [m[0] or m[1] for m in matches if any(m)]

all_patterns = []
for p in df['parsed']:
    if p:
        for expr in p['expressions']:
            patterns = extract_pattern(expr)
            if patterns:
                all_patterns.extend(patterns)

pattern_counts = Counter(all_patterns)
pd.Series(pattern_counts).head(15).plot(kind='bar', figsize=(12, 6))
plt.title('Common Expression Patterns')


# 5)Rule Clustering:

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.cluster import KMeans

# Create feature vectors based on actions and operators
def create_feature_text(rule_data):
    if not rule_data:
        return ""
    features = []
    features.extend([f"action_{a}" for a in rule_data['actions']])
    features.extend([f"op_{o}" for o in rule_data['operators']])
    return " ".join(features)

df['feature_text'] = df['parsed'].apply(create_feature_text)

# Vectorize and cluster
vectorizer = CountVectorizer()
X = vectorizer.fit_transform(df['feature_text'])

kmeans = KMeans(n_clusters=5)  # Adjust number of clusters as needed
df['cluster'] = kmeans.fit_predict(X)

# Analyze clusters
cluster_stats = df.groupby('cluster').agg({
    'parsed': lambda x: len(x),
    'rule_identifier': lambda x: list(set([p['rule_identifier'] for p in x if p]))[:5]
}).rename(columns={'parsed': 'count'})

print(cluster_stats)


# 6)Similarity Matrix:

from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Create similarity matrix (for a subset if 1000+ is too large)
sample_size = min(100, len(df))  # Adjust sample size as needed
sample_df = df.sample(sample_size)

X_sample = vectorizer.transform(sample_df['feature_text'])
similarity = cosine_similarity(X_sample)

plt.figure(figsize=(10, 8))
plt.imshow(similarity, cmap='viridis')
plt.colorbar()
plt.title('Rule Similarity Matrix')



# Network Analysis for Rule Redundancy Detection
# Based on your XML rule example (showing a rule named "Non IOS Watch List is TRUE"), I can provide guidance on implementing network analysis to detect redundancies in your collection of XML rules.

# Network Analysis Approach
# Network analysis is particularly effective for visualizing and detecting redundancies in rule-based systems. For your XML rules, this approach creates a graph representation where rules are connected based on their similarities in structure, conditions, and actions.

# Creating the Rule Network
# Node Definition:

# Each rule becomes a node in the network
# Node attributes can include rule name, identifier, and other metadata

# Edge Definition:
# Create edges between rules based on similarity metrics
# Edge weight can represent the degree of similarity
# Consider connections based on:
# Shared actions (e.g., "Alert" actions)
# Similar conditions (e.g., IS_TRUE operators)
# Common expressions (e.g., references to the same match lists)

# Implementation with NetworkX:


import networkx as nx
import matplotlib.pyplot as plt

# Create graph
G = nx.Graph()

# Add nodes (rules)
for rule_data in parsed_rules:
    G.add_node(rule_data['rule_id'], 
               name=rule_data['rule_name'], 
               identifier=rule_data['rule_identifier'])

# Add edges based on similarity
for i, rule1 in enumerate(parsed_rules):
    for j, rule2 in enumerate(parsed_rules[i+1:], i+1):
        similarity = calculate_similarity(rule1, rule2)
        if similarity > threshold:
            G.add_edge(rule1['rule_id'], rule2['rule_id'], 
                       weight=similarity)

# Visualize
pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True)
plt.show()


# Rule Redundancy Detection
# Once you've created the network representation, you can apply various techniques to identify redundant rules:

# 1. Cluster Analysis
# Identify clusters of highly similar rules using community detection algorithms:


from networkx.algorithms import community

# Find communities of similar rules
communities = community.greedy_modularity_communities(G)

# Print clusters of potentially redundant rules
for i, community in enumerate(communities):
    print(f"Cluster {i+1}:")
    for rule_id in community:
        rule_name = G.nodes[rule_id]['name']
        print(f"  - {rule_name}")


# 2. Similarity Coefficient Calculation
# Calculate similarity coefficients between rules to identify potential redundancies:

def calculate_similarity(rule1, rule2):
    """Calculate similarity between two rules based on shared elements"""
    # Similarity based on actions
    actions1 = set(rule1['actions'])
    actions2 = set(rule2['actions'])
    action_similarity = len(actions1.intersection(actions2)) / len(actions1.union(actions2))
    
    # Similarity based on conditions/operators
    operators1 = set(rule1['operators'])
    operators2 = set(rule2['operators'])
    operator_similarity = len(operators1.intersection(operators2)) / len(operators1.union(operators2))
    
    # Similarity based on expressions
    expr1 = set(rule1['expressions'])
    expr2 = set(rule2['expressions'])
    expr_similarity = len(expr1.intersection(expr2)) / len(expr1.union(expr2))
    
    # Weighted average
    return 0.4 * action_similarity + 0.3 * operator_similarity + 0.3 * expr_similarity


# 3. Identifying Redundant Rule Patterns
# Look for specific patterns that indicate redundancy:
# Subset Rules: Rules where one rule's conditions and actions are a subset of another
# Conflicting Rules: Rules with similar conditions but different actions
# Near-Duplicate Rules: Rules with high similarity coefficients (e.g., > 0.8)


def find_redundant_patterns(parsed_rules):
    redundancies = []
    
    for i, rule1 in enumerate(parsed_rules):
        for j, rule2 in enumerate(parsed_rules[i+1:], i+1):
            # Check for subset relationship
            if is_subset(rule1, rule2):
                redundancies.append((rule1['rule_id'], rule2['rule_id'], 'subset'))
            
            # Check for near-duplicates
            similarity = calculate_similarity(rule1, rule2)
            if similarity > 0.8:
                redundancies.append((rule1['rule_id'], rule2['rule_id'], 'near-duplicate'))
    
    return redundancies



# 4. Bayesian Network Approach
# For more sophisticated analysis, implement a Bayesian Network approach as mentioned in the research:


from pgmpy.models import BayesianNetwork
from pgmpy.factors.discrete import TabularCPD

# Create a simple Bayesian Network for rule similarity
model = BayesianNetwork([
    ('same_action', 'is_redundant'),
    ('same_condition', 'is_redundant'),
    ('same_expression', 'is_redundant')
])

# Define conditional probability distributions
# (This is a simplified example)
cpd_action = TabularCPD('same_action', 2, [[0.5], [0.5]])
cpd_condition = TabularCPD('same_condition', 2, [[0.5], [0.5]])
cpd_expression = TabularCPD('same_expression', 2, [[0.5], [0.5]])
cpd_redundant = TabularCPD('is_redundant', 2, 
                           [[0.1, 0.3, 0.3, 0.5, 0.3, 0.5, 0.5, 0.9],
                            [0.9, 0.7, 0.7, 0.5, 0.7, 0.5, 0.5, 0.1]],
                           evidence=['same_action', 'same_condition', 'same_expression'],
                           evidence_card=[2, 2, 2])

model.add_cpds(cpd_action, cpd_condition, cpd_expression, cpd_redundant)


# Visualization and Reporting
# After identifying potential redundancies, create visualizations and reports:


#Heatmap of Rule Similarities:


import seaborn as sns

# Create similarity matrix
similarity_matrix = np.zeros((len(parsed_rules), len(parsed_rules)))
for i, rule1 in enumerate(parsed_rules):
    for j, rule2 in enumerate(parsed_rules):
        similarity_matrix[i][j] = calculate_similarity(rule1, rule2)

# Plot heatmap
sns.heatmap(similarity_matrix, xticklabels=[r['rule_name'] for r in parsed_rules],
            yticklabels=[r['rule_name'] for r in parsed_rules])
plt.title('Rule Similarity Matrix')
plt.show()


# Network Visualization of Similar Rules:


# Color nodes by cluster
colors = []
for node in G:
    for i, comm in enumerate(communities):
        if node in comm:
            colors.append(i)
            break

# Draw network with community colors
nx.draw(G, pos, node_color=colors, with_labels=True)
plt.title('Rule Similarity Network')
plt.show()

# Redundancy Report:

def generate_redundancy_report(redundancies, parsed_rules):
    report = []
    for rule1_id, rule2_id, redundancy_type in redundancies:
        rule1 = next(r for r in parsed_rules if r['rule_id'] == rule1_id)
        rule2 = next(r for r in parsed_rules if r['rule_id'] == rule2_id)
        report.append({
            'rule1_name': rule1['rule_name'],
            'rule2_name': rule2['rule_name'],
            'redundancy_type': redundancy_type,
            'similarity': calculate_similarity(rule1, rule2),
            'recommendation': get_recommendation(redundancy_type)
        })
    return pd.DataFrame(report)
# By implementing these network analysis techniques, you can effectively identify redundant rules in your XML dataset, leading to a more optimized and maintainable rule base.
