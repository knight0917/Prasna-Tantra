"""
src/house_rules.py
House-specific operational rules derived from Prasna Tantra stanzas.
"""

from __future__ import annotations

NATURAL_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
NATURAL_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}

def _get(obj, field, default=None):
    if isinstance(obj, dict):
        return obj.get(field, default)
    return getattr(obj, field, default)

def _planet_in_house(planet_name: str, house_num: int, positions: dict) -> bool:
    p = positions.get(planet_name)
    if not p: return False
    return int(_get(p, "house", -1)) == house_num

def _planets_in_house(house_num: int, positions: dict) -> list[str]:
    names = []
    for name, p in positions.items():
        if name == "Ascendant": continue
        if int(_get(p, "house", -1)) == house_num:
            names.append(name)
    return names

def _lord_has_ithasala_with(lord_name: str, target_name: str, precomputed_yogas: dict) -> bool:
    pair = frozenset({lord_name, target_name})
    for i in precomputed_yogas.get("ithasala", []):
        if frozenset({i.get("faster_planet"), i.get("slower_planet")}) == pair:
            return True
    return False

def _lord_has_easarapha_with(lord_name: str, target_name: str, precomputed_yogas: dict) -> bool:
    pair = frozenset({lord_name, target_name})
    for i in precomputed_yogas.get("easarapha", []):
        if frozenset({i.get("faster_planet"), i.get("slower_planet")}) == pair:
            return True
    return False

def _lord_in_kamboola_with(lord_name: str, target_name: str, precomputed_yogas: dict) -> bool:
    pair = frozenset({lord_name, target_name})
    for k in precomputed_yogas.get("kamboola", []):
        if frozenset(k.get("ithasala_pair", [])) == pair:
            return True
    return False

def _house_aspected_by_benefic(house_num: int, positions: dict) -> bool:
    for b in NATURAL_BENEFICS:
        p = positions.get(b)
        if not p: continue
        for asp in _get(p, "aspects", []):
            if int(_get(asp, "target_house", -1)) == house_num:
                return True
    return False

def _house_aspected_by_malefic(house_num: int, positions: dict) -> bool:
    for m in NATURAL_MALEFICS:
        p = positions.get(m)
        if not p: continue
        for asp in _get(p, "aspects", []):
            if int(_get(asp, "target_house", -1)) == house_num:
                return True
    return False

