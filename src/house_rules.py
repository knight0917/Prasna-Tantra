"""
src/house_rules.py
Registry-based house-specific operational rules derived from Prasna Tantra.
"""

from __future__ import annotations

from dataclasses import dataclass

NATURAL_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
NATURAL_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
SIGN_TYPES = {
    "Aries": "Movable",
    "Cancer": "Movable",
    "Libra": "Movable",
    "Capricorn": "Movable",
    "Taurus": "Fixed",
    "Leo": "Fixed",
    "Scorpio": "Fixed",
    "Aquarius": "Fixed",
    "Gemini": "Common",
    "Virgo": "Common",
    "Sagittarius": "Common",
    "Pisces": "Common",
}
ZODIAC = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]


def _get(obj, field, default=None):
    if isinstance(obj, dict):
        return obj.get(field, default)
    return getattr(obj, field, default)


@dataclass
class RuleResult:
    specific_verdict: str
    specific_factors: list[str]


@dataclass
class RuleContext:
    query_house: int
    positions: dict
    house_lords: dict
    yogas: dict
    house_judgment: dict

    @property
    def lagna_lord(self) -> str | None:
        return self.house_judgment.get("lagna_lord")

    def house_lord(self, house_num: int) -> str | None:
        return self.house_lords.get(str(house_num))

    def planet(self, planet_name: str):
        return self.positions.get(planet_name)

    def planet_house(self, planet_name: str) -> int:
        return int(_get(self.planet(planet_name), "house", -1))

    def planet_sign(self, planet_name: str) -> str:
        return _get(self.planet(planet_name), "sign", "")

    def in_house(self, planet_name: str, house_num: int) -> bool:
        return self.planet_house(planet_name) == house_num

    def planets_in_house(self, house_num: int) -> list[str]:
        return [
            name
            for name, planet in self.positions.items()
            if name != "Ascendant" and int(_get(planet, "house", -1)) == house_num
        ]

    def house_aspected_by(self, house_num: int, planet_names: set[str]) -> bool:
        for planet_name in planet_names:
            planet = self.planet(planet_name)
            if not planet:
                continue
            for aspect in _get(planet, "aspects", []):
                if int(_get(aspect, "target_house", -1)) == house_num:
                    return True
        return False

    def house_aspected_by_benefic(self, house_num: int) -> bool:
        return self.house_aspected_by(house_num, NATURAL_BENEFICS)

    def house_aspected_by_malefic(self, house_num: int) -> bool:
        return self.house_aspected_by(house_num, NATURAL_MALEFICS)

    def has_ithasala(self, planet_a: str | None, planet_b: str | None) -> bool:
        if not planet_a or not planet_b:
            return False
        pair = frozenset({planet_a, planet_b})
        return any(
            frozenset({item.get("faster_planet"), item.get("slower_planet")}) == pair
            for item in self.yogas.get("ithasala", [])
        )

    def has_easarapha(self, planet_a: str | None, planet_b: str | None) -> bool:
        if not planet_a or not planet_b:
            return False
        pair = frozenset({planet_a, planet_b})
        return any(
            frozenset({item.get("faster_planet"), item.get("slower_planet")}) == pair
            for item in self.yogas.get("easarapha", [])
        )

    def has_kamboola(self, planet_a: str | None, planet_b: str | None) -> bool:
        if not planet_a or not planet_b:
            return False
        pair = frozenset({planet_a, planet_b})
        return any(frozenset(item.get("ithasala_pair", [])) == pair for item in self.yogas.get("kamboola", []))


RULE_HANDLERS: dict[int, callable] = {}


def register_house_rule(house_num: int):
    def decorator(func):
        RULE_HANDLERS[house_num] = func
        return func

    return decorator


