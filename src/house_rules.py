"""
Registry-based house rules grounded in the working notes from Prasna Tantra.

Priority is given to:
- the relevant house and its lord
- Lagna lord and Moon
- applying perfection, separation, and Moon reinforcement
- benefic/malefic support or affliction to the house concerned
"""

from __future__ import annotations

from dataclasses import dataclass, field

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
    source_rules: list[str] = field(default_factory=list)


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

    def planet(self, planet_name: str | None):
        if not planet_name:
            return None
        return self.positions.get(planet_name)

    def planet_house(self, planet_name: str | None) -> int:
        return int(_get(self.planet(planet_name), "house", -1))

    def planet_sign(self, planet_name: str | None) -> str:
        return _get(self.planet(planet_name), "sign", "")

    def in_house(self, planet_name: str | None, house_num: int) -> bool:
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

    def planet_aspects_house(self, planet_name: str | None, house_num: int) -> bool:
        planet = self.planet(planet_name)
        if not planet:
            return False
        for aspect in _get(planet, "aspects", []):
            if int(_get(aspect, "target_house", -1)) == house_num:
                return True
        return False

    def planet_aspects_planet(self, planet_name: str | None, target_name: str | None) -> bool:
        planet = self.planet(planet_name)
        if not planet or not target_name:
            return False
        for aspect in _get(planet, "aspects", []):
            if target_name in (_get(aspect, "aspected_planets", []) or []):
                return True
        return False

    def has_ithasala(self, planet_a: str | None, planet_b: str | None) -> bool:
        return self.get_ithasala(planet_a, planet_b) is not None

    def get_ithasala(self, planet_a: str | None, planet_b: str | None) -> dict | None:
        if not planet_a or not planet_b:
            return None
        pair = frozenset({planet_a, planet_b})
        return next(
            (
                item
                for item in self.yogas.get("ithasala", [])
                if frozenset({item.get("faster_planet"), item.get("slower_planet")}) == pair
            ),
            None,
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
        return any(
            frozenset(item.get("ithasala_pair", [])) == pair
            for item in self.yogas.get("kamboola", [])
        )

    def same_house(self, planet_a: str | None, planet_b: str | None) -> bool:
        house_a = self.planet_house(planet_a)
        house_b = self.planet_house(planet_b)
        return house_a != -1 and house_a == house_b

    def has_link(self, planet_a: str | None, planet_b: str | None) -> bool:
        return (
            self.has_ithasala(planet_a, planet_b)
            or self.same_house(planet_a, planet_b)
            or self.planet_aspects_planet(planet_a, planet_b)
            or self.planet_aspects_planet(planet_b, planet_a)
        )

    def house_is_supported(self, house_num: int, house_lord: str | None) -> bool:
        return (
            self.in_house(house_lord, house_num)
            or self.planet_aspects_house(house_lord, house_num)
            or self.house_aspected_by_benefic(house_num)
            or any(p in NATURAL_BENEFICS for p in self.planets_in_house(house_num))
        )

    def house_is_afflicted(self, house_num: int, house_lord: str | None) -> bool:
        return (
            self.house_aspected_by_malefic(house_num)
            or any(p in NATURAL_MALEFICS for p in self.planets_in_house(house_num))
            or self.planet_is_afflicted(house_lord)
        )

    def planet_is_afflicted(self, planet_name: str | None) -> bool:
        if not planet_name:
            return False
        if _get(self.planet(planet_name), "is_combust", False):
            return True
        house_num = self.planet_house(planet_name)
        if house_num == -1:
            return False
        occupants = [name for name in self.planets_in_house(house_num) if name != planet_name]
        return any(name in NATURAL_MALEFICS for name in occupants) or self.house_aspected_by_malefic(house_num)

    def slower_house_from_ithasala(self, planet_a: str | None, planet_b: str | None) -> int | None:
        inst = self.get_ithasala(planet_a, planet_b)
        if not inst:
            return None
        return self.planet_house(inst.get("slower_planet"))

    def derived_house(self, base_house: int, offset_house: int) -> int:
        return ((base_house - 1) + (offset_house - 1)) % 12 + 1

    def add_factor(self, factors: list[str], sources: list[str], text: str, source: str) -> None:
        factors.append(text)
        if source not in sources:
            sources.append(source)


RULE_HANDLERS: dict[int, callable] = {}


def register_house_rule(house_num: int):
    def decorator(func):
        RULE_HANDLERS[house_num] = func
        return func

    return decorator


@register_house_rule(2)
def rule_house_2(ctx: RuleContext) -> RuleResult:
    factors: list[str] = []
    sources: list[str] = []
    lord2 = ctx.house_lord(2)

    lagna_link = ctx.has_ithasala(lord2, ctx.lagna_lord)
    moon_link = ctx.has_ithasala(lord2, "Moon")
    supported_house = ctx.house_is_supported(2, lord2)
    afflicted_house = ctx.house_is_afflicted(2, lord2)
    hostile_money = any(ctx.has_ithasala(lord2, malefic) for malefic in NATURAL_MALEFICS if malefic != "Moon")
    separation = ctx.has_easarapha(lord2, ctx.lagna_lord)

    if lagna_link:
        ctx.add_factor(
            factors,
            sources,
            "2nd lord applies to the Lagna lord - gain is promised.",
            "Finance: 2nd lord forms Ithasala with Lagna lord.",
        )
    if moon_link:
        ctx.add_factor(
            factors,
            sources,
            "2nd lord applies to the Moon - gain is supported by the flow of events.",
            "Finance: 2nd lord forms Ithasala with Moon.",
        )
    if supported_house:
        ctx.add_factor(
            factors,
            sources,
            "The 2nd house or its lord receives benefic support.",
            "General vitality: house prospers when its lord or benefics support it.",
        )
    if afflicted_house:
        ctx.add_factor(
            factors,
            sources,
            "The 2nd house or its lord is afflicted by malefic influence.",
            "General vitality: house suffers when malefics join or aspect it.",
        )
    if hostile_money:
        ctx.add_factor(
            factors,
            sources,
            "The 2nd lord is drawn into harsh company, so gain is blemished by strain or anxiety.",
            "Finance warning: severe affliction to the 2nd or its lord gives strain.",
        )
    if separation:
        ctx.add_factor(
            factors,
            sources,
            "The significators are separating, so the promised gain recedes.",
            "Easarapha: separation, missed opportunity, event moving away.",
        )

    source_house = ctx.slower_house_from_ithasala(ctx.lagna_lord, lord2)
    if source_house:
        ctx.add_factor(
            factors,
            sources,
            f"The source of gain is shown through House {source_house}.",
            "Finance: slower planet in the Lagna lord / 2nd lord link shows source of gain.",
        )

    if separation and not lagna_link:
        verdict = "NO - Gain slips away rather than coming to hand."
    elif (lagna_link or moon_link) and supported_house and not afflicted_house:
        verdict = "YES - Dhana is promised; gain may come to hand."
    elif (lagna_link or moon_link) and (afflicted_house or hostile_money):
        verdict = "YES, WITH EFFORT - Dhana is promised, but strain, delay, or blemish attends it."
    elif afflicted_house or hostile_money:
        verdict = "NO - The chart shows anxiety, obstruction, or loss in money matters."
    else:
        verdict = "UNCLEAR - The chart does not give a firm promise of gain."

    return RuleResult(verdict, factors, sources)


@register_house_rule(7)
def rule_house_7(ctx: RuleContext) -> RuleResult:
    factors: list[str] = []
    sources: list[str] = []
    lord7 = ctx.house_lord(7)
    lord8 = ctx.house_lord(8)

    perfection = ctx.has_ithasala(ctx.lagna_lord, lord7)
    moon_reinforces = ctx.has_kamboola(ctx.lagna_lord, lord7)
    quick_union = ctx.in_house(lord7, 1) and ctx.has_link(lord7, ctx.lagna_lord)
    delayed_union = (
        ctx.has_link(lord7, ctx.lagna_lord)
        and not quick_union
        and not perfection
    )
    no_contact = not ctx.has_link(lord7, ctx.lagna_lord) and not ctx.planet_aspects_house(lord7, 1)
    afflicted_union = ctx.house_is_afflicted(7, lord7) or ctx.has_link(lord7, lord8)
    separation = ctx.has_easarapha(ctx.lagna_lord, lord7)

    if perfection:
        ctx.add_factor(
            factors,
            sources,
            "Lagna lord and 7th lord apply to perfection.",
            "Ithasala: agreement, union, event happening.",
        )
    if moon_reinforces:
        ctx.add_factor(
            factors,
            sources,
            "Moon reinforces the perfection by Kamboola.",
            "Kamboola: Moon sharply improves the promise of fulfilment.",
        )
    if quick_union:
        ctx.add_factor(
            factors,
            sources,
            "The significator is brought to Lagna and joins the querent's agency; the union is quicker.",
            "Immediate vs delayed success: significator in Lagna and linked to Lagna lord gives quicker success.",
        )
    elif delayed_union:
        ctx.add_factor(
            factors,
            sources,
            "The significator reaches the querent from another sign; the union is delayed.",
            "Immediate vs delayed success: aspect from another sign gives delayed success.",
        )
    if no_contact:
        ctx.add_factor(
            factors,
            sources,
            "The significator neither aspects Lagna nor joins the Lagna lord.",
            "Immediate vs delayed success: if significator does not aspect Lagna or Lagna lord, the object is not fulfilled.",
        )
    if afflicted_union:
        ctx.add_factor(
            factors,
            sources,
            "The 7th house or its lord is afflicted, so the union is obstructed.",
            "General vitality plus marriage warning: affliction to the 7th impedes union.",
        )
    if separation:
        ctx.add_factor(
            factors,
            sources,
            "The marriage significators are separating rather than joining.",
            "Easarapha: separation or event moving away.",
        )

    if perfection and moon_reinforces and not afflicted_union:
        verdict = "YES - Union is promised."
    elif perfection and afflicted_union:
        verdict = "YES, WITH EFFORT - Union is possible, but not without obstacle or delay."
    elif quick_union and not afflicted_union:
        verdict = "YES - Union is promised and may come quickly."
    elif delayed_union and not afflicted_union:
        verdict = "YES, WITH EFFORT - Union may be obtained, though after delay or seeking."
    elif separation or no_contact or afflicted_union:
        verdict = "NO - Obstructions prevail against union at present."
    else:
        verdict = "UNCLEAR - The combinations do not permit a firm judgment on union."

    return RuleResult(verdict, factors, sources)


@register_house_rule(6)
def rule_house_6(ctx: RuleContext) -> RuleResult:
    factors: list[str] = []
    sources: list[str] = []
    lord6 = ctx.house_lord(6)
    lord8 = ctx.house_lord(8)
    lord12 = ctx.house_lord(12)

    recovery_power = not ctx.planet_is_afflicted(ctx.lagna_lord) and not ctx.planet_is_afflicted("Moon")
    disease_supported = ctx.house_is_supported(6, lord6)
    disease_afflicted = ctx.house_is_afflicted(6, lord6)
    danger_heavy = ctx.has_link(ctx.lagna_lord, lord8) or ctx.has_link(ctx.lagna_lord, lord12) or ctx.house_is_afflicted(8, lord8)
    lagna_falls_to_dusthana = any(ctx.has_link(ctx.lagna_lord, lord) for lord in (lord6, lord8, lord12) if lord)
    separating_from_recovery = ctx.has_easarapha(ctx.lagna_lord, lord6)

    if recovery_power:
        ctx.add_factor(
            factors,
            sources,
            "Lagna lord and Moon retain recovery power.",
            "Health: 1st shows constitution and recovery power.",
        )
    else:
        ctx.add_factor(
            factors,
            sources,
            "Lagna lord or Moon is afflicted, weakening recovery.",
            "Health warning: heavy affliction to Lagna or Moon impairs recovery.",
        )
    if disease_supported:
        ctx.add_factor(
            factors,
            sources,
            "The 6th house and its lord are clearly active.",
            "Health: 6th shows the disease itself.",
        )
    if danger_heavy:
        ctx.add_factor(
            factors,
            sources,
            "The 8th or 12th joins the disease pattern, increasing danger and depletion.",
            "Health: 8th shows danger, 12th shows loss and vital depletion.",
        )
    if lagna_falls_to_dusthana:
        ctx.add_factor(
            factors,
            sources,
            "The Lagna lord is drawn into the 6th, 8th, or 12th pattern.",
            "Health warning: Lagna lord tied to 6th, 8th, or 12th lord.",
        )
    if separating_from_recovery:
        ctx.add_factor(
            factors,
            sources,
            "Recovery indicators separate rather than perfect.",
            "Health warning: Easarapha from recovery indicators shows failure or delay.",
        )

    lagna_type = SIGN_TYPES.get(ctx.planet_sign("Ascendant"), "")
    if lagna_type == "Movable":
        ctx.add_factor(factors, sources, "Movable Lagna - the disease is of shorter course.", "Timing by sign nature.")
    elif lagna_type == "Fixed":
        ctx.add_factor(factors, sources, "Fixed Lagna - the disease is prolonged.", "Timing by sign nature.")
    elif lagna_type == "Common":
        ctx.add_factor(factors, sources, "Common Lagna - the disease is of middle course.", "Timing by sign nature.")

    if danger_heavy and not recovery_power:
        verdict = "CRITICAL - The chart shows grave affliction and danger."
    elif separating_from_recovery or (lagna_falls_to_dusthana and danger_heavy):
        verdict = "NO - The affliction persists and recovery is doubtful."
    elif recovery_power and disease_afflicted and not danger_heavy:
        verdict = "YES - Recovery is promised."
    elif recovery_power and disease_supported:
        verdict = "YES, WITH EFFORT - Relief may come, though by treatment and time."
    else:
        verdict = "UNCLEAR - The combinations do not permit a firm judgment on recovery."

    return RuleResult(verdict, factors, sources)


@register_house_rule(10)
def rule_house_10(ctx: RuleContext) -> RuleResult:
    factors: list[str] = []
    sources: list[str] = []
    lord10 = ctx.house_lord(10)

    perfection = ctx.has_ithasala(ctx.lagna_lord, lord10)
    separation = ctx.has_easarapha(ctx.lagna_lord, lord10)
    supported_work = ctx.house_is_supported(10, lord10)
    afflicted_work = ctx.house_is_afflicted(10, lord10)
    angular_lord = ctx.planet_house(lord10) in {1, 4, 7, 10}
    moon_support = ctx.has_link("Moon", lord10) or ctx.has_link("Moon", ctx.lagna_lord)

    if perfection:
        ctx.add_factor(
            factors,
            sources,
            "Lagna lord and 10th lord apply to perfection.",
            "Main judgment factors: Lagna lord and significator mutually connect.",
        )
    if angular_lord:
        ctx.add_factor(
            factors,
            sources,
            "The 10th lord stands in an angle, strengthening station and authority.",
            "House meanings and general vitality: strong 10th favors authority and profession.",
        )
    if supported_work:
        ctx.add_factor(
            factors,
            sources,
            "The 10th house or its lord receives benefic support.",
            "General vitality: house prospers when lord or benefics support it.",
        )
    if afflicted_work:
        ctx.add_factor(
            factors,
            sources,
            "The 10th house or its lord is afflicted, so work is burdened.",
            "General vitality: house suffers when malefics join or aspect it.",
        )
    if moon_support:
        ctx.add_factor(
            factors,
            sources,
            "Moon joins the career pattern and helps the matter move.",
            "Main judgment factors: Moon connecting to the combination strengthens fulfilment.",
        )
    if separation:
        ctx.add_factor(
            factors,
            sources,
            "The work significators separate rather than perfect.",
            "Easarapha: missed opportunity or event moving away.",
        )

    if perfection and supported_work and not afflicted_work:
        verdict = "YES - Advancement in work and station is promised."
    elif perfection and afflicted_work:
        verdict = "YES, WITH EFFORT - Advancement is possible, but only after obstruction and labour."
    elif separation:
        verdict = "NO - The present undertaking appears to have slipped away."
    elif supported_work and angular_lord and not afflicted_work:
        verdict = "YES, WITH EFFORT - The station is supported, but full perfection is not yet shown."
    elif afflicted_work:
        verdict = "NO - Obstruction weighs on the matter of work and station."
    else:
        verdict = "UNCLEAR - The indications for work and station are mixed."

    return RuleResult(verdict, factors, sources)


@register_house_rule(3)
def rule_house_3(ctx: RuleContext) -> RuleResult:
    factors: list[str] = []
    sources: list[str] = []
    lord3 = ctx.house_lord(3)

    if ctx.house_is_supported(3, lord3):
        ctx.add_factor(factors, sources, "The 3rd house receives support.", "General vitality applied to the 3rd.")
    if ctx.house_is_afflicted(3, lord3):
        ctx.add_factor(factors, sources, "The 3rd house is afflicted.", "General vitality applied to the 3rd.")
    if ctx.has_ithasala(lord3, ctx.lagna_lord):
        ctx.add_factor(factors, sources, "The 3rd lord applies to the Lagna lord.", "Messages and brethren prosper when linked to the querent.")
        verdict = "YES - The matter of brethren and messages appears favourable."
    elif ctx.has_easarapha(lord3, ctx.lagna_lord):
        ctx.add_factor(factors, sources, "The 3rd lord separates from the Lagna lord.", "Easarapha applied to the 3rd.")
        verdict = "NO - The message or communication does not prosper."
    elif ctx.house_is_afflicted(3, lord3):
        verdict = "NO - Discord or affliction is shown in the matter of brethren."
    elif ctx.house_is_supported(3, lord3):
        verdict = "YES, WITH EFFORT - The matter is supported, though not fully perfected."
    else:
        verdict = "UNCLEAR - The combinations do not give a firm judgment on brethren."
    return RuleResult(verdict, factors, sources)


@register_house_rule(4)
def rule_house_4(ctx: RuleContext) -> RuleResult:
    factors: list[str] = []
    sources: list[str] = []
    lord4 = ctx.house_lord(4)
    seller_house = 7
    price_house = 10

    buyer_property_link = ctx.has_ithasala(ctx.lagna_lord, lord4)
    supported_property = ctx.house_is_supported(4, lord4)
    afflicted_property = ctx.house_is_afflicted(4, lord4)
    seller_active = ctx.house_is_supported(seller_house, ctx.house_lord(seller_house))
    price_heavy = ctx.house_is_afflicted(price_house, ctx.house_lord(price_house))

    if buyer_property_link:
        ctx.add_factor(
            factors,
            sources,
            "Lagna lord and 4th lord are joined by applying connection.",
            "Property: buyer and property prosper when Lagna lord and 4th lord connect strongly.",
        )
    if supported_property:
        ctx.add_factor(
            factors,
            sources,
            "The 4th house and its lord receive benefic support.",
            "Property: benefics supporting the 4th favor acquisition.",
        )
    if afflicted_property:
        ctx.add_factor(
            factors,
            sources,
            "The 4th house or its lord is afflicted.",
            "Property: malefic affliction to the 4th gives regret or obstruction.",
        )
    if seller_active:
        ctx.add_factor(
            factors,
            sources,
            "The seller's side is active in the matter.",
            "Property: 7th shows the seller.",
        )
    if price_heavy:
        ctx.add_factor(
            factors,
            sources,
            "The practical result or price is burdened.",
            "Property: 10th shows price/value or practical result.",
        )

    if buyer_property_link and supported_property and not afflicted_property:
        verdict = "YES - Acquisition of land or property is promised."
    elif buyer_property_link and afflicted_property:
        verdict = "YES, WITH EFFORT - The property matter tends toward settlement, but not without defect."
    elif afflicted_property or price_heavy:
        verdict = "NO - Strong obstruction stands in the property matter."
    else:
        verdict = "UNCLEAR - The property indications are mixed."
    return RuleResult(verdict, factors, sources)


@register_house_rule(5)
def rule_house_5(ctx: RuleContext) -> RuleResult:
    factors: list[str] = []
    sources: list[str] = []
    lord5 = ctx.house_lord(5)
    fulfilment_help = ctx.house_lord(11)

    if ctx.has_ithasala(ctx.lagna_lord, lord5):
        ctx.add_factor(factors, sources, "Lagna lord and 5th lord apply to perfection.", "Children: Ithasala between Lagna lord and 5th lord is good.")
    if ctx.has_link(lord5, "Moon"):
        ctx.add_factor(factors, sources, "Moon joins the matter of children or learning.", "Children: use 5th house, 5th lord, Moon, and Lagna lord.")
    if ctx.has_link(lord5, fulfilment_help):
        ctx.add_factor(factors, sources, "The 11th lord helps fulfilment of the matter.", "Children: support from the 11th lord helps fulfilment.")
    if ctx.house_is_afflicted(5, lord5):
        ctx.add_factor(factors, sources, "The 5th house or its lord is afflicted.", "Children: affliction blocks or delays the matter.")

    if ctx.has_ithasala(ctx.lagna_lord, lord5) and not ctx.house_is_afflicted(5, lord5):
        verdict = "YES - Children or learning are promised."
    elif ctx.has_ithasala(ctx.lagna_lord, lord5):
        verdict = "YES, WITH EFFORT - The matter may succeed, though after delay or effort."
    elif ctx.house_is_afflicted(5, lord5):
        verdict = "NO - Strong obstruction is shown in the matter of children or learning."
    else:
        verdict = "UNCLEAR - The combinations do not permit a firm judgment on children or learning."
    return RuleResult(verdict, factors, sources)


@register_house_rule(9)
def rule_house_9(ctx: RuleContext) -> RuleResult:
    factors: list[str] = []
    sources: list[str] = []
    lord9 = ctx.house_lord(9)

    if ctx.has_ithasala(ctx.lagna_lord, lord9):
        ctx.add_factor(factors, sources, "Lagna lord and 9th lord move toward perfection.", "Travel: connection of querent and journey lord supports travel.")
    if ctx.house_is_afflicted(9, lord9):
        ctx.add_factor(factors, sources, "The 9th house or its lord is afflicted.", "Travel: affliction impedes the journey.")
    if ctx.planet_house("Saturn") in {8, 9} and ctx.house_is_afflicted(9, lord9):
        ctx.add_factor(factors, sources, "Danger or illness may attend the journey.", "Travel warning: heavy affliction around 8th/9th gives danger abroad.")

    if ctx.has_ithasala(ctx.lagna_lord, lord9) and not ctx.house_is_afflicted(9, lord9):
        verdict = "YES - The journey is promised."
    elif ctx.has_ithasala(ctx.lagna_lord, lord9):
        verdict = "YES, WITH EFFORT - Travel is possible, but danger or hindrance attends it."
    elif ctx.has_easarapha(ctx.lagna_lord, lord9) or ctx.house_is_afflicted(9, lord9):
        verdict = "NO - The journey does not appear to proceed."
    else:
        verdict = "UNCLEAR - The combinations do not permit a firm judgment on travel."
    return RuleResult(verdict, factors, sources)


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
            [],
        )
    else:
        result = handler(ctx)

    specific_verdict = result.specific_verdict
    if (
        not house_judgment.get("ithasala_present")
        and house_judgment.get("easarapha_present")
        and specific_verdict.startswith("YES")
    ):
        specific_verdict = "NO - The matter separates rather than perfects."
    elif (
        not house_judgment.get("ithasala_present")
        and not house_judgment.get("easarapha_present")
        and specific_verdict.startswith("YES")
    ):
        specific_verdict = "UNCLEAR - House indications are supportive, but no applying perfection completes the matter."

    return {
        "specific_verdict": specific_verdict,
        "specific_factors": result.specific_factors,
        "source_rules": result.source_rules,
    }
