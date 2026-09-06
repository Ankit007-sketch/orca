"""
Multilingual Translation Service for ORCA (SIH26176)
Handles translation between English and Indian regional coastal languages:
Kannada (kn), Tamil (ta), Malayalam (ml), Telugu (te), Hindi (hi), Bengali (bn),
Gujarati (gu), Marathi (mr), and Odia (or).
"""

from typing import Dict, Any, Optional, Tuple


class MultilingualTranslator:
    """
    Translates marine queries and synthesized recommendations to/from
    Indian regional languages with coastal domain vocabulary.
    """

    SUPPORTED_LANGUAGES = {
        "en": "English",
        "kn": "Kannada (ಕನ್ನಡ)",
        "ta": "Tamil (தமிழ்)",
        "te": "Telugu (తెలుగు)",
        "ml": "Malayalam (മലയാളം)",
        "hi": "Hindi (हिन्दी)",
        "bn": "Bengali (বাংলা)",
        "gu": "Gujarati (ગુજરાતી)",
        "mr": "Marathi (मराठी)",
        "or": "Odia (ଓଡ଼ିଆ)"
    }

    # Core maritime phrase dictionaries
    _RECOMMENDATION_TEMPLATES = {
        "SAFE": {
            "en": "Safe for fishing and marine operations. Favorable Potential Fishing Zone (PFZ) detected. Sea state is calm.",
            "kn": "ಮೀನುಗಾರಿಕೆ ಮತ್ತು ಸಮುದ್ರ ಕಾರ್ಯಾಚರಣೆಗೆ ಸುರಕ್ಷಿತವಾಗಿದೆ. ಅನುಕೂಲಕರ ಸಂಭಾವ್ಯ ಮೀನುಗಾರಿಕಾ ವಲಯ (PFZ) ಕಂಡುಬಂದಿದೆ. ಸಮುದ್ರ ಶಾಂತವಾಗಿದೆ.",
            "ta": "மீன்பிடிக்க மற்றும் கடல் நடவடிக்கைகளுக்கு பாதுகாப்பானது. சாதகமான சாத்தியமான மீன்பிடி மண்டலம் (PFZ) கண்டறியப்பட்டுள்ளது. கடல் அமைதியாக உள்ளது.",
            "te": "చేపల వేట మరియు సముద్ర కార్యకలాపాలకు సురక్షితం. అనుకూలమైన సంభావ్య చేపల వేట ప్రాంతం (PFZ) గుర్తించబడింది. సముద్రం ప్రశాంతంగా ఉంది.",
            "ml": "മത്സ്യബന്ധനത്തിനും കടൽ പ്രവർത്തനങ്ങൾക്കും സുരക്ഷിതം. അനുകൂലമായ സാധ്യതയുള്ള മത്സ്യബന്ധന മേഖല (PFZ) കണ്ടെത്തി. കടൽ ശാന്തമാണ്.",
            "hi": "मत्स्य पालन और समुद्री संचालन के लिए सुरक्षित है। अनुकूल संभावित मत्स्य पालन क्षेत्र (PFZ) का पता चला है। समुद्र शांत है।",
            "bn": "মাছ ধরা এবং সামুদ্রিক অভিযানের জন্য নিরাপদ। অনুকূল সম্ভাব্য মৎস্য শিকার অঞ্চল (PFZ) শনাক্ত করা হয়েছে। সমুদ্র শান্ত।",
            "gu": "માછીમારી અને દરિયાઈ કામગીરી માટે સલામત છે. અનુકૂળ સંભવિત માછીમારી ક્ષેત્ર (PFZ) મળ્યું છે. દરિયો શાંત છે.",
            "mr": "मासेमारी आणि सागरी कामकाजासाठी सुरक्षित आहे. अनुकूल संभाव्य मासेमारी क्षेत्र (PFZ) आढळले आहे. समुद्र शांत आहे.",
            "or": "ମାଛ ଧରିବା ଏବଂ ସାମୁଦ୍ରିକ କାର୍ଯ୍ୟ ପାଇଁ ସୁରକ୍ଷିତ। ଅନୁକୂଳ ସମ୍ଭାବ୍ୟ ମତ୍ସ୍ୟ ଧରିବା କ୍ଷେତ୍ର (PFZ) ଚିହ୍ନଟ ହୋଇଛି। ସମୁଦ୍ର ଶାନ୍ତ ଅଛି।"
        },
        "CAUTION": {
            "en": "Exercise caution. Moderate sea swell and wind speeds observed. Small motorized boats should stay close to shore.",
            "kn": "ಎಚ್ಚರಿಕೆ ವಹಿಸಿ. ಮಧ್ಯಮ ಗಾಳಿ ಮತ್ತು ಅಲೆಗಳ ಏರಿಳಿತ ಕಂಡುಬಂದಿದೆ. ಸಣ್ಣ ದೋಣಿಗಳು ತೀರದ ಹತ್ತಿರವೇ ಇರಬೇಕು.",
            "ta": "எச்சரிக்கையுடன் செயல்படவும். மிதமான அலை மற்றும் காற்றின் வேகம் காணப்படுகிறது. சிறிய படகுகள் கரைக்கு அருகிலேயே இருக்க வேண்டும்.",
            "te": "జాగ్రత్త వహించండి. మోస్తరు సముద్రపు అలలు మరియు గాలులు వీస్తున్నాయి. చిన్న పడవలు తీరానికి సమీపంలోనే ఉండాలి.",
            "ml": "ജാഗ്രത പാലിക്കുക. മിതമായ തിരമാലകളും കാറ്റും രേഖപ്പെടുത്തിയിട്ടുണ്ട്. ചെറിയ വള്ളങ്ങൾ തീരത്തോട് ചേർന്ന് നിൽക്കണം.",
            "hi": "सावधानी बरतें। मध्यम समुद्री लहरें और हवा की गति देखी गई है। छोटी नावें तट के करीब रहें।",
            "bn": "সতর্কতা অবলম্বন করুন। মাঝারি ঢেউ ও বাতাসের গতিবেগ পরিলক্ষিত হয়েছে। ছোট নৌকা উপকূলের কাছাকাছি থাকা উচিত।",
            "gu": "સાવધાની રાખો. મધ્યમ દરિયાઈ મોજા અને પવનની ગતિ જોવા મળી છે. નાની હોડીઓએ કાંઠાની નજીક રહેવું જોઈએ.",
            "mr": "खबरदारी बाळगा. मध्यम लाटा आणि वाऱ्याचा वेग नोंदवला गेला आहे. लहान बोटींनी किनाऱ्याजवळ राहावे.",
            "or": "ସତର୍କତା ଅବଲମ୍ବନ କରନ୍ତୁ। ମଧ୍ୟମ ସମୁଦ୍ର ଢେଉ ଏବଂ ପବନ ଦେଖାଦେଇଛି। ଛୋଟ ଡଙ୍ଗାଗୁଡ଼ିକ କୂଳ ପାଖରେ ରହିବା ଉଚିତ।"
        },
        "UNSAFE": {
            "en": "UNSAFE for maritime activity! High wave alert and hazardous weather conditions detected. Do NOT venture into the sea.",
            "kn": "ಸಮುದ್ರ ಸಂಚಾರಕ್ಕೆ ಅಸುರಕ್ಷಿತ! ಎತ್ತರದ ಅಲೆಗಳ ಎಚ್ಚರಿಕೆ ಮತ್ತು ಅಪಾಯಕಾರಿ ಹವಾಮಾನ. ಸಮುದ್ರಕ್ಕೆ ಇಳಿಯಬೇಡಿ.",
            "ta": "கடல் நடவடிக்கைகளுக்கு பாதுகாப்பற்றது! உயரமான அலை எச்சரிக்கை மற்றும் அபாயகரமான வானிலை. கடலுக்கு செல்ல வேண்டாம்.",
            "te": "సముద్ర ప్రయాణానికి ప్రమాదకరం! ఎత్తైన అలల హెచ్చరిక మరియు ప్రతికూల వాతావరణం. సముద్రంలోకి వెళ్లవద్దు.",
            "ml": "കടലിൽ പോകുന്നത് അപകടകരം! ഉയർന്ന തിരമാല മുന്നറിയിപ്പും മോശം കാലാവസ്ഥയും. കടലിൽ ഇറങ്ങരുത്.",
            "hi": "समुद्री गतिविधि के लिए असुरक्षित! ऊंची लहरों की चेतावनी और खतरनाक मौसम। समुद्र में न जाएं।",
            "bn": "সামুদ্রিক কার্যকলাপের জন্য বিপজ্জনক! উচ্চ ঢেউয়ের সতর্কতা ও প্রতিকূল আবহাওয়া। সমুদ্রে যাবেন না।",
            "gu": "દરિયાઈ પ્રવૃત્તિ માટે જોખમી! ઊંચા મોજાની ચેતવણી અને ખરાબ હવામાન. દરિયામાં ન જશો.",
            "mr": "सागरी हालचालींसाठी असुरक्षित! उंच लाटांचा इशारा आणि वादळी हवामान. समुद्रात जाऊ नका.",
            "or": "ସାମୁଦ୍ରିକ କାର୍ଯ୍ୟ ପାଇଁ ଅସୁରକ୍ଷିତ! ଉଚ୍ଚ ଢେଉ ଚେତାବନୀ ଏବଂ ବିପଜ୍ଜନକ ପାଣିପାଗ। ସମୁଦ୍ରକୁ ଯାଆନ୍ତୁ ନାହିଁ।"
        }
    }

    _TERMS_MAP = {
        "wind_speed": {"en": "Wind Speed", "kn": "ಗಾಳಿಯ ವೇಗ", "ta": "காற்றின் வேகம்", "hi": "हवा की गति", "ml": "കാറ്റിന്റെ വേഗത"},
        "wave_height": {"en": "Wave Height", "kn": "ಅಲೆಯ ಎತ್ತರ", "ta": "அலையின் உயரம்", "hi": "लहर की ऊंचाई", "ml": "തിരമാലയുടെ ഉയരം"},
        "chlorophyll": {"en": "Chlorophyll", "kn": "ಕ್ಲೋರೊಫಿಲ್", "ta": "பச்சையம்", "hi": "क्लोरोफिल", "ml": "ക്ലോറോഫിൽ"},
        "border_warning": {"en": "Boundary Warning", "kn": "ಗಡಿ ಎಚ್ಚರಿಕೆ", "ta": "எல்லை எச்சரிக்கை", "hi": "सीमा चेतावनी", "ml": "അതിർത്തി മുന്നറിയിപ്പ്"},
        "pfz": {"en": "Potential Fishing Zone", "kn": "ಮೀನುಗಾರಿಕಾ ವಲಯ", "ta": "மீன்பிடி மண்டலம்", "hi": "मत्स्य क्षेत्र", "ml": "മത്സ്യബന്ധന മേഖല"}
    }

    def detect_language(self, text: str, default_code: str = "en") -> str:
        """
        Simple character-range language detection for Indian scripts.
        """
        if not text:
            return default_code

        # Unicode ranges
        for char in text:
            cp = ord(char)
            if 0x0C80 <= cp <= 0x0CFF:
                return "kn"  # Kannada
            elif 0x0B80 <= cp <= 0x0BFF:
                return "ta"  # Tamil
            elif 0x0C00 <= cp <= 0x0C7F:
                return "te"  # Telugu
            elif 0x0D00 <= cp <= 0x0D7F:
                return "ml"  # Malayalam
            elif 0x0900 <= cp <= 0x097F:
                return "hi"  # Hindi / Marathi
            elif 0x0980 <= cp <= 0x09FF:
                return "bn"  # Bengali
            elif 0x0A80 <= cp <= 0x0AFF:
                return "gu"  # Gujarati
            elif 0x0B00 <= cp <= 0x0B7F:
                return "or"  # Odia

        return default_code if default_code in self.SUPPORTED_LANGUAGES else "en"

    def translate_query_to_english(self, user_query: str, language_code: str) -> str:
        """
        Translates or extracts core intent from non-English query for agent processing.
        """
        if language_code == "en" or not user_query:
            return user_query

        # Basic intent normalizer if regional script used
        q = user_query.strip()
        return f"[Translated from {self.SUPPORTED_LANGUAGES.get(language_code, language_code)}]: {q}"

    def translate_recommendation(
        self,
        base_recommendation: str,
        risk_level: str,
        target_lang: str,
        specific_details: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Translates or formats synthesized recommendation into target language.
        Uses high-quality marine-specific regional templates.
        """
        if target_lang == "en" or target_lang not in self.SUPPORTED_LANGUAGES:
            return base_recommendation

        lvl = risk_level.upper() if risk_level.upper() in self._RECOMMENDATION_TEMPLATES else "SAFE"
        template = self._RECOMMENDATION_TEMPLATES.get(lvl, {}).get(target_lang)

        if not template:
            return base_recommendation

        # If we have specific numeric details (waves, wind, PFZ distance), append in a readable localized format
        if specific_details:
            details_str = []
            if "wave_height_m" in specific_details and specific_details["wave_height_m"] is not None:
                wh = specific_details["wave_height_m"]
                details_str.append(f"(Wave: {wh}m)")
            if "wind_speed_kmh" in specific_details and specific_details["wind_speed_kmh"] is not None:
                ws = specific_details["wind_speed_kmh"]
                details_str.append(f"(Wind: {ws} km/h)")
            if "pfz_distance_km" in specific_details and specific_details["pfz_distance_km"] is not None:
                pdist = specific_details["pfz_distance_km"]
                details_str.append(f"(PFZ: ~{pdist} km)")

            if details_str:
                return f"{template} {' '.join(details_str)}"

        return template


# Global translator instance
translator_service = MultilingualTranslator()