@register_house_rule(2)
def rule_house_2(ctx: RuleContext) -> RuleResult:
    factors: list[str] = []
    lord2 = ctx.house_lord(2)
    gain_indicated = False
    risk_flag = False

    if ctx.has_ithasala(lord2, ctx.lagna_lord) or ctx.has_ithasala(lord2, "Moon"):
        gain_indicated = True
        factors.append("Lord of 2nd in applying aspect with Lagna lord - gain of money predicted")

    h2_lord_house = ctx.planet_house(lord2) if lord2 else -1
    if h2_lord_house != -1:
        same_house = any(b in ctx.planets_in_house(h2_lord_house) for b in NATURAL_BENEFICS)
        if same_house or ctx.house_aspected_by_benefic(h2_lord_house):
            factors.append("Benefic influence on 2nd lord - financial gain")
            gain_indicated = True

    if any(m in ctx.planets_in_house(2) for m in NATURAL_MALEFICS):
        factors.append("Malefics in 2nd - gain possible but from distant land, with suffering")

    if any(ctx.has_ithasala(lord2, malefic) for malefic in NATURAL_MALEFICS):
        risk_flag = True
        factors.append("Warning: 2nd lord applying to malefic - serious financial risk")

    quad_trine = {1, 4, 5, 7, 9, 10}
    ll_house = ctx.planet_house(ctx.lagna_lord) if ctx.lagna_lord else -1
    moon_house = ctx.planet_house("Moon")
    if ll_house in quad_trine and h2_lord_house in quad_trine and moon_house in quad_trine:
        if (
            (ctx.has_ithasala(ctx.lagna_lord, lord2) or ll_house == h2_lord_house)
            and (ctx.has_ithasala(ctx.lagna_lord, "Moon") or ll_house == moon_house)
            and (ctx.has_ithasala(lord2, "Moon") or h2_lord_house == moon_house)
        ):
            factors.append("Triple conjunction of wealth indicators - immediate gain certain")
            gain_indicated = True

    if moon_house in {4, 7} and ctx.in_house("Sun", 10):
        if any(ctx.in_house(benefic, 1) for benefic in NATURAL_BENEFICS):
            factors.append("Classical wealth yoga present - immediate financial gain")
            gain_indicated = True

    if gain_indicated and not risk_flag:
        verdict = "YES - Dhana is promised; gain may come to hand."
    elif gain_indicated and risk_flag:
        verdict = "YES, WITH EFFORT - Dhana is promised, yet attended by toil or blemish."
    elif risk_flag:
        verdict = "NO - The indications show loss, anxiety, or obstruction in money matters."
    else:
        verdict = "NO - The chart does not clearly promise gain."
    return RuleResult(verdict, factors)


@register_house_rule(7)
def rule_house_7(ctx: RuleContext) -> RuleResult:
    factors: list[str] = []
    lord7 = ctx.house_lord(7)
    lord8 = ctx.house_lord(8)
    lord3 = ctx.house_lord(3)
    lord4 = ctx.house_lord(4)

    r1 = ctx.has_ithasala(ctx.lagna_lord, lord7)
    if r1:
        factors.append("Applying aspect between Lagna lord and 7th lord - marriage will occur")

    r2 = False
    if ctx.in_house(ctx.lagna_lord, 7):
        r2 = True
        factors.append("Lagna lord in 7th - bride secured with effort")
    elif ctx.in_house("Moon", 7):
        r2 = True
        factors.append("Moon in 7th - marriage will happen with some seeking")

    r3 = ctx.has_easarapha(ctx.lagna_lord, "Moon")
    if r3:
        factors.append("Lagna lord in Musaripha with Moon - past romantic connection indicated")

    r4 = False
    l7_house = ctx.planet_house(lord7) if lord7 else -1
    if l7_house != -1:
        for conjoined in ctx.planets_in_house(l7_house):
            if conjoined != lord7:
                planet = ctx.planet(conjoined)
                if _get(planet, "is_combust", False) or ctx.house_aspected_by_malefic(l7_house):
                    r4 = True
                    break
    if r4:
        factors.append("Warning: 7th lord afflicted - obstacles in marriage")

    r5 = False
    if lord8 in NATURAL_MALEFICS:
        p8 = ctx.planet(lord8)
        if p8:
            r5 = any(int(_get(asp, "target_house", -1)) == 7 for asp in _get(p8, "aspects", []))
    if r5:
        factors.append("Warning: 8th lord afflicts 7th - marriage may be blocked or delayed")

    r6 = lord3 in NATURAL_MALEFICS
    if r6:
        factors.append("Brothers may cause obstruction to marriage")

    r7 = lord4 in NATURAL_MALEFICS
    if r7:
        factors.append("Father figure may cause obstruction to marriage")

    r8 = ctx.has_kamboola(ctx.lagna_lord, lord7)
    if r8:
        factors.append("Kamboola Yoga - marriage is strongly indicated and will be auspicious")

    if r1 or r8:
        verdict = "YES - Union is promised."
    elif r2 and not (r4 or r5):
        verdict = "YES, WITH EFFORT - Union may be obtained, though only after effort and seeking."
    elif r4 or r5:
        verdict = "NO - Obstructions prevail against union at present."
    else:
        verdict = "UNCLEAR - The combinations do not permit a firm judgment on union."
    return RuleResult(verdict, factors)


