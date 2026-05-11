# pages/5_🛠️_Settings.py
import streamlit as st
import pandas as pd
import json
import traceback
from utils import load_settings, save_settings

st.set_page_config(page_title="⚙️ Paramètres", layout="wide")
st.title("⚙️ Paramètres de l'application")

# -----------------------
# Chargement sûr des settings
# -----------------------
try:
    settings = load_settings()
    if not isinstance(settings, dict):
        settings = {"regions": {}, "types_borne": []}
except Exception as e:
    st.error("Impossible de charger les paramètres : " + str(e))
    st.text(traceback.format_exc())
    settings = {"regions": {}, "types_borne": []}

# -----------------------
# Helpers utilitaires
# -----------------------
def settings_to_regions_df(s):
    rows = []
    for name, meta in (s.get("regions") or {}).items():
        if isinstance(meta, dict):
            acr = meta.get("acronyme", "") or ""
            lieux = meta.get("lieux", []) or []
            lieux_str = ", ".join(lieux)
        else:
            acr = ""
            lieux_str = str(meta)
        rows.append({"Région": name, "Acronyme": acr, "Lieux (séparés par ,)": lieux_str})
    if not rows:
        return pd.DataFrame(columns=["Région", "Acronyme", "Lieux (séparés par ,)"])
    return pd.DataFrame(rows)

def df_to_settings_regions(df, base_settings):
    """
    Convertit le DataFrame édité en structure settings['regions'].
    - Les lignes vides (Région vide) sont ignorées.
    - Les lieux sont séparés par , ou ;.
    """
    regs = {}
    for _, row in df.iterrows():
        name = str(row.get("Région") or "").strip()
        if not name:
            continue
        acr = str(row.get("Acronyme") or "").strip()
        lieux_raw = str(row.get("Lieux (séparés par ,)") or "").strip()
        if lieux_raw:
            lieux = [l.strip() for l in pd.Series(lieux_raw.split(",")).astype(str).tolist() if l.strip()]
        else:
            lieux = []
        # preserve existing extra meta if present
        existing = (base_settings.get("regions") or {}).get(name, {})
        if isinstance(existing, dict):
            regs[name] = {"acronyme": acr or existing.get("acronyme", ""), "lieux": list(dict.fromkeys(lieux or existing.get("lieux", [])))}
        else:
            regs[name] = {"acronyme": acr, "lieux": lieux}
    return regs

def safe_save_and_rerun(s, msg="Sauvegarde effectuée"):
    try:
        save_settings(s)
        st.success(msg)
        if hasattr(st, "experimental_rerun"):
            try:
                st.experimental_rerun()
            except Exception:
                st.session_state["_refresh_toggle"] = not st.session_state.get("_refresh_toggle", False)
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde : {e}")
        st.text(traceback.format_exc())

# -----------------------
# Top: tableau récapitulatif éditable (Regions)
# -----------------------
st.markdown("## Récapitulatif des régions")
st.markdown("Édite directement les cellules. **Région** est la clé principale (nom affiché). Les lieux sont séparés par des virgules.")
regions_df = settings_to_regions_df(settings)

# Utiliser st.data_editor si disponible, sinon fallback sur st.experimental_data_editor
data_editor = getattr(st, "data_editor", None) or getattr(st, "experimental_data_editor", None)

if data_editor:
    edited_df = data_editor(regions_df, use_container_width=True, key="regions_data_editor")
else:
    # fallback non éditable (rare), on affiche et propose un formulaire classique
    st.warning("Édition inline non disponible dans cette version de Streamlit. Utiliser les formulaires ci‑dessous.")
    st.dataframe(regions_df, use_container_width=True)
    edited_df = regions_df.copy()

col_apply, col_cancel = st.columns([1,1])
with col_apply:
    if st.button("Appliquer les modifications du tableau", key="apply_regions_table"):
        try:
            new_regions = df_to_settings_regions(edited_df, settings)
            settings["regions"] = new_regions
            safe_save_and_rerun(settings, "Modifications des régions appliquées.")
        except Exception as e:
            st.error("Erreur lors de l'application : " + str(e))
            st.text(traceback.format_exc())
with col_cancel:
    if st.button("Annuler les modifications (recharger)", key="cancel_regions_table"):
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
        else:
            st.session_state["_refresh_toggle"] = not st.session_state.get("_refresh_toggle", False)

st.markdown("---")

