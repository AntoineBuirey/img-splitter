from xml.etree import ElementTree

class Translator:
    def __init__(self, translation_dir : str):
        self.translation_dir = translation_dir
        self.language = "en"
        self.translations : dict[str, str] = {}
        
    def set_language(self, language : str):
        self.language = language
        self.translations = self.load_translation(language)
        
    def load_translation(self, language : str):
        translation_file = f"{self.translation_dir}/{language}.xml"
        try:
            tree = ElementTree.parse(translation_file)
            root = tree.getroot()
            return {str(entry.get("key")): str(entry.text) for entry in root.findall("entry")}
        except FileNotFoundError:
            if language != "en":
                print(f"Translation file for '{language}' not found. Falling back to English.")
                return self.load_translation("en")
            else:
                print("English translation file not found. No translations will be available.")
                return {}

    def __call__(self, key : str) -> str:
        return self.translations.get(key, key)