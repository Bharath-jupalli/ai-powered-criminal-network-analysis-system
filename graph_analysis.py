import networkx as nx
def build_graph():
 g=nx.Graph()
 groups={'person':[('P-001','Person A'),('P-002','Person B'),('P-003','Person C'),('P-004','Person D'),('P-005','Person E'),('P-006','Person F')],'location':[('LOC-001','Location X'),('LOC-002','Location Y'),('LOC-003','Location Z'),('LOC-004','Location Q')],'vehicle':[('V-001','V1'),('V-002','V2'),('V-003','V3')],'phone':[('PH-001','9000000001'),('PH-002','9000000002'),('PH-003','9000000003')],'account':[('ACC-001','ACC-001'),('ACC-002','ACC-002'),('ACC-003','ACC-003')]}
 for typ,items in groups.items():
  for i,n in items:g.add_node(i,node_type=typ,name=n)
 edges=[('P-001','P-002','COMMUNICATION'),('P-001','P-003','TRANSACTION'),('P-001','LOC-001','ASSOCIATED_WITH'),('P-001','V-001','USES'),('P-001','PH-001','CONTACT'),('P-001','ACC-001','TRANSACTION'),('P-002','P-003','COMMUNICATION'),('P-002','LOC-001','ASSOCIATED_WITH'),('P-002','V-002','USES'),('P-002','PH-002','CONTACT'),('P-003','LOC-002','ASSOCIATED_WITH'),('P-003','V-001','USES'),('P-003','PH-001','CONTACT'),('P-003','ACC-002','TRANSACTION'),('P-004','P-005','COMMUNICATION'),('P-004','LOC-003','ASSOCIATED_WITH'),('P-004','V-003','USES'),('P-004','PH-003','CONTACT'),('P-005','LOC-003','ASSOCIATED_WITH'),('P-005','ACC-003','TRANSACTION'),('P-006','P-004','COMMUNICATION'),('P-006','LOC-004','ASSOCIATED_WITH'),('P-006','V-003','USES')]
 for a,b,r in edges:g.add_edge(a,b,relationship=r)
 return g
def calculate_metrics(graph):
 d=nx.degree_centrality(graph); b=nx.betweenness_centrality(graph); out=[]
 for n,x in graph.nodes(data=True):out.append({'id':n,'name':x.get('name',n),'type':x.get('node_type','unknown'),'score':round(d.get(n,0)*.6+b.get(n,0)*.4,3),'connections':graph.degree(n)})
 return sorted(out,key=lambda x:x['score'],reverse=True)
def detect_communities(graph):
 try: cs=nx.community.greedy_modularity_communities(graph)
 except Exception: cs=[set(graph.nodes())]
 return {n:i for i,s in enumerate(cs) for n in s}
def detect_suspicious_patterns(graph):
 alerts=[]
 for x in calculate_metrics(graph)[:5]:
  if x['connections']>=3:alerts.append({'type':'HIGH_CONNECTIVITY','title':'High connectivity lead','description':f"{x['name']} has {x['connections']} observed synthetic connections and may warrant contextual review.",'entity_id':x['id']})
 t=sum(nx.triangles(graph).values())//3
 if t:alerts.append({'type':'CONNECTED_CLUSTER','title':'Connected cluster lead','description':f'{t} closed relationship cluster(s) were detected in the synthetic graph for review.'})
 return alerts
