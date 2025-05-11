
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import quote_plus
import io

st.set_page_config(page_title="Szybkie porównywanie ofert samochodowych by adi.kwiatkowsky", layout="wide")
st.image("banner.png", use_column_width=True)
st.title("SZYBKIE PORÓWNYWANIE OFERT SAMOCHODOWYCH by adi.kwiatkowsky")

paliwo_map = {
    "dowolne": "",
    "benzyna": "petrol",
    "diesel": "diesel",
    "hybryda": "hybrid",
    "elektryczny": "electric"
}

skrzynia_map = {
    "dowolna": "",
    "manualna": "manual",
    "automatyczna": "automatic"
}

st.subheader("Wybierz portale do przeszukania:")
use_otomoto = st.checkbox("Otomoto", value=True)
use_olx = st.checkbox("OLX", value=True)

st.subheader("Filtry wyszukiwania:")
marka = st.text_input("Marka", "Toyota")
model = st.text_input("Model", "Corolla")
rocznik_od = st.number_input("Rocznik od", 2000, 2025, 2015)
rocznik_do = st.number_input("Rocznik do", 2000, 2025, 2020)
paliwo = st.selectbox("Rodzaj paliwa", list(paliwo_map.keys()))
skrzynia = st.selectbox("Skrzynia biegów", list(skrzynia_map.keys()))
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
        if paliwo:
            url += f"&search%5Bfilter_enum_fuel_type%5D={paliwo}"
        if skrzynia:
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
            szczegoly = oferta.find_all("li")
            rocznik = ""
            przebieg = ""
            for item in szczegoly:
                txt = item.text.lower()
                if "rok produkcji" in txt:
                    rocznik = item.text.strip()
                if "km" in txt:
                    przebieg = item.text.strip()
            if tytul and cena and link_tag:
                wyniki.append({
                    "Portal": "Otomoto",
                    "Tytuł": tytul.text.strip(),
                    "Cena": cena.text.strip(),
                    "Rocznik": rocznik,
                    "Przebieg": przebieg,
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
        oferty = soup.find_all("div", {"data-cy": "l-card"})
        for oferta in oferty:
            tytul_tag = oferta.find("h6")
            cena_tag = oferta.find("p", class_="css-10b0gli")
            link_tag = oferta.find("a", href=True)
            opis = oferta.find("p", class_="css-1x3l0fo")
            rocznik = ""
            przebieg = ""
            if opis:
                parts = opis.text.split(" - ")
                for part in parts:
                    if "km" in part.lower():
                        przebieg = part.strip()
                    elif part.strip().isdigit():
                        rocznik = part.strip()
            if tytul_tag and cena_tag and link_tag:
                wyniki.append({
                    "Portal": "OLX",
                    "Tytuł": tytul_tag.text.strip(),
                    "Cena": cena_tag.text.strip(),
                    "Rocznik": rocznik,
                    "Przebieg": przebieg,
                    "Link": "https://www.olx.pl" + link_tag["href"]
                })
    return wyniki

if st.button("Szukaj ofert"):
    wszystkie_wyniki = []
    with st.spinner("Skanowanie..."):
        if use_otomoto:
            wszystkie_wyniki += skanuj_otomoto(marka, model, rocznik_od, rocznik_do, paliwo_map[paliwo], skrzynia_map[skrzynia],
                                               moc_od, moc_do, przebieg_od, przebieg_do, strony)
        if use_olx:
            wszystkie_wyniki += skanuj_olx(marka, model, rocznik_od, rocznik_do, strony)
    if wszystkie_wyniki:
        df = pd.DataFrame(wszystkie_wyniki)
        st.dataframe(df)
        csv = df.to_csv(index=False).encode("utf-8")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Oferty")
        excel_data = output.getvalue()
        st.download_button("📥 Pobierz jako Excel", data=excel_data, file_name="oferty.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.download_button("📥 Pobierz jako CSV", data=csv, file_name="oferty.csv", mime="text/csv")
    else:
        st.warning("Nie znaleziono żadnych ofert.")

st.markdown("---")
st.markdown("<h4 style='text-align: center;'>🔗 Obserwuj mnie na TikToku: <a href='https://www.tiktok.com/@adi.kwiatkowsky' target='_blank'>@adi.kwiatkowsky</a></h4>", unsafe_allow_html=True)
