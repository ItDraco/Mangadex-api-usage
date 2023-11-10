import requests, json, os

class Manga:
    def __init__(self, manga) -> None:        
        self.id = manga["id"]
        self.cover_url = self.get_cover(manga["relationships"])
        self.info = manga["info"]
        manga["altTitles"].append(manga["title"])
        self.titles = manga["altTitles"]
        self.titles = {key: value for dict_item in self.titles for key, value in dict_item.items()}
        self.title = self.titles.get("en") if self.titles.get("en") else self.titles.get(self.info["origninalLanguage"])
        self.language = "en" if "en" in self.info["availableTranslatedLanguages"] else self.info["availableTranslatedLanguages"][0]
        self.chapters = self.load_chapters()
        self.chapters = self.format_chapters(self.chapters["data"])
        
    def load_chapters(self):
        reponse = make_request(url_dict=format_url_data({
            "type":"chapters",
            "url":{"endpoint": "/manga/{id}/feed", "id":self.id},
            "params": {"includeEmptyPages":0, "includeFuturePublishAt":0, "includeExternalUrl":0}
        }))
        if reponse:
            return reponse
        return []
    
    def change_language(self, lan):
        if lan in self.info["availableTranslatedLanguages"]:
            self.language = lan

    def sort_chapters(self, data: list):
        return sorted(data, key=lambda x: (x["volume"], x["chapter"]))
    
    def get_cover(self, data):
        for relationship in data:
            if relationship["type"] == "cover_art":
                self.cover = f"https://uploads.mangadex.org/covers/{self.id}/{relationship['attributes']['fileName']}"
                return self.cover

    def format_chapters(self, data):
        for i in range(len(data)):
            volume = data[i]["attributes"].get("volume")
            chapter = data[i]["attributes"].get("chapter")
            data[i] = {
                "id": data[i]["id"],
                "volume": float(volume) if volume else -1,
                "chapter": float(chapter) if chapter else -1,
                "title": data[i]["attributes"].get("title"),
                "translatedLanguage": data[i]["attributes"]["translatedLanguage"],
                "pages": data[i]["attributes"]["pages"]
            }

        return self.sort_chapters(data)
    
    def get_chapter_image_urls(self, chapter_number):
        #if chapter["translatedLanguage"] == self.language:
        chapter = self.chapters[chapter_number]
        response = make_request(format_url_data({"type":"images", "url":{"id":chapter["id"]}}))
        if response:
            chapter_images = response["chapter"]["data"]
            chapter_hash = response["chapter"]["hash"]
            return [f"https://uploads.mangadex.org/data/{chapter_hash}/{image}" for image in chapter_images]
        return []

def format_url_data(data:dict) -> dict:
        if not("type" in data and "url" in data):
            raise ValueError("1.Invalid data")
        if not (all(isinstance(value, str) for value in data["url"].values())):
            raise ValueError("2.Invalid data")
        
        params = data.get("params")
        url = data.get("url")
        id = url.get("id")
        match data["type"]:
            case "chapters":
                if isinstance(params, dict) and isinstance(id, str):
                    endpoint = url['endpoint'].replace(r'{id}', id) if r"{id}" in url["endpoint"] else "/user/follows/manga/feed"
                    return {"url": f"https://api.mangadex.org/{endpoint}", "params":data["params"]}
            case "images":
                if isinstance(url.get("id"), str):
                    return {"url":f"https://api.mangadex.org/at-home/server/{id}"}
            case "search":
                if isinstance(params, dict):
                    if "title" in params and isinstance(params.get("title"),str):
                        return {"url":f"https://api.mangadex.org/manga/", "params":{"title":data["params"]["title"]}}
            case "cover":
                if isinstance(url.get("id"), str):
                    return {"url":f"https://api.mangadex.org/manga/{id}", "params": {"includes[]":"cover_art"}}
            case _:
                raise ValueError("3.Invalid data")
        raise ValueError("4.Invalid data Structure")

def save_json(data, file_name):
    folder_name = "./jsons"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    with open(f"jsons/{file_name}.json","w") as f:
        json.dump(data, f, indent=4)

def make_request(url_dict:dict):
        response = requests.get(**url_dict)
        print(response.url)
        status = response.status_code
        match status:
            case 200:
                data = response.json()
                return data
            case _:                
                try:
                    data = response.json()
                    print(json.dumps(data, indent=4))
                except Exception as e:
                    print(status)
                    print(e)

def search_manga(title:str):
    response = make_request({"url":f"https://api.mangadex.org/manga/", "params":{"title":title, "includes[]":"author", "includes[]":"artist", "includes[]":"cover_art"}})
    if response:
        return response
    
def create_template(data:dict) ->dict:
    attributes = data["attributes"]
    return {
        "id":data["id"],
        "title":attributes["title"],
        "altTitles":attributes["altTitles"],
        "description":attributes["description"],
        "relationships":data["relationships"],
        "info": {
            "status":attributes["status"],
            "origninalLanguage":attributes["originalLanguage"],
            "year":attributes["year"],
            "contentRating":attributes["contentRating"],
            "tags":attributes["tags"],
            "chapterNumbersResetOnNewVolume":attributes["chapterNumbersResetOnNewVolume"],
            "createdAt":attributes["createdAt"],
            "updatedAt":attributes["updatedAt"],
            "availableTranslatedLanguages":attributes["availableTranslatedLanguages"],
            "latestUploadedChapter":attributes["latestUploadedChapter"]
        }
    }
