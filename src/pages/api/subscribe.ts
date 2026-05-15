/* ===========================================================================
 * src/pages/api/subscribe.ts
 * Rhymes & Poetry — subscribe form handler (Astro endpoint)
 *
 * Handles POST submissions from both:
 *   - src/components/Subscribe.astro (inline block, every page)
 *   - src/pages/subscribe.astro      (dedicated /subscribe page)
 *
 * Flow:
 *   1. Validate honeypot ("website" field) — if filled, drop silently (bot)
 *   2. Validate email shape
 *   3. If NEWSLETTER_USERNAME is set, forward to Buttondown (durable storage
 *      of the subscriber list — Buttondown handles confirmation emails,
 *      unsubscribes, GDPR exports, etc.)
 *   4. Redirect to /subscribed (thank-you page)
 *
 * NOTE on persistence:
 * Until Buttondown is wired (set NEWSLETTER_USERNAME in src/consts/newsletter.ts),
 * submitted emails are NOT persisted anywhere — the redirect happens but the
 * email is dropped on the floor. This is intentional during pre-launch:
 * better to lose pre-launch signups than to maintain a homemade DB.
 *
 * If you want to also keep a Cloudflare-side copy of every signup
 * (independent of Buttondown), add Cloudflare D1 or KV bindings in
 * wrangler.toml and add a write step before the Buttondown forward —
 * see TODO marker below.
 * ========================================================================= */

import type { APIRoute } from "astro";
import { NEWSLETTER_USERNAME } from "../../consts/newsletter";

export const prerender = false;

const THANK_YOU_URL = "/subscribed";

function isLikelyEmail(value: string): boolean {
	// Lightweight check; real validation happens by Buttondown sending the
	// confirmation email. We're just filtering obvious garbage.
	return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value) && value.length <= 254;
}

export const POST: APIRoute = async ({ request, redirect }) => {
	let formData: FormData;
	try {
		formData = await request.formData();
	} catch {
		return new Response("Bad request", { status: 400 });
	}

	// Bot check — silent drop, redirect anyway so the bot can't probe.
	const honeypot = formData.get("website");
	if (typeof honeypot === "string" && honeypot.trim() !== "") {
		return redirect(THANK_YOU_URL, 303);
	}

	const emailRaw = formData.get("email");
	const email = typeof emailRaw === "string" ? emailRaw.trim() : "";
	if (!isLikelyEmail(email)) {
		return new Response("Invalid email", { status: 400 });
	}

	// TODO(persistence): if you want a redundant Cloudflare-side log of
	// every signup, write to D1 or KV here before the Buttondown forward.
	// Example with KV (after binding SUBSCRIBERS_KV in wrangler.toml):
	//   const env = (locals as any).runtime?.env;
	//   await env.SUBSCRIBERS_KV.put(email, new Date().toISOString());

	// Forward to Buttondown if wired up. Their endpoint handles the durable
	// storage, double-opt-in, unsubscribe, and GDPR mechanics so we don't
	// have to.
	if (NEWSLETTER_USERNAME) {
		try {
			const body = new URLSearchParams();
			body.set("email", email);
			body.set("embed", "1");
			await fetch(
				`https://buttondown.com/api/emails/embed-subscribe/${NEWSLETTER_USERNAME}`,
				{
					method: "POST",
					headers: {
						"Content-Type": "application/x-www-form-urlencoded",
					},
					body,
				}
			);
		} catch (err) {
			// Don't block the user on Buttondown being slow/down. Log only.
			console.error("Buttondown forward failed:", err);
		}
	}

	return redirect(THANK_YOU_URL, 303);
};
