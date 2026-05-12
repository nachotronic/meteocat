import requests
import csv
from datetime import datetime, timezone
 
def fetch_meta():
    print("Descarregant metadades...")
    r = requests.get("https://analisi.transparenciacatalunya.cat/resource/yqwd-vj5e.json?$limit=300&$select=codi_estacio,nom_estacio,latitud,longitud,altitud,nom_comarca", timeout=30)
    print(f"  Status: {r.status_code}")
    meta = {}
    for s in r.json():
        try:
            lat, lon = float(s["latitud"]), float(s["longitud"])
            if 40 < lat < 43 and -1 < lon < 4:
                meta[s["codi_estacio"]] = {"nom": s.get("nom_estacio",""), "lat": round(lat,5), "lon": round(lon,5), "comarca": s.get("nom_comarca",""), "altitud": s.get("altitud","")}
        except: pass
    print(f"  {len(meta)} estacions")
    return meta
 
def fetch_var(codi, nom):
    print(f"Descarregant {nom}...")
    url = "https://analisi.transparenciacatalunya.cat/resource/nzvn-apee.json?$where=codi_variable='" + codi + "'&$order=data_lectura DESC&$limit=600&$select=codi_estacio,valor_lectura,data_lectura"
    r = requests.get(url, timeout=30)
    print(f"  Status: {r.status_code}")
    r.raise_for_status()
    seen = {}
    for row in r.json():
        c = row.get("codi_estacio")
        if c and c not in seen:
            seen[c] = row
    print(f"  {len(seen)} estacions")
    return seen
 
def fetch_daily_temp():
    print("Descarregant maximes i minimes del dia...")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    url = "https://analisi.transparenciacatalunya.cat/resource/nzvn-apee.json?$where=codi_variable='32' AND data_lectura >= '" + today + "T00:00:00'&$limit=5000&$select=codi_estacio,valor_lectura"
    r = requests.get(url, timeout=30)
    print(f"  Status: {r.status_code}")
    r.raise_for_status()
    maxims, minims = {}, {}
    for row in r.json():
        c = row.get("codi_estacio")
        try:
            v = float(row["valor_lectura"])
        except:
            continue
        if c not in maxims or v > maxims[c]:
            maxims[c] = v
        if c not in minims or v < minims[c]:
            minims[c] = v
    print(f"  {len(maxims)} estacions amb dades del dia")
    return maxims, minims
 
def main():
    meta = fetch_meta()
    VARS = {"32":"temperatura","33":"humitat","35":"precipitacio","30":"vent"}
    data = {}
    for codi, nom in VARS.items():
        for c, row in fetch_var(codi, nom).items():
            if c not in data:
                data[c] = {}
            try:
                data[c][nom] = round(float(row["valor_lectura"]),1)
                data[c]["data"] = row.get("data_lectura","")
            except: pass
 
    maxims, minims = fetch_daily_temp()
 
    rows = []
    for codi, vals in data.items():
        s = meta.get(codi)
        if not s or "temperatura" not in vals:
            continue
        rows.append({
            "nom":          s["nom"],
            "lat":          s["lat"],
            "lon":          s["lon"],
            "comarca":      s["comarca"],
            "altitud":      s["altitud"],
            "temperatura":  vals.get("temperatura",""),
            "temp_max":     round(maxims[codi], 1) if codi in maxims else "",
            "temp_min":     round(minims[codi], 1) if codi in minims else "",
            "humitat":      vals.get("humitat",""),
            "precipitacio": vals.get("precipitacio",""),
            "vent":         vals.get("vent",""),
            "data":         vals.get("data",""),
        })
 
    rows.sort(key=lambda r: r["nom"])
    print(f"\n{len(rows)} estacions amb dades")
 
    with open("meteocat.csv","w",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["nom","lat","lon","comarca","altitud","temperatura","temp_max","temp_min","humitat","precipitacio","vent","data"], extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
 
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    open("last_update.txt","w").write(now)
    print(f"Fet! {now}")
 
main()
