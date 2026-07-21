# Opportunity Sources

The MVP catalog is a hand-curated research aid, not a complete directory,
eligibility engine, recommendation, or representation that an organization is
accepting applications. Each entry is based on the official page linked from
the result card. Public positioning was rechecked on **2026-07-17**. Founders
must verify live terms, geography, application timing, capacity, eligibility,
and conflicts directly with each organization.

## Catalog coverage

| Opportunity | Basis for inclusion | Official source checked |
| --- | --- | --- |
| Techstars AI Health Baltimore; Alabama EnergyTech; Anywhere | Techstars lists accelerators, including these general and specialized options. | https://www.techstars.com/accelerators |
| Y Combinator | YC's application/FAQ pages describe a global application process, funding from the idea stage, and the batch program. | https://www.ycombinator.com/apply.html |
| CDL AI; Computational Health | CDL publishes its AI and Computational Health streams. | https://creativedestructionlab.com/streams/ |
| HAX | HAX describes work with pre-seed hard-tech companies across computing, energy, health, manufacturing, and transportation. | https://hax.co/ |
| MassChallenge UK; Switzerland | MassChallenge’s program pages describe their early-stage programs, sector focus, and location-specific application details. | https://masschallenge.org/programs-united-kingdom/ and https://masschallenge.org/programs-switzerland/ |
| Alchemist Japan | Alchemist describes a three-month, Tokyo-based program for technical, B2B enterprise startups with global potential. | https://www.alchemistaccelerator.com/japan |
| America’s Seed Fund powered by NSF | NSF describes non-dilutive R&D funding for startups and small businesses. | https://seedfund.nsf.gov/our-program/ |
| EIC Accelerator | The European Innovation Council describes grants, equity, and blended-finance support for eligible startups and SMEs. | https://eic.ec.europa.eu/eic-funding-opportunities/eic-accelerator_en |
| AWS Activate | AWS describes its startup program, credits, technical support, and tiers. | https://aws.amazon.com/startups/ |
| Google for Startups Cloud Program | Google describes cloud credits, startup support, tiers, and exclusions. | https://cloud.google.com/startup/faq |
| Microsoft for Startups | Microsoft describes technical guidance, AI resources, and enterprise-readiness support for startups. | https://learn.microsoft.com/en-us/startups/ |
| NVIDIA Inception | NVIDIA describes a startup program for AI and accelerated-computing companies. | https://www.nvidia.com/en-us/startups/ |
| Andreessen Horowitz (a16z) | a16z publicly describes multi-stage technology investing across AI, bio and healthcare, consumer, crypto, enterprise, fintech, games, infrastructure, and American dynamism. | https://a16z.com/about/ |
| DCVC | DCVC’s official site describes its deep-tech investment focus across AI, compute, climate, biotech, cybersecurity, and manufacturing. | https://www.dcvc.com/ |
| Pantera Capital | Pantera describes its blockchain-focused venture-equity and early-stage token strategies. | https://panteracapital.com/ |
| Multicoin Capital | Multicoin publicly describes investments in FHE and cryptographic-primitives companies. | https://multicoin.capital/2024/03/07/the-holy-grail-of-cryptography/ |

No commercial directory has been scraped or redistributed.

## Audited public facts

`opportunity_facts.json` is a deliberately separate, source-backed layer for
published eligibility, program format, funding model, and thesis facts. It now
has one audited record for every catalog entry. It does not silently convert a
marketing claim into a scoring input. Run `make validate-data` to report
catalog and facts coverage.

## Starter conflict registry

The local resolver recognizes **54 company and protocol names**, with aliases
for common spelling variants. It contains publicly documented relationships for
four catalog investors: Multicoin (FHE and on-chain privacy); Pantera
(blockchain infrastructure); a16z (crypto plus AI, data, biotech, health,
climate, security, enterprise, fintech, consumer, and marketplace companies);
and DCVC (AI, biotech, climate, food/agriculture, robotics, security, data,
and advanced hardware). The versioned data and exact primary sources are in
[conflict_registry.json](conflict_registry.json). The registry is intentionally
private in the product flow: a founder may type a name, but is not shown its
coverage or another party's relationship map.

## Deliberate demo limitations

The six numeric fit fields are a transparent, hand-authored demonstration
rubric; they are **not** claims about program terms, investment preferences,
eligibility, or decision-making. The conflict registry is deliberately
incomplete and should never be treated as a comprehensive portfolio, absence
of a conflict, or investment recommendation. Only the four documented
relationship maps in `conflict_registry.json` are screened.
