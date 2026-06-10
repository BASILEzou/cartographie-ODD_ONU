import pandas as pd
from tqdm import tqdm
import pickle
import plotly.express as px
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import math
from scipy.stats import pearsonr
from dash.dependencies import Input, Output, State
import os

# Chemin absolu basé sur la position du script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE_DIR, "dico_variables.pkl"), "rb") as f:
    dico_variables = pickle.load(f)

with open(os.path.join(BASE_DIR,"dico_ODD.pkl"), "rb") as f:
    dico_ODD = pickle.load(f)

#pour les départements
with open(os.path.join(BASE_DIR,"mega_dico.pkl"), "rb") as f:
    mega_dico = pickle.load(f)

with open(os.path.join(BASE_DIR,"mega_dico_code.pkl"), "rb") as f:
    mega_dico_code = pickle.load(f)

with open(os.path.join(BASE_DIR,"nom_vers_code.pkl"), "rb") as f:
    nom_vers_code = pickle.load(f)

with open(os.path.join(BASE_DIR,"code_vers_nom.pkl"), "rb") as f:
    code_vers_nom = pickle.load(f)

#pour les régions
with open(os.path.join(BASE_DIR,"mega_dico_reg.pkl"), "rb") as f:
    mega_dico_reg = pickle.load(f)

with open(os.path.join(BASE_DIR,"mega_dico_reg_code.pkl"), "rb") as f:
    mega_dico_reg_code = pickle.load(f)

with open(os.path.join(BASE_DIR,"nom_vers_code_reg.pkl"), "rb") as f:
    nom_vers_code_reg = pickle.load(f)

with open(os.path.join(BASE_DIR,"code_vers_nom_reg.pkl"), "rb") as f:
    code_vers_nom_reg = pickle.load(f)

#fonction pour créer un dataframe adapter à la visualisation des donnée que l'on veut 
def dataframe(année, variable):
    liste_valeurs=[]
    for i in mega_dico_code.keys():
        liste_valeurs.append(mega_dico_code[i][année][variable])

    df = pd.DataFrame({
    "departement": list(mega_dico.keys()),
    "code": list(mega_dico_code.keys()),
    "valeur": list(liste_valeurs)
    })
    return df 

def dataframe_reg(année, variable):
    liste_valeurs=[]
    for i in mega_dico_reg_code.keys():
        liste_valeurs.append(mega_dico_reg_code[i][année][variable])

    df = pd.DataFrame({
    "région": list(mega_dico_reg.keys()),
    "code": list(mega_dico_reg_code.keys()),
    "valeur": list(liste_valeurs)
    })
    return df 

#fonction pour créer la liste des années non vide pour une variable donnée
def faire_liste_annee(variable, echelle):
    if echelle == "departement":
        dico = mega_dico
    elif echelle == "région":
        dico = mega_dico_reg
    else:
        raise ValueError("Échelle invalide. Choisir entre 'commune', 'departement' ou 'region'.")

    liste_annee = set()
    for entite in dico:
        for annee in dico[entite]:
            val = dico[entite][annee].get(variable, float("nan"))
            if not (isinstance(val, float) and math.isnan(val)):
                liste_annee.add(annee)
    return sorted(liste_annee)

#fonction pour créer la liste des variables d'un ODD donnée
def faire_liste_variable(ODD):
    liste_ODD=[]
    for variable in dico_variables.keys():
        if dico_variables[variable]['ODD']==ODD:
            liste_ODD.append(variable)
    return liste_ODD

# Création d'un DataFrame pour l'année 2021 avec le taux de pauvreté total
ODD_0=1
liste_variable_0=faire_liste_variable(ODD_0)
variable_0=liste_variable_0[0]

liste_annees = faire_liste_annee(variable_0, "departement")
df = dataframe(liste_annees[0], variable_0)
df_reg=dataframe_reg(liste_annees[0], variable_0)