@register_house_rule(6)
def rule_house_6(ctx: RuleContext) -> RuleResult:
    factors: list[str] = []
    lord6 = ctx.house_lord(6)
    lord8 = ctx.house_lord(8)

    r1 = ctx.in_house(lord6, 1) and ctx.in_house(lord8, 1)
    if r1:
        factors.append("CRITICAL: Lords of 6th and 8th in Lagna - life is threatened")

    r2 = ctx.in_house(lord6, 8) and ctx.in_house(lord8, 6)
    if r2:
        factors.append("Lords of 6th and 8th in mutual exchange - speedy recovery indicated")

    r3 = ctx.in_house(ctx.lagna_lord, 6) and ctx.in_house(lord6, 1)
    if r3:
        factors.append("Exchange of Lagna and 6th lords - long suffering, slow recovery")

    r4 = ctx.has_ithasala(ctx.lagna_lord, lord6)
    if r4:
        factors.append("Lagna lord applying to 6th lord - illness will continue until aspect is exact")

    r5 = any(ctx.in_house(benefic, 6) for benefic in NATURAL_BENEFICS)
    if r5:
        factors.append("Benefics in 6th - speedy recovery expected")

    r6 = ctx.house_aspected_by_malefic(6) and ctx.house_aspected_by_malefic(8)
    if r6:
        factors.append("Warning: Malefics afflict both 6th and 8th - recovery unlikely")

    r7 = ctx.planet_house(ctx.lagna_lord) in {1, 5, 9} and ctx.house_aspected_by_benefic(9)
    if r7:
        factors.append("Lagna lord in trine with benefic 9th - recovery after treatment")

    lagna_type = SIGN_TYPES.get(ctx.planet_sign("Ascendant"), "")
    if lagna_type == "Movable":
        factors.append("Movable Lagna - illness will be short")
    elif lagna_type == "Fixed":
        factors.append("Fixed Lagna - illness may be prolonged")
    elif lagna_type == "Common":
        factors.append("Common Lagna - illness of medium duration")

    if r1:
        verdict = "CRITICAL - The chart shows grave danger to life and severe affliction."
    elif r6:
        verdict = "NO - The disease is severe and recovery is doubtful."
    elif r2 or r5:
        verdict = "YES - Recovery is promised."
    elif r3 or r4:
        verdict = "NO - The affliction persists and recovery is delayed."
    elif r7:
        verdict = "YES, WITH EFFORT - Relief may come, though by treatment and time."
    else:
        verdict = "UNCLEAR - The combinations do not permit a firm judgment on recovery."
    return RuleResult(verdict, factors)


