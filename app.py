"""BuildOptima 360 V3 — civil engineering decision-support demonstrator."""
import io,json,uuid,os
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from core import metres,probabilites,planning,optimisation,storage,reports,demo

st.set_page_config(page_title='BuildOptima 360 | V3',page_icon='🏗️',layout='wide',initial_sidebar_state='expanded')
st.markdown('''<style>
[data-testid="stApp"]{background:#F2F5F9;color:#173049}
[data-testid="stSidebar"]{background:linear-gradient(170deg,#10283D,#173F5C)}
[data-testid="stSidebar"] *{color:#F4F8FA}
.block-container{padding-top:1.5rem;max-width:1500px}
.hero{background:linear-gradient(110deg,#102B43,#166384);padding:32px 35px;border-radius:22px;color:white;box-shadow:0 14px 34px #10314b25;margin-bottom:22px}
.hero h1{color:white;margin:0;font-size:2.25rem;letter-spacing:-.03em}.hero p{color:#cfe6f2;font-size:1rem}
.tile{background:white;padding:20px;border-radius:17px;border-top:4px solid #E79B40;box-shadow:0 6px 20px #18314910;margin:6px 0}
.tile .label{color:#738498;font-size:.88rem}.tile .value{font-size:1.55rem;font-weight:800;color:#15344E}
[data-testid="stDataFrame"],[data-testid="stForm"]{border-radius:12px}
@media(max-width:750px){.hero{padding:18px}.hero h1{font-size:1.55rem}.tile .value{font-size:1.25rem}}
</style>''',unsafe_allow_html=True)
def cash(x):return f'{x:,.0f}'.replace(',',' ')+' FCFA'
def tile(label,value):st.markdown(f'<div class="tile"><div class="label">{label}</div><div class="value">{value}</div></div>',unsafe_allow_html=True)
def dataframe(p):return pd.DataFrame(p.get('lignes',[]),columns=metres.COLUMNS)
def saved(p):storage.save(conn,p);st.success('Enregistré dans SQLite sur ce serveur.')
def database():return storage.connect(os.environ.get('BUILDOPTIMA_DB','data/buildoptima.db'))
conn=database()
if 'active' not in st.session_state:st.session_state.active=None
if 'risk' not in st.session_state:st.session_state.risk=None
projects=storage.list_projects(conn)
with st.sidebar:
 st.markdown('## 🏗️ BuildOptima **360**')
 st.caption('CONSTRUCTION INTELLIGENCE / V3')
 pages=['Vue générale','Projets','Métrés & devis','Calculateur BTP','Statistiques & données','Simulation Monte-Carlo','Planning CPM','Optimisation','Rapports & sauvegardes','Guide méthodologique']
 page=st.radio('Espace de travail',pages)
 if st.button('🧪 Créer le projet de démonstration',use_container_width=True):
  p=demo.project();storage.save(conn,p);st.session_state.active=p['id'];st.rerun()
 if projects:
  labels={f"{p['nom']} · {p['id'][:5]}":p['id'] for p in projects}
  keys=list(labels);ids=list(labels.values());idx=ids.index(st.session_state.active) if st.session_state.active in ids else 0
  selection=st.selectbox('Projet actif',keys,index=idx)
  st.session_state.active=labels[selection]
 st.caption('⚠️ Sur hébergement cloud gratuit, SQLite peut être réinitialisé : exportez les projets.')
