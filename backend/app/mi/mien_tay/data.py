"""
Miền Tây Vietnamese Human Communication & Cultural Intelligence Database

A living database of Southern/Mekong Delta language patterns.
NOT a dictionary — a human communication & emotional culture system.

Categories:
  SLANG            — word-level regional vocabulary
  REACTIONS        — exclamations, emotional outbursts
  EMOTIONAL        — intensity markers + emotional graph
  SOFT_NEGOTIATION — indirect communication patterns
  HUMOR            — playful exaggeration markers
  SOCIAL_WARMTH    — affectionate/warm social phrases
  FOOD_CULTURE     — food, drinking, lai rai culture
  DRINKING         — social drinking patterns
  PRONOUNS         — regional pronoun variations
  NO_ACCENT        — no-accent form mappings
  TYPOS            — extended typo normalization
  PACING           — rhythm/pacing markers
  RELATIONSHIP     — relationship tone signals
  CONTEXTUAL       — contextual interpretation rules
  EXAGGERATION     — hyperbole patterns
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


# ── Enums ─────────────────────────────────────────────────────────────────────

class EmotionalSignal(str, Enum):
    SURPRISE       = "surprise"
    FATIGUE        = "fatigue"
    STRESS         = "stress"
    HUMOR          = "humor"
    WARMTH         = "warmth"
    EXAGGERATION   = "exaggeration"
    SOFT_REJECT    = "soft_reject"
    INVITATION     = "invitation"
    COMPLAINT      = "complaint"
    EXCITEMENT     = "excitement"
    DISCOMFORT     = "discomfort"
    AFFECTION      = "affection"
    CONFUSION      = "confusion"
    RESIGNATION    = "resignation"
    PLAYFUL        = "playful"


class ResponseTone(str, Enum):
    WARM_CASUAL   = "warm_casual"
    PLAYFUL       = "playful"
    SOFT          = "soft"
    EMPATHETIC    = "empathetic"
    LAI_RAI       = "lai_rai"    # relaxed social pacing
    TEASING       = "teasing"    # light humor back


@dataclass
class SlangEntry:
    """A single Miền Tây slang term with full linguistic metadata."""
    term: str
    standard_vn: str                          # standard Vietnamese equivalent
    meaning: str                              # human meaning / intent signal
    signals: list[EmotionalSignal]            # emotional tags
    intensity: float                          # 0.0–1.0 emotional weight
    literal: bool = False                     # False = do NOT interpret literally
    no_accent_forms: list[str] = field(default_factory=list)
    typo_forms: list[str] = field(default_factory=list)
    response_tone: ResponseTone = ResponseTone.WARM_CASUAL


@dataclass
class EmotionalMarker:
    """Phrase → emotional graph node."""
    phrase: str
    signals: list[EmotionalSignal]
    intensity: float                          # 0.0–1.0
    literal: bool = False
    infer: list[str] = field(default_factory=list)   # what to infer from this
    response_tone: ResponseTone = ResponseTone.WARM_CASUAL
    no_accent: str = ""
    typo_forms: list[str] = field(default_factory=list)


# ── REACTIONS database ─────────────────────────────────────────────────────────
# Strong emotional outbursts — NEVER literal, always emotional intensity signals

REACTIONS: list[EmotionalMarker] = [
    EmotionalMarker(
        phrase="mèn đét ơi",
        signals=[EmotionalSignal.SURPRISE, EmotionalSignal.EXAGGERATION],
        intensity=0.85, literal=False,
        infer=["high emotional intensity", "surprise or shock", "may need acknowledgement"],
        response_tone=ResponseTone.WARM_CASUAL,
        no_accent="men det oi",
        typo_forms=["men det oi", "ménnn đétttt", "men dettt", "mennn det"],
    ),
    EmotionalMarker(
        phrase="trời quơi",
        signals=[EmotionalSignal.SURPRISE, EmotionalSignal.EXAGGERATION, EmotionalSignal.STRESS],
        intensity=0.80, literal=False,
        infer=["overwhelmed", "something unexpected happened", "needs empathy"],
        response_tone=ResponseTone.EMPATHETIC,
        no_accent="troi quoi",
        typo_forms=["troi quoiii", "trời quơiiiii"],
    ),
    EmotionalMarker(
        phrase="má ơi",
        signals=[EmotionalSignal.SURPRISE, EmotionalSignal.EXAGGERATION, EmotionalSignal.DISCOMFORT],
        intensity=0.80, literal=False,
        infer=["shock or dismay", "something overwhelming", "Southern emotional release"],
        response_tone=ResponseTone.WARM_CASUAL,
        no_accent="ma oi",
        typo_forms=["ma oiii", "má ơiiiii"],
    ),
    EmotionalMarker(
        phrase="chết cha",
        signals=[EmotionalSignal.SURPRISE, EmotionalSignal.STRESS, EmotionalSignal.EXAGGERATION],
        intensity=0.85, literal=False,
        infer=["something went wrong", "stressed or alarmed", "needs help or sympathy"],
        response_tone=ResponseTone.EMPATHETIC,
        no_accent="chet cha",
        typo_forms=["chet chaaaa", "chết chaaaaa"],
    ),
    EmotionalMarker(
        phrase="dữ thần",
        signals=[EmotionalSignal.EXAGGERATION, EmotionalSignal.SURPRISE],
        intensity=0.75, literal=False,
        infer=["intensifier — something is very extreme", "emphasis on degree"],
        response_tone=ResponseTone.PLAYFUL,
        no_accent="du than",
        typo_forms=["dữ thầnnn", "du thannnn"],
    ),
    EmotionalMarker(
        phrase="dữ dằn",
        signals=[EmotionalSignal.EXAGGERATION, EmotionalSignal.SURPRISE],
        intensity=0.70, literal=False,
        infer=["something is very intense or extreme", "amplifier"],
        response_tone=ResponseTone.PLAYFUL,
        no_accent="du dan",
    ),
    EmotionalMarker(
        phrase="trời đất quỷ thần ơi",
        signals=[EmotionalSignal.SURPRISE, EmotionalSignal.EXAGGERATION, EmotionalSignal.STRESS],
        intensity=0.95, literal=False,
        infer=["maximum emotional intensity", "completely overwhelmed", "urgent empathy needed"],
        response_tone=ResponseTone.EMPATHETIC,
        no_accent="troi dat quy than oi",
    ),
    EmotionalMarker(
        phrase="trời ơi đất hỡi",
        signals=[EmotionalSignal.SURPRISE, EmotionalSignal.EXAGGERATION, EmotionalSignal.STRESS],
        intensity=0.90, literal=False,
        infer=["extremely overwhelmed", "very dramatic emphasis"],
        response_tone=ResponseTone.EMPATHETIC,
        no_accent="troi oi dat hoi",
    ),
    EmotionalMarker(
        phrase="quá cha nội",
        signals=[EmotionalSignal.EXAGGERATION, EmotionalSignal.HUMOR, EmotionalSignal.SURPRISE],
        intensity=0.75, literal=False,
        infer=["playful exaggeration", "something is ridiculously extreme"],
        response_tone=ResponseTone.PLAYFUL,
        no_accent="qua cha noi",
        typo_forms=["qua cha noiiii", "quá cha nộiiii"],
    ),
    EmotionalMarker(
        phrase="quá trời quá đất",
        signals=[EmotionalSignal.EXAGGERATION, EmotionalSignal.HUMOR],
        intensity=0.75, literal=False,
        infer=["extreme emphasis", "playful exaggeration"],
        response_tone=ResponseTone.PLAYFUL,
        no_accent="qua troi qua dat",
    ),
    EmotionalMarker(
        phrase="ghê dữ",
        signals=[EmotionalSignal.SURPRISE, EmotionalSignal.EXAGGERATION],
        intensity=0.65, literal=False,
        infer=["something is intense or impressive", "Southern amplifier"],
        response_tone=ResponseTone.WARM_CASUAL,
        no_accent="ghe du",
        typo_forms=["ghê dữzzz", "gheee duuu"],
    ),
    EmotionalMarker(
        phrase="thiệt luôn á hả",
        signals=[EmotionalSignal.SURPRISE, EmotionalSignal.WARMTH],
        intensity=0.60, literal=False,
        infer=["genuine surprise", "seeking confirmation", "warm disbelief"],
        response_tone=ResponseTone.WARM_CASUAL,
        no_accent="thiet luon a ha",
    ),
    EmotionalMarker(
        phrase="ủa alo",
        signals=[EmotionalSignal.SURPRISE, EmotionalSignal.CONFUSION, EmotionalSignal.HUMOR],
        intensity=0.55, literal=False,
        infer=["mild surprise or confusion", "playful 'are you serious?'"],
        response_tone=ResponseTone.PLAYFUL,
        no_accent="ua alo",
    ),
]


# ── SLANG database ─────────────────────────────────────────────────────────────

SLANG: list[SlangEntry] = [
    # Core Miền Tây vocabulary
    SlangEntry(
        term="hông ấy",
        standard_vn="không à",
        meaning="soft indirect question / invitation — very low pressure",
        signals=[EmotionalSignal.INVITATION, EmotionalSignal.SOFT_REJECT],
        intensity=0.3, literal=False,
        no_accent_forms=["hong ay", "hong a"],
        response_tone=ResponseTone.SOFT,
    ),
    SlangEntry(
        term="hong ấy",
        standard_vn="không à",
        meaning="same as hông ấy — soft indirect question",
        signals=[EmotionalSignal.INVITATION],
        intensity=0.3, literal=False,
        no_accent_forms=["hong ay"],
        response_tone=ResponseTone.SOFT,
    ),
    SlangEntry(
        term="hay vầy đi",
        standard_vn="hay vậy đi / như thế này đi",
        meaning="collaborative soft suggestion — 'how about this instead?'",
        signals=[EmotionalSignal.INVITATION, EmotionalSignal.SOFT_REJECT],
        intensity=0.4, literal=True,
        no_accent_forms=["hay vay di"],
        response_tone=ResponseTone.SOFT,
    ),
    SlangEntry(
        term="mắc cười ghê",
        standard_vn="buồn cười quá",
        meaning="something is really funny — Southern humor marker",
        signals=[EmotionalSignal.HUMOR, EmotionalSignal.PLAYFUL],
        intensity=0.65, literal=False,
        no_accent_forms=["mac cuoi ghe"],
        response_tone=ResponseTone.PLAYFUL,
    ),
    SlangEntry(
        term="thiệt tình luôn",
        standard_vn="thật sự luôn",
        meaning="genuine exasperation or genuine affirmation",
        signals=[EmotionalSignal.EXAGGERATION, EmotionalSignal.COMPLAINT],
        intensity=0.60, literal=False,
        no_accent_forms=["thiet tinh luon"],
        response_tone=ResponseTone.WARM_CASUAL,
    ),
    SlangEntry(
        term="muốn xỉu",
        standard_vn="muốn ngất",
        meaning="extreme fatigue / overwhelming situation — NOT literal",
        signals=[EmotionalSignal.FATIGUE, EmotionalSignal.EXAGGERATION],
        intensity=0.80, literal=False,
        no_accent_forms=["muon xiu"],
        typo_forms=["muốn xiuuuu", "muon xiuuu"],
        response_tone=ResponseTone.EMPATHETIC,
    ),
    SlangEntry(
        term="muốn chết",
        standard_vn="kiệt sức / quá mức",
        meaning="extreme fatigue or frustration — hyperbole, NOT literal",
        signals=[EmotionalSignal.FATIGUE, EmotionalSignal.EXAGGERATION, EmotionalSignal.STRESS],
        intensity=0.85, literal=False,
        no_accent_forms=["muon chet"],
        response_tone=ResponseTone.EMPATHETIC,
    ),
    SlangEntry(
        term="xỉu up xỉu down",
        standard_vn="mệt cực kỳ / kiệt sức hoàn toàn",
        meaning="absolute exhaustion — playful hyperbole",
        signals=[EmotionalSignal.FATIGUE, EmotionalSignal.HUMOR, EmotionalSignal.EXAGGERATION],
        intensity=0.85, literal=False,
        no_accent_forms=["xiu up xiu down"],
        typo_forms=["xỉuuu up xỉuuu down"],
        response_tone=ResponseTone.EMPATHETIC,
    ),
    SlangEntry(
        term="mệt dữ",
        standard_vn="mệt lắm",
        meaning="genuinely very tired — Southern intensifier",
        signals=[EmotionalSignal.FATIGUE],
        intensity=0.70, literal=True,
        no_accent_forms=["met du"],
        response_tone=ResponseTone.EMPATHETIC,
    ),
    SlangEntry(
        term="mệt ngang",
        standard_vn="mệt ngang người",
        meaning="extremely tired — humor + real exhaustion",
        signals=[EmotionalSignal.FATIGUE, EmotionalSignal.HUMOR],
        intensity=0.75, literal=False,
        no_accent_forms=["met ngang"],
        response_tone=ResponseTone.EMPATHETIC,
    ),
    SlangEntry(
        term="mắc mệt ghê",
        standard_vn="mệt ghê luôn",
        meaning="strong exhaustion with Southern flavor",
        signals=[EmotionalSignal.FATIGUE, EmotionalSignal.COMPLAINT],
        intensity=0.70, literal=True,
        no_accent_forms=["mac met ghe"],
        response_tone=ResponseTone.EMPATHETIC,
    ),
    SlangEntry(
        term="xỉu thiệt chớ",
        standard_vn="mệt thật sự",
        meaning="genuine exhaustion, not joking",
        signals=[EmotionalSignal.FATIGUE],
        intensity=0.80, literal=True,
        no_accent_forms=["xiu thiet cho"],
        response_tone=ResponseTone.EMPATHETIC,
    ),
    SlangEntry(
        term="dữ hông",
        standard_vn="dữ không / ghê không",
        meaning="isn't it intense/extreme? — seeking confirmation",
        signals=[EmotionalSignal.SURPRISE, EmotionalSignal.EXAGGERATION],
        intensity=0.55, literal=False,
        no_accent_forms=["du hong"],
        response_tone=ResponseTone.WARM_CASUAL,
    ),
    SlangEntry(
        term="ghê hông",
        standard_vn="ghê không / kinh không",
        meaning="isn't it scary/extreme? — Southern confirmation seeker",
        signals=[EmotionalSignal.SURPRISE, EmotionalSignal.EXAGGERATION],
        intensity=0.55, literal=False,
        no_accent_forms=["ghe hong"],
        typo_forms=["ghê honggg", "gheee hong"],
        response_tone=ResponseTone.PLAYFUL,
    ),
    SlangEntry(
        term="gì kỳ vậy trời",
        standard_vn="cái gì kỳ lạ vậy trời",
        meaning="confused or amused by something strange",
        signals=[EmotionalSignal.CONFUSION, EmotionalSignal.HUMOR],
        intensity=0.60, literal=False,
        no_accent_forms=["gi ky vay troi"],
        response_tone=ResponseTone.PLAYFUL,
    ),
    SlangEntry(
        term="dễ sợ thiệt",
        standard_vn="đáng sợ / kinh thật",
        meaning="Southern way of saying 'wow that's intense/scary/extreme'",
        signals=[EmotionalSignal.SURPRISE, EmotionalSignal.EXAGGERATION],
        intensity=0.65, literal=False,
        no_accent_forms=["de so thiet"],
        response_tone=ResponseTone.WARM_CASUAL,
    ),
    SlangEntry(
        term="nghe cưng",
        standard_vn="nghe thương / dễ thương lắm",
        meaning="that sounds cute/sweet — warm affection",
        signals=[EmotionalSignal.AFFECTION, EmotionalSignal.WARMTH],
        intensity=0.60, literal=True,
        no_accent_forms=["nghe cung"],
        response_tone=ResponseTone.WARM_CASUAL,
    ),
    SlangEntry(
        term="thấy ghê",
        standard_vn="thấy kinh / thấy sợ",
        meaning="that's wild/extreme — Southern intensifier",
        signals=[EmotionalSignal.SURPRISE, EmotionalSignal.EXAGGERATION],
        intensity=0.60, literal=False,
        no_accent_forms=["thay ghe"],
        response_tone=ResponseTone.PLAYFUL,
    ),
    SlangEntry(
        term="quải chè đậu",
        standard_vn="trời ơi / thôi chết",
        meaning="playful Southern exclamation — humor + mild exasperation",
        signals=[EmotionalSignal.HUMOR, EmotionalSignal.PLAYFUL, EmotionalSignal.SURPRISE],
        intensity=0.65, literal=False,
        no_accent_forms=["quai che dau"],
        response_tone=ResponseTone.PLAYFUL,
    ),
    SlangEntry(
        term="căng à nghen",
        standard_vn="căng thẳng đó nhé",
        meaning="that's tense/intense — acknowledging a difficult situation warmly",
        signals=[EmotionalSignal.STRESS, EmotionalSignal.WARMTH],
        intensity=0.60, literal=True,
        no_accent_forms=["cang a nghen"],
        response_tone=ResponseTone.EMPATHETIC,
    ),
    SlangEntry(
        term="xạo ke",
        standard_vn="xạo / nói bậy",
        meaning="you're joking / that can't be right — playful disbelief",
        signals=[EmotionalSignal.HUMOR, EmotionalSignal.SURPRISE],
        intensity=0.55, literal=False,
        no_accent_forms=["xao ke"],
        response_tone=ResponseTone.PLAYFUL,
    ),
    SlangEntry(
        term="lầy dữ",
        standard_vn="lầy lội / hài hước dữ",
        meaning="hilariously extra / very playful",
        signals=[EmotionalSignal.HUMOR, EmotionalSignal.PLAYFUL],
        intensity=0.60, literal=False,
        no_accent_forms=["lay du"],
        response_tone=ResponseTone.PLAYFUL,
    ),
    SlangEntry(
        term="hông biết nữa",
        standard_vn="không biết nữa",
        meaning="genuinely confused or indifferent — soft resignation",
        signals=[EmotionalSignal.CONFUSION, EmotionalSignal.RESIGNATION],
        intensity=0.45, literal=True,
        no_accent_forms=["hong biet nua"],
        response_tone=ResponseTone.SOFT,
    ),
    SlangEntry(
        term="thôi kệ đi",
        standard_vn="thôi kệ đi / cứ vậy đi",
        meaning="let it go / doesn't matter — Southern resignation/acceptance",
        signals=[EmotionalSignal.RESIGNATION],
        intensity=0.40, literal=True,
        no_accent_forms=["thoi ke di"],
        response_tone=ResponseTone.SOFT,
    ),
    SlangEntry(
        term="quạo à nha",
        standard_vn="bực lắm đó nhé",
        meaning="genuinely annoyed — mild anger with Southern softener",
        signals=[EmotionalSignal.COMPLAINT, EmotionalSignal.STRESS],
        intensity=0.65, literal=True,
        no_accent_forms=["quao a nha"],
        response_tone=ResponseTone.EMPATHETIC,
    ),
    SlangEntry(
        term="muốn đi bụi luôn",
        standard_vn="muốn bỏ đi / chạy trốn hết",
        meaning="so fed up want to run away — humorous exaggeration",
        signals=[EmotionalSignal.FATIGUE, EmotionalSignal.HUMOR, EmotionalSignal.EXAGGERATION],
        intensity=0.80, literal=False,
        no_accent_forms=["muon di bui luon"],
        response_tone=ResponseTone.EMPATHETIC,
    ),
    SlangEntry(
        term="dzậy",
        standard_vn="vậy",
        meaning="so / like that — general Southern particle",
        signals=[EmotionalSignal.WARMTH],
        intensity=0.15, literal=True,
        no_accent_forms=["vay", "day"],
        response_tone=ResponseTone.WARM_CASUAL,
    ),
    SlangEntry(
        term="dzô",
        standard_vn="vô / vào",
        meaning="go in / come in — casual Southern direction",
        signals=[EmotionalSignal.WARMTH],
        intensity=0.15, literal=True,
        no_accent_forms=["vo", "do"],
        response_tone=ResponseTone.WARM_CASUAL,
    ),
    SlangEntry(
        term="hông",
        standard_vn="không",
        meaning="no / not — standard Southern negation",
        signals=[EmotionalSignal.SOFT_REJECT],
        intensity=0.20, literal=True,
        no_accent_forms=["hong"],
        typo_forms=["honggg", "hôngg"],
        response_tone=ResponseTone.WARM_CASUAL,
    ),
    SlangEntry(
        term="hổng",
        standard_vn="không",
        meaning="no / not — variant Southern negation",
        signals=[EmotionalSignal.SOFT_REJECT],
        intensity=0.20, literal=True,
        no_accent_forms=["hong"],
        response_tone=ResponseTone.WARM_CASUAL,
    ),
    SlangEntry(
        term="thiệt tình",
        standard_vn="thật sự / thật mà",
        meaning="I'm serious / honestly — earnest Southern emphasis",
        signals=[EmotionalSignal.WARMTH, EmotionalSignal.EXAGGERATION],
        intensity=0.50, literal=False,
        no_accent_forms=["thiet tinh"],
        response_tone=ResponseTone.WARM_CASUAL,
    ),
]


# ── SOFT NEGOTIATION patterns ──────────────────────────────────────────────────
# Miền Tây avoids direct confrontation — these are indirect communication tools

SOFT_NEGOTIATION: list[EmotionalMarker] = [
    EmotionalMarker(
        phrase="hay vầy đi",
        signals=[EmotionalSignal.INVITATION, EmotionalSignal.SOFT_REJECT],
        intensity=0.40, literal=True,
        infer=["user is proposing an alternative", "collaborative negotiation", "soft re-direction"],
        response_tone=ResponseTone.SOFT,
        no_accent="hay vay di",
    ),
    EmotionalMarker(
        phrase="thôi mình đổi nhẹ ha",
        signals=[EmotionalSignal.SOFT_REJECT, EmotionalSignal.INVITATION],
        intensity=0.40, literal=True,
        infer=["user wants to change plan", "low-pressure suggestion", "open to alternatives"],
        response_tone=ResponseTone.SOFT,
        no_accent="thoi minh doi nhe ha",
    ),
    EmotionalMarker(
        phrase="hông ấy",
        signals=[EmotionalSignal.INVITATION, EmotionalSignal.SOFT_REJECT],
        intensity=0.30, literal=False,
        infer=["very soft indirect question", "user is gauging interest", "no pressure intended"],
        response_tone=ResponseTone.SOFT,
        no_accent="hong ay",
    ),
    EmotionalMarker(
        phrase="để coi sao nha",
        signals=[EmotionalSignal.RESIGNATION, EmotionalSignal.SOFT_REJECT],
        intensity=0.30, literal=True,
        infer=["user is uncertain", "wants to wait and see", "no urgency"],
        response_tone=ResponseTone.SOFT,
        no_accent="de coi sao nha",
    ),
    EmotionalMarker(
        phrase="từ từ tính",
        signals=[EmotionalSignal.RESIGNATION],
        intensity=0.25, literal=True,
        infer=["user needs more time", "don't rush them", "slow pacing preferred"],
        response_tone=ResponseTone.SOFT,
        no_accent="tu tu tinh",
    ),
    EmotionalMarker(
        phrase="tính sau hen",
        signals=[EmotionalSignal.RESIGNATION, EmotionalSignal.SOFT_REJECT],
        intensity=0.25, literal=True,
        infer=["user wants to defer", "not urgent", "soft decline of immediate action"],
        response_tone=ResponseTone.SOFT,
        no_accent="tinh sau hen",
    ),
    EmotionalMarker(
        phrase="thôi kệ heng",
        signals=[EmotionalSignal.RESIGNATION],
        intensity=0.35, literal=True,
        infer=["user is letting go", "accepting situation", "doesn't want more action"],
        response_tone=ResponseTone.SOFT,
        no_accent="thoi ke heng",
    ),
    EmotionalMarker(
        phrase="tính sao cũng được",
        signals=[EmotionalSignal.RESIGNATION, EmotionalSignal.WARMTH],
        intensity=0.20, literal=True,
        infer=["user is easy-going", "no strong preference", "defer to companion"],
        response_tone=ResponseTone.WARM_CASUAL,
        no_accent="tinh sao cung duoc",
    ),
    EmotionalMarker(
        phrase="cũng được nhen",
        signals=[EmotionalSignal.WARMTH, EmotionalSignal.RESIGNATION],
        intensity=0.20, literal=True,
        infer=["soft agreement", "flexible", "easy-going"],
        response_tone=ResponseTone.WARM_CASUAL,
        no_accent="cung duoc nhen",
    ),
    EmotionalMarker(
        phrase="thôi được rồi nha",
        signals=[EmotionalSignal.RESIGNATION, EmotionalSignal.WARMTH],
        intensity=0.30, literal=True,
        infer=["user accepts a solution", "satisfied enough to move on"],
        response_tone=ResponseTone.WARM_CASUAL,
        no_accent="thoi duoc roi nha",
    ),
]


# ── HUMOR markers ─────────────────────────────────────────────────────────────
# Playful exaggeration — detect to respond playfully not literally

HUMOR_MARKERS: list[EmotionalMarker] = [
    EmotionalMarker(
        phrase="quải chè đậu",
        signals=[EmotionalSignal.HUMOR, EmotionalSignal.PLAYFUL],
        intensity=0.65, literal=False,
        infer=["user is in playful mood", "light humor", "respond with warmth + play"],
        response_tone=ResponseTone.PLAYFUL,
        no_accent="quai che dau",
    ),
    EmotionalMarker(
        phrase="xỉu up xỉu down",
        signals=[EmotionalSignal.HUMOR, EmotionalSignal.FATIGUE, EmotionalSignal.EXAGGERATION],
        intensity=0.80, literal=False,
        infer=["playful exhaustion", "humor + real tiredness", "empathize but stay light"],
        response_tone=ResponseTone.EMPATHETIC,
        no_accent="xiu up xiu down",
        typo_forms=["xiu up xiu downnn"],
    ),
    EmotionalMarker(
        phrase="mắc cười ghê",
        signals=[EmotionalSignal.HUMOR, EmotionalSignal.PLAYFUL],
        intensity=0.65, literal=False,
        infer=["user finds something funny", "respond with matching lightness"],
        response_tone=ResponseTone.PLAYFUL,
        no_accent="mac cuoi ghe",
    ),
    EmotionalMarker(
        phrase="mệt ngang",
        signals=[EmotionalSignal.FATIGUE, EmotionalSignal.HUMOR],
        intensity=0.70, literal=False,
        infer=["real exhaustion expressed humorously", "empathize + don't overcomplicate"],
        response_tone=ResponseTone.EMPATHETIC,
        no_accent="met ngang",
    ),
    EmotionalMarker(
        phrase="xạo ke",
        signals=[EmotionalSignal.HUMOR, EmotionalSignal.SURPRISE],
        intensity=0.55, literal=False,
        infer=["playful disbelief", "respond with matching playfulness"],
        response_tone=ResponseTone.PLAYFUL,
        no_accent="xao ke",
    ),
    EmotionalMarker(
        phrase="lầy dữ",
        signals=[EmotionalSignal.HUMOR, EmotionalSignal.PLAYFUL],
        intensity=0.60, literal=False,
        infer=["user appreciates humor", "safe to be more playful in response"],
        response_tone=ResponseTone.PLAYFUL,
        no_accent="lay du",
    ),
    EmotionalMarker(
        phrase="muốn đi bụi luôn",
        signals=[EmotionalSignal.HUMOR, EmotionalSignal.FATIGUE, EmotionalSignal.EXAGGERATION],
        intensity=0.75, literal=False,
        infer=["humorous exasperation", "user venting playfully", "empathize + light touch"],
        response_tone=ResponseTone.EMPATHETIC,
        no_accent="muon di bui luon",
    ),
    EmotionalMarker(
        phrase="gì kỳ vậy trời",
        signals=[EmotionalSignal.HUMOR, EmotionalSignal.CONFUSION],
        intensity=0.55, literal=False,
        infer=["amused confusion", "something weird happened", "respond with curiosity + warmth"],
        response_tone=ResponseTone.PLAYFUL,
        no_accent="gi ky vay troi",
    ),
]


# ── SOCIAL WARMTH phrases ──────────────────────────────────────────────────────

SOCIAL_WARMTH: list[EmotionalMarker] = [
    EmotionalMarker(
        phrase="nghe cưng",
        signals=[EmotionalSignal.AFFECTION, EmotionalSignal.WARMTH],
        intensity=0.60, literal=True,
        infer=["warm affection expressed", "user is in a good social mood"],
        response_tone=ResponseTone.WARM_CASUAL,
        no_accent="nghe cung",
    ),
    EmotionalMarker(
        phrase="dễ thương dữ",
        signals=[EmotionalSignal.AFFECTION, EmotionalSignal.WARMTH, EmotionalSignal.EXAGGERATION],
        intensity=0.65, literal=False,
        infer=["strong affection", "user is feeling warm toward someone/something"],
        response_tone=ResponseTone.WARM_CASUAL,
        no_accent="de thuong du",
    ),
    EmotionalMarker(
        phrase="thiệt tình",
        signals=[EmotionalSignal.WARMTH, EmotionalSignal.EXAGGERATION],
        intensity=0.50, literal=False,
        infer=["genuine sincerity marker", "user being earnest"],
        response_tone=ResponseTone.WARM_CASUAL,
        no_accent="thiet tinh",
    ),
    EmotionalMarker(
        phrase="thương ghê",
        signals=[EmotionalSignal.AFFECTION, EmotionalSignal.WARMTH],
        intensity=0.70, literal=False,
        infer=["strong warm affection", "user cares about the subject"],
        response_tone=ResponseTone.WARM_CASUAL,
        no_accent="thuong ghe",
    ),
    EmotionalMarker(
        phrase="thấy cưng",
        signals=[EmotionalSignal.AFFECTION, EmotionalSignal.WARMTH],
        intensity=0.60, literal=False,
        infer=["finding something cute/endearing", "warm social mood"],
        response_tone=ResponseTone.WARM_CASUAL,
        no_accent="thay cung",
    ),
    EmotionalMarker(
        phrase="thương dữ thần",
        signals=[EmotionalSignal.AFFECTION, EmotionalSignal.WARMTH, EmotionalSignal.EXAGGERATION],
        intensity=0.80, literal=False,
        infer=["very strong affection expressed", "peak Southern warmth"],
        response_tone=ResponseTone.WARM_CASUAL,
        no_accent="thuong du than",
    ),
    EmotionalMarker(
        phrase="cưng dữ",
        signals=[EmotionalSignal.AFFECTION, EmotionalSignal.WARMTH],
        intensity=0.65, literal=False,
        infer=["very cute/endearing", "warm social tone"],
        response_tone=ResponseTone.WARM_CASUAL,
        no_accent="cung du",
    ),
]


# ── FOOD & DRINKING culture ────────────────────────────────────────────────────

FOOD_CULTURE: dict[str, dict] = {
    # Social drinking terms
    "nhậu hông": {
        "meaning": "want to go drinking together? — very casual social invitation",
        "signals": [EmotionalSignal.INVITATION, EmotionalSignal.WARMTH],
        "infer": ["social bonding invitation", "low-pressure", "respond with enthusiasm or gentle alternative"],
        "no_accent": "nhau hong",
        "category": "drinking",
    },
    "làm vài lon": {
        "meaning": "have a few cans — casual drinking invitation",
        "signals": [EmotionalSignal.INVITATION, EmotionalSignal.WARMTH],
        "infer": ["social drinking", "relaxed evening activity", "group bonding"],
        "no_accent": "lam vai lon",
        "category": "drinking",
    },
    "kiếm mồi": {
        "meaning": "find something to eat with drinks — drinking culture food",
        "signals": [EmotionalSignal.WARMTH, EmotionalSignal.INVITATION],
        "infer": ["looking for food to accompany drinks", "social eating"],
        "no_accent": "kiem moi",
        "category": "drinking",
    },
    "quán lai rai": {
        "meaning": "a casual place to drink slowly and relax — Southern slow social culture",
        "signals": [EmotionalSignal.WARMTH, EmotionalSignal.RESIGNATION],
        "infer": ["user wants slow relaxed social time", "not in a rush", "lai rai culture"],
        "no_accent": "quan lai rai",
        "category": "drinking",
    },
    "đồ nhắm": {
        "meaning": "food to go with drinks (appetizers/snacks for drinking session)",
        "signals": [EmotionalSignal.WARMTH],
        "infer": ["looking for drinking food", "social meal context"],
        "no_accent": "do nham",
        "category": "food",
    },
    "quán ruột": {
        "meaning": "a person's go-to favorite local spot — trusted regular place",
        "signals": [EmotionalSignal.WARMTH, EmotionalSignal.AFFECTION],
        "infer": ["user has a trusted spot", "or asking for a reliable local recommendation"],
        "no_accent": "quan ruot",
        "category": "food",
    },
    "cafe võng": {
        "meaning": "hammock cafe — very Southern relaxed cafe culture",
        "signals": [EmotionalSignal.WARMTH, EmotionalSignal.RESIGNATION],
        "infer": ["user wants maximum relaxation", "slow Southern pacing", "healing/rest mode"],
        "no_accent": "cafe vong",
        "category": "cafe",
    },
    "cafe sân vườn": {
        "meaning": "garden cafe — outdoor, relaxed, nature-surrounded",
        "signals": [EmotionalSignal.WARMTH],
        "infer": ["user wants chill outdoor setting", "relaxed atmosphere preferred"],
        "no_accent": "cafe san vuon",
        "category": "cafe",
    },
    "quán local": {
        "meaning": "neighborhood local joint — not touristy, cheap, authentic",
        "signals": [EmotionalSignal.WARMTH],
        "infer": ["user prefers authentic local over tourist-oriented spots"],
        "no_accent": "quan local",
        "category": "food",
    },
    "lai rai": {
        "meaning": "slow relaxed drinking/eating session — Southern cultural rhythm",
        "signals": [EmotionalSignal.WARMTH, EmotionalSignal.RESIGNATION],
        "infer": ["user wants slow pacing", "social relaxation mode", "no rush"],
        "no_accent": "lai rai",
        "category": "drinking",
    },
    "quất vài": {
        "meaning": "down a few drinks — casual drinking",
        "signals": [EmotionalSignal.INVITATION, EmotionalSignal.WARMTH],
        "infer": ["social drinking invitation"],
        "no_accent": "quat vai",
        "category": "drinking",
    },
}


# ── PRONOUNS — regional variations ───────────────────────────────────────────

PRONOUNS: dict[str, dict] = {
    # Southern first-person
    "tui": {"standard": "tôi/tao", "register": "casual", "region": "mien_tay"},
    "tao":  {"standard": "tôi/mình", "register": "very_casual", "region": "southern"},
    "mầy": {"standard": "mày/bạn", "register": "casual", "region": "mien_tay"},
    # Third person
    "ổng":  {"standard": "ông ấy/anh ấy", "register": "casual", "region": "mien_tay"},
    "bả":   {"standard": "bà ấy/chị ấy", "register": "casual", "region": "mien_tay"},
    "ổng bả": {"standard": "họ/cả hai", "register": "casual", "region": "mien_tay"},
    "nó":   {"standard": "nó/người đó", "register": "casual", "region": "southern"},
    "mấy ổng": {"standard": "mấy người đó/họ", "register": "casual", "region": "mien_tay"},
    # Inclusive plural
    "tụi mình": {"standard": "chúng mình/chúng ta", "register": "warm", "region": "southern"},
    "tụi bạn":  {"standard": "các bạn", "register": "warm", "region": "southern"},
    "mấy bạn":  {"standard": "các bạn", "register": "warm", "region": "southern"},
    "tụi em":   {"standard": "chúng em", "register": "warm", "region": "southern"},
}


# ── NO-ACCENT map — Southern specific ─────────────────────────────────────────
# These supplement the base no-accent map with Miền Tây-specific forms

NO_ACCENT_MAP: dict[str, str] = {
    # Core Miền Tây no-accent
    "hong ay":      "hông ấy",
    "hong a":       "hông ấy",
    "men det oi":   "mèn đét ơi",
    "men det":      "mèn đét",
    "du than":      "dữ thần",
    "met ngang":    "mệt ngang",
    "xiu up xiu down": "xỉu up xỉu down",
    "ghe hong":     "ghê hông",
    "hay vay di":   "hay vầy đi",
    "thiet luon a ha": "thiệt luôn á hả",
    "mac cuoi ghe": "mắc cười ghê",
    "thiet tinh luon": "thiệt tình luôn",
    "muon xiu":     "muốn xỉu",
    "muon chet":    "muốn chết",
    "met du":       "mệt dữ",
    "mac met ghe":  "mắc mệt ghê",
    "xiu thiet cho": "xỉu thiệt chớ",
    "du hong":      "dữ hông",
    "gi ky vay troi": "gì kỳ vậy trời",
    "de so thiet":  "dễ sợ thiệt",
    "nghe cung":    "nghe cưng",
    "thay ghe":     "thấy ghê",
    "quai che dau": "quải chè đậu",
    "cang a nghen": "căng à nghen",
    "xao ke":       "xạo ke",
    "lay du":       "lầy dữ",
    "hong biet nua": "hông biết nữa",
    "thoi ke di":   "thôi kệ đi",
    "troi quoi":    "trời quơi",
    "ma oi":        "má ơi",
    "chet cha":     "chết cha",
    "qua cha noi":  "quá cha nội",
    "qua troi qua dat": "quá trời quá đất",
    "ghe du":       "ghê dữ",
    "thiet luon":   "thiệt luôn",
    "ua alo":       "ủa alo",
    "quao a nha":   "quạo à nha",
    "muon di bui luon": "muốn đi bụi luôn",
    "vay nhen":     "vầy nhen",
    "thoi nha":     "thôi nha",
    "thoi ke heng": "thôi kệ heng",
    "de coi sao nha": "để coi sao nha",
    "tu tu tinh":   "từ từ tính",
    "tinh sau hen": "tính sau hen",
    "cung duoc nhen": "cũng được nhen",
    "thuong ghe":   "thương ghê",
    "thay cung":    "thấy cưng",
    "thuong du than": "thương dữ thần",
    "cung du":      "cưng dữ",
    "nghe cung":    "nghe cưng",
    "nhau hong":    "nhậu hông",
    "lam vai lon":  "làm vài lon",
    "kiem moi":     "kiếm mồi",
    "quan lai rai": "quán lai rai",
    "do nham":      "đồ nhắm",
    "quan ruot":    "quán ruột",
    "cafe vong":    "cafe võng",
    "cafe san vuon": "cafe sân vườn",
    "quat vai":     "quất vài",
    # Pronunciation variants
    "dzay":  "vậy",
    "dzậy":  "vậy",
    "dzo":   "vô",
    "dzô":   "vô",
    "dze":   "về",
    "dzề":   "về",
    "dzua":  "vua",
    "hong":  "không",
    "hông":  "không",
    "nhen":  "nhé",
    "nghen": "nhé",
    "hen":   "hé/nhé",
    "ha":    "hả/à",
}


# ── TYPO patterns — Southern internet typing ──────────────────────────────────

TYPO_PATTERNS: dict[str, str] = {
    # Elongated vowels (emphasis)
    "honggg":     "hông",
    "hôngg":      "hông",
    "mennn":      "mèn",
    "dettt":      "đét",
    "duzz":       "dữ",
    "gheee":      "ghê",
    "xiuuuu":     "xỉu",
    "xiuuu":      "xỉu",
    "cunggg":     "cưng",
    "thươnggg":   "thương",
    "mettt":      "mệt",
    "coiii":      "coi",
    "roiii":      "rồi",
    "nhaaa":      "nha",
    "hennn":      "hen",
    "okeeee":     "oke",
    "okeee":      "oke",
    "chettt":     "chết",
    "chaaaa":     "cha",
    "oiii":       "ơi",
    "quoiii":     "quơi",
    "thầnnn":     "thần",
    "thiệttt":    "thiệt",
    "ghêzzz":     "ghê",
    "nghennn":    "nghen",
    "cuiiii":     "cưng",
    "alooo":      "alo",
}


# ── PACING markers ────────────────────────────────────────────────────────────
# These signal desired conversation rhythm

PACING_MARKERS: dict[str, dict] = {
    "lai rai": {
        "pace": "very_slow",
        "infer": "user wants extended relaxed conversation, no rushing",
        "response_style": "short, warm, open-ended",
    },
    "từ từ tính": {
        "pace": "slow",
        "infer": "user needs time, don't push",
        "response_style": "brief, patient, supportive",
    },
    "tính sau hen": {
        "pace": "deferred",
        "infer": "user wants to postpone decision",
        "response_style": "acknowledge, don't push action",
    },
    "để coi": {
        "pace": "slow",
        "infer": "user needs time to think",
        "response_style": "give space, don't overwhelm",
    },
    "thôi kệ": {
        "pace": "closed",
        "infer": "user is done with this topic",
        "response_style": "acknowledge and redirect, don't push",
    },
    "hỏi vậy thôi": {
        "pace": "casual",
        "infer": "user just asking casually, low stakes",
        "response_style": "casual, brief",
    },
    "nhanh nhanh": {
        "pace": "fast",
        "infer": "user wants quick answer",
        "response_style": "direct, short, immediate",
    },
    "mau lên": {
        "pace": "urgent",
        "infer": "user is in a hurry",
        "response_style": "ultra short, immediate answer only",
    },
}


# ── RELATIONSHIP tone signals ──────────────────────────────────────────────────

RELATIONSHIP_TONES: dict[str, dict] = {
    "bạn bè": {
        "warmth": 0.8, "formality": 0.2,
        "mi_style": "casual, peer, equal energy",
        "endings": ["nhen", "nha", "ha", "hen"],
    },
    "anh chị": {
        "warmth": 0.9, "formality": 0.5,
        "mi_style": "warm, slightly respectful, em-style",
        "endings": ["nha anh/chị", "hen anh/chị", "ạ"],
    },
    "người lớn tuổi": {
        "warmth": 0.9, "formality": 0.7,
        "mi_style": "gentle, slower, cô chú style",
        "endings": ["ạ", "nha cô/chú/bác"],
    },
    "khách lạ": {
        "warmth": 0.6, "formality": 0.5,
        "mi_style": "friendly but slightly careful",
        "endings": ["nha", "nhé"],
    },
    "bạn thân": {
        "warmth": 1.0, "formality": 0.1,
        "mi_style": "maximum warmth, full playfulness OK",
        "endings": ["nhen ơi", "nha bạn ơi", "ha"],
    },
    "người mới quen": {
        "warmth": 0.65, "formality": 0.45,
        "mi_style": "warm but measured",
        "endings": ["nha", "nhé"],
    },
}


# ── EXAGGERATION patterns ──────────────────────────────────────────────────────
# These should NEVER be interpreted literally

EXAGGERATION_PHRASES: frozenset[str] = frozenset([
    "muốn xỉu", "muốn chết", "xỉu up xỉu down", "muốn đi bụi luôn",
    "chết cha", "trời ơi đất hỡi", "trời đất quỷ thần ơi",
    "quá trời quá đất", "quá cha nội", "dữ thần", "dữ dằn",
    "mệt ngang", "mắc mệt ghê", "ghê dữ", "dễ sợ thiệt",
    "căng à nghen", "thiệt tình luôn", "thương dữ thần",
    "dễ thương dữ", "cưng dữ", "thấy ghê", "ghê hông",
    "thôi chết rồi", "xỉu thiệt chớ",
])


# ── MI RESPONSE WARMTH SUFFIXES ───────────────────────────────────────────────
# Authentic Southern sentence endings for Mi's responses

WARMTH_SUFFIXES: dict[str, list[str]] = {
    "casual":  ["nhen 😊", "nha", "hen", "heng", "ha"],
    "warm":    ["nhen 😄", "nha bạn ơi", "nhen ơi", "ha 😊"],
    "soft":    ["nha", "hen", "nhen", "nghen"],
    "playful": ["nhen 😄", "he he", "nhen ơi 😄", "ha 😊"],
    "empathetic": ["nha", "nhen", "nghen", "nha bạn 😊"],
}


# ── FAST LOOKUP SETS (built from above data at module load) ───────────────────

def _build_lookup_sets() -> tuple[frozenset, frozenset, frozenset, frozenset, frozenset]:
    """Build frozensets for O(1) membership testing."""
    all_slang_terms: set[str] = set()
    all_reaction_phrases: set[str] = set()
    all_soft_neg_phrases: set[str] = set()
    all_humor_phrases: set[str] = set()
    all_warmth_phrases: set[str] = set()

    for s in SLANG:
        all_slang_terms.add(s.term.lower())
        all_slang_terms.update(f.lower() for f in s.no_accent_forms)
        all_slang_terms.update(f.lower() for f in s.typo_forms)

    for r in REACTIONS:
        all_reaction_phrases.add(r.phrase.lower())
        if r.no_accent:
            all_reaction_phrases.add(r.no_accent.lower())
        all_reaction_phrases.update(f.lower() for f in r.typo_forms)

    for n in SOFT_NEGOTIATION:
        all_soft_neg_phrases.add(n.phrase.lower())
        if n.no_accent:
            all_soft_neg_phrases.add(n.no_accent.lower())

    for h in HUMOR_MARKERS:
        all_humor_phrases.add(h.phrase.lower())
        if h.no_accent:
            all_humor_phrases.add(h.no_accent.lower())

    for w in SOCIAL_WARMTH:
        all_warmth_phrases.add(w.phrase.lower())
        if w.no_accent:
            all_warmth_phrases.add(w.no_accent.lower())

    return (
        frozenset(all_slang_terms),
        frozenset(all_reaction_phrases),
        frozenset(all_soft_neg_phrases),
        frozenset(all_humor_phrases),
        frozenset(all_warmth_phrases),
    )


(
    SLANG_LOOKUP,
    REACTION_LOOKUP,
    SOFT_NEG_LOOKUP,
    HUMOR_LOOKUP,
    WARMTH_LOOKUP,
) = _build_lookup_sets()


# ── MIEN TAY DIALECT MARKERS — expanded ───────────────────────────────────────
# Used for fast dialect detection

DIALECT_MARKERS: frozenset[str] = frozenset([
    # Core markers (4+ chars to avoid substring false positives)
    "hông", "hổng", "dzậy", "dzô", "dzề",
    "nhen", "nghen", "heng",
    "ổng", "bả", "tui", "mầy", "nà", "thía",
    # Multi-word markers (safe — too long to false-positive)
    "vậy nhen", "thôi nha", "cái này nè", "mà nè",
    "mèn đét", "trời quơi", "má ơi", "quải chè đậu",
    "hay vầy đi", "hông ấy", "hong ấy", "thiệt tình",
    "muốn xỉu", "mắc cười", "ghê dữ", "dữ thần",
    "lai rai", "nhậu hông", "quán ruột", "cafe võng",
    "mầy tui", "tụi mình", "tụi bạn",
    "lầy dữ", "xạo ke", "căng à nghen",
    "xỉu up xỉu down", "xiu up xiu down",
    "thương ghê", "thuong ghe", "thấy cưng", "thay cung",
    "thương dữ thần", "dễ thương dữ",
    "muốn đi bụi luôn", "muon di bui luon",
    "mệt ngang", "met ngang", "mắc mệt ghê", "mac met ghe",
    "quạo à nha", "gì kỳ vậy trời",
    "thôi kệ đi", "thôi kệ heng", "thoi ke heng",
    "hông biết nữa", "hong biet nua",
    "tính sau hen", "từ từ tính", "để coi sao nha",
    "thiệt tình luôn", "thiet tinh luon",
    "xạo ke", "xao ke", "lầy dữ", "lay du",
    "quá cha nội", "qua cha noi",
    # No-accent forms (4+ chars only to be safe)
    "hong", "nhen", "nghe",
    "men det", "troi quoi", "ma oi",
    "hay vay di", "hong ay",
    "dzay", "dzậy", "nhau hong",
])
