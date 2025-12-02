# app/billing/routes.py
from flask import render_template, current_app, request, redirect, url_for, flash
from flask_login import login_required, current_user
from flask import Blueprint

from ..subscriptions import PLANS, get_plan, apply_plan
from ..extensions import razorpay_client

billing_bp = Blueprint("billing", __name__, url_prefix="/billing")


@billing_bp.route("/pricing")
@login_required
def pricing():
    return render_template(
        "billing/pricing.html",
        plans=PLANS,
        current_plan=current_user.plan
    )


@billing_bp.route("/subscribe/<plan_key>", methods=["GET"])
@login_required
def subscribe(plan_key):
    if plan_key not in PLANS or plan_key == "free":
        flash("Invalid plan.", "danger")
        return redirect(url_for("billing.pricing"))

    plan = get_plan(plan_key)
    amount_paisa = plan["price_inr"] * 100  # Razorpay uses paise

    # Create Razorpay order
    order = razorpay_client.order.create({
        "amount": amount_paisa,
        "currency": "INR",
        "payment_capture": 1
    })

    return render_template(
        "billing/checkout.html",
        plan_key=plan_key,
        plan=plan,
        razorpay_key=current_app.config['RAZORPAY_KEY_ID'],
        order=order
    )


@billing_bp.route("/payment/callback", methods=["POST"])
@login_required
def payment_callback():
    data = request.form

    params_dict = {
        "razorpay_order_id": data.get("razorpay_order_id"),
        "razorpay_payment_id": data.get("razorpay_payment_id"),
        "razorpay_signature": data.get("razorpay_signature"),
    }

    plan_key = data.get("plan_key")

    if plan_key not in PLANS:
        flash("Invalid plan key.", "danger")
        return redirect(url_for("billing.pricing"))

    try:
        razorpay_client.utility.verify_payment_signature(params_dict)
    except Exception:
        flash("Payment verification failed.", "danger")
        return redirect(url_for("billing.pricing"))

    apply_plan(current_user, plan_key)
    flash(f"Subscribed to {PLANS[plan_key]['name']} plan!", "success")
    return redirect(url_for("billing.pricing"))
