# 📣 GoodBooks — Social Launch Kit for Testing

> **Goal**: get real readers testing the app and capturing feedback fast.
> **Link to share**: `https://goodbooks-recommender.pages.dev`
> **When**: run `npm run deploy` first (see README), then use the copy below.

---

## 1. Which platform, and why (thought through)

The app's core moment is **"tell us what you love → get personalized picks with reasons."**
So the best testing platforms are where *high-intent readers already ask for recommendations*.

| Platform | Fit for testing | Verdict |
|---|---|---|
| **Reddit — r/suggestmeabook & r/books** | 🟢 **Best**. Users literally post "recommend me a book like X" all day. Our value prop is the direct answer. Direct links allowed; high-intent traffic; free. | **Primary** |
| **Discord reading servers** | 🟢 Great for *feedback* — small groups, deep conversations, bug reports. | **Secondary (beta testers)** |
| **Twitter / X (#BookTwitter)** | 🟡 Good reach + easy link sharing; strong for the "AI + reading" angle and for creators to share the OG card. | **Secondary (reach)** |
| **Instagram / TikTok (BookTok)** | 🟡 Massive audience but *link-in-bio* friction; visual-first — our covers/onboarding are camera-worthy. | Later phase |
| **LinkedIn** | 🔴 Wrong audience for a reading app. | Skip |
| **Goodreads groups** | 🔴 Amazon-owned; promo rules strict, risk of removal. | Skip |

**Recommendation**: launch testing on **Reddit** (r/suggestmeabook, r/books, r/booksuggestions) + a
**Discord** server. These deliver the highest-quality testers with the least friction.

---

## 2. Ready-to-post copy

### Reddit (r/suggestmeabook / r/booksuggestions)
> Posting self-promo? Respect each subreddit's rules — many allow it with a clear disclosure.

**Title**: I built a free tool that recommends books based on your taste — with reasons why

**Body**:
> Hey readers! I've been frustrated by generic "everyone loves this" recommendations, so I
> built **GoodBooks** — a free, private reading companion.
>
> 🎯 You pick your favorite genres (takes 30 seconds) and it ranks books for *you*, telling you
> *why* each one ("because you love Science Fiction").
> 🤖 There's also an AI assistant — ask "what should I read next?" in plain language.
> 📚 Track goals, wishlists, and your reading shelf.
>
> **Try it**: https://goodbooks-recommender.pages.dev
>
> It's early-stage, so feedback is hugely appreciated — especially "these recs are off, here's
> why." What's a book you loved and did the tool get it right? 👇

### Twitter / X
> 🚀 I made a thing: **GoodBooks** — personalized book recommendations that tell you *why*.
> Pick your genres → get a shelf ranked for your taste → ask the AI "what next?"
>
> Free, private, no signup spam. Try it: https://goodbooks-recommender.pages.dev
>
> `#BookTwitter #reading #books #AI #readercommunity`

### Discord (intro message to a reading server / beta channel)
> 👋 Hey everyone — I built **GoodBooks**, a personalized book recommendation app, and I'm
> looking for beta testers. It learns your taste from a 30-second quiz and explains every pick.
>
> **Link**: https://goodbooks-recommender.pages.dev
>
> **What would help most**: create an account → pick your genres → tell me (1) which
> recommendations felt *right*, (2) which felt *off*, and (3) anything that confused you.
> Bug reports welcome — screenshots are gold. Thanks for helping shape it! 📚

---

## 3. Shareable link & previews

- **Canonical link**: `https://goodbooks-recommender.pages.dev`
- **Social preview card**: the `og:image` (`/og-cover.png`, 1200×630) + title/description render
  automatically on Twitter/X, Facebook, LinkedIn, WhatsApp, iMessage, Slack, Discord.
- **Verify the preview before posting**:
  - X: https://cards-dev.twitter.com/validator (paste link)
  - OpenGraph: https://www.opengraph.xyz/ (paste link)
  - LinkedIn: paste into a post draft and check the preview thumbnail.

> If you attach a custom domain, update `index.html` (`og:url`, `og:image`, canonical) to the
> new URL and rebuild.

---

## 4. Tester onboarding checklist (what to ask testers to try)

1. Open the link → complete the 3-step onboarding (welcome → account → taste quiz).
2. On the Dashboard, check the "Personalized for you" picks — do the reasons make sense?
3. Try Discover → is the "Personalized for you" badge showing? Do the top picks match your taste?
4. Open the AI assistant (`⌘K`) → ask "recommend me a book" → do the suggestion cards render?
5. Toggle dark mode, save a book to your wishlist, and check the Wishlist page.
6. Reload the page — are you still signed in? (accounts persist in the browser; a database-backed
   sync is active when Supabase is configured — see `docs/SUPABASE_ACCOUNTS.md`.)

## 5. Feedback capture

- Create a simple feedback channel: `#feedback` on Discord, or a pinned comment on the post.
- Track: activation funnel (who completed the quiz), recommendation CTR, and the two questions
  above ("right / off / confusing") — see `docs/USER_GROWTH.md` for the metrics that matter.
