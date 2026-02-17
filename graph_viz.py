# graph_viz.py
import networkx as nx
import matplotlib.pyplot as plt
import streamlit as st

def visualize_medical_graph():
    # 1. Create a simple Graph
    G = nx.DiGraph()
    
    # 2. Add "Knowledge" (Nodes & Edges)
    relationships = [
        ("Symptom: Chest Pain", "Condition: Heart Issue"),
        ("Condition: Heart Issue", "Specialist: Cardiologist"),
        ("Specialist: Cardiologist", "Dr. Mehta (Ahmedabad)"),
        ("Specialist: Cardiologist", "Dr. Desai (Surat)"),
        
        ("Symptom: Acne", "Condition: Skin Infection"),
        ("Condition: Skin Infection", "Specialist: Dermatologist"),
        ("Specialist: Dermatologist", "Dr. Shah (Ahmedabad)"),
        
        ("Symptom: Knee Pain", "Condition: Joint Issue"),
        ("Condition: Joint Issue", "Specialist: Orthopedic"),
        ("Specialist: Orthopedic", "Dr. Patel (Rajkot)")
    ]
    
    G.add_edges_from(relationships)
    
    # 3. Draw the Graph
    fig, ax = plt.subplots(figsize=(10, 6))
    pos = nx.spring_layout(G, seed=42)  # Consistent layout
    
    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_size=2000, node_color='lightblue', ax=ax)
    nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, arrowsize=20, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=10, font_family="sans-serif", ax=ax)
    
    # Remove axis for clean look
    ax.axis("off")
    
    return fig