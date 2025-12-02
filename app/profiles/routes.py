import os
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from . import profiles_bp
from ..extensions import db


@profiles_bp.route("/me", methods=["GET", "POST"])
@login_required
def me():
    user = current_user

    if request.method == "POST":
        user.year = request.form.get("year")
        user.branch = request.form.get("branch")
        user.bio = request.form.get("bio")
        user.interests = request.form.get("interests")
        user.looking_for = request.form.get("looking_for")

        file = request.files.get("photo")
        if file and file.filename:
            filename = f"user_{user.id}_{file.filename}"
            path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            user.photo = filename

        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("profiles.me"))

    return render_template("profiles/me.html", user=user)
