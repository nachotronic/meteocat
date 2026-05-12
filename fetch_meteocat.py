import requests, csv
from datetime import datetime, timezone

def main():
    print("Metadades...")
    meta = {}
    for s in requests.get("https://analisi.transparenciacatalunya.cat/resource/yqwd-vj5e.json?$limit=300&$select=codi_estacio,nom_estacio,latitud,longitud,altitud,nom_comarca", timeout=30).json():
        try:
            lat, lon = float(s["latitud"]), float(s["longitud"])
            if 40 < lat < 43 and -1 < lon < 4:
                meta[s["codi_estacio"]] = {"nom":s.get("nom_estacio",""),"lat":round(lat,5),"lon":round(lon,5),"comarca":s.get("nom_comarca",""),"altitud":s.get("altitud","")}
        except: pass
    print(f"{len(meta)} estacions")

    rows = []
    for codi, nom in {"32":"temperatura","33":"humitat","35":"precipitacio","30":"vent"}.items():
        print(f"{nom}...")
        url = "https://analisi.transparenciacatalunya.cat/resource/nzvn-apee.json?$where=codi_variable='" + codi + "'&$order=data_lectura DESC&$limit=600&$select=codi_estacio,valor_lectura,data_lectura"
        seen = {}
        for row in requests.get(url, timeout=30).json():
            c = row.get("codi_estacio")
            if c and c not in seen: seen[c] = row
        for c, row in seen.items():
            if c not in meta: continue
            entry = next((r for r in rows if r["codi"]==c), None)
            if not entry:
                entry = {"codi":c,"nom":meta[c]["nom"],"lat":meta[c]["lat"],"lon":meta[c]["lon"],"comarca":meta[c]["comarca"],"altitud":meta[c]["altitud"]}
                rows.append(entry)
            try: entry[nom] = round(float(row["valor_lectura"]),1)
            except: pass

    rows = [r for r in rows if "temperatura" in r]
    rows.sort(key=lambda r: r["nom"])
    print(f"{len(rows)} estacions amb dades")

    with open("meteocat.csv","w",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["nom","lat","lon","comarca","altitud","temperatura","humitat","precipitacio","vent"], extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    open("last_update.txt","w").write(datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    print("Fet!")

main()