p=next((x for x in projects if x['id']==st.session_state.active),None)
if p and p.get('fictif'):st.warning('🧪 PROJET DE DÉMONSTRATION : toutes les quantités, les prix et les variantes sont FICTIFS.')
if page=='Vue générale':
 st.markdown('<div class="hero"><h1>BuildOptima 360 <span style="color:#F0AD58">V3</span></h1><p>Un centre de décision pour vos projets BTP : métrés, incertitudes, chemin critique et compromis économiques.</p></div>',unsafe_allow_html=True)
 if not p:st.info('Créez un projet dans « Projets » ou chargez la démonstration depuis le menu latéral.')
 else:
  try:
   d=metres.clean(dataframe(p));value=float(d['montant'].sum());tasks,horizon=planning.cpm(p.get('taches',[]))
   a,b,c,dcol=st.columns(4)
   with a:tile('Coût prévisionnel',cash(value))
   with b:tile('Budget',cash(p['budget']))
   with c:tile('Solde',cash(p['budget']-value))
   with dcol:tile('Durée CPM',f'{horizon} jours')
   left,right=st.columns([1.35,1])
   with left:st.plotly_chart(px.bar(d,x='poste',y='montant',color='categorie',title='Répartition du coût par poste',labels={'montant':'FCFA'}),use_container_width=True)
   with right:st.plotly_chart(px.pie(d,names='categorie',values='montant',hole=.58,title='Composition par famille'),use_container_width=True)
   st.info('Le budget et les prix sont fournis par l’utilisateur. La plateforme ne certifie ni les quantités ni la conformité technique.')
  except ValueError as e:st.warning(str(e))
elif page=='Projets':
 st.title('📁 Gestion des projets')
 with st.form('create'):
  name=st.text_input('Nom du nouveau projet');budget=st.number_input('Budget FCFA',min_value=0.,value=10000000.,step=100000.)
  if st.form_submit_button('Créer',type='primary'):
   if not name.strip():st.error('Nom obligatoire.')
   else:
    obj={'id':str(uuid.uuid4()),'nom':name.strip(),'budget':budget,'fictif':False,'lignes':[],'taches':[],'variantes':[]}
    saved(obj);st.session_state.active=obj['id'];st.rerun()
 if p:
  with st.form('edit_project'):
   newname=st.text_input('Nom du projet actif',value=p['nom']);newbudget=st.number_input('Budget du projet actif',value=float(p['budget']),min_value=0.)
   if st.form_submit_button('Mettre à jour'):
    if newname.strip():p.update(nom=newname.strip(),budget=newbudget);saved(p);st.rerun()
    else:st.error('Nom obligatoire.')
  if st.button('Supprimer définitivement ce projet'):
   storage.delete(conn,p['id']);st.session_state.active=None;st.rerun()
elif page=='Métrés & devis':
 st.title('📐 Bordereau des quantités et prix')
 if p:
  edited=st.data_editor(dataframe(p),num_rows='dynamic',use_container_width=True,key=f'metres_{p["id"]}',column_config={'quantite':st.column_config.NumberColumn('Quantité',min_value=0.),'prix':st.column_config.NumberColumn('Prix unitaire FCFA',min_value=0.),'incert_q_pct':st.column_config.NumberColumn('± Qté %',min_value=0.,max_value=100.),'incert_p_pct':st.column_config.NumberColumn('± Prix %',min_value=0.,max_value=100.)})
  if st.button('Enregistrer le bordereau',type='primary'):
   try:
    d=metres.clean(edited);p['lignes']=d[metres.COLUMNS].to_dict('records');saved(p);st.session_state.risk=None;st.rerun()
   except ValueError as e:st.error(str(e))
  try:
   d=metres.clean(dataframe(p));st.metric('Montant total',cash(d['montant'].sum()))
   st.dataframe(d,use_container_width=True,hide_index=True)
  except ValueError as e:st.info(str(e))
 else:st.info('Créez un projet.')
