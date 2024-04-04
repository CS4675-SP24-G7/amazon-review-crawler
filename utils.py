from url_extractor import Review_Type


def Join_JSON(isbn):

    import os
    import json

    # copy all json files from save folder to temp_data folder
    # os.system("cp ./save/*.json ./temp_data/")

    # read all json files from temp_data folder
    json_files = [f for f in os.listdir('./temp_data/') if f.endswith('.json')]

    data = {
        "product_title": "",
        "isbn": isbn,
        Review_Type.ONE_STAR.name.lower(): [],
        Review_Type.TWO_STAR.name.lower(): [],
        Review_Type.THREE_STAR.name.lower(): [],
        Review_Type.FOUR_STAR.name.lower(): [],
        Review_Type.FIVE_STAR.name.lower(): []
    }

    for file in json_files:
        for review_type in Review_Type:
            if f"{isbn}_{review_type.name}" in file:
                with open(f'./temp_data/{file}', 'r') as f:
                    temp = json.load(f)
                    if (data["product_title"] == ""):
                        data["product_title"] = temp["product_title"]
                    data[review_type.name.lower()] += temp["reviews"]

    # join all json files into one json file
    with open(f'./data/{isbn}.json', 'w') as f:
        json.dump(data, f, indent=2)

    # delete all json files from temp_data folder
    os.system(f"rm ./temp_data/{isbn}_*.json")
