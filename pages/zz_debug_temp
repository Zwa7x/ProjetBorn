# pages/99_debug_temp.py
import streamlit as st
import traceback

st.set_page_config(page_title="DEBUG TEMP", layout="wide")
st.title("DEBUG TEMPORAIRE — Diagnostics utils / data")

st.markdown("**But** : vérifier import utils, load_settings(), load_data() et afficher les erreurs complètes.")

try:
    import utils
    st.success("Module `utils` importé")
    st.write("utils.__file__:", getattr(utils, "__file__", "n/a"))
except Exception as e:
    st.error("Erreur à l'import de `utils` : " + str(e))
    st.text(traceback.format_exc())
    st.stop()

# Tester load_settings
st.header("load_settings()")
try:
    s = utils.load_settings()
    st.success("load_settings() OK")
    st.write("Clés racine:", list(s.keys()) if isinstance(s, dict) else type(s))
    st.write("Aperçu regions:", list(s.get("regions", {}).keys()) if isinstance(s, dict) else "n/a")
except Exception as e:
    st.error("Erreur lors de load_settings(): " + str(e))
    st.text(traceback.format_exc())

# Tester load_data
st.header("load_data()")
try:
    if hasattr(utils, "load_data") and callable(utils.load_data):
        df = utils.load_data()
        st.success("load_data() OK")
        try:
            st.write("Aperçu dataframe (head):")
            st.dataframe(df.head(20))
        except Exception:
            st.write("Retour non-dataframe :", type(df))
    else:
        st.error("utils.load_data n'est pas défini ou n'est pas callable.")
except Exception as e:
    st.error("Erreur lors de load_data(): " + str(e))
    st.text(traceback.format_exc())

st.markdown("---")
st.write("Quand tu as fini, supprime ce fichier `pages/99_debug_temp.py` pour le retirer du menu.")
