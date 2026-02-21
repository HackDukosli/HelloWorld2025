import streamlit as st
import pandas as pd
from movie_vectorizer import get_ideal_movie_vector, get_movieid_vector_dict
from kdtree import rknn_id


st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")

st.markdown("""
<style>

.stButton > button {
  background-color: #0A84FF;
  color: #ffffff;
  border: 1px solid #0A84FF;
  border-radius: 10px;
}

.stButton > button:hover {
  background-color: #006DDB;
  border-color: #006DDB;
}

.stButton > button:disabled {
  background-color: #333333 !important;
  border-color: #333333 !important;
  color: #888888 !important;
}

</style>
""", unsafe_allow_html=True)

df = pd.read_csv("movies.csv")
movie_list = df["title"].tolist()

st.session_state.setdefault("movies", [])
st.session_state.setdefault("genres", [])
st.session_state.setdefault("movie_name", "")
st.session_state.setdefault("movie_rating", 1)
st.session_state.setdefault("locked", False)
st.session_state.setdefault("results", None)



BASE_IMG = "https://image.tmdb.org/t/p/w200"

def poster_url_from_path(p):
    return f"{BASE_IMG}{p}" if isinstance(p, str) and p else None

def build_movie_dict(row):
    return {
        "title": row["title"],
        "rating": row["vote_average"],
        "overview": row["overview"],
        "poster": f"{BASE_IMG}{row['poster_path']}" if isinstance(row["poster_path"], str) else None,
    }

def add_movie():
    name = st.session_state["movie_name"]
    rating = st.session_state["movie_rating"]

    if not name.strip(): return

    name_norm = str(name).strip().lower()
    if any(m["name"].strip().lower() == name_norm for m in st.session_state["movies"]):
        st.toast("Already added that movie")
        return
    
    match = df[df["title"].str.lower() == name_norm]
    if not match.empty:
        poster = poster_url_from_path(match.iloc[0]["poster_path"])
    else:
        poster = None


    st.session_state["movies"].append({
        "name": name,
        "rating": rating,
        "poster": poster,
    })

    st.session_state["movie_name"] = ""

def render_movie_grid(movies, n):
    if not movies:
        return
    
    cols = None

    for i, m in enumerate(movies):
        if i % n == 0:
            cols = st.columns(n, gap="medium")
        with cols[i % n]:
            if m.get("poster"):
                st.image(m["poster"], use_container_width=True)
            else:
                st.write("No image")
            st.markdown(f"**{m['name']}**")
            st.markdown(f"⭐ {m['rating']}/10")


def remove_movie():
    st.session_state["movies"].clear()
    st.session_state["movie_name"] = ""
    st.session_state["movie_rating"] = 1

def run_recommend():
    st.session_state["locked"] = True
    st.session_state["results"] = {"Placeholder A": 1, "Placeholder B": 2, "Placeholder C": 3, "Placeholder D": 4, "Placeholder E": 5}

def restart():
    st.session_state["locked"] = False
    st.session_state["movies"].clear()
    st.session_state["genres"] = []
    st.session_state["movie_name"] = ""
    st.session_state["movie_rating"] = 1
    st.session_state["results"] = None



st.markdown("<h1 style='text-align: center; color: #0A84FF;'>Movie Recommender</h1>", unsafe_allow_html=True)

st.write(
    "### Tell us what kinds of movies you’re in the mood for:\n"
    "###### &emsp; 1. Pick a few genres. With these, we'll fill recommendations that include all these tags... and more!\n"
    "###### &emsp; 2. Next, add at least TWO movies you’ve seen with these genres and rate them.\n"
    "###### &emsp; 3. Once you're done, hit \"Recommend 5\" and we'll recommend five movies we think you'll love.\n"
)

with st.container(border=True):
    genres = st.multiselect("Enter a genre:", [
        'Action', 'Adventure', 'Animation', 'Comedy', 
        'Crime', 'Documentary', 'Drama', 'Family', 'Fantasy', 
        'History', 'Horror', 'Music', 'Mystery', 'Romance', 
        'Science Fiction', 'TV Movie', 'Thriller', 'War', 'Western'
        ], key="genres", disabled=st.session_state["locked"])

    movie_name = st.selectbox("Enter a movie name:", movie_list, key="movie_name", disabled=st.session_state["locked"])

    col_1, col_2, col_3, col_4 = st.columns([3, 1, 1, 1])
    with col_1:
        movie_rating = st.slider("Rate the movie:", 1, 10, 1, key="movie_rating", disabled=st.session_state["locked"])
    with col_2:
        st.button("Add Movie", use_container_width=True, on_click=add_movie, disabled=st.session_state["locked"])
    with col_3:
        st.button("Remove All Movies", use_container_width=True, on_click=remove_movie, disabled=st.session_state["locked"] or not st.session_state["movies"])
    with col_4:
        st.button(f"Recommend 5", use_container_width=True, on_click=run_recommend, disabled=st.session_state["locked"] or len(st.session_state["movies"]) < 2 or not genres)

if st.session_state["movies"]:
    with st.container(border=True):
        st.subheader("Movies:")
        render_movie_grid(st.session_state["movies"], 8)


if st.session_state["results"]:
    with st.container(border=True):
        st.subheader("Recommendations:")

        ideal_vector = get_ideal_movie_vector(st.session_state["movies"])
        movie_id_vector = get_movieid_vector_dict(st.session_state["genres"])

        if movie_id_vector == "error":
            st.toast("Your query parameters are too specific to recommend 5 movies!")
        else: 
            recommended_ids = rknn_id(dict_in=movie_id_vector, query=ideal_vector, k=10)
            recommended_rows = df[df["id"].isin(recommended_ids)]
            recommended_rows = df.set_index("id").loc[recommended_ids]

            user_titles = []
            for m in st.session_state["movies"]:
                user_titles.append((m.get("title") or m.get("name") or "").strip().lower())
            
            movies = [build_movie_dict(row) for _, row in recommended_rows.iterrows()]
            movies = [m for m in movies if m["title"].strip().lower() not in user_titles]
            movies = movies[:5]

            if len(movies) < 5:
                st.toast("Your query parameters are too specific to recommend 5 movies!")
            else:
                for movie in movies:
                    col_1, col_2 = st.columns([1, 4])
                    with col_1:
                        st.image(movie["poster"], use_container_width=True)
                    with col_2:
                        st.markdown(f"**{movie['title']}**")
                        st.markdown(f"⭐ Rating: {movie['rating']}/10")
                        st.markdown(f"{movie['overview']}")
                    st.divider()

if st.session_state["locked"]:
    st.button("Restart", on_click=restart)

col_1, col_2, _ = st.columns([1, 3, 14])
with col_1:
    st.markdown("###### Credits:")
with col_2:
    st.image("movide_db_img.svg", width=120)