@register_house_rule(10)
def rule_house_10(ctx: RuleContext) -> RuleResult:
    factors: list[str] = []
    lord10 = ctx.house_lord(10)

    r1 = ctx.has_ithasala(ctx.lagna_lord, lord10)
    if r1:
        factors.append("Applying aspect between Lagna lord and 10th lord - career success indicated")

    r2 = ctx.planet_house(lord10) in {1, 4, 7, 10}
    if r2:
        factors.append("10th lord in angular house - strong career position")

    r3 = ctx.house_aspected_by_benefic(10)
    if r3:
        factors.append("Benefic aspect on 10th - professional recognition coming")

    r4 = any(m in ctx.planets_in_house(10) for m in NATURAL_MALEFICS)
    if r4:
        factors.append("Malefics in 10th - career obstacles, effort required")

    lagna_planet = ctx.planet(ctx.lagna_lord)
    r5 = _get(lagna_planet, "speed_deg_per_day", 0.0) < 0 and ctx.has_ithasala(ctx.lagna_lord, lord10)
    if r5:
        factors.append("Retrograde Lagna lord applying to 10th lord - job change or reversal likely")

    ll_house = ctx.planet_house(ctx.lagna_lord)
    r6 = ll_house in {1, 4, 7, 10} and not ctx.has_ithasala(ctx.lagna_lord, ctx.house_lord(6)) and not ctx.has_ithasala(ctx.lagna_lord, ctx.house_lord(12))
    if r6:
        factors.append("Stable employment - no change of master indicated")

    r7 = ctx.has_easarapha(lord10, ctx.lagna_lord)
    if r7:
        factors.append("Separating aspect - opportunity may have passed")

    if r1 and not r4:
        verdict = "YES - Advancement in work and station is promised."
    elif r1 and r4:
        verdict = "YES, WITH EFFORT - Advancement is possible, but only after obstruction and labour."
    elif r5:
        verdict = "YES, WITH EFFORT - Change in work is indicated more than settlement in the present post."
    elif r6:
        verdict = "YES - The present station appears stable."
    elif r7:
        verdict = "NO - The present undertaking appears to have slipped away."
    else:
        verdict = "UNCLEAR - The indications for work and station are mixed."
    return RuleResult(verdict, factors)


@register_house_rule(3)
def rule_house_3(ctx: RuleContext) -> RuleResult:
    factors: list[str] = []
    lord3 = ctx.house_lord(3)
    lord6 = ctx.house_lord(6)

    p3 = ctx.planet(lord3)
    lord3_aspects_3 = any(int(_get(asp, "target_house", -1)) == 3 for asp in _get(p3, "aspects", [])) if p3 else False
    r1 = lord3_aspects_3 or ctx.house_aspected_by_benefic(3)
    if r1:
        factors.append("Brothers/sisters are well and happy")

    r2 = _get(p3, "is_combust", False)
    if r2:
        factors.append("Brother faces danger or serious difficulty")

    r3 = ctx.planet_house(lord3) == 6 and ctx.has_ithasala(lord3, lord6)
    if r3:
        factors.append("Brother is ill or in trouble")

    l3_house = ctx.planet_house(lord3)
    l3_afflicted = l3_house != -1 and (
        any(m in ctx.planets_in_house(l3_house) for m in NATURAL_MALEFICS) or ctx.house_aspected_by_malefic(l3_house)
    )
    r4 = l3_house == 8 and l3_afflicted
    if r4:
        factors.append("Brother's life may be in danger")

    r5 = any(m in ctx.planets_in_house(3) for m in NATURAL_MALEFICS)
    if r5:
        factors.append("Discord between querent and siblings")

    r6 = ctx.has_ithasala(lord3, ctx.lagna_lord)
    if r6:
        factors.append("Communication or message will be received favourably")

    r7 = ctx.has_easarapha(lord3, ctx.lagna_lord)
    if r7:
        factors.append("Message or communication has already gone unfavourably")

    if r1 and r6:
        verdict = "YES - The matter of brethren and messages appears favourable."
    elif r2 or r4:
        verdict = "NO - The brother or sister faces grave affliction."
    elif r3:
        verdict = "YES, WITH EFFORT - There is affliction, but not beyond remedy."
    elif r5 and not r1:
        verdict = "NO - Discord is shown in the matter of brethren."
    elif r7:
        verdict = "NO - The message or communication does not prosper."
    else:
        verdict = "UNCLEAR - The combinations do not give a firm judgment on brethren."
    return RuleResult(verdict, factors)