elif page=='Calculateur BTP':
 st.title('🧮 Calculateurs de quantités')
 st.caption('Calculateurs géométriques d’aide au métré ; ils ne remplacent pas le dimensionnement technique.')
 t1,t2,t3=st.tabs(['Béton rectangulaire','Masse d’acier','Maçonnerie'])
 with t1:
  a,b,c=st.columns(3)
  with a:L=st.number_input('Longueur (m)',min_value=.01,value=5.,key='bet_l')
  with b:l=st.number_input('Largeur (m)',min_value=.01,value=.4,key='bet_w')
  with c:h=st.number_input('Hauteur (m)',min_value=.01,value=.5,key='bet_h')
  st.metric('Volume',f'{metres.volume_rectangular(L,l,h):.3f} m³')
 with t2:
  a,b,c=st.columns(3)
  with a:long=st.number_input('Longueur par barre (m)',min_value=.01,value=12.)
  with b:diam=st.number_input('Diamètre nominal (mm)',min_value=.01,value=12.)
  with c:nb=st.number_input('Nombre de barres',min_value=1,value=20)
  st.metric('Masse théorique',f'{metres.steel_mass(long,diam,nb):.2f} kg');st.caption('Densité acier supposée : 7 850 kg/m³.')
 with t3:
  a,b,c=st.columns(3)
  with a:ll=st.number_input('Longueur mur (m)',min_value=0.,value=8.)
  with b:hh=st.number_input('Hauteur mur (m)',min_value=0.,value=3.)
  with c:ouv=st.number_input('Surface ouvertures (m²)',min_value=0.,value=2.)
  try:st.metric('Surface nette',f'{metres.masonry_area(ll,hh,ouv):.2f} m²')
  except ValueError as e:st.error(str(e))
elif page=='Statistiques & données':
 st.title('📊 Analyse descriptive des données')
 st.caption('Importez des données observées ; aucun historique de prix réel n’est inclus par défaut.')
 up=st.file_uploader('CSV ou Excel contenant des colonnes numériques',type=['csv','xlsx'])
 if up:
  try:
   df=pd.read_csv(up,sep=None,engine='python') if up.name.lower().endswith('.csv') else pd.read_excel(up)
   if len(df)>200000:raise ValueError('Fichier limité à 200 000 lignes.')
   st.subheader('1 · Données brutes — avant toute analyse')
   st.write(f'Source : fichier importé « {up.name} » · Observations : {len(df)} · Variables : {len(df.columns)}')
   st.dataframe(df.head(200),use_container_width=True)
   st.caption('Aperçu des 200 premières lignes. Unités, provenance et dates doivent être vérifiées dans le fichier source.')
   st.subheader('2 · Qualité et valeurs manquantes')
   st.dataframe(pd.DataFrame({'colonne':df.columns,'manquants':df.isna().sum().to_numpy(),'type':df.dtypes.astype(str).to_numpy()}),hide_index=True)
   numeric=df.select_dtypes(include='number')
   if numeric.empty:st.warning('Aucune colonne numérique.')
   else:
    st.subheader('3 · Statistiques descriptives');st.dataframe(numeric.describe().T,use_container_width=True)
    col=st.selectbox('Variable à explorer',list(numeric.columns))
    st.plotly_chart(px.histogram(df,x=col,nbins=35,title=f'Distribution : {col}'),use_container_width=True)
    if len(numeric.columns)>1:st.plotly_chart(px.imshow(numeric.corr(),text_auto='.2f',title='Corrélations linéaires (Pearson)'),use_container_width=True)
  except Exception as e:st.error(f'Impossible de traiter ce fichier : {e}')
 else:st.info('Importez vos observations pour afficher les données brutes, la qualité et les statistiques.')
elif page=='Simulation Monte-Carlo':
 st.title('🎲 Analyse du risque budgétaire')
 if p:
  try:
   d=metres.clean(dataframe(p))
   with st.form('risk_form'):
    n=st.slider('Nombre de tirages',100,50000,10000,step=100)
    corr=st.slider('Corrélation commune des variations de prix (copule gaussienne)',0.,1.,0.,step=.1)
    seed=st.number_input('Graine de reproductibilité',min_value=0,value=42)
    if st.form_submit_button('Simuler',type='primary'):
     sims=probabilites.simulate(d,n,int(seed),corr)
     st.session_state.risk={'id':p['id'],'budget':p['budget'],'signature':json.dumps(p['lignes'],sort_keys=True),'sims':sims,'stats':probabilites.summary(sims,p['budget'])}
   result=st.session_state.risk
   if result and result['id']==p['id'] and result['budget']==p['budget'] and result['signature']==json.dumps(p['lignes'],sort_keys=True):
    s=result['sims'];stats=result['stats'];a,b,c=st.columns(3)
    with a:tile('Coût moyen simulé',cash(stats['moyenne']))
    with b:tile('Risque de dépassement',f"{stats['depassement']*100:.2f} %")
    with c:tile('Quantile P90',cash(stats['p90']))
    st.plotly_chart(px.histogram(x=s,nbins=55,labels={'x':'Coût FCFA'},title='Distribution simulée des coûts'),use_container_width=True)
    st.plotly_chart(px.line(x=np.sort(s),y=np.arange(1,len(s)+1)/len(s),labels={'x':'Coût FCFA','y':'Fréquence cumulée'},title='Fonction de répartition empirique'),use_container_width=True)
    st.dataframe(pd.DataFrame([stats]).T.rename(columns={0:'Valeur'}))
    st.caption(f"Erreur Monte-Carlo (1 écart-type) sur la probabilité : ± {stats['erreur_mc']*100:.3f} point(s). Ce n'est pas une incertitude sur la validité des hypothèses.")
   else:st.info('Cliquez sur « Simuler ». Les résultats sont recalculés à chaque modification des métrés.')
  except Exception as e:st.error(str(e))
 else:st.info('Créez un projet avec des métrés.')
