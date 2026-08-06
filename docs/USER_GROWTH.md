# 📈 GoodBooks — Monthly Active Users Generation Strategy

> **Goal**: Take GoodBooks from launch to a repeatable monthly-active-user engine.
> This plan treats the onboarding + personalization features as the product's growth
> engine: every new account gets a personalized experience in under a minute — the
> "aha moment" that drives activation and word-of-mouth.
>
> **Date**: 2026-08-06 · **Owner**: Growth / Product

---

## 1. North-Star Metric & Targets

**North star**: *Weekly Active Readers with ≥1 personalized pick saved* (engagement that
compounds: saved picks → better recommendations → return visits).

### Monthly active user (MAU) ramp — 12 months

| Month | MAU target | Focus | Primary channel |
|---|---|---|---|
| 1–2 | 500–1,000 | Seed & validate (closed beta, BookTok/Discord) | Direct / community seeding |
| 3–4 | 2,000–5,000 | Content-led acquisition (blog, "best books for X") | SEO + social |
| 5–6 | 8,000–15,000 | Partnership + referral loop | Book clubs, newsletters, influencers |
| 7–9 | 20,000–40,000 | Product-led growth (shareable Wrapped, club invites) | Viral loops |
| 10–12 | 60,000–120,000 | Scale (paid acquisition on proven cohorts) | Paid + organic mix |

**Reality check**: book platforms are habit-forming but slow to acquire. Goodreads has ~19M
active users after a decade+; StoryGraph grew via community. Our wedge is **explainable,
instant personalization** — the fastest "wow" in the category.

---

## 2. The Activation Funnel (map to the product)

| Step | Product moment | Metric to hit |
|---|---|---|
| Landing | Beautiful dashboard teaser | bounce < 45% |
| **Account creation** | 3-step onboarding (welcome → account → taste quiz) | 80% of visits start it |
| **Taste quiz complete** | ≤ 60 seconds, pick ≥ 1 genre | 70% complete |
| **First "aha"** | Personalized picks with reasons ("Because you love Sci-Fi") | ≥ 3 picks seen, < 5s render |
| **First save** | Heart a pick / add to wishlist | 40% save within session |
| **AI assistant** | Ask "what should I read next?" | 25% try it in week 1 |

**The product was built for this**: onboarding → personalization → reasons → saves → the AI
assistant is the retention hook. Every percentage point in "taste quiz complete" compounds.

---

## 3. Acquisition Channels (ranked by fit)

### 3.1 Community seeding (Month 1–2) — highest trust per dollar
- **Book clubs & Discord servers** (r/books, book club discords): share the onboarding as "the
  30-second taste test" — irresistible and cheap.
- **BookTok / Bookstagram micro-influencers** (5–20K followers): gift access + a "personalized
  top-10 for your followers" campaign they can reshare.
- **University/humanities programs**: the "who am I as a reader" angle resonates with students.

### 3.2 Content marketing (Month 3–4) — compounding
- SEO landing pages: *"Best [genre] books like [popular title]"* — powered by our catalog +
  explanations (we can auto-generate these from the recommendation engine).
- Data-led posts: "What 2.4M Goodreads readers actually finish" — our explainability data is
  the hook.
- Weekly newsletter: "Your reading mood of the week" with personalized picks (drives return).

### 3.3 Product-led growth (Month 5+)
- **Shareable Year-in-Books "Wrapped"** (roadmap feature): users share a beautiful recap →
  viral acquisition loop.
- **Book club invites**: clubs get group recommendations; each new member pulls in their club.
- **Referral**: "Invite a friend, both get a personalized reading report."

### 3.4 Paid (Month 10+ — only after cohorts prove LTV)
- Test on 1–2 proven acquisition cohorts (e.g., self-improvement readers who convert to the
  reading-goal feature). CAC < ⅓ of 6-month LTV before scaling.

---

## 4. Retention Loops (why users come back)

| Loop | Mechanism | Retention metric |
|---|---|---|
| **Taste loop** | Every save/rating sharpens the ranking → better picks → more saves | D30 retention ≥ 30% |
| **Companion loop** | AI assistant asks "what are you in the mood for?" on return | Weekly active chat ≥ 2 msgs |
| **Goal loop** | Reading goals + streak + milestone celebrations | Weekly goal check-ins |
| **Discovery loop** | "New for you" refresh + mood sliders | Weekly browse sessions |
| **Social loop** *(roadmap)* | Clubs + wrapped share | Invites per user ≥ 0.5/yr |

Target: **D30 retention ≥ 30%** (healthy for content apps; Goodreads is ~20% D30).

---

## 5. Instrumentation (build before scaling)

- **Event tracking** (frontend, privacy-respecting): `onboarding_started`, `quiz_completed`,
  `recommendation_viewed`, `recommendation_saved`, `assistant_message`, `goal_progress`,
  `wrapped_shared`.
- **Funnel dashboard**: conversion at each activation step (see §2).
- **Quality metric**: **Recommendation CTR** — % of personalized picks saved/clicked. Target
  ≥ 15% (industry rec CTR is 5–10%; explainable recs over-index).
- **NPS / satisfaction**: in-app 1-tap rating after the 5th save ("how well did we know you?").

---

## 6. 90-Day Execution Plan

| Week | Action | Owner |
|---|---|---|
| 1–2 | Seed 100 trusted beta users; instrument activation events | Product |
| 3–4 | Fix funnel leaks (taste-quiz drop-off, first-save friction); measure CTR | Growth + Eng |
| 5–6 | Launch 10 SEO "best [genre] books" pages; ship newsletter signup | Content |
| 7–8 | Recruit 5 micro-influencers; measure trial → save conversion | Growth |
| 9–10 | Ship referral loop + "personalized report" share card | Eng |
| 11–12 | Review cohort LTV; set paid acquisition budget (if proven) | Growth |

---

## 7. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Onboarding friction (users skip quiz) | Keep quiz ≤ 60s; allow "surprise me" default profile |
| Recommendation quality perceived as "canned" | Transparency: show reasons; let users tune genres anytime |
| Backend ML not yet live | Client personalization already delivers value; backend upgrades silently |
| Cold-start trust (no social proof) | Ratings count + "loved by readers" badges on cards |
| Seasonality (reading spikes in Jan/Sept) | Plan launches around New Year resolutions & back-to-school |

---

## 8. TAM & monetization recap (context)

- Book recommendation SaaS niche: **$2–5B TAM**; 5-year realistic goal 2–5M MAU.
- Freemium: Free (ads + affiliate) → Plus $4.99/mo (unlimited AI) → Pro $9.99/mo (research +
  API). At 2M MAU with 8% Plus conversion → ~$7–15M ARR.
- **Growth precedes monetization**: the plan above targets MAU first; pricing lands at
  Month 6+ once retention ≥ 30% is proven.

---

*See `docs/PROJECT_STATUS.md` for product status and `docs/DEPLOYMENT_PLAN.md` for the
engineering roadmap that supports this growth.*