@register_house_rule(4)
def rule_house_4(ctx: RuleContext) -> RuleResult:
    factors: list[str] = []
    lord4 = ctx.house_lord(4)

    r1 = ctx.in_house("Moon", 4) and ctx.has_ithasala(ctx.lagna_lord, "Moon")
    if r1:
        factors.append("Querent will acquire land or property")

    r2 = ctx.has_ithasala(lord4, ctx.lagna_lord)
    if r2:
        factors.append("Property matter will be resolved favourably")

    r3 = any(m in ctx.planets_in_house(4) for m in NATURAL_MALEFICS)
    if r3:
        factors.append("No benefit from property even if acquired. Mother may suffer.")

    l4_house = ctx.planet_house(lord4)
    r4 = l4_house in {6, 8}
    if r4:
        factors.append("Property matter faces serious obstacles")

    r5 = ctx.house_aspected_by_benefic(4)
    if r5:
        factors.append("Property acquisition is favoured")

    pmars = ctx.planet("Mars")
    p4 = ctx.planet(lord4)
    r6 = False
    if pmars and p4:
        if ctx.in_house("Mars", l4_house) and l4_house != -1:
            r6 = True
        elif ctx.has_ithasala("Mars", lord4):
            r6 = True
        else:
            for asp in _get(pmars, "aspects", []):
                if lord4 in _get(asp, "aspected_planets", []):
                    r6 = True
                    break
                if int(_get(asp, "target_house", -1)) == l4_house and l4_house != -1:
                    r6 = True
    if r6:
        factors.append("Do not purchase vehicle or property now")

    if r2:
        factors.append("Property purchase recommended")

    if r1 or r2:
        verdict = "YES - Acquisition of land or property is promised."
    elif r2 and r5:
        verdict = "YES - The property matter tends toward settlement."
    elif r3 and not r2:
        verdict = "NO - Even if acquired, the property does not yield benefit."
    elif r4:
        verdict = "NO - Strong obstruction stands in the property matter."
    elif r6:
        verdict = "NO - This is not a favourable time for vehicle or property purchase."
    else:
        verdict = "UNCLEAR - The property indications are mixed."
    return RuleResult(verdict, factors)


@register_house_rule(5)
def rule_house_5(ctx: RuleContext) -> RuleResult:
    factors: list[str] = []
    lord5 = ctx.house_lord(5)
    p5 = ctx.planet(lord5)

    r1 = ctx.has_ithasala(lord5, ctx.lagna_lord) or ctx.has_ithasala(lord5, "Moon")
    if r1:
        factors.append("Children/education matter will succeed")

    lord5_aspects_1 = any(int(_get(asp, "target_house", -1)) == 1 for asp in _get(p5, "aspects", [])) if p5 else False
    r2 = not ctx.has_ithasala(ctx.lagna_lord, lord5) and not lord5_aspects_1
    if r2:
        factors.append("No children indicated - no mutual connection")

    r3 = any(ctx.has_ithasala(lord5, malefic) for malefic in NATURAL_MALEFICS)
    if r3:
        factors.append("Children matter is blocked or delayed by malefic influence")

    asc_sign = ctx.planet_sign("Ascendant")
    house5_sign = ZODIAC[(ZODIAC.index(asc_sign) + 4) % 12] if asc_sign in ZODIAC else ""
    r4 = house5_sign in {"Leo", "Taurus", "Scorpio", "Virgo"} and ctx.house_aspected_by_malefic(5)
    if r4:
        factors.append("Very few or no children indicated")

    r5 = any(b in ctx.planets_in_house(5) for b in NATURAL_BENEFICS) or ctx.house_aspected_by_benefic(5)
    if r5:
        factors.append("Children/education success strongly indicated")

    r6 = ctx.has_ithasala(ctx.lagna_lord, lord5) and ctx.has_ithasala(ctx.lagna_lord, "Moon") and ctx.has_ithasala(lord5, "Moon")
    if r6:
        factors.append("Triple confirmation - children or exam success certain")

    r7 = _get(p5, "is_combust", False)
    if r7:
        factors.append("Children matter delayed due to weak significator")

    if r6:
        verdict = "YES - Children or learning are strongly promised."
    elif r1 and r5:
        verdict = "YES - The indications favour children or learning."
    elif r1 and not r3:
        verdict = "YES, WITH EFFORT - Success may come, though after delay or effort."
    elif r2 or r3:
        verdict = "NO - The desired issue is not supported by the chart."
    elif r4:
        verdict = "NO - Strong obstruction to children is shown."
    elif r7:
        verdict = "YES, WITH EFFORT - The matter is delayed, yet not denied."
    else:
        verdict = "UNCLEAR - The combinations do not permit a firm judgment on children or learning."
    return RuleResult(verdict, factors)


