# pages/99_debug_data.py
import streamlit as st, traceback, importlib

st.set_page_config(page_title="DEBUG data_loader", layout="wide")
st.title("DEBUG utils.data_loader")

st.markdown("Vérifie import utils, import utils.data_loader et exécution de load_data().")

# 1) import utils
try:
    import utils
    st.success("Module utils importé")
    st.write("utils.__file__:", getattr(utils, "__file__", "n/a"))
except Exception as e:
    st.error("Erreur à l'import de utils: " + str(e))
    st.text(traceback.format_exc())
    st.stop()

# 2) import explicite du module data_loader
st.header("Import explicite utils.data_loader")
try:
    dl = importlib.import_module("utils.data_loader")
    st.success("utils.data_loader importé")
    st.write("fichier:", getattr(dl, "__file__", "n/a"))
    st.write("load_data callable:", callable(getattr(dl, "load_data", None)))
except Exception as e:
    st.error("Erreur import utils.data_loader: " + str(e))
    st.text(traceback.format_exc())
    st.stop()

# 3) appel de load_data via utils (wrapper) et via module direct
st.header("Appel load_data() via utils")
try:
    if hasattr(utils, "load_data"):
        res = utils.load_data()
        st.success("utils.load_data() exécuté")
        try:
            st.write("Aperçu (head) :")
            st.dataframe(res.head(20))
        except Exception:
            st.write("Retour non-dataframe :", type(res))
    else:
        st.error("utils.load_data n'existe pas.")
except Exception as e:
    st.error("Erreur lors de utils.load_data(): " + str(e))
    st.text(traceback.format_exc())

st.header("Appel load_data() via module direct")
try:
    if hasattr(dl, "load_data"):
        res2 = dl.load_data()
        st.success("dl.load_data() exécuté")
        try:
            st.dataframe(res2.head(20))
        except Exception:
            st.write("Retour non-dataframe :", type(res2))
    else:
        st.error("dl.load_data n'existe pas.")
except Exception as e:
    st.error("Erreur lors de dl.load_data(): " + str(e))
    st.text(traceback.format_exc())
