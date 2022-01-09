# Gets master list of venue information from NUSMods' GitHub
# Preprocesses data with venue availability before insertion into database
import urllib.request
import requests
import json
import pandas as pd

data_url = "https://raw.githubusercontent.com/nusmodifications/nusmods/" \
    + "master/website/src/data/venues.json"

with urllib.request.urlopen(data_url) as url:
    data = json.loads(url.read().decode())
    column_names = ["name", "lat", "long"]
    df = pd.DataFrame(columns=column_names)

    for venue in data:
        try:
            long = data[venue]["location"]["x"]
            lat = data[venue]["location"]["y"]
            new_row = {"name": venue.upper(),
                       "lat": lat,
                       "long": long}
            df = df.append(new_row, ignore_index=True)
        except KeyError:
            print(venue + " has no location coordinates available.")
            continue
    df.drop_duplicates(inplace=True, ignore_index=True)
    df.sort_values(by=["name"], inplace=True, ignore_index=True)
    df.set_index("name", inplace=True)
    venues_dict = df.to_dict("index")

    response = requests.get("https://api.nusmods.com/v2/2021-2022/semesters/2/venueInformation.json")
    venues = response.json()

    for venue in venues:
        day_list = venues[venue]
        avail_dict = {}
        for day_dict in day_list:
            avail_dict[day_dict["day"]] = day_dict["availability"]

        venue = venue.upper()
        if venue in venues_dict:
            venues_dict[venue]["availability"] = avail_dict

    with open("venue_data_n.json", "w") as outfile:
        json.dump({"venues": venues_dict}, outfile, indent=4, sort_keys=True, ensure_ascii=False)