@register_house_rule(9)
def rule_house_9(ctx: RuleContext) -> RuleResult:
    factors: list[str] = []
    lord9 = ctx.house_lord(9)
    ll_house = ctx.planet_house(ctx.lagna_lord)

    r1 = ll_house in {1, 4, 7, 10} and ctx.has_ithasala(ctx.lagna_lord, lord9)
    if r1:
        factors.append("Journey will be undertaken")

    p9 = ctx.planet(lord9)
    l9_house = ctx.planet_house(lord9)
    has_trine_aspect = any(int(_get(asp, "target_house", -1)) in {5, 9} for asp in _get(p9, "aspects", [])) if p9 else False
    base_r23 = l9_house == 1 and ctx.has_ithasala(lord9, ctx.lagna_lord)
    r2 = base_r23 and not has_trine_aspect
    r3 = base_r23 and has_trine_aspect
    if r2:
        factors.append("Journey will NOT take place")
    if r3:
        factors.append("Journey will be undertaken despite initial doubt")

    r4 = False
    if ll_house in {1, 4, 7, 10}:
        has_ith_3 = any(ctx.has_ithasala(ctx.lagna_lord, p3) for p3 in ctx.planets_in_house(3))
        malefic_aspects_ll = any(
            any(int(_get(asp, "target_house", -1)) == ll_house for asp in _get(ctx.planet(malefic), "aspects", []))
            for malefic in NATURAL_MALEFICS
            if ctx.planet(malefic)
        )
        if has_ith_3 and not malefic_aspects_ll:
            r4 = True
    if r4:
        factors.append("Short journey will occur")

    r5 = any(m in ctx.planets_in_house(house) for house in {1, 4, 7, 10} for m in NATURAL_MALEFICS)
    if r5:
        factors.append("Journey will not take place")

    r6 = ctx.planet_house("Jupiter") in {2, 3} and ctx.planet_house("Venus") in {2, 3}
    if r6:
        factors.append("Traveller will return soon")

    l9_type = SIGN_TYPES.get(ctx.planet_sign(lord9), "")
    if l9_type == "Movable":
        factors.append("Quick journey and return")
    elif l9_type == "Fixed":
        factors.append("Long absence")
    elif l9_type == "Common":
        factors.append("Change of route, visiting multiple places")

    sat_house = ctx.planet_house("Saturn")
    r8 = sat_house in {8, 9} and (
        any(m in ctx.planets_in_house(sat_house) and m != "Saturn" for m in NATURAL_MALEFICS)
        or ctx.house_aspected_by_malefic(sat_house)
    )
    if r8:
        factors.append("Traveller will fall ill or face serious danger abroad")

    if r1 and not r5:
        verdict = "YES - The journey is promised."
    elif r3:
        verdict = "YES, WITH EFFORT - The journey may take place, though not without hindrance."
    elif r4:
        verdict = "YES - A short journey is indicated."
    elif r2 or r5:
        verdict = "NO - The journey does not appear to proceed."
    elif r8:
        verdict = "YES, WITH EFFORT - Travel is possible, but danger or affliction attends it."
    else:
        verdict = "UNCLEAR - The combinations do not permit a firm judgment on travel."
    return RuleResult(verdict, factors)


def apply_house_rules(query_house: int, positions: dict, house_lords: dict, precomputed_yogas: dict, house_judgment: dict) -> dict:
    ctx = RuleContext(
        query_house=query_house,
        positions=positions,
        house_lords=house_lords,
        yogas=precomputed_yogas,
        house_judgment=house_judgment,
    )

    handler = RULE_HANDLERS.get(query_house)
    if not handler:
        result = RuleResult(
            "General house judgment applied. House-specific rules are only configured for target areas.",
            [],
        )
    else:
        result = handler(ctx)

    return {
        "specific_verdict": result.specific_verdict,
        "specific_factors": result.specific_factors,
    }