#fonction pour calculer un score de corrélation entre deux variable 
#avec la méthode de pearson 
def indice_pearson(echelle, année1, année2, var1, var2):
    if echelle=="departement":
        df1=dataframe(année1, var1)
        df2=dataframe(année2, var2)
        df1 = df1.rename(columns={"valeur": "valeur1"})
        df2 = df2.rename(columns={"valeur": "valeur2"})
    elif echelle=="région":
        df1=dataframe_reg(année1, var1)
        df2=dataframe_reg(année2, var2)
        df1 = df1.rename(columns={"valeur": "valeur1"})
        df2 = df2.rename(columns={"valeur": "valeur2"})
    df_fusion = pd.merge(df1, df2, on="code", suffixes=("_1", "_2"))
    df_fusion = df_fusion.dropna(subset=["valeur1", "valeur2"])
    r, p_value = pearsonr(df_fusion["valeur1"], df_fusion["valeur2"])
    score_corr = int(r * 100)
    return score_corr

# === App ===
app = dash.Dash(__name__)

app.layout = html.Div([

     html.Div([
        html.Button("ℹ️ À propos", id="btn-open-modal", n_clicks=0, style={
            "position": "absolute", "top": "20px", "left": "20px", 
            "backgroundColor": "#003366", "color": "white", "border": "none", 
            "padding": "10px 30px", "borderRadius": "5px", "cursor": "pointer"
        })
    ]),

    # Fenêtre modale
    html.Div(id="modal", style={"display": "none", "position": "fixed", "top": 0, "left": 0,
        "width": "100%", "height": "100%", "backgroundColor": "rgba(0,0,0,0.5)", "zIndex": 1000}, children=[
        html.Div(style={
            "backgroundColor": "white", "width": "80%", "maxWidth": "600px", 
            "margin": "10% auto", "padding": "30px", "borderRadius": "10px", 
            "boxShadow": "0 5px 15px rgba(0,0,0,0.3)", "position": "relative"
        }, children=[
            html.H2("À propos de l'application"),
            html.P("Ce tableau de bord permet de visualiser et comparer deux cartes de France "
                   "en fonction des Objectifs de Développement Durable (ODD) de l’ONU."),
            html.P("Utilisez les menus déroulants pour choisir l’échelle (département ou région), "
                   "l’ODD, la variable et l’année pour chaque carte."),
            html.P("La boîte de score affiche la corrélation entre les deux cartes choisies selon la méthode de Pearson. Si il est à 100 les deux variables sont parfaitement corrélés, à -100 la corrélation est inverse, et autour de 0 il n'y a aucune corrélations."),
            html.Button("Fermer", id="btn-close-modal", n_clicks=0, style={
                "marginTop": "20px", "backgroundColor": "#003366", "color": "white",
                "border": "none", "padding": "10px 20px", "borderRadius": "5px", "cursor": "pointer"
            })
        ])
    ]),
    
    html.H1(
        "Cartes de France des Objectifs de Développement Durable de l'ONU", 
        style={
            "fontSize": "28px",
            "textAlign": "center",
            "fontWeight": "bold",
            "padding": "20px",
            "backgroundColor": "#003366",
            "color": "white",
            "marginBottom": "30px"
        }
    ),

    # Sélections verticales (occupent toute la largeur)
    html.Div([
        html.Div([
            html.H3("Carte 1 - Sélection", style={"color": "#003366"}),

            html.Label("Échelle géographique"),
            dcc.Dropdown(id="dropdown-echelle-1", options=[
                {"label": "Département", "value": "departement"},
                {"label": "Région", "value": "région"},
            ], value="departement", style={"width": "100%"}),

            html.Label("Objectif de Développement Durable"),
            dcc.Dropdown(id="dropdown-variable_ODD-1", options=[
                {"label": f"{i}: {dico_ODD[i]}", "value": i} for i in range(1, 16)
            ], value=ODD_0, style={"width": "100%"}),

            html.Label("Variable"),
            dcc.Dropdown(id="dropdown-variable-1", options=liste_variable_0, value=variable_0, style={"width": "100%"}),

            html.Label("Année"),
            dcc.Slider(
                id="slider-annee-1", 
                min=0, max=len(liste_annees)-1, step=1,
                marks={i: liste_annees[i][1:] for i in range(len(liste_annees))},
                value=0
            ),

            dcc.Store(id="store-liste-annees-1")
        ], style={"padding": "20px", "backgroundColor": "#E3F2FD", "borderRadius": "10px", "marginBottom": "20px"}),

        html.Div([
            html.H3("Carte 2 - Sélection", style={"color": "#003366"}),

            html.Label("Échelle géographique"),
            dcc.Dropdown(id="dropdown-echelle-2", options=[
                {"label": "Département", "value": "departement"},
                {"label": "Région", "value": "région"},
            ], value="departement", style={"width": "100%"}),

            html.Label("Objectif de Développement Durable"),
            dcc.Dropdown(id="dropdown-variable_ODD-2", options=[
                {"label": f"{i}: {dico_ODD[i]}", "value": i} for i in range(1, 16)
            ], value=ODD_0, style={"width": "100%"}),

            html.Label("Variable"),
            dcc.Dropdown(id="dropdown-variable-2", options=liste_variable_0, value=variable_0, style={"width": "100%"}),

            html.Label("Année"),
            dcc.Slider(
                id="slider-annee-2", 
                min=0, max=len(liste_annees)-1, step=1,
                marks={i: liste_annees[i][1:] for i in range(len(liste_annees))},
                value=0
            ),

            dcc.Store(id="store-liste-annees-2")
        ], style={"padding": "20px", "backgroundColor": "#E3F2FD", "borderRadius": "10px", "marginBottom": "20px"})
    ], style={"width": "90%", "margin": "0 auto", "display": "flex", "flexDirection": "column"}),

    # Boîte de score de corrélation entre les deux sélections
    html.Div(id="box-score-correlation", style={
        "marginTop": "20px",
        "marginBottom": "40px",
        "padding": "20px",
        "backgroundColor": "#fff8e1",
        "border": "2px solid #fbc02d",
        "borderRadius": "10px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
        "maxWidth": "600px",
        "marginLeft": "auto",
        "marginRight": "auto",
        "fontSize": "18px",
        "fontWeight": "bold",
        "color": "#333",
        "textAlign": "center"
    }),

    # Légendes + Graphiques côte à côte
    html.Div([
        html.Div([
            html.Div(id="texte-variable-1", style={
                "fontSize": "16px",
                "marginBottom": "10px",
                "fontWeight": "bold",
                "textAlign": "center"
            }),
            dcc.Graph(id="graph-carte-1", style={"height": "400px"})
        ], style={"width": "48%", "padding": "10px"}),

        html.Div([
            html.Div(id="texte-variable-2", style={
                "fontSize": "16px",
                "marginBottom": "10px",
                "fontWeight": "bold",
                "textAlign": "center"
            }),
            dcc.Graph(id="graph-carte-2", style={"height": "400px"})
        ], style={"width": "48%", "padding": "10px"})
    ], style={
        "display": "flex",
        "justifyContent": "space-between",
        "maxWidth": "1200px",
        "margin": "0 auto"
    })

],style={"backgroundColor": "#F5F5F5", "minHeight": "100vh", "paddingBottom": "50px"})

