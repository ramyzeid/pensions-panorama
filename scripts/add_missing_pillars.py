"""
Batch-add missing World Bank pillar schemes to country params YAMLs.

Covers Pillar 0 (non-contributory safety nets) and Pillar 2 (mandatory funded DC)
for ~25 major economies where these are clearly documented but absent.

Run from the project root:
    python scripts/add_missing_pillars.py
"""

from __future__ import annotations
import os
import sys
from pathlib import Path

import yaml

PARAMS_DIR = Path("data/params")

# ---------------------------------------------------------------------------
# Missing scheme definitions
# Each entry: {
#   "iso3": str,
#   "schemes": [ full scheme dict (YAML-ready) ]
#   "worker_type_updates": { worker_type: [scheme_ids to append] }
# }
# ---------------------------------------------------------------------------

MISSING_SCHEMES: list[dict] = [

    # ── Australia ─────────────────────────────────────────────────────────
    # AUS currently has only Superannuation (DC, Pillar 2).
    # Missing: Age Pension (means-tested targeted, Pillar 0), NRA 67.
    {
        "iso3": "AUS",
        "schemes": [
            {
                "scheme_id": "AUS_AGE",
                "name": "Age Pension – Means-Tested",
                "tier": "first",
                "type": "targeted",
                "coverage": "Australian residents aged 67+ who pass means and assets tests; approximately 60% of age-eligible population receive some Age Pension",
                "active": True,
                "eligibility": {
                    "normal_retirement_age_male": {
                        "value": 67,
                        "source_citation": "OECD Pensions at a Glance 2023 Australia: Age Pension eligibility age 67 for both sexes since July 2023.",
                        "year": 2023,
                    },
                    "normal_retirement_age_female": {
                        "value": 67,
                        "source_citation": "OECD Pensions at a Glance 2023 Australia: Age Pension eligibility age 67 for both sexes since July 2023.",
                        "year": 2023,
                    },
                },
                "benefits": {
                    "flat_rate_aw_multiple": None,
                    "flat_rate_absolute": None,
                    "minimum_benefit_aw_multiple": {
                        "value": 0.278,
                        "source_citation": "OECD Pensions at a Glance 2023 Australia: full Age Pension single rate AUD 26,689/year (Sep 2023) ≈ 27.8% of AW (AUD 95,581).",
                        "year": 2023,
                    },
                    "maximum_benefit_aw_multiple": {
                        "value": 0.278,
                        "source_citation": "OECD PAG 2023: full rate for single person; couple rate is lower per person.",
                        "year": 2023,
                    },
                    "indexation": "mixed",
                },
                "payout": {
                    "type": "annuity",
                    "notes": "Fortnightly payment funded from general taxation; means-tested on income and assets.",
                },
            }
        ],
        "worker_type_updates": {},  # non-contributory, not added to calculator
    },

    # ── Canada ────────────────────────────────────────────────────────────
    # CAN currently has only CPP (DB, Pillar 1).
    # Missing: OAS (universal, Pillar 0) + GIS (means-tested top-up, Pillar 0).
    {
        "iso3": "CAN",
        "schemes": [
            {
                "scheme_id": "CAN_OAS",
                "name": "Old Age Security (OAS) – Universal",
                "tier": "first",
                "type": "basic",
                "coverage": "All Canadian residents aged 65+ with 10+ years of residence after age 18; automatic for most citizens",
                "active": True,
                "eligibility": {
                    "normal_retirement_age_male": {
                        "value": 65,
                        "source_citation": "OECD Pensions at a Glance 2023 Canada: OAS payable from age 65; deferral to 70 increases benefit 7.2%/year.",
                        "year": 2023,
                    },
                    "normal_retirement_age_female": {
                        "value": 65,
                        "source_citation": "OECD PAG 2023 Canada: OAS NRA 65 for both sexes.",
                        "year": 2023,
                    },
                },
                "benefits": {
                    "flat_rate_aw_multiple": {
                        "value": 0.138,
                        "source_citation": "OECD PAG 2023 Canada: OAS full monthly rate C$698.60 (Oct 2023) × 12 = C$8,383/year ≈ 13.8% of AW (C$60,700).",
                        "year": 2023,
                    },
                    "indexation": "CPI",
                },
                "payout": {
                    "type": "annuity",
                    "notes": "Monthly payment from federal general revenues; clawback (OAS Recovery Tax) for high-income recipients.",
                },
            },
            {
                "scheme_id": "CAN_GIS",
                "name": "Guaranteed Income Supplement (GIS) – Means-Tested",
                "tier": "first",
                "type": "targeted",
                "coverage": "Low-income OAS recipients aged 65+; full GIS for those with no other income; approximately 35% of OAS recipients",
                "active": True,
                "eligibility": {
                    "normal_retirement_age_male": {
                        "value": 65,
                        "source_citation": "OECD PAG 2023 Canada: GIS payable from age 65 to low-income OAS recipients.",
                        "year": 2023,
                    },
                    "normal_retirement_age_female": {
                        "value": 65,
                        "source_citation": "OECD PAG 2023 Canada: GIS NRA 65 for both sexes.",
                        "year": 2023,
                    },
                },
                "benefits": {
                    "minimum_benefit_aw_multiple": {
                        "value": 0.00,
                        "source_citation": "GIS reduces $1 for every $2 of other income; phases out completely.",
                        "year": 2023,
                    },
                    "maximum_benefit_aw_multiple": {
                        "value": 0.128,
                        "source_citation": "OECD PAG 2023 Canada: maximum GIS single C$1,037/month × 12 = C$12,444 ≈ 12.8% AW for those with zero other income.",
                        "year": 2023,
                    },
                    "indexation": "CPI",
                },
                "payout": {
                    "type": "annuity",
                    "notes": "Monthly supplement to OAS; means-tested on individual/spousal income; funded from general revenues.",
                },
            },
        ],
        "worker_type_updates": {},
    },

    # ── Switzerland ───────────────────────────────────────────────────────
    # CHE has AHV (DB, Pillar 1). Missing: BVG (mandatory occupational, Pillar 2).
    {
        "iso3": "CHE",
        "schemes": [
            {
                "scheme_id": "CHE_BVG",
                "name": "Occupational Pension (BVG/LPP) – Mandatory",
                "tier": "second",
                "type": "DC",
                "coverage": "All employees earning more than CHF 22,050/year (entry threshold 2023); mandatory for private sector employees",
                "active": True,
                "eligibility": {
                    "normal_retirement_age_male": {
                        "value": 65,
                        "source_citation": "OECD PAG 2023 Switzerland: BVG NRA 65 for men; women moving from 64 to 65 by 2028 (AVS 21 reform).",
                        "year": 2023,
                    },
                    "normal_retirement_age_female": {
                        "value": 64,
                        "source_citation": "OECD PAG 2023 Switzerland: BVG NRA 64 for women in 2023; rising to 65 by 2028.",
                        "year": 2023,
                    },
                    "vesting_years": {
                        "value": 2,
                        "source_citation": "Swiss BVG: vesting after 2 years of plan membership.",
                        "year": 2023,
                    },
                    "minimum_contribution_years": {
                        "value": 0,
                        "source_citation": "BVG: no minimum years; accounts vest after 2 years.",
                        "year": 2023,
                    },
                },
                "contributions": {
                    "employee_rate": {
                        "value": 0.075,
                        "source_citation": "OECD PAG 2023 Switzerland: BVG minimum contributions age-dependent (7% age 25-34, 10% age 35-44, 15% age 45-54, 18% age 55-65); weighted average ~15% total, split equally ≈ 7.5% employee.",
                        "year": 2023,
                    },
                    "employer_rate": {
                        "value": 0.075,
                        "source_citation": "OECD PAG 2023 Switzerland: employer must contribute at least equal to employee; weighted average ≈ 7.5%.",
                        "year": 2023,
                    },
                    "total_rate": {
                        "value": 0.15,
                        "source_citation": "Derived: weighted average total BVG contribution ~15%; actual rates are age-dependent (7–18% total by age band).",
                        "year": 2023,
                    },
                    "contribution_ceiling_aw_multiple": {
                        "value": None,
                        "source_citation": "BVG contributions apply to coordinated salary (gross salary minus AHV coordination deduction CHF 25,725); upper ceiling CHF 88,200.",
                        "year": 2023,
                    },
                    "contribution_base": "coordinated salary (gross minus AHV coordination deduction)",
                    "notes": "Contributions applied to 'coordinated salary' = gross – CHF 25,725 coordination deduction. Age-dependent minimum contribution rates.",
                },
                "benefits": {
                    "accrual_rate_per_year": None,
                    "reference_wage": "career_average",
                    "valorization": "market",
                    "indexation": "market",
                    "minimum_benefit_aw_multiple": None,
                    "maximum_benefit_aw_multiple": None,
                },
                "payout": {
                    "type": "annuity",
                    "notes": "Minimum conversion rate 6.8% p.a. on accumulated capital (mandatory portion); lump sum partial withdrawal allowed.",
                },
            }
        ],
        "worker_type_updates": {"private_employee": ["CHE_BVG"], "civil_servant": ["CHE_BVG"]},
    },

    # ── Sweden ────────────────────────────────────────────────────────────
    # SWE has Income Pension NDC (Pillar 1). Missing: Premium Pension DC (Pillar 2) + Guarantee Pension (Pillar 0).
    {
        "iso3": "SWE",
        "schemes": [
            {
                "scheme_id": "SWE_PP",
                "name": "Premium Pension (Premiepension) – Mandatory DC",
                "tier": "second",
                "type": "DC",
                "coverage": "All workers in Sweden paying social insurance contributions; mandatory funded DC component alongside NDC income pension",
                "active": True,
                "eligibility": {
                    "normal_retirement_age_male": {
                        "value": 63,
                        "source_citation": "OECD PAG 2023 Sweden: Premium Pension can be drawn from age 63 (rising to 64 in 2026); flexible deferral to 70.",
                        "year": 2023,
                    },
                    "normal_retirement_age_female": {
                        "value": 63,
                        "source_citation": "OECD PAG 2023 Sweden: Premium Pension NRA 63 for both sexes.",
                        "year": 2023,
                    },
                    "vesting_years": {
                        "value": 0,
                        "source_citation": "Premium Pension: individual account; no vesting period.",
                        "year": 2023,
                    },
                    "minimum_contribution_years": {
                        "value": 0,
                        "source_citation": "Premium Pension: contributions recorded from first year of covered earnings.",
                        "year": 2023,
                    },
                },
                "contributions": {
                    "employee_rate": {
                        "value": 0.00,
                        "source_citation": "OECD PAG 2023 Sweden: 2.5% premium pension contribution paid entirely by employer (as part of total 18.5% social insurance fee).",
                        "year": 2023,
                    },
                    "employer_rate": {
                        "value": 0.025,
                        "source_citation": "OECD PAG 2023 Sweden: 2.5% of pensionable income directed to premium pension individual fund account (employer payroll tax).",
                        "year": 2023,
                    },
                    "total_rate": {
                        "value": 0.025,
                        "source_citation": "Derived: 2.5% total Premium Pension contribution (part of 18.5% total mandatory pension contribution).",
                        "year": 2023,
                    },
                    "contribution_ceiling_aw_multiple": {
                        "value": 7.5,
                        "source_citation": "OECD PAG 2023 Sweden: pension contributions apply up to 7.5× income base amount (IBB); IBB 2023 SEK 71,000 × 7.5 = SEK 532,500 ceiling.",
                        "year": 2023,
                    },
                    "contribution_base": "gross earnings (up to 7.5 IBB ceiling)",
                    "notes": "Contributions part of the 18.5% total mandatory pension contribution (16% NDC + 2.5% PP).",
                },
                "benefits": {
                    "accrual_rate_per_year": None,
                    "reference_wage": "career_average",
                    "valorization": "market",
                    "indexation": "market",
                    "minimum_benefit_aw_multiple": None,
                    "maximum_benefit_aw_multiple": None,
                },
                "payout": {
                    "type": "annuity",
                    "notes": "Individual fund choice from ~800 approved funds; default Sjunde AP-fonden (AP7 Såfa); annuitized at retirement.",
                },
            },
            {
                "scheme_id": "SWE_GP",
                "name": "Guarantee Pension (Garantipension) – Non-Contributory",
                "tier": "first",
                "type": "targeted",
                "coverage": "Swedish residents aged 65+ with low or zero income pension; full guarantee for zero contributory earnings; reduced for those with income pension up to ~SEK 12,000/month",
                "active": True,
                "eligibility": {
                    "normal_retirement_age_male": {
                        "value": 65,
                        "source_citation": "OECD PAG 2023 Sweden: Guarantee Pension payable from age 65 (rising to 66 in 2026); requires 40 years of Swedish residence for full benefit.",
                        "year": 2023,
                    },
                    "normal_retirement_age_female": {
                        "value": 65,
                        "source_citation": "OECD PAG 2023 Sweden: Guarantee Pension NRA 65 for both sexes.",
                        "year": 2023,
                    },
                },
                "benefits": {
                    "minimum_benefit_aw_multiple": {
                        "value": 0.202,
                        "source_citation": "OECD PAG 2023 Sweden: Guarantee Pension single rate SEK 9,573/month = SEK 114,876/year ≈ 20.2% of AW (SEK 569,000).",
                        "year": 2023,
                    },
                    "maximum_benefit_aw_multiple": {
                        "value": 0.202,
                        "source_citation": "OECD PAG 2023 Sweden: maximum guarantee for those with zero income pension; phases out with income pension.",
                        "year": 2023,
                    },
                    "indexation": "CPI",
                },
                "payout": {
                    "type": "annuity",
                    "notes": "Monthly payment from general revenues; income-tested against NDC + Premium Pension income.",
                },
            },
        ],
        "worker_type_updates": {"private_employee": ["SWE_PP"], "civil_servant": ["SWE_PP"]},
    },

    # ── Denmark ───────────────────────────────────────────────────────────
    # DNK has Folkepension (basic, Pillar 0). Missing: ATP (quasi-mandatory DC, Pillar 2).
    {
        "iso3": "DNK",
        "schemes": [
            {
                "scheme_id": "DNK_ATP",
                "name": "Supplementary Labour Market Pension (ATP)",
                "tier": "second",
                "type": "DC",
                "coverage": "All wage earners and most self-employed; quasi-mandatory through labor agreements covering ~95% of workforce",
                "active": True,
                "eligibility": {
                    "normal_retirement_age_male": {
                        "value": 67,
                        "source_citation": "OECD PAG 2023 Denmark: ATP drawdown from age 67 (linked to Folkepension eligibility age).",
                        "year": 2023,
                    },
                    "normal_retirement_age_female": {
                        "value": 67,
                        "source_citation": "OECD PAG 2023 Denmark: ATP NRA 67 for both sexes.",
                        "year": 2023,
                    },
                    "vesting_years": {
                        "value": 0,
                        "source_citation": "ATP: individual account; vests immediately.",
                        "year": 2023,
                    },
                    "minimum_contribution_years": {
                        "value": 0,
                        "source_citation": "ATP: no minimum; accounts credited from first year of covered employment.",
                        "year": 2023,
                    },
                },
                "contributions": {
                    "employee_rate": {
                        "value": 0.009,
                        "source_citation": "OECD PAG 2023 Denmark: ATP employee contribution DKK 1,186/year = approx 0.9% of AW (DKK 131,000). Fixed DKK amount, not % of earnings.",
                        "year": 2023,
                    },
                    "employer_rate": {
                        "value": 0.018,
                        "source_citation": "OECD PAG 2023 Denmark: ATP employer contribution 2× employee = DKK 2,372/year ≈ 1.8% of AW. Fixed DKK amount.",
                        "year": 2023,
                    },
                    "total_rate": {
                        "value": 0.027,
                        "source_citation": "Derived: DKK 3,558/year total ATP ≈ 2.7% of AW. Note: ATP uses fixed DKK contributions, not earnings-percentage.",
                        "year": 2023,
                    },
                    "contribution_ceiling_aw_multiple": None,
                    "contribution_base": "fixed DKK annual contribution (not percentage of earnings)",
                    "notes": "ATP contributions are fixed DKK amounts (DKK 3,558 total/year 2023), not earnings-related. Rates above are AW-equivalents for comparison only.",
                },
                "benefits": {
                    "accrual_rate_per_year": None,
                    "reference_wage": None,
                    "valorization": "market",
                    "indexation": "market",
                    "minimum_benefit_aw_multiple": None,
                    "maximum_benefit_aw_multiple": None,
                },
                "payout": {
                    "type": "annuity",
                    "notes": "Lifelong annuity from account balance at retirement; includes bonus adjustments.",
                },
            }
        ],
        "worker_type_updates": {"private_employee": ["DNK_ATP"], "civil_servant": ["DNK_ATP"]},
    },

    # ── Finland ───────────────────────────────────────────────────────────
    # FIN has Earnings-related pension (DB, Pillar 1). Missing: National Pension (targeted, Pillar 0).
    {
        "iso3": "FIN",
        "schemes": [
            {
                "scheme_id": "FIN_KANSANELAKE",
                "name": "National Pension (Kansaneläke) – Means-Tested",
                "tier": "first",
                "type": "targeted",
                "coverage": "Finnish residents aged 65+ with low or zero earnings-related pension; full pension for those with zero earnings pension, phased out with higher earnings pension",
                "active": True,
                "eligibility": {
                    "normal_retirement_age_male": {
                        "value": 65,
                        "source_citation": "OECD PAG 2023 Finland: National Pension payable from age 65 (early from 63 with reduction).",
                        "year": 2023,
                    },
                    "normal_retirement_age_female": {
                        "value": 65,
                        "source_citation": "OECD PAG 2023 Finland: National Pension NRA 65 for both sexes.",
                        "year": 2023,
                    },
                },
                "benefits": {
                    "minimum_benefit_aw_multiple": {
                        "value": 0.203,
                        "source_citation": "OECD PAG 2023 Finland: full National Pension single €886/month = €10,632/year ≈ 20.3% of AW (€52,200).",
                        "year": 2023,
                    },
                    "maximum_benefit_aw_multiple": {
                        "value": 0.203,
                        "source_citation": "OECD PAG 2023 Finland: maximum for those with zero earnings pension; reduced €1 for €2 of earnings pension above threshold.",
                        "year": 2023,
                    },
                    "indexation": "CPI",
                },
                "payout": {
                    "type": "annuity",
                    "notes": "Monthly payment from general revenues via Kela (Social Insurance Institution of Finland).",
                },
            }
        ],
        "worker_type_updates": {},
    },

    # ── Norway ────────────────────────────────────────────────────────────
    # NOR has Earnings-related NDC (Pillar 1). Missing: Minimum Pension Guarantee (Pillar 0).
    {
        "iso3": "NOR",
        "schemes": [
            {
                "scheme_id": "NOR_MINPENSION",
                "name": "Minimum Pension Guarantee (Garantipensjon)",
                "tier": "first",
                "type": "minimum",
                "coverage": "All Norwegian residents aged 67+ with low contributory pension entitlement; full guarantee for those with zero earnings history",
                "active": True,
                "eligibility": {
                    "normal_retirement_age_male": {
                        "value": 67,
                        "source_citation": "OECD PAG 2023 Norway: Minimum Pension Guarantee (Garantipensjon) payable from age 67.",
                        "year": 2023,
                    },
                    "normal_retirement_age_female": {
                        "value": 67,
                        "source_citation": "OECD PAG 2023 Norway: Garantipensjon NRA 67 for both sexes.",
                        "year": 2023,
                    },
                },
                "benefits": {
                    "minimum_benefit_aw_multiple": {
                        "value": 0.257,
                        "source_citation": "OECD PAG 2023 Norway: Garantipensjon single rate NOK 204,690/year ≈ 25.7% of AW (NOK 796,100).",
                        "year": 2023,
                    },
                    "maximum_benefit_aw_multiple": {
                        "value": 0.257,
                        "source_citation": "OECD PAG 2023 Norway: full guarantee for zero earnings; reduced kroner-for-kroner above threshold.",
                        "year": 2023,
                    },
                    "indexation": "mixed",
                },
                "payout": {
                    "type": "annuity",
                    "notes": "Monthly benefit from National Insurance (NAV); reduced as earnings-related pension (inntektspensjon) rises.",
                },
            }
        ],
        "worker_type_updates": {},
    },

    # ── South Korea ───────────────────────────────────────────────────────
    # KOR has NPS (DB, Pillar 1). Missing: Basic Pension (targeted, Pillar 0).
    {
        "iso3": "KOR",
        "schemes": [
            {
                "scheme_id": "KOR_BASICPENSION",
                "name": "Basic Pension (기초연금) – Means-Tested",
                "tier": "first",
                "type": "targeted",
                "coverage": "Bottom 70% of income distribution among Koreans aged 65+; approximately 6.6 million recipients (2023)",
                "active": True,
                "eligibility": {
                    "normal_retirement_age_male": {
                        "value": 65,
                        "source_citation": "OECD PAG 2023 Korea: Basic Pension payable from age 65 to bottom 70% of seniors by income.",
                        "year": 2023,
                    },
                    "normal_retirement_age_female": {
                        "value": 65,
                        "source_citation": "OECD PAG 2023 Korea: Basic Pension NRA 65 for both sexes.",
                        "year": 2023,
                    },
                },
                "benefits": {
                    "minimum_benefit_aw_multiple": {
                        "value": 0.091,
                        "source_citation": "OECD PAG 2023 Korea: Basic Pension maximum KRW 323,180/month (2023) × 12 = KRW 3,878,160 ≈ 9.1% of AW (KRW 42,700,000).",
                        "year": 2023,
                    },
                    "maximum_benefit_aw_multiple": {
                        "value": 0.091,
                        "source_citation": "OECD PAG 2023 Korea: full rate for zero-NPS income; reduced for NPS recipients.",
                        "year": 2023,
                    },
                    "indexation": "CPI",
                },
                "payout": {
                    "type": "annuity",
                    "notes": "Monthly payment; means-tested on income recognition amount; funded from general revenues.",
                },
            }
        ],
        "worker_type_updates": {},
    },

    # ── United Kingdom ────────────────────────────────────────────────────
    # GBR has New State Pension (basic, Pillar 1). Missing: auto-enrollment (DC, Pillar 2) + Pension Credit (targeted, Pillar 0).
    {
        "iso3": "GBR",
        "schemes": [
            {
                "scheme_id": "GBR_AUTOENROLL",
                "name": "Workplace Pension – Auto-Enrollment",
                "tier": "second",
                "type": "DC",
                "coverage": "All employees aged 22-66 earning above £10,000/year; auto-enrolled since 2012; opt-out permitted",
                "active": True,
                "eligibility": {
                    "normal_retirement_age_male": {
                        "value": 55,
                        "source_citation": "UK Pensions Act 2004: minimum pension age 55 (rising to 57 in 2028); most take funds alongside State Pension at 66.",
                        "year": 2023,
                    },
                    "normal_retirement_age_female": {
                        "value": 55,
                        "source_citation": "UK Pensions Act 2004: minimum pension age 55 for both sexes.",
                        "year": 2023,
                    },
                    "vesting_years": {
                        "value": 0,
                        "source_citation": "UK auto-enrollment: individual account; fully owned from first contribution.",
                        "year": 2023,
                    },
                    "minimum_contribution_years": {
                        "value": 0,
                        "source_citation": "UK auto-enrollment: no minimum contribution period.",
                        "year": 2023,
                    },
                },
                "contributions": {
                    "employee_rate": {
                        "value": 0.05,
                        "source_citation": "OECD PAG 2023 UK: minimum employee contribution 5% of qualifying earnings (including 1% tax relief).",
                        "year": 2023,
                    },
                    "employer_rate": {
                        "value": 0.03,
                        "source_citation": "OECD PAG 2023 UK: minimum employer contribution 3% of qualifying earnings.",
                        "year": 2023,
                    },
                    "total_rate": {
                        "value": 0.08,
                        "source_citation": "Derived: 5% + 3% = 8% minimum total auto-enrollment contribution.",
                        "year": 2023,
                    },
                    "contribution_ceiling_aw_multiple": None,
                    "contribution_base": "qualifying earnings (£6,240–£50,270 band, 2023)",
                    "notes": "Qualifying earnings band 2023: £6,240–£50,270. Employee contribution includes 1% basic rate tax relief.",
                },
                "benefits": {
                    "accrual_rate_per_year": None,
                    "reference_wage": "career_average",
                    "valorization": "market",
                    "indexation": "market",
                    "minimum_benefit_aw_multiple": None,
                    "maximum_benefit_aw_multiple": None,
                },
                "payout": {
                    "type": "lump_sum",
                    "notes": "Flexible access from age 55 (57 from 2028); annuity, drawdown, or lump sum; 25% tax-free lump sum allowed.",
                },
            },
            {
                "scheme_id": "GBR_PENSIONCREDIT",
                "name": "Pension Credit – Means-Tested",
                "tier": "first",
                "type": "targeted",
                "coverage": "UK residents aged 66+ with income below guarantee credit threshold; approximately 1.4 million households receive Pension Credit",
                "active": True,
                "eligibility": {
                    "normal_retirement_age_male": {
                        "value": 66,
                        "source_citation": "DWP UK: Pension Credit (Guarantee Credit) claimable from State Pension age 66.",
                        "year": 2023,
                    },
                    "normal_retirement_age_female": {
                        "value": 66,
                        "source_citation": "DWP UK: Pension Credit NRA 66 for both sexes.",
                        "year": 2023,
                    },
                },
                "benefits": {
                    "minimum_benefit_aw_multiple": {
                        "value": 0.192,
                        "source_citation": "DWP UK: Pension Credit (Guarantee Credit) minimum income £201.05/week single (2023) × 52 = £10,455 ≈ 19.2% of AW (£54,400).",
                        "year": 2023,
                    },
                    "maximum_benefit_aw_multiple": {
                        "value": 0.192,
                        "source_citation": "DWP UK: Guarantee Credit tops up income to £201.05/week; any income above this reduces entitlement pound-for-pound.",
                        "year": 2023,
                    },
                    "indexation": "CPI",
                },
                "payout": {
                    "type": "annuity",
                    "notes": "Weekly payment from DWP general revenues; means-tested on all income and some capital.",
                },
            },
        ],
        "worker_type_updates": {"private_employee": ["GBR_AUTOENROLL"], "civil_servant": ["GBR_AUTOENROLL"]},
    },

    # ── Brazil ────────────────────────────────────────────────────────────
    # BRA has RGPS (DB, Pillar 1). Missing: BPC (means-tested, Pillar 0).
    {
        "iso3": "BRA",
        "schemes": [
            {
                "scheme_id": "BRA_BPC",
                "name": "Benefício de Prestação Continuada (BPC) – Means-Tested",
                "tier": "first",
                "type": "targeted",
                "coverage": "Brazilian residents aged 65+ with household per capita income below ¼ of minimum wage; approximately 2.5 million elderly recipients (2023)",
                "active": True,
                "eligibility": {
                    "normal_retirement_age_male": {
                        "value": 65,
                        "source_citation": "Lei Orgânica da Assistência Social (LOAS): BPC payable from age 65 to low-income elderly.",
                        "year": 2023,
                    },
                    "normal_retirement_age_female": {
                        "value": 65,
                        "source_citation": "LOAS Brazil: BPC NRA 65 for both sexes.",
                        "year": 2023,
                    },
                },
                "benefits": {
                    "minimum_benefit_aw_multiple": {
                        "value": 0.175,
                        "source_citation": "BPC benefit = 1 minimum wage (BRL 1,320/month in 2023) × 12 = BRL 15,840 ≈ 17.5% of AW (BRL 90,700).",
                        "year": 2023,
                    },
                    "maximum_benefit_aw_multiple": {
                        "value": 0.175,
                        "source_citation": "BPC is flat at 1 minimum wage; no top-up.",
                        "year": 2023,
                    },
                    "indexation": "minimum_wage",
                },
                "payout": {
                    "type": "annuity",
                    "notes": "Monthly payment from INSS/MDS; means-tested on household per capita income < ¼ minimum wage; reviewed every 2 years.",
                },
            }
        ],
        "worker_type_updates": {},
    },

    # ── Chile ─────────────────────────────────────────────────────────────
    # CHL has AFP (DC, Pillar 2). Missing: Pensión Garantizada Universal/PGU (basic, Pillar 0).
    {
        "iso3": "CHL",
        "schemes": [
            {
                "scheme_id": "CHL_PGU",
                "name": "Pensión Garantizada Universal (PGU) – Basic",
                "tier": "first",
                "type": "basic",
                "coverage": "All Chileans aged 65+ in bottom 90% of income distribution; universal basic pension replacing the previous APS solidarity pillar (since March 2022)",
                "active": True,
                "eligibility": {
                    "normal_retirement_age_male": {
                        "value": 65,
                        "source_citation": "Ley 21.419 (Chile, 2022): PGU payable from age 65 to Chilean residents in bottom 90% income distribution.",
                        "year": 2023,
                    },
                    "normal_retirement_age_female": {
                        "value": 60,
                        "source_citation": "Ley 21.419 (Chile, 2022): PGU payable from age 60 for women, 65 for men.",
                        "year": 2023,
                    },
                },
                "benefits": {
                    "flat_rate_aw_multiple": {
                        "value": 0.162,
                        "source_citation": "OECD PAG 2023 Chile: PGU CLP 214,296/month (2023) × 12 = CLP 2,571,552 ≈ 16.2% of AW (CLP 15,870,000).",
                        "year": 2023,
                    },
                    "indexation": "CPI",
                },
                "payout": {
                    "type": "annuity",
                    "notes": "Monthly payment from general revenues; income-tested against total pension income including AFP.",
                },
            }
        ],
        "worker_type_updates": {},
    },

    # ── Mexico ────────────────────────────────────────────────────────────
    # MEX has IMSS mandatory DC accounts (AFORE, Pillar 2). Missing: Bienestar 65+ non-contributory (Pillar 0).
    {
        "iso3": "MEX",
        "schemes": [
            {
                "scheme_id": "MEX_BIENESTAR",
                "name": "Pensión para el Bienestar de los Adultos Mayores – Non-Contributory",
                "tier": "first",
                "type": "basic",
                "coverage": "All Mexican residents aged 65+; universal non-contributory pension; approximately 10.5 million recipients (2023)",
                "active": True,
                "eligibility": {
                    "normal_retirement_age_male": {
                        "value": 65,
                        "source_citation": "DOF Mexico: Bienestar 65+ universal pension payable from age 65.",
                        "year": 2023,
                    },
                    "normal_retirement_age_female": {
                        "value": 65,
                        "source_citation": "DOF Mexico: Bienestar 65+ NRA 65 for both sexes.",
                        "year": 2023,
                    },
                },
                "benefits": {
                    "flat_rate_aw_multiple": {
                        "value": 0.082,
                        "source_citation": "IMSS/SEDESOL Mexico: Bienestar 65+ MXN 3,000/month (Jan 2024) × 12 = MXN 36,000 ≈ 8.2% of AW (MXN 438,000).",
                        "year": 2023,
                    },
                    "indexation": "CPI",
                },
                "payout": {
                    "type": "annuity",
                    "notes": "Bimonthly payment of MXN 6,000 per 2 months; funded from federal budget. No contributions required.",
                },
            }
        ],
        "worker_type_updates": {},
    },

    # ── South Africa ──────────────────────────────────────────────────────
    # ZAF has Government Employees Pension Fund (DB, Pillar 1). Missing: Old Age Grant (targeted, Pillar 0).
    {
        "iso3": "ZAF",
        "schemes": [
            {
                "scheme_id": "ZAF_OAG",
                "name": "Old Age Grant (Social Pension) – Means-Tested",
                "tier": "first",
                "type": "targeted",
                "coverage": "South African residents aged 60+ who pass means test; approximately 3.9 million elderly recipients (2023); covers majority of elderly outside formal employment",
                "active": True,
                "eligibility": {
                    "normal_retirement_age_male": {
                        "value": 60,
                        "source_citation": "Social Assistance Act 2004 South Africa: Old Age Grant payable from age 60 for both sexes.",
                        "year": 2023,
                    },
                    "normal_retirement_age_female": {
                        "value": 60,
                        "source_citation": "Social Assistance Act 2004 South Africa: Old Age Grant NRA 60 for both sexes.",
                        "year": 2023,
                    },
                },
                "benefits": {
                    "minimum_benefit_aw_multiple": {
                        "value": 0.063,
                        "source_citation": "SASSA South Africa: Old Age Grant ZAR 2,090/month (2023) × 12 = ZAR 25,080 ≈ 6.3% of AW (ZAR 399,600).",
                        "year": 2023,
                    },
                    "maximum_benefit_aw_multiple": {
                        "value": 0.073,
                        "source_citation": "SASSA: those aged 75+ receive ZAR 2,110/month = ZAR 25,320 ≈ 7.3% of AW.",
                        "year": 2023,
                    },
                    "indexation": "CPI",
                },
                "payout": {
                    "type": "annuity",
                    "notes": "Monthly payment via SASSA; means-tested on income and assets; funded from general revenues.",
                },
            }
        ],
        "worker_type_updates": {},
    },

    # ── Argentina ─────────────────────────────────────────────────────────
    # ARG has ANSES DB pension. Missing: PUAM (non-contributory universal, Pillar 0).
    {
        "iso3": "ARG",
        "schemes": [
            {
                "scheme_id": "ARG_PUAM",
                "name": "Prestación Universal para el Adulto Mayor (PUAM) – Non-Contributory",
                "tier": "first",
                "type": "basic",
                "coverage": "Argentine residents aged 65+ without sufficient contributory pension entitlement; approximately 700,000 recipients (2023)",
                "active": True,
                "eligibility": {
                    "normal_retirement_age_male": {
                        "value": 65,
                        "source_citation": "Ley 27.260 Argentina (2016): PUAM payable from age 65 for both sexes.",
                        "year": 2023,
                    },
                    "normal_retirement_age_female": {
                        "value": 65,
                        "source_citation": "Ley 27.260 Argentina: PUAM NRA 65 for both sexes.",
                        "year": 2023,
                    },
                },
                "benefits": {
                    "flat_rate_aw_multiple": {
                        "value": 0.225,
                        "source_citation": "ANSES Argentina: PUAM = 80% of minimum contributory pension (haber mínimo); minimum pension ≈ 28% AW → PUAM ≈ 22.5% AW.",
                        "year": 2023,
                    },
                    "indexation": "wages",
                },
                "payout": {
                    "type": "annuity",
                    "notes": "80% of minimum contributory pension (haber mínimo jubilatorio); incompatible with other pensions.",
                },
            }
        ],
        "worker_type_updates": {},
    },

    # ── Colombia ──────────────────────────────────────────────────────────
    # COL currently has COLPENSIONES DB. Missing: Colombia Mayor non-contributory (Pillar 0).
    {
        "iso3": "COL",
        "schemes": [
            {
                "scheme_id": "COL_COLOMBIAMAYOR",
                "name": "Colombia Mayor – Non-Contributory Subsidy",
                "tier": "first",
                "type": "targeted",
                "coverage": "Colombians aged 55 (women) / 60 (men) in extreme poverty without formal pension; approximately 1.8 million recipients (2023)",
                "active": True,
                "eligibility": {
                    "normal_retirement_age_male": {
                        "value": 60,
                        "source_citation": "Decreto 3771 (Colombia): Colombia Mayor payable from age 60 for men in extreme poverty.",
                        "year": 2023,
                    },
                    "normal_retirement_age_female": {
                        "value": 55,
                        "source_citation": "Decreto 3771 (Colombia): Colombia Mayor payable from age 55 for women.",
                        "year": 2023,
                    },
                },
                "benefits": {
                    "minimum_benefit_aw_multiple": {
                        "value": 0.022,
                        "source_citation": "Prosperidad Social Colombia: Colombia Mayor urban subsidy COP 80,000/month × 12 = COP 960,000 ≈ 2.2% of AW (COP 43,500,000).",
                        "year": 2023,
                    },
                    "maximum_benefit_aw_multiple": {
                        "value": 0.036,
                        "source_citation": "Prosperidad Social Colombia: some rural beneficiaries receive COP 130,000/month = COP 1,560,000 ≈ 3.6% of AW.",
                        "year": 2023,
                    },
                    "indexation": "CPI",
                },
                "payout": {
                    "type": "annuity",
                    "notes": "Bimonthly transfer via bank/digital payment; means-tested on SISBEN poverty index; funded from general revenues.",
                },
            }
        ],
        "worker_type_updates": {},
    },

    # ── Peru ──────────────────────────────────────────────────────────────
    # PER has AFP DC. Missing: Pensión 65 non-contributory (Pillar 0).
    {
        "iso3": "PER",
        "schemes": [
            {
                "scheme_id": "PER_PENSION65",
                "name": "Pensión 65 – Non-Contributory",
                "tier": "first",
                "type": "basic",
                "coverage": "Peruvians aged 65+ in extreme poverty not covered by formal pension; approximately 600,000 recipients (2023); primarily rural and indigenous communities",
                "active": True,
                "eligibility": {
                    "normal_retirement_age_male": {
                        "value": 65,
                        "source_citation": "Decreto Supremo 081-2011-PCM Peru: Pensión 65 payable from age 65.",
                        "year": 2023,
                    },
                    "normal_retirement_age_female": {
                        "value": 65,
                        "source_citation": "Decreto Supremo 081-2011-PCM Peru: Pensión 65 NRA 65 for both sexes.",
                        "year": 2023,
                    },
                },
                "benefits": {
                    "flat_rate_aw_multiple": {
                        "value": 0.041,
                        "source_citation": "MIDIS Peru: Pensión 65 PEN 250/month × 12 = PEN 3,000 ≈ 4.1% of AW (PEN 72,000).",
                        "year": 2023,
                    },
                    "indexation": "CPI",
                },
                "payout": {
                    "type": "annuity",
                    "notes": "Bimonthly transfer PEN 500 per payment; means-tested on SISFOH poverty index; funded from general revenues.",
                },
            }
        ],
        "worker_type_updates": {},
    },

    # ── Japan ─────────────────────────────────────────────────────────────
    # JPN has Employees' Pension (Kosei Nenkin, DB, Pillar 1). Missing: Basic Pension/Kokumin Nenkin (Pillar 0/1).
    {
        "iso3": "JPN",
        "schemes": [
            {
                "scheme_id": "JPN_KOKUMIN",
                "name": "National Pension (Kokumin Nenkin) – Universal Basic",
                "tier": "first",
                "type": "basic",
                "coverage": "All Japanese residents aged 20-59 (mandatory); self-employed, non-employed, and students. Employees receive this as the first-tier component of Kosei Nenkin.",
                "active": True,
                "eligibility": {
                    "normal_retirement_age_male": {
                        "value": 65,
                        "source_citation": "OECD PAG 2023 Japan: National Pension (Kokumin Nenkin) NRA 65 for both sexes; early from 60 with reduction.",
                        "year": 2023,
                    },
                    "normal_retirement_age_female": {
                        "value": 65,
                        "source_citation": "OECD PAG 2023 Japan: National Pension NRA 65 for both sexes.",
                        "year": 2023,
                    },
                    "vesting_years": {
                        "value": 10,
                        "source_citation": "OECD PAG 2023 Japan: minimum 10 years of contributions (120 months) for any pension entitlement; 40 years for full pension.",
                        "year": 2023,
                    },
                    "minimum_contribution_years": {
                        "value": 10,
                        "source_citation": "Japanese Pension Act: 10-year minimum for any basic pension entitlement.",
                        "year": 2023,
                    },
                },
                "contributions": {
                    "employee_rate": {
                        "value": 0.0795,
                        "source_citation": "OECD PAG 2023 Japan: Kosei Nenkin total rate 18.3% (2017-) split equally; 9.15% employee. Kokumin Nenkin for self-employed: flat JPY 16,520/month (2023) ≈ 7.95% of AW.",
                        "year": 2023,
                    },
                    "employer_rate": {
                        "value": 0.0795,
                        "source_citation": "OECD PAG 2023 Japan: Kosei Nenkin 9.15% employer; total 18.3% split equally.",
                        "year": 2023,
                    },
                    "total_rate": {
                        "value": 0.159,
                        "source_citation": "Derived: Kosei Nenkin 18.3% total (includes both Kokumin and Kosei tiers); 15.9% here refers to Kosei portion excl. spouse/child supplements.",
                        "year": 2023,
                    },
                    "contribution_ceiling_aw_multiple": None,
                    "contribution_base": "monthly standardised remuneration (monthly salary banded into 30 grades)",
                    "notes": "National Pension (Tier 1) flat contribution JPY 16,520/month for self-employed. Employees pay via Kosei Nenkin which covers both tiers.",
                },
                "benefits": {
                    "flat_rate_aw_multiple": {
                        "value": 0.178,
                        "source_citation": "OECD PAG 2023 Japan: full National Pension JPY 795,000/year (2023) ≈ 17.8% of AW (JPY 4,460,000).",
                        "year": 2023,
                    },
                    "indexation": "mixed",
                },
                "payout": {
                    "type": "annuity",
                    "notes": "Monthly annuity from GPIF-managed reserves; proportional for less than 40 years of contributions.",
                },
            }
        ],
        "worker_type_updates": {},
    },

    # ── Germany ───────────────────────────────────────────────────────────
    # DEU has Rentenversicherung (Points, Pillar 1). Missing: Grundrente/Grundsicherung minimum (Pillar 0).
    {
        "iso3": "DEU",
        "schemes": [
            {
                "scheme_id": "DEU_GRUNDSICHERUNG",
                "name": "Grundsicherung im Alter (Basic Income Security) – Means-Tested",
                "tier": "first",
                "type": "targeted",
                "coverage": "German residents aged 65+ whose total income falls below the socio-cultural minimum; approximately 650,000 elderly recipients (2023)",
                "active": True,
                "eligibility": {
                    "normal_retirement_age_male": {
                        "value": 65,
                        "source_citation": "SGB XII Germany: Grundsicherung im Alter payable from age 65+ (gradually from 65 to 67).",
                        "year": 2023,
                    },
                    "normal_retirement_age_female": {
                        "value": 65,
                        "source_citation": "SGB XII Germany: Grundsicherung im Alter NRA 65 for both sexes.",
                        "year": 2023,
                    },
                },
                "benefits": {
                    "minimum_benefit_aw_multiple": {
                        "value": 0.193,
                        "source_citation": "BMAS Germany: Grundsicherung standard need €563/month (2023) + housing/heating ≈ €930/month total ≈ 19.3% of AW (€58,000).",
                        "year": 2023,
                    },
                    "maximum_benefit_aw_multiple": {
                        "value": 0.193,
                        "source_citation": "BMAS Germany: benefit tops up total income to subsistence minimum; reduces euro-for-euro with other income.",
                        "year": 2023,
                    },
                    "indexation": "CPI",
                },
                "payout": {
                    "type": "annuity",
                    "notes": "Monthly payment from local authority social offices (Sozialamt); asset-tested and income-tested. Does not require asset claw-back from adult children since 2020.",
                },
            }
        ],
        "worker_type_updates": {},
    },

    # ── United States ─────────────────────────────────────────────────────
    # USA has Social Security (DB, Pillar 1). Missing: SSI (means-tested, Pillar 0).
    {
        "iso3": "USA",
        "schemes": [
            {
                "scheme_id": "USA_SSI",
                "name": "Supplemental Security Income (SSI) – Means-Tested",
                "tier": "first",
                "type": "targeted",
                "coverage": "US residents aged 65+ (or disabled) with very low income and assets; approximately 1.2 million elderly SSI recipients (2023); federal supplement plus state top-ups",
                "active": True,
                "eligibility": {
                    "normal_retirement_age_male": {
                        "value": 65,
                        "source_citation": "SSA USA: SSI payable from age 65 (or any age if disabled); means-tested on income and countable resources.",
                        "year": 2023,
                    },
                    "normal_retirement_age_female": {
                        "value": 65,
                        "source_citation": "SSA USA: SSI NRA 65 for both sexes.",
                        "year": 2023,
                    },
                },
                "benefits": {
                    "minimum_benefit_aw_multiple": {
                        "value": 0.082,
                        "source_citation": "SSA USA: federal SSI maximum $914/month single (2023) × 12 = $10,968 ≈ 8.2% of AW ($133,700).",
                        "year": 2023,
                    },
                    "maximum_benefit_aw_multiple": {
                        "value": 0.082,
                        "source_citation": "SSA USA: federal maximum SSI single $914/month. Many states add state supplements.",
                        "year": 2023,
                    },
                    "indexation": "CPI",
                },
                "payout": {
                    "type": "annuity",
                    "notes": "Monthly federal payment; asset limit $2,000 single; income-tested. States may add supplemental payments. Counted separately from Social Security benefits.",
                },
            }
        ],
        "worker_type_updates": {},
    },

    # ── Turkey ────────────────────────────────────────────────────────────
    # TUR has SGK (DB, Pillar 1). Missing: Social Assistance (Pillar 0) for those without pension.
    {
        "iso3": "TUR",
        "schemes": [
            {
                "scheme_id": "TUR_YAŞLIBAKIM",
                "name": "Elderly Social Assistance (65 Yaş Aylığı) – Non-Contributory",
                "tier": "first",
                "type": "targeted",
                "coverage": "Turkish citizens aged 65+ without any social insurance pension and with income below means-test threshold; approximately 1.2 million recipients (2023)",
                "active": True,
                "eligibility": {
                    "normal_retirement_age_male": {
                        "value": 65,
                        "source_citation": "Law 2022/2657 Turkey: 65 Yaş Aylığı (elderly monthly allowance) payable from age 65 to low-income non-pensioners.",
                        "year": 2023,
                    },
                    "normal_retirement_age_female": {
                        "value": 65,
                        "source_citation": "Law 2022/2657 Turkey: elderly allowance NRA 65 for both sexes.",
                        "year": 2023,
                    },
                },
                "benefits": {
                    "minimum_benefit_aw_multiple": {
                        "value": 0.046,
                        "source_citation": "SYDGM Turkey: 65 Yaş Aylığı TRY 3,000/month (2023) × 12 = TRY 36,000 ≈ 4.6% of AW (TRY 780,000).",
                        "year": 2023,
                    },
                    "maximum_benefit_aw_multiple": {
                        "value": 0.046,
                        "source_citation": "Turkey elderly allowance: flat TRY 3,000/month; no top-up.",
                        "year": 2023,
                    },
                    "indexation": "CPI",
                },
                "payout": {
                    "type": "annuity",
                    "notes": "Monthly means-tested payment from Ministry of Family and Social Services (ASPB); funded from general revenues.",
                },
            }
        ],
        "worker_type_updates": {},
    },

    # ── Russia ────────────────────────────────────────────────────────────
    # RUS has OP (Points/NDC, Pillar 1). Missing: Social Pension (Pillar 0) for non-contributors.
    {
        "iso3": "RUS",
        "schemes": [
            {
                "scheme_id": "RUS_SOCIALPENSION",
                "name": "Social Pension (Социальная пенсия) – Non-Contributory",
                "tier": "first",
                "type": "basic",
                "coverage": "Russian citizens aged 65+ (men) / 60+ (women) without insurance pension entitlement; also disabled persons",
                "active": True,
                "eligibility": {
                    "normal_retirement_age_male": {
                        "value": 70,
                        "source_citation": "Federal Law No. 166-FZ Russia: Social Pension payable 5 years after standard NRA — age 70 men (NRA 65) and 65 women (NRA 60).",
                        "year": 2023,
                    },
                    "normal_retirement_age_female": {
                        "value": 65,
                        "source_citation": "Federal Law No. 166-FZ Russia: Social Pension for women 5 years after NRA of 60 = age 65.",
                        "year": 2023,
                    },
                },
                "benefits": {
                    "minimum_benefit_aw_multiple": {
                        "value": 0.070,
                        "source_citation": "PFR Russia: Social Old-Age Pension RUB 6,627/month (2023) × 12 = RUB 79,524 ≈ 7.0% of AW (RUB 1,139,000).",
                        "year": 2023,
                    },
                    "maximum_benefit_aw_multiple": {
                        "value": 0.070,
                        "source_citation": "Russia social pension: flat rate; no top-up.",
                        "year": 2023,
                    },
                    "indexation": "CPI",
                },
                "payout": {
                    "type": "annuity",
                    "notes": "Monthly payment from Pension Fund of Russia (SFR); paid 5 years after standard retirement age to ensure contributory pension priority.",
                },
            }
        ],
        "worker_type_updates": {},
    },

    # ── India ─────────────────────────────────────────────────────────────
    # IND has EPS (DB, Pillar 1) + EPFO (DC). Missing: IGNOAPS non-contributory (Pillar 0).
    {
        "iso3": "IND",
        "schemes": [
            {
                "scheme_id": "IND_IGNOAPS",
                "name": "Indira Gandhi National Old Age Pension Scheme (IGNOAPS) – Non-Contributory",
                "tier": "first",
                "type": "targeted",
                "coverage": "Indian citizens aged 60+ below the poverty line; approximately 22 million beneficiaries (2023); funded under National Social Assistance Programme",
                "active": True,
                "eligibility": {
                    "normal_retirement_age_male": {
                        "value": 60,
                        "source_citation": "Ministry of Rural Development India: IGNOAPS payable from age 60; enhanced benefit from age 80.",
                        "year": 2023,
                    },
                    "normal_retirement_age_female": {
                        "value": 60,
                        "source_citation": "Ministry of Rural Development India: IGNOAPS NRA 60 for both sexes.",
                        "year": 2023,
                    },
                },
                "benefits": {
                    "minimum_benefit_aw_multiple": {
                        "value": 0.003,
                        "source_citation": "MoRD India: IGNOAPS central benefit INR 200/month (60-79) × 12 = INR 2,400. With state top-ups avg ≈ INR 500-1500/month. Central share ≈ 0.3% of AW (INR 700,000).",
                        "year": 2023,
                    },
                    "maximum_benefit_aw_multiple": {
                        "value": 0.007,
                        "source_citation": "MoRD India: IGNOAPS INR 500/month for those 80+ (central share) × 12 = INR 6,000 ≈ 0.7% of AW. States supplement substantially.",
                        "year": 2023,
                    },
                    "indexation": "CPI",
                },
                "payout": {
                    "type": "annuity",
                    "notes": "Monthly transfer; central contribution INR 200-500/month supplemented by state governments (total varies INR 500–3,000/month by state). Targeted at BPL households.",
                },
            }
        ],
        "worker_type_updates": {},
    },

    # ── Israel ────────────────────────────────────────────────────────────
    # ISR has Mandatory Pension (DC, Pillar 2). Missing: Old Age Allowance (universal, Pillar 0).
    {
        "iso3": "ISR",
        "schemes": [
            {
                "scheme_id": "ISR_OAA",
                "name": "Old Age Allowance (קצבת זקנה) – Universal",
                "tier": "first",
                "type": "basic",
                "coverage": "All Israeli residents who paid National Insurance contributions for at least 60 qualifying months (or 144 months total) and reached NRA; effectively universal",
                "active": True,
                "eligibility": {
                    "normal_retirement_age_male": {
                        "value": 67,
                        "source_citation": "OECD PAG 2023 Israel: Old Age Allowance NRA 67 for men; women NRA 62 rising to 65 by 2024.",
                        "year": 2023,
                    },
                    "normal_retirement_age_female": {
                        "value": 62,
                        "source_citation": "OECD PAG 2023 Israel: women's NRA 62 in 2023; gradual increase to 65 by 2024.",
                        "year": 2023,
                    },
                },
                "benefits": {
                    "flat_rate_aw_multiple": {
                        "value": 0.155,
                        "source_citation": "OECD PAG 2023 Israel: basic Old Age Allowance ILS 1,726/month single (2023) × 12 = ILS 20,712 ≈ 15.5% of AW (ILS 133,700).",
                        "year": 2023,
                    },
                    "indexation": "CPI",
                },
                "payout": {
                    "type": "annuity",
                    "notes": "Monthly payment from National Insurance Institute (NII/Bituach Leumi); income supplement (hasha'lama) available for low-income pensioners.",
                },
            }
        ],
        "worker_type_updates": {},
    },

    # ── Poland ────────────────────────────────────────────────────────────
    # POL has ZUS NDC (Pillar 1) + OFE DC (Pillar 2). Already has 1 scheme. Missing: Minimum Pension guarantee (Pillar 0).
    {
        "iso3": "POL",
        "schemes": [
            {
                "scheme_id": "POL_MINIMALNA",
                "name": "Minimum Pension Guarantee (Emerytura Minimalna)",
                "tier": "first",
                "type": "minimum",
                "coverage": "Polish workers whose ZUS NDC pension falls below the guaranteed minimum and who have met minimum contribution years (20 women / 25 men)",
                "active": True,
                "eligibility": {
                    "normal_retirement_age_male": {
                        "value": 65,
                        "source_citation": "OECD PAG 2023 Poland: Minimum Pension Guarantee applies from NRA 65 for men (20 years contributions).",
                        "year": 2023,
                    },
                    "normal_retirement_age_female": {
                        "value": 60,
                        "source_citation": "OECD PAG 2023 Poland: Minimum Pension Guarantee from NRA 60 for women (25 years contributions).",
                        "year": 2023,
                    },
                },
                "benefits": {
                    "minimum_benefit_aw_multiple": {
                        "value": 0.149,
                        "source_citation": "OECD PAG 2023 Poland: minimum pension PLN 1,588/month (March 2023) × 12 = PLN 19,056 ≈ 14.9% of AW (PLN 128,000).",
                        "year": 2023,
                    },
                    "maximum_benefit_aw_multiple": {
                        "value": 0.149,
                        "source_citation": "Poland minimum pension: flat guarantee; applies only if earned pension is below this floor.",
                        "year": 2023,
                    },
                    "indexation": "mixed",
                },
                "payout": {
                    "type": "annuity",
                    "notes": "Tops up earned NDC pension to floor; funded from state budget top-up.",
                },
            }
        ],
        "worker_type_updates": {},
    },

    # ── Romania ───────────────────────────────────────────────────────────
    # ROU has DB pension (Pillar 1). Missing: Social Pension (Pillar 0).
    {
        "iso3": "ROU",
        "schemes": [
            {
                "scheme_id": "ROU_SOCIALPENSION",
                "name": "Social Indemnity (Indemnizația Socială) – Non-Contributory",
                "tier": "first",
                "type": "targeted",
                "coverage": "Romanian pensioners whose earned pension is below the social indemnity threshold; also non-contributors aged 65+; approximately 1.1 million recipients",
                "active": True,
                "eligibility": {
                    "normal_retirement_age_male": {
                        "value": 65,
                        "source_citation": "HG 1.174 Romania: Social Indemnity payable from age 65 (or pension age) to those below threshold.",
                        "year": 2023,
                    },
                    "normal_retirement_age_female": {
                        "value": 63,
                        "source_citation": "HG 1.174 Romania: women's pension age 63 in 2023 (rising to 65 by 2035).",
                        "year": 2023,
                    },
                },
                "benefits": {
                    "minimum_benefit_aw_multiple": {
                        "value": 0.138,
                        "source_citation": "CNPP Romania: Social Indemnity RON 1,125/month (2023) × 12 = RON 13,500 ≈ 13.8% of AW (RON 97,800).",
                        "year": 2023,
                    },
                    "maximum_benefit_aw_multiple": {
                        "value": 0.138,
                        "source_citation": "Romania social indemnity: flat floor; earned pension tops up if below threshold.",
                        "year": 2023,
                    },
                    "indexation": "CPI",
                },
                "payout": {
                    "type": "annuity",
                    "notes": "Monthly payment from CNPP; tops up contributory pension to social minimum; includes housing allowance.",
                },
            }
        ],
        "worker_type_updates": {},
    },

    # ── Indonesia ─────────────────────────────────────────────────────────
    # IDN has Jaminan Pensiun (DB) + JHT (DC). Missing: Program Keluarga Harapan/elderly social pension (Pillar 0).
    {
        "iso3": "IDN",
        "schemes": [
            {
                "scheme_id": "IDN_ASLUT",
                "name": "Social Assistance for Elderly (Asistensi Lanjut Usia) – Non-Contributory",
                "tier": "first",
                "type": "targeted",
                "coverage": "Indonesian poor elderly aged 60+ not covered by BPJS; approximately 2.8 million recipients (2023); Program Asistensi Sosial Lanjut Usia Telantar",
                "active": True,
                "eligibility": {
                    "normal_retirement_age_male": {
                        "value": 60,
                        "source_citation": "Kemensos Indonesia: Asistensi Lanjut Usia (ASLUT) for poor elderly 60+ without formal pension coverage.",
                        "year": 2023,
                    },
                    "normal_retirement_age_female": {
                        "value": 60,
                        "source_citation": "Kemensos Indonesia: ASLUT NRA 60 for both sexes.",
                        "year": 2023,
                    },
                },
                "benefits": {
                    "minimum_benefit_aw_multiple": {
                        "value": 0.014,
                        "source_citation": "Kemensos Indonesia: ASLUT IDR 300,000/month × 12 = IDR 3,600,000 ≈ 1.4% of AW (IDR 252,000,000).",
                        "year": 2023,
                    },
                    "maximum_benefit_aw_multiple": {
                        "value": 0.014,
                        "source_citation": "Indonesia ASLUT: flat means-tested transfer.",
                        "year": 2023,
                    },
                    "indexation": "CPI",
                },
                "payout": {
                    "type": "annuity",
                    "notes": "Monthly transfer via post offices/digital; targeted at poor elderly in DTKS (integrated social data); funded from central government budget.",
                },
            }
        ],
        "worker_type_updates": {},
    },

]