elif page=='Planning CPM':
 st.title('📅 Planification et chemin critique')
 st.caption('Prédécesseurs séparés par des virgules. Les durées sont en jours calendaires.')
 if p:
  tasks=pd.DataFrame(p.get('taches',[]),columns=['tache','duree','predecesseurs'])
  edited=st.data_editor(tasks,num_rows='dynamic',use_container_width=True,key=f'tasks_{p["id"]}')
  if st.button('Enregistrer les tâches'):
   try:
    planning.cpm(edited.to_dict('records'));p['taches']=edited.to_dict('records');saved(p);st.rerun()
   except Exception as e:st.error(str(e))
  try:
   rows,duration=planning.cpm(p.get('taches',[]));st.metric('Durée totale',f'{duration} jours')
   if rows:
    d=pd.DataFrame(rows);st.dataframe(d,use_container_width=True,hide_index=True)
    base=pd.Timestamp('2026-01-01');d['start']=base+pd.to_timedelta(d['debut'],unit='D');d['end']=base+pd.to_timedelta(d['fin'],unit='D')
    st.plotly_chart(px.timeline(d,x_start='start',x_end='end',y='tache',color='critique',title='Gantt relatif (date de référence fictive)'),use_container_width=True)
    st.caption('Les tâches de marge nulle constituent le chemin critique selon les dépendances saisies.')
  except Exception as e:st.error(str(e))
 else:st.info('Créez un projet.')
elif page=='Optimisation':
 st.title('⚖️ Compromis coût / délai')
 if p:
  try:
   d=metres.clean(dataframe(p));pct=st.slider('Choc individuel sur les prix (%)',1,50,20)
   sen=metres.sensitivity(d,pct/100)
   st.plotly_chart(px.bar(sen,x='poste',y='impact_fcfa',color='categorie',title='Sensibilité du coût total aux prix',labels={'impact_fcfa':'Impact ± FCFA'}),use_container_width=True)
  except Exception as e:st.warning(str(e))
  st.subheader('Variantes techniques')
  st.caption('Seules les variantes cochées « validée » sont considérées dans le front de Pareto. Cette case est une déclaration de l’utilisateur, non une vérification automatique.')
  variants=pd.DataFrame(p.get('variantes',[]),columns=['variante','cout','duree','validee'])
  edited=st.data_editor(variants,num_rows='dynamic',use_container_width=True,key=f'var_{p["id"]}')
  if st.button('Enregistrer les variantes'):
   try:
    if len(edited):optimisation.compare(edited)
    p['variantes']=edited.to_dict('records');saved(p);st.rerun()
   except Exception as e:st.error(str(e))
  if p.get('variantes'):
   try:
    v=optimisation.compare(pd.DataFrame(p['variantes']));st.dataframe(v,use_container_width=True,hide_index=True)
    st.plotly_chart(px.scatter(v,x='duree',y='cout',color='pareto',symbol='validee',text='variante',title='Front de Pareto parmi les variantes déclarées admissibles'),use_container_width=True)
   except Exception as e:st.error(str(e))
 else:st.info('Créez un projet.')