# -----------------------
# Section Lieux (dédiée, plus lisible)
# -----------------------
st.markdown("## Lieux (par région)")
regions_list = sorted(list(settings.get("regions", {}).keys()))
if not regions_list:
    st.info("Aucune région définie. Ajoute d'abord une région dans le tableau ci‑dessus.")
else:
    # colonne gauche: sélection région + liste des lieux
    col_l1, col_l2 = st.columns([2,1])
    with col_l1:
        sel_region = st.selectbox("Choisir une région", [""] + regions_list, key="select_lieux_region")
        if sel_region:
            st.subheader(f"Lieux pour {sel_region}")
            lieux = settings["regions"].get(sel_region, {}).get("lieux", []) or []
            if lieux:
                # affichage en tableau simple
                df_lieux = pd.DataFrame({"Lieu": lieux})
                st.dataframe(df_lieux, use_container_width=True)
            else:
                st.info("Aucun lieu pour cette région.")

            # ajout rapide
            with st.form(f"form_add_lieu_{sel_region}", clear_on_submit=True):
                new_lieu = st.text_input("Ajouter un lieu", "")
                if st.form_submit_button("Ajouter le lieu"):
                    nl = new_lieu.strip()
                    if not nl:
                        st.warning("Nom du lieu requis.")
                    else:
                        if nl in settings["regions"][sel_region].get("lieux", []):
                            st.warning("Ce lieu existe déjà pour la région.")
                        else:
                            settings["regions"][sel_region].setdefault("lieux", []).append(nl)
                            safe_save_and_rerun(settings, f"Lieu '{nl}' ajouté à {sel_region}.")

    # colonne droite: suppression multiple
    with col_l2:
        st.markdown("### Supprimer des lieux")
        if sel_region:
            lieux = settings["regions"].get(sel_region, {}).get("lieux", []) or []
            if lieux:
                to_remove = st.multiselect("Sélectionner les lieux à supprimer", options=lieux, key=f"multisel_lieux_{sel_region}")
                if st.button("Supprimer les lieux sélectionnés", key=f"btn_del_lieux_{sel_region}"):
                    if to_remove:
                        settings["regions"][sel_region]["lieux"] = [l for l in lieux if l not in to_remove]
                        safe_save_and_rerun(settings, f"{len(to_remove)} lieu(x) supprimé(s) de {sel_region}.")
                    else:
                        st.warning("Aucun lieu sélectionné.")
            else:
                st.info("Aucun lieu à supprimer pour cette région.")

st.markdown("---")

# -----------------------
# Section Types de borne
# -----------------------
st.markdown("## Types de borne")
tb = settings.get("types_borne", []) or []

# Normaliser affichage : si liste d'objets, afficher label; si strings, afficher string
def tb_label(t):
    return t if isinstance(t, str) else (t.get("label") or t.get("code") or str(t))

if tb:
    df_tb = pd.DataFrame({"Type": [tb_label(t) for t in tb]})
    st.dataframe(df_tb, use_container_width=True)
else:
    st.info("Aucun type de borne défini.")

# Ajouter un type
with st.form("form_add_type", clear_on_submit=True):
    new_type = st.text_input("Ajouter un type (ex: AC 22kW)", "")
    if st.form_submit_button("Ajouter le type"):
        nt = new_type.strip()
        if not nt:
            st.warning("Libellé requis.")
        else:
            existing_labels = [tb_label(t) for t in settings.setdefault("types_borne", [])]
            if nt in existing_labels:
                st.warning("Ce type existe déjà.")
            else:
                # on stocke en string pour simplicité
                settings["types_borne"].append(nt)
                safe_save_and_rerun(settings, f"Type '{nt}' ajouté.")

# Supprimer types
if settings.get("types_borne"):
    options = [tb_label(t) for t in settings["types_borne"]]
    rem = st.multiselect("Sélectionner les types à supprimer", options=options, key="multisel_types_main")
    if st.button("Supprimer les types sélectionnés"):
        if rem:
            settings["types_borne"] = [t for t in settings["types_borne"] if tb_label(t) not in rem]
            safe_save_and_rerun(settings, f"{len(rem)} type(s) supprimé(s).")
        else:
            st.warning("Aucun type sélectionné.")

st.markdown("---")
st.write("Debug rapide: nombre de régions =", len(settings.get("regions", {})), " | types =", len(settings.get("types_borne", [])))