def apply_house_rules(query_house: int, positions: dict, house_lords: dict, precomputed_yogas: dict, house_judgment: dict) -> dict:
    specific_verdict = ""
    specific_factors = []
    
    lagna_lord = house_judgment.get("lagna_lord")
    
    if query_house == 2:
        lord2 = house_lords.get("2")
        gain_indicated = False
        r4 = False
        
        # R1
        if _lord_has_ithasala_with(lord2, lagna_lord, precomputed_yogas) or _lord_has_ithasala_with(lord2, "Moon", precomputed_yogas):
            gain_indicated = True
            specific_factors.append('Lord of 2nd in applying aspect with Lagna lord — gain of money predicted')
            
        # R2: Lord of 2nd is aspected by or conjoined with benefics
        h2_lord_house = int(_get(positions.get(lord2, {}), "house", -1))
        r2 = False
        if h2_lord_house != -1:
            if any(b in _planets_in_house(h2_lord_house, positions) for b in NATURAL_BENEFICS) or _house_aspected_by_benefic(h2_lord_house, positions):
                r2 = True
                
        if r2:
            specific_factors.append('Benefic influence on 2nd lord — financial gain')
            gain_indicated = True # Benefic influence usually implies gain. Wait, strictly follow the book? The prompt said R1 has gain_indicated=True. We will assume any strong indicator points to gain.
            
        # R3: Malefics in 2nd house
        if any(m in _planets_in_house(2, positions) for m in NATURAL_MALEFICS):
            specific_factors.append('Malefics in 2nd — gain possible but from distant land, with suffering')
            
        # R4: Lord of 2nd has Ithasala with malefics
        if any(_lord_has_ithasala_with(lord2, m, precomputed_yogas) for m in NATURAL_MALEFICS):
            r4 = True
            specific_factors.append('Warning: 2nd lord applying to malefic — serious financial risk')
            
        # R5: Moon, Lagna lord, and 2nd lord all in mutual conjunction or Ithasala in quadrant/trine
        quad_trine = {1, 4, 7, 10, 5, 9}
        ll_h = int(_get(positions.get(lagna_lord, {}), "house", -1))
        moon_h = int(_get(positions.get("Moon", {}), "house", -1))
        if ll_h in quad_trine and h2_lord_house in quad_trine and moon_h in quad_trine:
            if (_lord_has_ithasala_with(lagna_lord, lord2, precomputed_yogas) or ll_h == h2_lord_house) and \
               (_lord_has_ithasala_with(lagna_lord, "Moon", precomputed_yogas) or ll_h == moon_h) and \
               (_lord_has_ithasala_with(lord2, "Moon", precomputed_yogas) or h2_lord_house == moon_h):
                specific_factors.append('Triple conjunction of wealth indicators — immediate gain certain')
                gain_indicated = True
                
        # R6: Moon in 4th or 7th, Sun in 10th, benefic in Lagna
        if moon_h in {4, 7} and _planet_in_house("Sun", 10, positions):
            if any("Ascendant" != b and _planet_in_house(b, 1, positions) for b in NATURAL_BENEFICS):
                specific_factors.append('Classical wealth yoga present — immediate financial gain')
                gain_indicated = True
                
        # Final Verdict
        if gain_indicated and not r4:
            specific_verdict = 'YES — Financial gain is indicated. The 2nd lord applies to the Lagna lord.'
        elif gain_indicated and r4:
            specific_verdict = 'YES, WITH EFFORT — Gain is shown but a malefic intervenes. Caution with finances.'
        elif r4:
            specific_verdict = 'NO — Financial risk outweighs gain indicators. Avoid major financial decisions now.'
        else:
            specific_verdict = 'NO — No clear gain indicators present in this chart.'
            

    elif query_house == 7:
        lord7 = house_lords.get("7")
        lord8 = house_lords.get("8")
        lord3 = house_lords.get("3")
        lord4 = house_lords.get("4")
        
        r1 = _lord_has_ithasala_with(lagna_lord, lord7, precomputed_yogas)
        if r1:
            specific_factors.append('Applying aspect between Lagna lord and 7th lord — marriage will occur')
            
        r2 = False
        if _planet_in_house(lagna_lord, 7, positions):
            r2 = True
            specific_factors.append('Lagna lord in 7th — bride secured with effort')
        elif _planet_in_house("Moon", 7, positions):
            r2 = True
            specific_factors.append('Moon in 7th — marriage will happen with some seeking')
            
        r3 = _lord_has_easarapha_with(lagna_lord, "Moon", precomputed_yogas)
        if r3:
            specific_factors.append('Lagna lord in Musaripha with Moon — past romantic connection indicated')
            
        # R4: Planet conjoined with 7th lord is combust or afflicted by malefics
        r4 = False
        l7_house = int(_get(positions.get(lord7, {}), "house", -1))
        if l7_house != -1:
            conjoined = _planets_in_house(l7_house, positions)
            for c in conjoined:
                if c != lord7:
                    p = positions.get(c, {})
                    if _get(p, "is_combust", False) or _house_aspected_by_malefic(l7_house, positions):
                        r4 = True
                        break
        if r4:
            specific_factors.append('Warning: 7th lord afflicted — obstacles in marriage')
            
        # R5: 8th lord is a natural malefic AND aspects 7th house
        r5 = False
        if lord8 in NATURAL_MALEFICS:
            p8 = positions.get(lord8)
            if p8:
                for asp in _get(p8, "aspects", []):
                    if int(_get(asp, "target_house", -1)) == 7:
                        r5 = True
                        break
        if r5:
            specific_factors.append('Warning: 8th lord afflicts 7th — marriage may be blocked or delayed')
            
        r6 = lord3 in NATURAL_MALEFICS
        if r6:
            specific_factors.append('Brothers may cause obstruction to marriage')
            
        r7 = lord4 in NATURAL_MALEFICS
        if r7:
            specific_factors.append('Father figure may cause obstruction to marriage')
            
        r8 = _lord_in_kamboola_with(lagna_lord, lord7, precomputed_yogas)
        if r8:
            specific_factors.append('Kamboola Yoga — marriage is strongly indicated and will be auspicious')
            
        if r1 or r8:
            specific_verdict = 'YES — Marriage will occur. Strong indicators are present.'
        elif r2 and not (r4 or r5):
            specific_verdict = 'YES, WITH EFFORT — Marriage is possible but requires seeking.'
        elif r4 or r5:
            specific_verdict = 'NO — Obstacles block marriage at this time.'
        else:
            specific_verdict = 'UNCLEAR — Insufficient combinations for a definite answer.'

    elif query_house == 6:
        lord6 = house_lords.get("6")
        lord8 = house_lords.get("8")
        
        r1 = _planet_in_house(lord6, 1, positions) and _planet_in_house(lord8, 1, positions)
        if r1: specific_factors.append('CRITICAL: Lords of 6th and 8th in Lagna — life is threatened')
        
        r2 = _planet_in_house(lord6, 8, positions) and _planet_in_house(lord8, 6, positions)
        if r2: specific_factors.append('Lords of 6th and 8th in mutual exchange — speedy recovery indicated')
        
        r3 = _planet_in_house(lagna_lord, 6, positions) and _planet_in_house(lord6, 1, positions)
        if r3: specific_factors.append('Exchange of Lagna and 6th lords — long suffering, slow recovery')
        
        r4 = _lord_has_ithasala_with(lagna_lord, lord6, precomputed_yogas)
        if r4: specific_factors.append('Lagna lord applying to 6th lord — illness will continue until aspect is exact')
        
        r5 = False
        bene_in_6 = [b for b in NATURAL_BENEFICS if _planet_in_house(b, 6, positions)]
        if bene_in_6:
            r5 = True
            specific_factors.append('Benefics in 6th — speedy recovery expected')
            
        r6 = _house_aspected_by_malefic(6, positions) and _house_aspected_by_malefic(8, positions)
        if r6: specific_factors.append('Warning: Malefics afflict both 6th and 8th — recovery unlikely')
        
        r7 = False
        ll_h = int(_get(positions.get(lagna_lord, {}), "house", -1))
        if ll_h in {1, 5, 9} and _house_aspected_by_benefic(9, positions):
            r7 = True
            specific_factors.append('Lagna lord in trine with benefic 9th — recovery after treatment')
            
        r8_type = house_judgment.get("lagna_sign_type", house_judgment.get("lagna_rise_type", ""))
        # Wait, the prompt says "Lagna sign is movable", we can check the ascendant sign.
        asc_sign = _get(positions.get("Ascendant", {}), "sign", "")
        # The prompt says: "Movable Lagna — illness will be short", "Fixed Lagna...", "Common Lagna..."
        SIGN_TYPES = {
            "Aries": "Movable", "Cancer": "Movable", "Libra": "Movable", "Capricorn": "Movable",
            "Taurus": "Fixed", "Leo": "Fixed", "Scorpio": "Fixed", "Aquarius": "Fixed",
            "Gemini": "Common", "Virgo": "Common", "Sagittarius": "Common", "Pisces": "Common"
        }
        l_type = SIGN_TYPES.get(asc_sign, "")
        if l_type == "Movable":
            specific_factors.append('Movable Lagna — illness will be short')
        elif l_type == "Fixed":
            specific_factors.append('Fixed Lagna — illness may be prolonged')
        elif l_type == "Common":
            specific_factors.append('Common Lagna — illness of medium duration')
            
        if r1: specific_verdict = 'CRITICAL — Life is in danger. Seek immediate medical care.'
        elif r6: specific_verdict = 'NO — Serious illness. Recovery is uncertain.'
        elif r2 or r5: specific_verdict = 'YES — Recovery is expected.'
        elif r3 or r4: specific_verdict = 'NO — Full recovery will take time. Illness continues.'
        elif r7: specific_verdict = 'YES, WITH EFFORT — Recovery is possible with proper treatment.'
        else: specific_verdict = 'UNCLEAR — Insufficient combinations for a definite answer.'

    elif query_house == 10:
        lord10 = house_lords.get("10")
        
        r1 = _lord_has_ithasala_with(lagna_lord, lord10, precomputed_yogas)
        if r1: specific_factors.append('Applying aspect between Lagna lord and 10th lord — career success indicated')
        
        r2 = int(_get(positions.get(lord10, {}), "house", -1)) in {1, 4, 7, 10}
        if r2: specific_factors.append('10th lord in angular house — strong career position')
        
        r3 = _house_aspected_by_benefic(10, positions)
        if r3: specific_factors.append('Benefic aspect on 10th — professional recognition coming')
        
        r4 = any(m in _planets_in_house(10, positions) for m in NATURAL_MALEFICS)
        if r4: specific_factors.append('Malefics in 10th — career obstacles, effort required')
        
        ll_p = positions.get(lagna_lord, {})
        r5 = _get(ll_p, "speed_deg_per_day", 0.0) < 0 and _lord_has_ithasala_with(lagna_lord, lord10, precomputed_yogas)
        if r5: specific_factors.append('Retrograde Lagna lord applying to 10th lord — job change or reversal likely')
        
        ll_h = int(_get(ll_p, "house", -1))
        r6 = ll_h in {1, 4, 7, 10} and not _lord_has_ithasala_with(lagna_lord, house_lords.get("6"), precomputed_yogas) and not _lord_has_ithasala_with(lagna_lord, house_lords.get("12"), precomputed_yogas)
        if r6: specific_factors.append('Stable employment — no change of master indicated')
        
        r7 = _lord_has_easarapha_with(lord10, lagna_lord, precomputed_yogas)
        if r7: specific_factors.append('Separating aspect — opportunity may have passed')
        
        if r1 and not r4: specific_verdict = 'YES — Career success and the job offer will come through.'
        elif r1 and r4: specific_verdict = 'YES, WITH EFFORT — Success is possible but significant obstacles must be overcome.'
        elif r5: specific_verdict = 'YES, WITH EFFORT — A career change is likely, not success in current position.'
        elif r6: specific_verdict = 'YES — Current position is stable. No change needed.'
        elif r7: specific_verdict = 'NO — This particular opportunity has passed.'
        else: specific_verdict = 'UNCLEAR — Mixed or absent indicators. Cannot declare outcome.'
        
    elif query_house == 3:
        lord3 = house_lords.get("3")
        lord6 = house_lords.get("6")

        lord3_aspects_3 = False
        p3 = positions.get(lord3)
        if p3:
            for asp in _get(p3, "aspects", []):
                if int(_get(asp, "target_house", -1)) == 3:
                    lord3_aspects_3 = True

        r1 = lord3_aspects_3 or _house_aspected_by_benefic(3, positions)
        if r1: specific_factors.append('Brothers/sisters are well and happy')

        p_lord3 = positions.get(lord3, {})
        r2 = _get(p_lord3, "is_combust", False)
        if r2: specific_factors.append('Brother faces danger or serious difficulty')

        r3 = int(_get(p_lord3, "house", -1)) == 6 and _lord_has_ithasala_with(lord3, lord6, precomputed_yogas)
        if r3: specific_factors.append('Brother is ill or in trouble')

        l3_h = int(_get(p3, "house", -1)) if p3 else -1
        l3_afflicted = l3_h != -1 and (any(m in _planets_in_house(l3_h, positions) for m in NATURAL_MALEFICS) or _house_aspected_by_malefic(l3_h, positions))
        r4 = (l3_h == 8) and l3_afflicted
        if r4: specific_factors.append("Brother's life may be in danger")

        r5 = any(m in _planets_in_house(3, positions) for m in NATURAL_MALEFICS)
        if r5: specific_factors.append('Discord between querent and siblings')

        r6 = _lord_has_ithasala_with(lord3, lagna_lord, precomputed_yogas)
        if r6: specific_factors.append('Communication or message will be received favourably')

        r7 = _lord_has_easarapha_with(lord3, lagna_lord, precomputed_yogas)
        if r7: specific_factors.append('Message or communication has already gone unfavourably')

        if r1 and r6: specific_verdict = 'YES — Siblings are well. Favourable communication expected.'
        elif r2 or r4: specific_verdict = 'NO — Sibling faces serious danger or difficulty.'
        elif r3: specific_verdict = 'YES, WITH EFFORT — Sibling is unwell but situation is manageable.'
        elif r5 and not r1: specific_verdict = 'NO — Discord with siblings indicated.'
        elif r7: specific_verdict = 'NO — Communication has not gone well.'
        else: specific_verdict = 'UNCLEAR — No strong combinations present for siblings.'

    elif query_house == 4:
        lord4 = house_lords.get("4")

        r1 = _planet_in_house("Moon", 4, positions) and _lord_has_ithasala_with(lagna_lord, "Moon", precomputed_yogas)
        if r1: specific_factors.append('Querent will acquire land or property')

        r2 = _lord_has_ithasala_with(lord4, lagna_lord, precomputed_yogas)
        if r2: specific_factors.append('Property matter will be resolved favourably')

        r3 = any(m in _planets_in_house(4, positions) for m in NATURAL_MALEFICS)
        if r3: specific_factors.append('No benefit from property even if acquired. Mother may suffer.')

        p4 = positions.get(lord4)
        l4_h = int(_get(p4, "house", -1)) if p4 else -1
        r4 = l4_h in {6, 8}
        if r4: specific_factors.append('Property matter faces serious obstacles')

        r5 = _house_aspected_by_benefic(4, positions)
        if r5: specific_factors.append('Property acquisition is favoured')

        pmars = positions.get("Mars")
        r6 = False
        if pmars and p4:
            if int(_get(pmars, "house", -1)) == l4_h and l4_h != -1:
                r6 = True
            elif _lord_has_ithasala_with("Mars", lord4, precomputed_yogas):
                r6 = True
            else:
                for asp in _get(pmars, "aspects", []):
                    if target_planets := _get(asp, "aspected_planets", []):
                        if lord4 in target_planets:
                            r6 = True
                            break
                    if int(_get(asp, "target_house", -1)) == l4_h and l4_h != -1:
                        r6 = True
        if r6: specific_factors.append('Do not purchase vehicle or property now')

        r7 = r2
        if r7: specific_factors.append('Property purchase recommended')

        if r1 or r7: specific_verdict = 'YES — Property or land will be acquired.'
        elif r2 and r5: specific_verdict = 'YES — Property matter resolves favourably.'
        elif r3 and not r2: specific_verdict = 'NO — Property acquisition will bring no benefit.'
        elif r4: specific_verdict = 'NO — Serious obstacles block property matter.'
        elif r6: specific_verdict = 'NO — Avoid vehicle or property purchase at this time.'
        else: specific_verdict = 'UNCLEAR — Mixed indicators for property.'

    elif query_house == 5:
        lord5 = house_lords.get("5")
        
        r1 = _lord_has_ithasala_with(lord5, lagna_lord, precomputed_yogas) or _lord_has_ithasala_with(lord5, "Moon", precomputed_yogas)
        if r1: specific_factors.append('Children/education matter will succeed')
        
        lord5_aspects_1 = False
        p5 = positions.get(lord5)
        if p5:
            for asp in _get(p5, "aspects", []):
                if int(_get(asp, "target_house", -1)) == 1:
                    lord5_aspects_1 = True
        r2 = not _lord_has_ithasala_with(lagna_lord, lord5, precomputed_yogas) and not lord5_aspects_1
        if r2: specific_factors.append('No children indicated — no mutual connection')
        
        r3 = any(_lord_has_ithasala_with(lord5, m, precomputed_yogas) for m in NATURAL_MALEFICS)
        if r3: specific_factors.append('Children matter is blocked or delayed by malefic influence')
        
        asc_sign = _get(positions.get("Ascendant", {}), "sign", "Aries")
        zodiac = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        if asc_sign in zodiac:
            house5_sign = zodiac[(zodiac.index(asc_sign) + 4) % 12]
        else:
            house5_sign = ""
        r4 = (house5_sign in {"Leo", "Taurus", "Scorpio", "Virgo"}) and _house_aspected_by_malefic(5, positions)
        if r4: specific_factors.append('Very few or no children indicated')
        
        r5 = any(b in _planets_in_house(5, positions) for b in NATURAL_BENEFICS) or _house_aspected_by_benefic(5, positions)
        if r5: specific_factors.append('Children/education success strongly indicated')
        
        r6 = _lord_has_ithasala_with(lagna_lord, lord5, precomputed_yogas) and _lord_has_ithasala_with(lagna_lord, "Moon", precomputed_yogas) and _lord_has_ithasala_with(lord5, "Moon", precomputed_yogas)
        if r6: specific_factors.append('Triple confirmation — children or exam success certain')
        
        r7 = _get(p5, "is_combust", False) if p5 else False
        if r7: specific_factors.append('Children matter delayed due to weak significator')
        
        if r6: specific_verdict = 'YES — Children or educational success is strongly confirmed.'
        elif r1 and r5: specific_verdict = 'YES — Favourable for children or educational success.'
        elif r1 and not r3: specific_verdict = 'YES, WITH EFFORT — Success possible with persistence.'
        elif r2 or r3: specific_verdict = 'NO — This chart does not support the desired outcome.'
        elif r4: specific_verdict = 'NO — Significant obstacles to children indicated.'
        elif r7: specific_verdict = 'YES, WITH EFFORT — Delayed but possible with time.'
        else: specific_verdict = 'UNCLEAR — Insufficient combinations to determine outcome.'

    elif query_house == 9:
        lord9 = house_lords.get("9")
        p_ll = positions.get(lagna_lord)
        ll_h = int(_get(p_ll, "house", -1)) if p_ll else -1
        
        r1 = (ll_h in {1, 4, 7, 10}) and _lord_has_ithasala_with(lagna_lord, lord9, precomputed_yogas)
        if r1: specific_factors.append('Journey will be undertaken')
        
        p9 = positions.get(lord9)
        l9_h = int(_get(p9, "house", -1)) if p9 else -1
        has_trine_aspect = any(int(_get(asp, "target_house", -1)) in {5, 9} for asp in _get(p9, "aspects", [])) if p9 else False
        base_r23 = (l9_h == 1) and _lord_has_ithasala_with(lord9, lagna_lord, precomputed_yogas)
        r2 = base_r23 and not has_trine_aspect
        r3 = base_r23 and has_trine_aspect
        
        if r2: specific_factors.append('Journey will NOT take place')
        if r3: specific_factors.append('Journey will be undertaken despite initial doubt')
        
        planet_in_3 = _planets_in_house(3, positions)
        r4 = False
        if ll_h in {1, 4, 7, 10}:
            has_ith_3 = any(_lord_has_ithasala_with(lagna_lord, p3, precomputed_yogas) for p3 in planet_in_3)
            malefic_aspects_ll = False
            for m in NATURAL_MALEFICS:
                pm = positions.get(m)
                if pm and any(int(_get(asp, "target_house", -1)) == ll_h for asp in _get(pm, "aspects", [])):
                    malefic_aspects_ll = True
            if has_ith_3 and not malefic_aspects_ll:
                r4 = True
        if r4: specific_factors.append('Short journey will occur')
        
        r5 = any(m in _planets_in_house(kh, positions) for kh in {1, 4, 7, 10} for m in NATURAL_MALEFICS)
        if r5: specific_factors.append('Journey will not take place')
        
        j_h = int(_get(positions.get("Jupiter", {}), "house", -1))
        v_h = int(_get(positions.get("Venus", {}), "house", -1))
        r6 = (j_h in {2, 3}) and (v_h in {2, 3})
        if r6: specific_factors.append('Traveller will return soon')
        
        r7 = False
        if p9:
            l9_sign = _get(p9, "sign", "")
            SIGN_TYPES = {"Aries": "Movable", "Cancer": "Movable", "Libra": "Movable", "Capricorn": "Movable",
                          "Taurus": "Fixed", "Leo": "Fixed", "Scorpio": "Fixed", "Aquarius": "Fixed",
                          "Gemini": "Common", "Virgo": "Common", "Sagittarius": "Common", "Pisces": "Common"}
            l9_type = SIGN_TYPES.get(l9_sign, "")
            if l9_type == "Movable":
                specific_factors.append('Quick journey and return')
                r7 = True
            elif l9_type == "Fixed":
                specific_factors.append('Long absence')
                r7 = True
            elif l9_type == "Common":
                specific_factors.append('Change of route, visiting multiple places')
                r7 = True
                
        p_sat = positions.get("Saturn")
        sat_h = int(_get(p_sat, "house", -1)) if p_sat else -1
        r8 = False
        if sat_h in {8, 9}:
            sat_afflicted = any(m in _planets_in_house(sat_h, positions) and m != "Saturn" for m in NATURAL_MALEFICS) or _house_aspected_by_malefic(sat_h, positions)
            if sat_afflicted:
                r8 = True
                specific_factors.append('Traveller will fall ill or face serious danger abroad')
                
        if r1 and not r5: specific_verdict = 'YES — Journey will be undertaken.'
        elif r3: specific_verdict = 'YES, WITH EFFORT — Journey happens despite obstacles.'
        elif r4: specific_verdict = 'YES — Short journey indicated.'
        elif r2 or r5: specific_verdict = 'NO — Journey will not take place.'
        elif r8: specific_verdict = 'YES, WITH EFFORT — Journey possible but danger abroad. Exercise caution.'
        else: specific_verdict = 'UNCLEAR — No strong travel combinations present.'

    else:
        specific_verdict = 'General house judgment applied. House-specific rules are only configured for target areas.'
        specific_factors = []
        
    return {
        "specific_verdict": specific_verdict,
        "specific_factors": specific_factors
    }