# === Callbacks ===
@app.callback(
    Output("modal", "style"),
    Input("btn-open-modal", "n_clicks"),
    Input("btn-close-modal", "n_clicks"),
    State("modal", "style")
)
def toggle_modal(n_open, n_close, style):
    ctx = dash.callback_context

    if not ctx.triggered:
        return style
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "btn-open-modal":
        return {"display": "block", "position": "fixed", "top": 0, "left": 0,
                "width": "100%", "height": "100%", "backgroundColor": "rgba(0,0,0,0.5)", "zIndex": 1000}
    elif button_id == "btn-close-modal":
        return {"display": "none"}
    return style

@app.callback(
    Output("box-score-correlation", "children"),
    Input("dropdown-variable-1", "value"),
    Input("slider-annee-1", "value"),
    Input("store-liste-annees-1", "data"),
    Input("dropdown-echelle-1", "value"),
    Input("dropdown-variable-2", "value"),
    Input("slider-annee-2", "value"),
    Input("store-liste-annees-2", "data"),
    Input("dropdown-echelle-2", "value"),
)
def update_score_corr(var1, idx1, annees1, echelle1, var2, idx2, annees2, echelle2):
    if not annees1 or not annees2:
        return "Aucune année disponible"
    annee1 = annees1[idx1]
    annee2 = annees2[idx2]
    if echelle1 != echelle2:
        return "Veuillez sélectionner la même échelle géographique pour comparer les deux variables."
    try:
        score = indice_pearson(echelle1, annee1, annee2, var1, var2)
        return f"Indice de corrélation de Pearson entre les deux variables : {score} / 100"
    except Exception as e:
        return f"Erreur lors du calcul de la corrélation : {str(e)}"

