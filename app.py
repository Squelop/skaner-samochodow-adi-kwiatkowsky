
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import quote_plus

st.set_page_config(page_title="Szybkie porównywanie ofert samochodowych by adi.kwiatkowsky", layout="wide")
st.title("SZYBKIE PORÓWNYWANIE OFERT SAMOCHODOWYCH by adi.kwiatkowsky")

st.subheader("Wybierz portale do przeszukania:")
use_otomoto = st.checkbox("Otomoto", value=True)
use_olx = st.checkbox("OLX", value=True)

st.subheader("Filtry wyszukiwania:")
marka = st.text_input("Marka", "Toyota")
model = st.text_input("Model", "Corolla")
rocznik_od = st.number_input("Rocznik od", 2000, 2025, 2015)
rocznik_do = st.number_input("Rocznik do", 2000, 2025, 2020)
paliwo = st.selectbox("Rodzaj paliwa", ["dowolne", "benzyna", "diesel", "hybryda", "elektryczny"])
skrzynia = st.selectbox("Skrzynia biegów", ["dowolna", "manualna", "automatyczna"])
moc_od = st.number_input("Moc od (KM)", 0, 1000, 0)
moc_do = st.number_input("Moc do (KM)", 0, 1000, 1000)
przebieg_od = st.number_input("Przebieg od (km)", 0, 1000000, 0)
przebieg_do = st.number_input("Przebieg do (km)", 0, 1000000, 1000000)
strony = st.slider("Liczba stron do przeszukania", 1, 10, 3)

def skanuj_otomoto(marka, model, rocznik_od, rocznik_do, paliwo, skrzynia, moc_od, moc_do, przebieg_od, przebieg_do, strony):
    wyniki = []
    for strona in range(1, strony + 1):
        url = f"https://www.otomoto.pl/osobowe/{marka.lower()}/{model.lower()}/?page={strona}"
        url += f"&search%5Bfilter_enum_year%3Afrom%5D={rocznik_od}&search%5Bfilter_enum_year%3Ato%5D={rocznik_do}"

        if paliwo != "dowolne":
            url += f"&search%5Bfilter_enum_fuel_type%5D={paliwo}"
        if skrzynia != "dowolna":
            url += f"&search%5Bfilter_enum_gearbox%5D={skrzynia}"
        if moc_od > 0:
            url += f"&search%5Bfilter_float_engine_power%3Afrom%5D={moc_od}"
        if moc_do < 1000:
            url += f"&search%5Bfilter_float_engine_power%3Ato%5D={moc_do}"
        if przebieg_od > 0:
            url += f"&search%5Bfilter_float_mileage%3Afrom%5D={przebieg_od}"
        if przebieg_do < 1000000:
            url += f"&search%5Bfilter_float_mileage%3Ato%5D={przebieg_do}"

        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        oferty = soup.find_all("article")

        for oferta in oferty:
            tytul = oferta.find("h1") or oferta.find("h2")
            cena = oferta.find("h3")
            link_tag = oferta.find("a", href=True)

            if tytul and cena and link_tag:
                wyniki.append({
                    "Portal": "Otomoto",
                    "Tytuł": tytul.text.strip(),
                    "Cena": cena.text.strip(),
                    "Link": "https://www.otomoto.pl" + link_tag["href"]
                })
    return wyniki

def skanuj_olx(marka, model, rocznik_od, rocznik_do, strony):
    wyniki = []
    query = f"{marka} {model} {rocznik_od}-{rocznik_do}"
    for strona in range(1, strony + 1):
        url = f"https://www.olx.pl/motoryzacja/samochody/q-{quote_plus(query)}/?page={strona}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        oferty = soup.find_all("div", class_="css-1sw7q4x")

        for oferta in oferty:
            tytul_tag = oferta.find("h6")
            cena_tag = oferta.find("p", class_="css-wpfvmn")
            link_tag = oferta.find("a", href=True)

            if tytul_tag and cena_tag and link_tag:
                wyniki.append({
                    "Portal": "OLX",
                    "Tytuł": tytul_tag.text.strip(),
                    "Cena": cena_tag.text.strip(),
                    "Link": "https://www.olx.pl" + link_tag["href"]
                })
    return wyniki

if st.button("Szukaj ofert"):
    wszystkie_wyniki = []

    with st.spinner("Skanowanie..."):
        if use_otomoto:
            wszystkie_wyniki += skanuj_otomoto(marka, model, rocznik_od, rocznik_do, paliwo, skrzynia, moc_od, moc_do, przebieg_od, przebieg_do, strony)
        if use_olx:
            wszystkie_wyniki += skanuj_olx(marka, model, rocznik_od, rocznik_do, strony)

    if wszystkie_wyniki:
        df = pd.DataFrame(wszystkie_wyniki)

        def extract_price(text):
            try:
                return int(''.join(filter(str.isdigit, text)))
            except:
                return None

        df["Cena (PLN)"] = df["Cena"].apply(extract_price)
        srednia = df["Cena (PLN)"].dropna().mean()

        st.success(f"Znaleziono {len(df)} ofert.")
        st.dataframe(df)

        if not pd.isna(srednia):
            st.subheader(f"Średnia cena: {int(srednia):,} PLN".replace(",", " "))
        else:
            st.warning("Nie udało się obliczyć średniej ceny – brak danych liczbowych.")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Pobierz jako CSV", data=csv, file_name="oferty.csv", mime="text/csv")
    else:
        st.warning("Nie znaleziono żadnych ofert.")
