import networkx as nx
import pandas as pd
import sqlite3 as sql
import matplotlib.pyplot as plt
import pyvis
from pyvis.network import Network

conn = sql.connect('friends3.sqlite')
cur = conn.cursor

df = pd.read_sql('''
SELECT
	B.name as from_name,
	A.name as to_name,
	Ranks.rank
FROM
	Follows
JOIN
	People A
ON
	to_id = A.id
JOIN
	People B
ON
	from_id = B.id
JOIN
	Ranks
ON
	to_id = Ranks.id
WHERE rank > 150
LIMIT 1000''', conn)

G = nx.from_pandas_edgelist(df, source = 'from_name', target = 'to_name')
#G = nx.from_pandas_edgelist(df, source = 'from_name', target = 'to_name', edge_attr = 'rank')

net = Network(height = "800px", width = "1000px", notebook = True)
nt = Network('1500px', '1000px')
net.from_nx(G)
net.show_buttons(filter_=['physics'])
# net.toggle_physics(False)
net.show("example.html")

# nx.draw_networkx(G, with_labels = True, node_color = 'green')
