"""
Audio Synthesis and Podcast Script Generation Service.
Faithfully extracted from app.py without altering language-specific templates,
voice alternation, or audio compilation logic.
"""

import io
import logging
from typing import List, Tuple, Dict, Any, Optional

from gtts import gTTS

logger = logging.getLogger(__name__)


def build_podcast_segments(
    main_articles: List[Dict[str, Any]],
    mini_articles: List[Dict[str, Any]],
    category: str,
    audio_lang_code: str = "en"
) -> List[Tuple[str, int]]:
    """
    Compiles full podcast script segments with alternating host assignments (0 and 1).
    Uses exact multilingual introductions, story enumerations, and outros from app.py.
    """
    audio_segments: List[Tuple[str, int]] = []

    # 1. Language-specific Intro & Outro
    if audio_lang_code == "ml":
        intro = f"നമസ്കാരം, {category} വാർത്താ പോഡ്‌കാസ്റ്റിലേക്ക് സ്വാഗതം. ഇന്നത്തെ പ്രധാന വാർത്തകൾ ഇതാ. "
        outro = "വാർത്തകൾ അവസാനിച്ചു. ശ്രവിച്ചതിന് നന്ദി."
    elif audio_lang_code == "ta":
        intro = f"வணக்கம், {category} செய்திகள் பாட்காஸ்டிற்கு உங்களை வரவேற்கிறோம். இன்றைய முக்கிய செய்திகள் இதோ. "
        outro = "செய்திகள் நிறைவடைந்தது. கேட்டதற்கு நன்றி."
    elif audio_lang_code == "hi":
        intro = f"नमस्कार, {category} समाचार पॉडकास्ट में आपका स्वागत है। आज के मुख्य समाचार इस प्रकार हैं। "
        outro = "समाचार समाप्त हुए। सुनने के लिए धन्यवाद।"
    elif audio_lang_code == "kn":
        intro = f"ನಮಸ್ಕಾರ, {category} ಸುದ್ದಿ ಪಾಡ್‌ಕಾಸ್ಟ್‌ಗೆ ಸ್ವಾಗತ. ಇಂದಿನ ಪ್ರಮುಖ ಸುದ್ದಿಗಳು ಇಲ್ಲಿವೆ. "
        outro = "ಸುದ್ದಿಗಳು ಮುಗಿದವು. ಕೇಳಿದ್ದಕ್ಕಾಗಿ ಧನ್ಯವಾದಗಳು."
    else:
        intro = f"Welcome to your daily news briefing podcast on {category}. Here is the summary of the latest events. "
        outro = "That concludes your news podcast update. Thank you for listening."

    audio_segments.append((intro, 0))

    # 2. Main Story Briefings with Alternating Hosts
    for idx, art in enumerate(main_articles):
        host_num = idx % 2  # Alternate Host 0 and Host 1
        summary_text = art.get("summary") or art.get("description") or ""
        title_text = art.get("title") or ""

        if audio_lang_code in ["ml", "ta", "hi", "kn"]:
            body = f"വാർത്ത {idx + 1}. {title_text}. {summary_text}. "
        else:
            body = f"Story number {idx + 1}. {title_text}. {summary_text}. "

        audio_segments.append((body, host_num))

    # 3. Quick Bullet Updates
    if mini_articles:
        if audio_lang_code == "ml":
            bullet_intro = "മറ്റ് പ്രധാന വിവരങ്ങൾ ചുരുക്കത്തിൽ ഇതാ. "
        elif audio_lang_code == "ta":
            bullet_intro = "இதர செய்திகள் சுருக்கமாக இதோ. "
        elif audio_lang_code == "hi":
            bullet_intro = "अन्य समाचार संक्षेप में। "
        elif audio_lang_code == "kn":
            bullet_intro = "ಇತರ ಸುದ್ದಿಗಳು ಸಂಕ್ಷಿಪ್ತವಾಗಿ ಇಲ್ಲಿವೆ. "
        else:
            bullet_intro = "Here are some quick bullet updates. "

        audio_segments.append((bullet_intro, 0))

        for idx, art in enumerate(mini_articles):
            host_num = idx % 2
            bullet_title = (art.get("title") or "").strip()
            audio_segments.append((f"{bullet_title}. ", host_num))

    # 4. Outro
    audio_segments.append((outro, 0))

    return audio_segments


def generate_audio(text: str, lang: str = "en", tld: str = "com") -> Optional[io.BytesIO]:
    """
    Generates single-speaker gTTS audio written into an in-memory BytesIO buffer.
    """
    if not text or not text.strip():
        return None
    try:
        if lang == "en":
            tts = gTTS(text=text, lang=lang, tld=tld, slow=False)
        else:
            tts = gTTS(text=text, lang=lang, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp
    except Exception as e:
        logger.error(f"TTS Generation Error: {e}")
        return None


def generate_dual_host_audio(
    segments: List[Tuple[str, int]],
    lang_code: str = "en",
    accent_tld: str = "com"
) -> Optional[io.BytesIO]:
    """
    Dual-Host Audio Generation Helper (voice modulation by alternating accents/speeds).
    Sequentially appends synthesized MP3 bytes into an in-memory buffer.
    """
    if not segments:
        return None

    combined_bytes = b""
    for text, host_num in segments:
        if not text or not text.strip():
            continue
        try:
            if lang_code == "en":
                # Alternate TLDs for English (US vs UK accent)
                current_tld = accent_tld if host_num == 0 else "co.uk"
                tts = gTTS(text=text, lang=lang_code, tld=current_tld, slow=False)
            else:
                # Alternate speeds for non-English languages
                current_slow = False if host_num == 0 else True
                tts = gTTS(text=text, lang=lang_code, slow=current_slow)

            fp = io.BytesIO()
            tts.write_to_fp(fp)
            combined_bytes += fp.getvalue()
        except Exception as e:
            logger.error(f"Segment TTS Error: {e}")

    if combined_bytes:
        buffer = io.BytesIO(combined_bytes)
        buffer.seek(0)
        return buffer
    return None