elif page=='Rapports & sauvegardes':
 st.title('📑 Rapports et sauvegardes')
 if p:
  try:
   d=metres.clean(dataframe(p));risk=st.session_state.risk
   stats=risk['stats'] if risk and risk['id']==p['id'] and risk['budget']==p['budget'] and risk['signature']==json.dumps(p['lignes'],sort_keys=True) else None
   st.download_button('📄 Télécharger le rapport PDF',reports.pdf(p,d,stats),'buildoptima_rapport.pdf','application/pdf')
   st.download_button('📊 Télécharger le métré CSV',d.to_csv(index=False).encode('utf-8-sig'),'buildoptima_metres.csv','text/csv')
   excel=io.BytesIO()
   with pd.ExcelWriter(excel,engine='openpyxl') as writer:d.to_excel(writer,index=False,sheet_name='Devis')
   st.download_button('📗 Télécharger le métré Excel',excel.getvalue(),'buildoptima_metres.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
  except Exception as e:st.warning(str(e))
 st.download_button('💾 Exporter tous les projets JSON',json.dumps(storage.list_projects(conn),ensure_ascii=False,indent=2).encode(),'buildoptima_backup.json','application/json')
 uploaded=st.file_uploader('Importer une sauvegarde JSON',type=['json'])
 if uploaded and st.button('Restaurer les projets'):
  try:
   items=json.load(uploaded)
   if not isinstance(items,list) or len(items)>100:raise ValueError('Maximum 100 projets.')
   for item in items:
    if not isinstance(item,dict) or not all(k in item for k in ('id','nom','budget','lignes','taches','variantes')):raise ValueError('Format de projet invalide.')
    if not isinstance(item['lignes'],list) or not isinstance(item['taches'],list) or not isinstance(item['variantes'],list):raise ValueError('Format de tableaux invalide.')
    if item['lignes']:metres.clean(pd.DataFrame(item['lignes']))
    if item['taches']:planning.cpm(item['taches'])
    if item['variantes']:optimisation.compare(pd.DataFrame(item['variantes']))
    storage.save(conn,item)
   st.success(f'{len(items)} projet(s) restauré(s).');st.rerun()
  except Exception as e:st.error(f'Sauvegarde rejetée : {e}')
else:
 st.title('🎓 Guide méthodologique')
 st.markdown('''### Parcours de démonstration
1. Créer le **projet fictif** dans le menu latéral.
2. Examiner les **métrés** et le **budget**.
3. Dans **Statistiques & données**, importer un historique réel CSV/Excel, afficher **les données brutes** et les valeurs manquantes avant toute analyse.
4. Lancer **10 000 simulations Monte-Carlo** et interpréter P(C > budget).
5. Étudier le **chemin critique** (CPM) et les marges des tâches.
6. Comparer les **variantes admissibles** sur un graphique de Pareto.
7. Exporter un rapport PDF et une sauvegarde JSON.

### Méthodes scientifiques
- **Coût déterministe :** C = Σ Qᵢ × Pᵢ.
- **Monte-Carlo :** quantités et prix multipliés par des facteurs triangulaires bornés par ± les incertitudes saisies. Les chocs de prix sont reliés par une copule gaussienne dont le paramètre est choisi par l'utilisateur.
- **Risque budgétaire :** fréquence des simulations pour lesquelles C > budget.
- **CPM :** calcul des dates au plus tôt / au plus tard, des marges et du chemin critique dans un graphe acyclique de tâches.
- **Pareto :** variantes déclarées techniquement admissibles qui ne sont dominées ni en coût ni en durée.

### Limites à annoncer lors de la soutenance
Les prix, incertitudes et durées sont fournis par l'utilisateur. Aucune calibration statistique automatique n'est effectuée sur des marchés camerounais. Les calculs géométriques ne vérifient pas la résistance des structures. SQLite conserve les projets sur le disque local, mais **n'est pas une base durable sur un hébergement gratuit à disque éphémère** : export JSON conseillé. L'application n'inclut pas d'authentification ni de gestion multi-utilisateur.
''')