def make_callbacks(suffix):
    @app.callback(
        Output(f"dropdown-variable-{suffix}", "options"),
        Output(f"dropdown-variable-{suffix}", "value"),
        Input(f"dropdown-variable_ODD-{suffix}", "value")
    )
    def update_dropdown_variable(ODD):
        liste_variables = faire_liste_variable(ODD)
        options = [{
            "label": f"{dico_variables[k]['libellé']}, {dico_variables[k]['libellé_sous']}",
            "value": str(k)
        } for k in liste_variables]
        valeur_defaut = liste_variables[0] if liste_variables else None
        return options, valeur_defaut

    @app.callback(
        Output(f"store-liste-annees-{suffix}", "data"),
        Input(f"dropdown-variable-{suffix}", "value"),
        Input(f"dropdown-echelle-{suffix}", "value")
    )
    def update_liste_annees(variable, echelle):
        return faire_liste_annee(variable, echelle)

    @app.callback(
        Output(f"slider-annee-{suffix}", "min"),
        Output(f"slider-annee-{suffix}", "max"),
        Output(f"slider-annee-{suffix}", "marks"),
        Output(f"slider-annee-{suffix}", "value"),
        Input(f"store-liste-annees-{suffix}", "data")
    )
    def update_slider(liste_annees):
        if not liste_annees:
            return 0, 0, {}, 0
        return 0, len(liste_annees) - 1, {i: liste_annees[i][1:] for i in range(len(liste_annees))}, 0

    @app.callback(
        Output(f"graph-carte-{suffix}", "figure"),
        Output(f"texte-variable-{suffix}", "children"),
        Input(f"dropdown-variable-{suffix}", "value"),
        Input(f"slider-annee-{suffix}", "value"),
        Input(f"store-liste-annees-{suffix}", "data"),
        Input(f"dropdown-echelle-{suffix}", "value")
    )
    def update_carte(variable, annee_index, liste_annees, echelle):
        if not liste_annees:
            return dash.no_update, "Aucune année disponible."
        annee = liste_annees[annee_index]
        if echelle == "departement":
            df = dataframe(annee, variable)
            geojson_url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements-version-simplifiee.geojson"
            location_key = "code"
            feature_key = "properties.code"
            hover = ["departement", "valeur", "code"]
        elif echelle == "région":
            df = dataframe_reg(annee, variable)
            geojson_url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/regions-version-simplifiee.geojson"
            location_key = "code"
            feature_key = "properties.code"
            hover = ["région", "valeur", "code"]
        else:
            return dash.no_update, "Échelle non supportée."
        fig = px.choropleth(
            df, geojson=geojson_url, locations=location_key, featureidkey=feature_key,
            color="valeur", color_continuous_scale="Viridis", scope="europe", hover_data=hover
        )
        fig.update_geos(fitbounds="locations", visible=False)
        texte = f"{dico_variables[variable]['libellé']}, {dico_variables[variable]['libellé_sous']}, en ({dico_variables[variable]['Unité']}) en {annee[1:]}, à l’échelle {echelle}"
        return fig, texte

# Callbacks des deux cartes
make_callbacks("1")
make_callbacks("2")

if __name__ == "__main__":
    app.run(debug=True)
