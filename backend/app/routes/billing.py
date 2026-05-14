import logging
from fastapi import APIRouter, Request, HTTPException, Header
from pydantic import BaseModel
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

PLANS = {
    "starter":      {"name": "Starter",      "price_eur": 49,  "price_id": "price_starter"},
    "professional": {"name": "Professional", "price_eur": 149, "price_id": "price_professional"},
    "enterprise":   {"name": "Enterprise",   "price_eur": 499, "price_id": "price_enterprise"},
}


class CheckoutRequest(BaseModel):
    plan: str
    success_url: str = "http://localhost:3000/dashboard?payment=success"
    cancel_url: str = "http://localhost:3000/dashboard?payment=cancelled"


@router.get("/plans")
async def list_plans():
    return {"plans": list(PLANS.values())}


@router.post("/checkout")
async def create_checkout_session(body: CheckoutRequest):
    """Create a Stripe Checkout Session for the requested plan."""
    if not settings.STRIPE_SECRET_KEY or settings.STRIPE_SECRET_KEY == "sk_test_xxxxxxxxxxxxxxxxxx":
        raise HTTPException(
            status_code=503,
            detail="Stripe no está configurado. Añade STRIPE_SECRET_KEY al .env",
        )

    plan = PLANS.get(body.plan)
    if not plan:
        raise HTTPException(status_code=400, detail=f"Plan desconocido: {body.plan}")

    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": plan["price_id"], "quantity": 1}],
            mode="subscription",
            success_url=body.success_url,
            cancel_url=body.cancel_url,
        )
        logger.info(f"[Billing] Checkout session creada: {session.id} — plan {body.plan}")
        return {"session_id": session.id, "url": session.url}

    except Exception as exc:
        logger.error(f"[Billing] Error creando checkout: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
):
    """Handle Stripe webhook events (payment confirmations, cancellations)."""
    if not settings.STRIPE_WEBHOOK_SECRET or settings.STRIPE_WEBHOOK_SECRET == "whsec_xxxxxxxxxxxxxxxxxx":
        raise HTTPException(status_code=503, detail="Stripe webhook secret no configurado")

    payload = await request.body()

    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as exc:
        logger.warning(f"[Billing] Webhook signature inválida: {exc}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]
    logger.info(f"[Billing] Webhook recibido: {event_type}")

    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        customer_email = session.get("customer_details", {}).get("email", "unknown")
        plan_amount = session.get("amount_total", 0)
        logger.info(f"[Billing] Pago completado — {customer_email}, {plan_amount/100:.2f}€")
        # TODO: activate subscription in DB, send welcome email

    elif event_type in ("customer.subscription.deleted", "invoice.payment_failed"):
        logger.info(f"[Billing] Suscripción cancelada/fallida — {event['data']['object'].get('id')}")
        # TODO: downgrade user to free tier

    return {"received": True, "type": event_type}
