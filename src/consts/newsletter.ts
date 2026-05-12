/* ===========================================================================
 * src/consts/newsletter.ts
 * Rhymes & Poetry — newsletter provider configuration
 *
 * Single source of truth for the subscribe form's action URL. Both the
 * inline Subscribe component (home + blog post pages) and the dedicated
 * /subscribe page import from here. Change one constant; both surfaces
 * update.
 *
 * Provider: Buttondown (https://buttondown.com)
 *   - $9/mo under 1000 subscribers
 *   - Form submits via standard HTML POST — no third-party JS in our page
 *   - Markdown-native email composition
 *   - Single embed URL: api/emails/embed-subscribe/{username}
 *
 * To activate:
 *   1. Sign up at buttondown.com
 *   2. Pick your username (this becomes part of public URLs — make it
 *      memorable. Suggested: rhymesandpoetry or rhymesandpoetry-jtc)
 *   3. Replace the empty string below with your username
 *   4. Push. The form starts working immediately on the next deploy.
 *
 * Until NEWSLETTER_USERNAME is set, the form silently no-ops on submit
 * (action="#") — no broken submissions, no errors. Visitors who try will
 * see the page reload but nothing happen, which is acceptable for a
 * pre-launch state.
 *
 * Push tie-in: this is a clean integration pattern for any third-party
 * SaaS — provider config in one file, surface code references it by
 * name. Migrating later (e.g., to ConvertKit) means changing this one
 * file, not chasing endpoint URLs across the codebase.
 * ========================================================================= */

// TODO(setup): replace with your Buttondown username after signing up
export const NEWSLETTER_USERNAME = "";

export const NEWSLETTER_PROVIDER = "buttondown" as const;

// Computed form action URL. If username isn't set yet, "#" (no-op submit).
export const NEWSLETTER_ACTION_URL = NEWSLETTER_USERNAME
	? `https://buttondown.com/api/emails/embed-subscribe/${NEWSLETTER_USERNAME}`
	: "#";

// When the form is wired to a real provider, submission opens a popup
// window with their confirmation page. Until then, default to same-window
// (no-op behavior).
export const NEWSLETTER_SUBMIT_TARGET = NEWSLETTER_USERNAME
	? "popupwindow"
	: "_self";

// Subscribe-confirmation URL the popup loads after submit. Buttondown
// shows a "thanks for subscribing" page at /{username}.
export const NEWSLETTER_CONFIRM_URL = NEWSLETTER_USERNAME
	? `https://buttondown.com/${NEWSLETTER_USERNAME}`
	: "";

// Whether the integration is wired up. Lets components render different
// states (e.g., hide the form entirely if not yet set up — but for now
// we render it disabled-but-present so visitors know it's coming).
export const NEWSLETTER_IS_LIVE = !!NEWSLETTER_USERNAME;