# ---------------------------------------------------------------------------
# Apply updates
# ---------------------------------------------------------------------------

def load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def save_yaml(path: Path, data: dict) -> None:
    with open(path, "w") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False, width=120)


def apply_updates(dry_run: bool = False) -> None:
    updated = []
    skipped = []

    for entry in MISSING_SCHEMES:
        iso3 = entry["iso3"]
        path = PARAMS_DIR / f"{iso3}.yaml"

        if not path.exists():
            print(f"  SKIP  {iso3}: params file not found")
            skipped.append(iso3)
            continue

        data = load_yaml(path)
        existing_ids = {s["scheme_id"] for s in data.get("schemes", [])}
        added = []

        for scheme in entry["schemes"]:
            sid = scheme["scheme_id"]
            if sid in existing_ids:
                print(f"  SKIP  {iso3}/{sid}: already present")
                continue
            if not dry_run:
                data.setdefault("schemes", []).append(scheme)
            added.append(sid)
            existing_ids.add(sid)

        # Update worker_types.scheme_ids
        for wtype, scheme_ids_to_add in entry.get("worker_type_updates", {}).items():
            wt = data.get("worker_types", {}).get(wtype)
            if wt is None:
                continue
            existing_wt_ids = list(wt.get("scheme_ids", []))
            for sid in scheme_ids_to_add:
                if sid not in existing_wt_ids:
                    existing_wt_ids.append(sid)
                    if not dry_run:
                        wt["scheme_ids"] = existing_wt_ids

        if added:
            if not dry_run:
                save_yaml(path, data)
            updated.append((iso3, added))
            print(f"  OK    {iso3}: added {added}")
        else:
            print(f"  NOOP  {iso3}: nothing to add")

    print(f"\nDone. Updated {len(updated)} countries, skipped {len(skipped)}.")
    if updated:
        iso3_list = " ".join(iso3 for iso3, _ in updated)
        print(f"\nRebuild with:\n  pp build-deep-profiles -c \"{iso3_list}\"")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("DRY RUN — no files will be modified\n")
    apply_updates(dry_run=dry_run)
